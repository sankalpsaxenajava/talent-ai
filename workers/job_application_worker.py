"""

FileName: job_application_worker.py.

Purpose: JobApplication Worker which encapsulates all the work for processing
the job application data.
"""

import json
import timeit
import traceback
from intai.ml.scoring_utils import (
    match_certificate_skills_with_jd_skills,
    ja_calculate_matching_skill_score,
    ja_calculate_matching_percentage,
    ja_get_bucket,
    ja_match_industry_with_jd,
    ja_match_title_with_jd,
)
from intai.models.models import (
    JobApplicationDb,
    JobPostingDb,
    JobApplicationDetailDb,
    JobApplicationCertificationSkillDb,
    JobApplicationExperienceDb,
    JobApplicationSkillDb,
    JobApplicationScoreDb,
    BackgroundTaskDb,
    SessionLocal
)
from intai.schemas.job_application import (
    JobApplication,
    JobApplicationScore,
    JobApplicationDetail,
)
from intai.schemas.job_application_fe import JobApplicationFrontEnd
from intai.utils.fe_utils import update_candidate_frontend_service, update_ja_frontend_service
from intai.utils.file_utils import extract_text, get_bytes_from_url
from intai.utils.ja_utils import ja_get_basics, ja_parse_jd, ja_parse_application, ja_calculate_factor_score, ja_get_score_summary
from intai.utils.json_data_utils import ja_populate_from_basics
from intai.utils.model_utils import insert_applicant_entities, update_job_application_detail
from loguru import logger
import asyncio

def update_if_not_null(jafe_dict, key, val):
    """Update the dict if not null helper function."""
    if val is not None:
        jafe_dict[key] = val


