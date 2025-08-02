"""

FileName: job_application_worker.py.

Purpose: JobApplication Worker which encapsulates all the work for processing
the job application data.
"""

import json
import timeit
from loguru import logger

from intai.ml.ai_prompt import JobApplicationAIPrompt
from intai.ml.llm_client import LLMClient
from intai.ml.openai_client import OpenAIClient
from intai.models.models import BackgroundTaskDb, CandidateDb, JobApplicationDetailDb
from intai.schemas.candidate_fe import CandidateFrontEnd, CandidateSkillFrontEnd
from intai.schemas.job_application import Candidate, JobApplicationDetail
from intai.utils.fe_utils import update_candidate_frontend_service
from intai.utils.file_utils import extract_text, get_bytes_from_url
from intai.utils.ja_utils import ja_get_basics
from intai.utils.json_data_utils import ja_populate_from_basics
from intai.utils.model_utils import insert_applicant_entities, update_job_application_detail

def update_if_not_null(jafe_dict, key, val):
    """Update the dict if not null helper function."""
    if val is not None:
        jafe_dict[key] = val


class CandidateWorker:
    """
    CandidateWorker Class.

    This class processes the candidate and executes the pipeline.
    NOTE: This will process the work in the background task.
    """

    def __init__(self, candidate: Candidate, session:any, task_id: int):
        """Init method for the class."""
        logger.info(f"CandidateWorker is initialized {candidate} ")
        self.db = session
        self.task_id = task_id
        self.candidate: Candidate = candidate
        self.company_id = candidate.company_id
        self.candidate_fe = CandidateFrontEnd(companyId=self.company_id)

        try:
            # Get job_posting_id for client_job_id from JobPosting Table
            self.candidate_db = CandidateDb(
                candidate=candidate
            )
            self.candidate_db.status = "Started"

            self.ja_detail = None
            self.ja_extracted_text = ""

        except Exception as err:
            logger.error(f"Exception while creating job application: {err}\n")

    def __repr__(self) -> str:
        return "<CandidateWorker: company_id:{}; candidate: {};  ext_text_len: {}".format(
            self.company_id,
            self.candidate_db,
            len(self.ja_extracted_text),
        )

    def insert_update_entity(self, is_update: bool):
        """Insert or update the candidate entity in database.

        NOTE: In case of Update it will delete all candidate and
        related entities (like address, experience etc.) as well.
        """
        try:
            logger.info(f"{'Update' if is_update else 'Insert'} Candidate Entity")
            if is_update:
                # Delete the entities.
                CandidateDb.delete_entities(
                    self.db,
                    self.company_id,
                    self.candidate.client_candidate_id,
                )
            
            # Persist in db
            # Insert the jobapplicationdetail entity
            self.ja_detail_db = JobApplicationDetailDb(JobApplicationDetail(company_id=self.company_id))
            self.ja_detail_db.insert(self.db)
            logger.info(f"JobApplicationDetail inserted with id: {self.ja_detail_db.id}")
            self.candidate.jad_id = self.ja_detail_db.id
            self.candidate_db.jad_id = self.ja_detail_db.id

            self.candidate_db.insert_candidate(self.db)
            self.candidate_id = self.candidate_db.id
            self.client_candidate_id = self.candidate_db.client_candidate_id
            
            logger.debug(f"candidateid is {self.candidate_db.id}")
        except Exception as err:
            logger.error(
                f"Exception while inserting or updating candidate entity: {err}\n CandidateWorker: {self}"
            )
            raise err
        
    def extract_save_entities(self):
        """Extract the entities from Candidate & store in the database.

        This will call openAI and get the parsed json entities for
        Candidate.
        """
        # TODO #C Potentially refactor extract_entities
        # into a common utility method later.

        try:
            ja_bytes_data, ja_docType = get_bytes_from_url(
                self.candidate.resume_doc_url,
            )
            self.ja_extracted_text = extract_text(ja_bytes_data, ja_docType)
            logger.debug(self.ja_extracted_text)

            self._get_ja_basics()
        

            # Call OpenAI directly. Previously we were using the cached entities but now we are always call openAI.
            # NOTE: For repeat calls if job posting is not changing in future we can store a checksum in db and decide that
            # to determine whether to call openai or not.
            ai_client = LLMClient(session_id=self.task_id, client_id=self.company_id)
            prompt = JobApplicationAIPrompt(ja_text=self.ja_extracted_text)
            extracted_entities = ai_client.get_model_response(prompt)

            if extracted_entities is not None and len(extracted_entities) > 0:
                logger.debug(f"len of Extracted Entities: {len(extracted_entities)}")
                logger.debug(f"Extracted ENtities: {extracted_entities}")

                extracted_entities_dict = json.loads(
                    extracted_entities
                )  # Can throw Json decode exception
                extracted_entities = json.dumps(
                    extracted_entities_dict
                )  # Trim the json by dumping from dict.
                logger.debug(f"Length after trimming is {len(extracted_entities)}")

            # Store the Candidate data in the table
            self.candidate_db.update_candidate(
                session=self.db,
                jad_id=self.candidate_db.jad_id,
                parsed_resume=extracted_entities,
                extracted_text=self.ja_extracted_text,
                status="Extracted Entities",
            )
            return extracted_entities

        except Exception as err:
            logger.error(
                f"Exception while extracting save entities: {err}\n Candidate: {self}"
            )
            raise err

    def _get_ja_basics(self):
        try:
            logger.info(f"Getting ja basics for {self.candidate}")
            start_time = timeit.default_timer()

            ja_basics_str = ja_get_basics(self.ja_extracted_text, session_idd=self.task_id, client_id=self.company_id)
            ja_basics = json.loads(ja_basics_str)
            logger.debug(f"ja_basics: {ja_basics}")
            
            ja_populate_from_basics(ja_basics, candidate_fe=self.candidate_fe)
            logger.info(f"sending update to frontend: {self.candidate_fe}")

            # NOTE: doing this as accessing self.jad_detail_db.id is throwing error with bounding issue in different sessionlocal
            jad_id = self.candidate.jad_id 
            
            update_job_application_detail(
                db=self.db,jad_id=jad_id, json_entities=None, json_basics=ja_basics, company_id=self.company_id)
                
            candidate_fe_success = update_candidate_frontend_service(candidate_fe=self.candidate_fe)
            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"oooooo=====( Execution time for basics parsing is: {execution_time} seconds )===ooooo")
        except Exception as err:
            logger.error(
                            f"Exception while getting ja basics: {err}\n JobApplication: {self}"
                        )
            raise err

    def populate_skills_fe(self, skill_score_dict):
        """Populate the skills fe.

        skill_score_dict is a dict with skill as key and score as value."""

        for skill in skill_score_dict.keys():
            score = round(skill_score_dict[skill] * 5)
            skill_fe = CandidateSkillFrontEnd(name=skill, proficiency=score)
            self.candidate_fe.candidateSkills.append(skill_fe)
            logger.debug(f"skill_fe: {skill_fe}")

    def run(self, task_id: int = 0, is_update: bool = False):
        """Run the application workflow code for this worker.
        
        Steps: 
        1. Insert of Update the Candidate Entity in Database that was passed in the constructor.
        2. Update the Candidate front end with status. 
        3. Extract the entities from the resume.
        4. Save the extracted entities in database for candidate like details, education, experience etc.
        5. Update the front end with extracted entities.
        6. 
        """
        logger.trace("JobPostingWorker: run")
        try:
            status = "STARTED"
            job_application_fe = {}
            BackgroundTaskDb.update_background_task(self.db, task_id, status)

            # Insert or update the entity in db.
            # NOTE: In case of update it will delete the previous entities.
            self.insert_update_entity(is_update)
            # TODO Insert Candidate Front end update service 
            # Extract the JSON entities from the resume.
            entities = self.extract_save_entities()
            BackgroundTaskDb.update_background_task(
                self.db, task_id, "EXTRACTED ENTITIES"
            )
            logger.debug(f"Entities: {entities}.")
            assert self.candidate.jad_id is not None

            # Save all entities tables with extracted entities and return the candidate_fe object.
            candidate_fe, ja_detail_db = insert_applicant_entities(db=self.db, jad_id=self.candidate.jad_id, entities=entities, resume_url=self.candidate.resume_doc_url, company_id=self.candidate.company_id)
            jad_id = ja_detail_db.id
            BackgroundTaskDb.update_background_task(
                self.db, task_id, "INSERTED ENTITIES"
            )
            status = "PROCESSED"
            self.candidate_db.update_candidate(session=self.db, status=status, jad_id=jad_id)
            candidate_fe_success = update_candidate_frontend_service(candidate_fe=candidate_fe)
            bg_status = (
                "COMPLETED SUCCESS"
                if  candidate_fe_success
                else "COMPLETED FE ERROR"
            )
            BackgroundTaskDb.update_background_task(self.db, task_id, bg_status)

        except Exception as err:
            # Log the error and continue
            logger.error(f"JA:run failed {err} \n {self}")
            status = "ERROR"
            #self.update_ja_frontend_service(job_application_fe, status, 100)
            BackgroundTaskDb.update_background_task(self.db, task_id, status)
            self.candidate_db.update_candidate(self.db, status=status)

            raise err
