"""
FileName: job_posting_worker.py.

Purpose: JobPosting Worker which encapsulates all the work for processing
the job posting data.
"""

import json
import traceback
import intai.config as config
import requests
from intai.config import load_weightage_config
from intai.ml.llm_client import LLMClient
from intai.ml.openai_client import OpenAIClient
from intai.ml.scoring_utils import get_ideal_candidate_score_for_job
from intai.ml.ai_prompt import JobPostingAIPrompt
from intai.models.models import (
    JobPostingDb,
    JobPostingSkillDb,
    SkillDb,
    BackgroundTaskDb,
)
from intai.schemas.job_posting import JobPosting
from intai.utils.file_utils import extract_text, get_bytes_from_url
from loguru import logger


class JobPostingWorker:
    """
    JobPostingWorker Class.

    This class processes the job posting and executes the pipeline.
    NOTE: This will process the work in the background task.
    """

    def __init__(self, jobPosting: JobPosting, session, task_id):
        """Init method for the class."""
        logger.info(f"JobPostingWorker is initialized {jobPosting}")
        self.db = session
        self.task_id = task_id
        self.jobPosting = jobPosting
        self.company_id = jobPosting.company_id
        self.jobPostingDb = JobPostingDb(self.jobPosting)
        self.jobPostingDb.status = "Started"

    def __repr__(self) -> str:
        return "<JobPostingWorker: company_id:{}; job_posting: {}; >".format(
            self.company_id,
            self.jobPostingDb,
        )

    def insert_update_entities(self, is_update: bool = False):
        """Insert or Update JobPostingDb entity.

        NOTE: In case of Update it will delete jobposting and jp_skills db
        as well."""
        try:
            logger.info(
                f"{is_update}; {'Update' if is_update else 'Insert'} JobPosting Entity"
            )

            if is_update:
                JobPostingDb.delete_entities(
                    self.db, self.company_id, self.jobPosting.client_job_id
                )

            # Store the jobposting data in the table
            self.jobPostingDb.insert_job_posting(self.db)
            logger.debug(f"jobPosting after insert: {self.jobPostingDb}")

        except Exception as err:
            logger.error(
                f"Exception while inserting or updating jobposting entity: {err}\n JobPostingWorker: {self}"
            )
            raise err

    def extract_save_entities(self):
        """Extract the entities from the JobPosting and store in database.

        This will either make the call to OpenAI and get the parsed json (and
        save the embedding, parsed json and input text for later in vector db)
        or will get the cached json from vector db based on previously retrieved
        json by using text embedding.

        Returns the entity (which is basically gpt response with
        parsed json for job posting).
        """
        try:
            bytes_data, docType = get_bytes_from_url(
                self.jobPosting.job_posting_doc_url,
            )
            extracted_text = extract_text(bytes_data, docType)

            # Call OpenAI directly. Previously we were using the cached entities
            # but now we are always call openAI.
            # NOTE: For repeat calls if job posting is not changing in future
            # we can store a checksum in db and decide that to determine
            # whether to call openai or not.
            ai_client = LLMClient(session_id=self.task_id, client_id=self.company_id)
            prompt = JobPostingAIPrompt(jp_text=extracted_text)
            extracted_entities = ai_client.get_model_response(prompt)

            self.jobPostingDb.update_job_posting(
                self.db,
                parsed_jd=extracted_entities,
                extracted_text=extracted_text,
                status="Extracted Entities",
            )

            return extracted_entities
        except Exception as err:
            logger.error(
                f"Exception while extracting entitites: {err}\n JobPosting: {self}"
            )
            raise err

    def extract_save_skill_names(self, parsed_skills):
        """Extract the skill names from skill list."""
        logger.debug(f"Parsed Skills: {parsed_skills}")
        try:
            skills = [
                skill["skillName"] for skill in parsed_skills if "skillName" in skill
            ]
            logger.debug(skills)

            # filter out the ones already in db.
            existing_skills = SkillDb.get_skills(self.db, self.company_id, skills)

            existing_skill_names = [x.skill_name for x in existing_skills]
            logger.debug(f"existing skills from db: {existing_skill_names}")
            new_skills = [x for x in skills if x not in existing_skill_names]
            logger.debug(f"new skills from this session {new_skills}")

            # insert the new skills in skills Table in Db.

            # TODO #A: Check if this is still needed?
            # open_ai_client = LLMClient(model=LLMModelType.EMBEDDING_ADA, session_id=self.task_id, client_id=self.company_id)
            # TODO: We are not calcualting standardized skill names anymore.
            # standardized_new_skills = find_cluster_center_skills(new_skills, open_ai_client)

            # NOTE: List of Tuple where first entry in tuple is skill_name
            # and second is standard skill name.
            skills_list = list(zip(new_skills, new_skills))
            SkillDb.insert_skills_no_duplicates(self.db, self.company_id, skills_list)
            return new_skills
        except Exception as err:
            logger.error(
                f"Exception while extracting save skill names: {err}\n JobPosting: {self}"
            )
            raise err

    def calc_save_candidate_score(self, skills, experience):
        """Calculate the ideal candidate score and save in db."""
        try:
            weightage_dict = load_weightage_config()
            logger.debug(f"{weightage_dict}")
            logger.debug(f"{skills} {experience}")

            # skill_cum_score is a dict
            total_cum_score, skill_cum_scores = get_ideal_candidate_score_for_job(
                skills, experience, weightage_dict
            )
            logger.debug(f"{total_cum_score} skill_cum_scores:{skill_cum_scores}")

            # NOTE: We have to store all skill scores and skills in JobPostingDb
            # not just the new ones.
            JobPostingSkillDb.insert_many(
                self.db, self.company_id, self.jobPostingDb.id, skill_cum_scores
            )

            self.jobPostingDb.update_ideal_candidate_score(self.db, total_cum_score)

        except Exception as err:
            logger.error(
                f"Exception while calcuating candidate score: {err}\n JobPosting: {self}"
            )
            raise err

    def update_frontend_status(self, status: str, progress: int):
        """Send the frontend with status update.

        NOTE: In case of error it just logs the error and returns false
        """
        logger.trace(
            f"updating front end for {self.jobPosting.client_job_id} with status: {status}"
        )
        try:
            # This states need to match in front end as well.
            assert status in ["INIT", "SUBMITTED", "WORKING", "PROCESSED", "ERROR"]

            url = f"{config.FRONT_END_URL}/api/jobs/{self.jobPosting.client_job_id}"
            data = {"processingStatus": status, "processingStatusProgress": progress}
            logger.info(f"calling {url} with {data}")
            response = requests.put(url, json=data)
            logger.info(f"response: {response.content} {response.status_code}")
            response.raise_for_status()
            return True
        except Exception as err:
            # Log the error and continue
            # TODO #B: Should we log in database
            logger.error(err)
            return False

    def run(self, task_id: int = 0, is_update: bool = False):
        """Run the jobposting workflow code for this worker."""
        logger.trace("JobPostingWorker: run")
        try:

            BackgroundTaskDb.update_background_task(self.db, task_id, "STARTED")
            self.insert_update_entities(is_update)

            entities = self.extract_save_entities()
            # logger.debug(f"Entities: {entities}.")
            BackgroundTaskDb.update_background_task(
                self.db, task_id, "EXTRACTED ENTITIES"
            )

            # Parse and Store the skills infor in jp_skills table
            parsed_job_posting = json.loads(entities)

            # Validate that parsed_job_posting has valid data points
            # TODO #C: Move all these string constants for keys in a constant file.
            assert "skills" in parsed_job_posting
            assert "overallYearsOfExperience" in parsed_job_posting

            parsed_skills = parsed_job_posting["skills"]
            parsed_experience = parsed_job_posting["overallYearsOfExperience"]

            self.extract_save_skill_names(parsed_skills)

            # Calculate ideal candidate score and store in the
            # jp_ideal_candidate_score table
            self.calc_save_candidate_score(parsed_skills, parsed_experience)

            BackgroundTaskDb.update_background_task(
                self.db, task_id, "CALCULATED IDEAL SCORE"
            )

            # Update the gpt logs table with extracted entities and other gpt stuff

            # Update status table
            status = "PROCESSED"
            bg_status = "COMPLETED"

            # Call upstream frontend service with updated information.
            if not self.update_frontend_status(status, 100):
                status = "PROCESSED_FE_ERROR"
                bg_status = "COMPLETED FE ERROR"

            self.jobPostingDb.update_job_posting(self.db, status=status)
            BackgroundTaskDb.update_background_task(self.db, task_id, bg_status)
            return self.jobPosting.company_id

        except Exception as err:
            # Log the error and continue
            logger.error(f"JP:run failed {err} \n {self}")
            logger.error(traceback.format_exc())
            try:
                status = "ERROR"
                self.update_frontend_status(status, progress=100)
                BackgroundTaskDb.update_background_task(self.db, task_id, status)
            except Exception as ex:
                logger.error(f"JA:run exception while updating failed status: {ex}")

            return 0