class JobApplicationWorker:
    """
    JobApplicationWorker Class.

    This class processes the job application and executes the pipeline.
    NOTE: This will process the work in the background task.
    """

    def __init__(self, jobApplication: JobApplication, task_id: int):
        """Init method for the class."""
        logger.info(f"JobApplicationWorker is initialized {jobApplication} ")
        self.job_application: JobApplication = jobApplication
        self.task_id = task_id
        self.company_id = jobApplication.company_id
        self._progressBarCompletion = 0

        try:
            

            self.ja_detail_db = None
            self.ja_extracted_text = ""

        except Exception as err:
            logger.error(f"Exception while creating job application: {err}\n")

    def __repr__(self) -> str:
        return "<JobApplicationWorker: company_id:{}; job_application: {}; job_posting: {}; ext_text_len: {}".format(
            self.company_id,
            self.job_application,
            self.job_posting_db,
            len(self.ja_extracted_text),
        )

    @property
    def progressBarCompletion(self):
        return self._progressBarCompletion

    @progressBarCompletion.setter
    def progressBarCompletion(self, value):
        self._progressBarCompletion = value
        self.job_application_fe.processingStatusProgress = min(value, 100)

    def run(self, is_update: bool = False):
        """
        Run the application workflow code for this worker.

        This method is responsible for the following tasks:
        1. Update the background task status in the database.
        2. Insert or update the job application entity in the database.
        3. Update the job application frontend service with the current status and progress.
        4. Extract and save the entities from the job application.
        5. Update the job application details in the database.
        6. Check if the candidate meets the job criteria.
        7. Calculate and save the ranking for the job application.
        8. Update the job application status in the database.
        9. Update the job application frontend service with the final status and progress.
        10. Update the candidate frontend service.
        11. Update the background task status in the database based on the success of the frontend updates.

        If any exception occurs during the execution of this method, it will log the error and continue to update the job application and background task status accordingly.
        """
        logger.trace("JobApplicationWorker: run")
       
        try:
            
            self._load_job()

            # Insert or update the entity in db.
            # NOTE: In case of update it will delete the previous entities.
            asyncio.run(self._save_db_and_extract_text(is_update))

            asyncio.run(self._get_score_summay_and_basics())

            # Filtering Criteria: Check if Candidate meets the criteria
            self.check_job_criteria()                # Send FE with failur      

            asyncio.run(self._finish_processing())

        except Exception as err:
            # Log the error and continue
            logger.error(f"JA:run failed {err} \n {self}")
            traceback.print_exc()
            status = "ERROR"
            job_application_fe = JobApplicationFrontEnd(companyId=self.company_id, processingStatus=status, processingStatusProgress=100)
            update_ja_frontend_service(self.job_application.client_job_application_id, job_application_fe)
            with SessionLocal() as db:
                BackgroundTaskDb.update_background_task(db, self.task_id, status)
                self.job_application_db.update_job_application(db, status=status)

            raise err

    ### - Top Level methods called by run 

    def _load_job(self):
        """Load the job posting db from the database for this jobapplication"""
        logger.trace("Loading JobPosting from application")
        status = "STARTED"
        with SessionLocal() as db:
            BackgroundTaskDb.update_background_task(db, self.task_id, status)

            self.job_posting_db: JobPostingDb = JobPostingDb.get_job_posting(
                db, self.company_id, self.job_application.client_job_id
            )
            logger.debug(f"job_posting_db: {self.job_posting_db}")
            if self.job_posting_db is None:
                raise Exception("job_posting not found")

            self.client_job_id = self.job_posting_db.client_job_id
            self.job_posting_id = self.job_posting_db.id
       
        
    async def _save_db_and_extract_text(self, is_update: bool):
        """Insert or update the job application entity in database.

        NOTE: In case of Update it will delete all jobapplication and
        related entities (like address, experience etc.) as well.
        """
        try:
            logger.info(f"{'Update' if is_update else 'Insert'} JobApplication Entity")
            if self.job_posting_db is None or self.client_job_id is None:
                raise Exception(f"Job Posting not populated or exists. CHECK: if _load_job was called.")

             # Get job_posting_id for client_job_id from JobPosting Table
            self.job_application_db = JobApplicationDb(
                self.job_application, self.job_posting_id
            )
            self.job_application_db.status = "Started"
            self.job_application_fe = JobApplicationFrontEnd(
            companyId=self.company_id, processingStatus="WORKING")
            self.progressBarCompletion += 15
            logger.warning(f"started progress bar: {self.job_application_fe.processingStatusProgress}")
            # Create tasks for parallel execution
            insert_task = asyncio.to_thread(self._insert_job_application, is_update)
            frontend_update_task = asyncio.to_thread(update_ja_frontend_service,
                                                        self.job_application.client_job_application_id,
                                                        job_application_fe=self.job_application_fe)
            extract_text_task = asyncio.create_task(self._extract_text())

            # Wait for both tasks to complete
            await asyncio.gather(insert_task, frontend_update_task, extract_text_task)

            logger.debug(f"jobapplicationid is {self.job_application_db.id}")
        except Exception as err:
            logger.error(
                f"Exception while saving JobApplication or calling frontend. Error: {err}\n JobApplicatinoWorker: {self}"
            )
            raise err
    
    async def _get_score_summay_and_basics(self):
        """Calculate the candidate ranking for the associated job.

        NOTE: Also saves the results in database. Assumes hard job criteria
        is already checked before it.
        """
        try:
            logger.info("Calculating score summary and parsing application")
            start_time = timeit.default_timer()
            parse_task = asyncio.create_task(asyncio.to_thread(self._parse_and_match_application))
            
            # Create tasks for parallel execution
            parse_basic_task = asyncio.create_task(asyncio.to_thread(self._get_ja_basics))
            factor_score_summary_task = asyncio.create_task(self._get_factor_score_summary())  # Call as coroutine

            async def update_progress():
                #job_application_fe = JobApplicationFrontEnd(companyId=self.company_id, processingStatus=self.job_application_fe.processingStatus)
                
                while not all(task.done() for task in [parse_task, parse_basic_task, factor_score_summary_task]):
                    self.progressBarCompletion = min(self.progressBarCompletion + 4, 90)
                    #job_application_fe.processingStatusProgress = self.progressBarCompletion

                    logger.debug(f"processStatusProgress is {self.job_application_fe.processingStatusProgress} LOCAL ja_fe: {self.job_application_fe}")
                    await asyncio.to_thread(update_ja_frontend_service,
                        client_job_application_id=self.job_application.client_job_application_id,
                        job_application_fe=self.job_application_fe
                    )
                    await asyncio.sleep(4)

            # Start the progress update task
            progress_task = asyncio.create_task(update_progress())

            # Wait for all tasks to complete
            ja_score_parse, _, ja_score_factor, _ = await asyncio.gather(
                parse_task, parse_basic_task, factor_score_summary_task, progress_task
            )
            ja_score_parse.factor_calculation = ja_score_factor.factor_calculation
            ja_score_parse.factor_explanation = ja_score_factor.factor_explanation
            ja_score_parse.factor_summary = ja_score_factor.factor_summary
            ja_score_parse.factor_score = ja_score_factor.factor_score
            self.job_application_fe.score = str(ja_score_factor.factor_score)
            self.job_application_fe.scoreSummary = str(ja_score_factor.factor_summary)

            #combine the parsed data score and factor score response. 
            # Save score to database after we have the fully parsed data.
            self._save_job_application_score(ja_score_parse)
            self.progressBarCompletion = min(self.progressBarCompletion + 10, 90)
            update_ja_frontend_service(
                client_job_application_id=self.job_application.client_job_application_id,
                job_application_fe=self.job_application_fe)

            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"oooooo=====( Execution time for parsing and score is: {execution_time} seconds )===ooooo")
  
        except Exception as err:
            logger.error(
                f"Exception while calculate save ranking: {err}\n JobApplication: {self}"
            )
            traceback.print_exc()
            logger.error(err)
            raise err

    ##### - Helper methods 
    def _insert_job_application(self, is_update: bool):
        """Insert job application into the database."""
        
        logger.info(f"{'Update' if is_update else 'Insert'} JobApplication Entity")

        with SessionLocal() as db:
            if is_update:
                # Delete the entities.
                JobApplicationDb.delete_entities(
                    db,
                    self.company_id,
                    self.job_application.client_job_application_id,
                )
            # Insert the jobapplicationdetail entity
            self.ja_detail_db = JobApplicationDetailDb(JobApplicationDetail(company_id=self.company_id))
            self.ja_detail_db.insert(db)
            logger.info(f"JobApplicationDetail inserted with id: {self.ja_detail_db.id}")
            self.job_application.jad_id = self.ja_detail_db.id
            self.job_application_db.jad_id = self.ja_detail_db.id
            self.job_application_db.insert_job_application(db)
        self.job_application_id = self.job_application_db.id
        self.client_job_application_id = (
            self.job_application_db.client_job_application_id
        )
        logger.info(f"JobApplication inserted with id: {self.job_application_id}")

    async def _extract_text(self):
        """Extract text from the resume document asynchronously."""
        logger.info(f"Extracting text from resume document")

        ja_bytes_data, ja_docType = await asyncio.to_thread(get_bytes_from_url, self.job_application.resume_doc_url)
        self.ja_extracted_text = await asyncio.to_thread(extract_text, ja_bytes_data, ja_docType)
        logger.debug(self.ja_extracted_text)

    def _parse_and_match_application(self):
        """
        Parse the job application, match it with the job description, and calculate various scores.

        This function performs the following tasks:
        1. Extracts entities from the job application
        2. Parses the job description
        3. Matches candidate skills with job description skills
        4. Calculates learnability score based on certification skills
        5. Calculates skill matching score and percentage
        6. Determines the candidate's bucket based on the matching percentage
        7. Matches industry and job title with the candidate's experience
        8. Creates and returns a JobApplicationScore object with all calculated scores

        Returns:
            JobApplicationScore: An object containing all calculated scores and matches

        Raises:
            Exception: If any error occurs during the parsing and matching process

        TODO: Move this function to ja_utils.py for better code organization
        """
        try:
            logger.debug(f"Parsing and matching application")
            jad_id = self.job_application.jad_id
            assert jad_id is not None
            with SessionLocal() as db:
                start_time = timeit.default_timer()

                extracted_entities = ja_parse_application(self.ja_extracted_text, session_id=self.task_id, client_id=self.company_id)
                # Save extracted entities, parsed_resume etc. in db.
                self._update_applicant_entities(db, jad_id, extracted_entities)

                organizationsIndustrySegment, job_title, jd_skill_names, overall_experience, management_experience = ja_parse_jd(self.job_posting_db.parsed_jd)

                logger.debug(
                    f"JD Information \n skills: {jd_skill_names} \n"
                    f"experience in years: {overall_experience}\n"
                    f"peopleManagementExperience: {management_experience}\n"
                    f"orgIndSeg: {organizationsIndustrySegment}\n"
                    f"job_title: {job_title}\n"
                    f"jad_id: {self.job_application.jad_id}"
                )

                # Get the skills, certificate skills for candidate and calculate
                # learnability score
                experience_skills = JobApplicationSkillDb.get_skills_by_jad(
                    db, self.company_id, self.job_application.jad_id
                )
                certification_skills_db = (
                    JobApplicationCertificationSkillDb.get_skills_by_jad(
                        db, self.company_id, self.job_application.jad_id
                    )
                )

                certification_skills = [x.skill_name for x in certification_skills_db]

                logger.debug(
                    f"Experience Skills: {experience_skills}\n Certification Skills: {certification_skills}"
                )
                learnability = match_certificate_skills_with_jd_skills(
                    certification_skills, jd_skill_names, company_id=self.company_id, session_id=self.task_id
                )
                logger.debug(
                    f"learnability (match cert skills with jd skills) {learnability}"
                )

                # get the standardized skill name for candidate skills and
                # calculate skill score
                ja_matching_score, ja_matching_skills = ja_calculate_matching_skill_score(
                    experience_skills, jd_skill_names, session_id=self.task_id, client_id=self.company_id
                )
                #
                # Calculate the percentage for candidate based on ideal candidate score and skill score.
                ja_matching_percentage = ja_calculate_matching_percentage(
                    ja_matching_score, self.job_posting_db.ideal_candidate_score
                )
                logger.debug(
                    f"ja_matching_score: {ja_matching_score} \n ja_matching_skills: {ja_matching_skills} \nPercentage: {ja_matching_percentage}"
                )
                # Find the buckets for this candidate score.
                bucket = ja_get_bucket(ja_matching_percentage)
                logger.debug(f"Bucket: {bucket}, score: {ja_matching_score}")

                latest_experiences = JobApplicationExperienceDb.get_experience_by_jad(
                        db, self.company_id, self.job_application.jad_id, limit=3)
                industry_match = ja_match_industry_with_jd(
                    latest_experiences, organizationsIndustrySegment
                )
                title_match = ja_match_title_with_jd(latest_experiences, job_title, session_id=self.task_id, client_id=self.company_id)
                #
                # Create a new JobApplicationScore with the calculated values
                ja_score = JobApplicationScore(
                    company_id=self.company_id,
                    bucket=bucket,
                    score=ja_matching_score,
                    match_percent=ja_matching_percentage,
                    learnability=learnability,
                    industry_match=industry_match,
                    title_match=title_match,
                    matching_skills=str(ja_matching_skills)
                )
                # Return the calculated data
                
                end_time = timeit.default_timer()
                execution_time = end_time - start_time
                logger.warning(f"oooooo=====( Execution time for full parsing is: {execution_time} seconds )===ooooo")
                return ja_score
        except Exception as err:
            logger.error(
                            f"Exception while calculate save ranking: {err}\n JobApplication: {self}"
                        )
            raise err

    def _get_ja_basics(self):
        try:
            logger.info(f"Getting ja basics for {self.job_application}")
            start_time = timeit.default_timer()

            ja_basics_str = ja_get_basics(self.ja_extracted_text, session_id=self.task_id, client_id=self.company_id)
            ja_basics = json.loads(ja_basics_str)
            logger.debug(f"ja_basics: {ja_basics}")
            
            self.progressBarCompletion = min(self.progressBarCompletion + 10, 90)
            ja_populate_from_basics(ja_basics, candidate_fe=self.job_application_fe)
            logger.info(f"sending update to frontend: {self.job_application_fe}")

            # NOTE: doing this as accessing self.jad_detail_db.id is throwing error with bounding issue in different sessionlocal
            jad_id = self.job_application.jad_id 
            with SessionLocal() as db:
                update_job_application_detail(
                    db=db,jad_id=jad_id, json_entities=None, json_basics=ja_basics, company_id=self.company_id)
                
            update_ja_frontend_service(client_job_application_id=self.job_application.client_job_application_id,
                    job_application_fe=self.job_application_fe)
            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"oooooo=====( Execution time for basics parsing is: {execution_time} seconds )===ooooo")
        except Exception as err:
            logger.error(
                            f"Exception while getting ja basics: {err}\n JobApplication: {self}"
                        )
            raise err
    
    async def _get_factor_score_summary(self):
        logger.info(f"Calculating factor score for {self.job_application}")
        try:
            start_time = timeit.default_timer()

            ja_text = self.ja_extracted_text
            jp_text = self.job_posting_db.extracted_text
            jp_parsed = json.loads(self.job_posting_db.parsed_jd)
            logger.debug(f"jp_parsed: {jp_parsed}")
            factor_score_task = asyncio.create_task(asyncio.to_thread(ja_calculate_factor_score, ja_text=ja_text, jp_text=jp_text, jp_parsed=jp_parsed, session_id=self.task_id, client_id=self.company_id))
            summary_task = asyncio.create_task(asyncio.to_thread(ja_get_score_summary, ja_text, jp_text, self.task_id, self.company_id))

            factor_score_dict, score_summary = await asyncio.gather(factor_score_task, summary_task)
            assert "final_score_explanation" in factor_score_dict
            assert "calculations" in factor_score_dict
            assert "final_score" in factor_score_dict

            ja_score = JobApplicationScore(
                        company_id=self.company_id,
                        factor_calculation=json.dumps(factor_score_dict["calculations"]),
                        factor_score=factor_score_dict["final_score"],
                        factor_explanation=json.dumps(factor_score_dict["final_score_explanation"]),
                        factor_summary=score_summary,
                    )
            
            # Update frontend with factor score and summary
            self.job_application_fe.score = str(ja_score.factor_score)
            self.job_application_fe.scoreSummary = str(ja_score.factor_summary)
            update_ja_frontend_service(
                client_job_application_id=self.job_application.client_job_application_id,
                job_application_fe=self.job_application_fe
            )
            
            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"oooooo=====( Execution time for factor scoring and summary is: {execution_time} seconds )===ooooo")
            return ja_score
        except Exception as err:
            logger.error(
                            f"Exception while calculate factor score: {err}\n JobApplication: {self}"
                        )
            raise err


    def _save_job_application_score(self, ja_score: JobApplicationScore):
        """Store JobApplicationScore into the database."""
        try:
            with SessionLocal() as db: 

                ja_score_db = JobApplicationScoreDb(ja_score, self.job_application_id)
                logger.debug(f"inserting ja_score_db in database:  {ja_score_db}")
                ja_score_db.insert_job_application_score(db)

                
                BackgroundTaskDb.update_background_task(
                    db, self.task_id, "PARSING AND SCORING DONE"
                )

        except Exception as err:
            logger.error(f"Exception while saving job application score: {err}")
            raise err

    def _update_applicant_entities(self, db, jad_id, entities):
        """Update entities tables with extracted entities."""
        try:
            # Store the jobapplication data in the table
            self.job_application_db.update_job_application(
                db,
                jad_id=jad_id,
                parsed_resume=entities,
                extracted_text=self.ja_extracted_text,
                status="Extracted Entities",
            )
            # TODO: Move this to after the parsing is done in the _get_score_summay_and_basics function to 
            # combine with basics from other prompt.
            self.candidate_fe, self.ja_detail_db = insert_applicant_entities(
                db=db,
                jad_id=jad_id,
                entities=entities,
                resume_url=self.job_application.resume_doc_url,
                company_id=self.company_id)
            self.job_application.jad_id = self.ja_detail_db.id
            self.job_application_fe = JobApplicationFrontEnd.create_copy(self.candidate_fe)
            self.job_application_db.update_job_application(session=db,
                                                        status="UPDATED_JAD_ENTITIES",
                                                        jad_id=self.job_application.jad_id)
            self.job_application_fe.processingStatus = "WORKING"
            self.progressBarCompletion = min(self.progressBarCompletion + 5, 90)
        except Exception as e:
            logger.error(f"Error inserting applicant entities: {str(e)}")
            raise

    def check_job_criteria(self):
        """Check the filtering criteria matches for this job."""
        filtering_criteria_json = self.job_posting_db.filtering_criteria
        try:
            assert self.ja_detail_db is not None
            if filtering_criteria_json:
                filter_criteria = json.loads(filtering_criteria_json)
                for criteria_name, criteria_value in filter_criteria.items():
                    if (
                        criteria_name == "maxSalary"
                        and self.ja_detail_db.expected_salary > int(criteria_value)
                    ):
                        logger.info(
                            f"Failed maxSalary criteria: {self.ja_detail_db.expected_salary} {criteria_value}"
                        )
                        return False

                    if (
                        criteria_name == "minSalary"
                        and self.ja_detail_db.expected_salary < float(criteria_value)
                    ):
                        logger.info(
                            f"Failed minSalary criteria: {self.ja_detail_db.expected_salary} {criteria_value}"
                        )
                        return False
                    if (
                        criteria_name == "AverageTenureInOrganizationInYear"
                        and self.ja_detail_db.avg_tenure_org_years < float(criteria_value)
                    ):
                        logger.info(
                            f"Failed AverageTenureInOrganizationInYear criteria: {self.ja_detail_db.avg_tenure_org_years} {criteria_value}"
                        )
                        return False
                    if (
                        criteria_name == "overallYearsOfExperience"
                        and self.ja_detail_db.experience_years < float(criteria_value)
                    ):
                        logger.info(
                            f"Failed overallYearsOfExperience criteria: {self.ja_detail_db.experience_years} {criteria_value}"
                        )
                        return False
            return True

        except Exception as err:
            logger.error(
                f"Exception while checking job criteria: {err}\n JobApplication: {self}"
            )
            raise err
       

    async def _finish_processing(self):
        status = "PROCESSED"
        self.job_application_fe.processingStatus = status
        self.progressBarCompletion = 100

        # Update job application status
        tasks = [
            asyncio.to_thread(self._update_job_application_status, status=status),
            asyncio.to_thread(update_ja_frontend_service, self.job_application.client_job_application_id, self.job_application_fe),
            asyncio.to_thread(update_candidate_frontend_service, candidate_fe=self.candidate_fe)
        ]
        db_result, ja_fe_success, candidate_fe_success = await asyncio.gather(*tasks)
        logger.info(f"db_result: {db_result}, ja_fe_success: {ja_fe_success}, candidate_fe_success: {candidate_fe_success}")

        with SessionLocal() as db:

            # Determine final background task status
            bg_status = (
                "COMPLETED SUCCESS"
                if ja_fe_success and candidate_fe_success
                else "COMPLETED FE ERROR"
            )
            logger.info(f"Final background task status: {bg_status} id: {self.task_id}")
            # Update background task with final status
            BackgroundTaskDb.update_background_task(db, self.task_id, bg_status)
    
    def _update_job_application_status(self, status):
        """Update the job application status."""
        try:
            with SessionLocal() as db:
                self.job_application_db.update_job_application(session=db, status=status)
        except Exception as err:
            logger.error(f"Error updating job application status: {str(err)}")
            raise