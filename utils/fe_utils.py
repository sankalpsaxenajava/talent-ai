"""fe_utils.py: This file contains all the utility functions to populate data for front end and 
call the front end API's."""
import json
import traceback
import requests
from loguru import logger

from intai import config
from intai.models.models import JobApplicationDetailDb
from intai.schemas.candidate_fe import CandidateExperienceFrontEnd, CandidateFrontEnd, CandidateQualificationFrontEnd, CandidateSkillFrontEnd
from intai.schemas.job_application_fe import JobApplicationFrontEnd
from intai.schemas.job_application import JobApplicationDetail, JobApplicationEducation, JobApplicationExperience
from intai.utils.str_utils import check_str_not_null


def update_if_not_null(fe_dict, key, val):
    """Update the dict if not null helper function."""
    if val is not None:
        fe_dict[key] = val


def populate_candidate_basics(
        company_id: int,
        resume_url: str,
        jad_detail_db: JobApplicationDetailDb) -> None:
    """Populate the candidate fe based on ja_detail_db entities."""
    firstName = ""
    lastName = ""
    if jad_detail_db and check_str_not_null(jad_detail_db.applicant_name):
        name_parts = jad_detail_db.applicant_name.split()
        if name_parts and len(name_parts) > 0:
            firstName = name_parts[0]
            if len(name_parts) > 1:
                lastName = name_parts[1]

    candidate_fe = CandidateFrontEnd(
        firstName=firstName,
        lastName=lastName,
        companyId=company_id,
        yearsOfExperience=jad_detail_db.experience_years,
        email=jad_detail_db.applicant_resume_email,
        phone=jad_detail_db.applicant_resume_phone,
        linkedInUrl=jad_detail_db.applicant_resume_linkedin,
        resumeUrl=resume_url,
        technicalTools=jad_detail_db.software_skills,
        currentCompensation=jad_detail_db.current_salary,
        expectedCompensation=jad_detail_db.expected_salary,
        noticePeriodInDays=jad_detail_db.notice_period,
    )
    logger.debug(f"candidate_fe: {candidate_fe}")

    return candidate_fe

def populate_skills_fe(self, skill_score_dict: dict[str, float]):
    """Populate the skills fe.

    skill_score_dict is a dict with skill as key and score as value."""

    for skill in skill_score_dict.keys():
        score = round(skill_score_dict[skill] * 5)
        skill_fe = CandidateSkillFrontEnd(name=skill, proficiency=score)
        self.candidate_fe.candidateSkills.append(skill_fe)
        logger.debug(f"skill_fe: {skill_fe}")

def populate_experience_fe(
        candidate_fe: CandidateFrontEnd, experience: JobApplicationExperience, is_current: bool
    ):
        """Populate the experience fe object."""
        if experience.team_lead_experience:
            candidate_fe.peopleManagement = True
        try:

            experience_fe = CandidateExperienceFrontEnd(
                designation=experience.title,
                companyName=experience.experience_company,
                location=experience.location,
                startDate=experience.start_date,
                endDate=experience.end_date,
                currentlyEmployedAt=is_current,
            )
            logger.debug(f"Adding experience_fe: {experience_fe}")
            candidate_fe.candidateExperiences.append(experience_fe)
        except Exception as err:
            logger.error(
                f"Exception while inserting experience skills: {err}\n "
            )
            raise err


def populate_education_fe(
    candidate_fe: CandidateFrontEnd,
    education: JobApplicationEducation, is_current: bool
):
    """Populate the education fe object."""
    try:
        is_current = candidate_fe.latestInstitution is None or len(candidate_fe.latestInstitution) == 0 
        #if is_current:
            # candidate_fe.latestInstitution = education.institution
            # candidate_fe.latestDegree = education.degree_field
            # candidate_fe.yearOfGraduation = education.end_date
            # # if year of graduation is of form 10-2022 then set it to 2022
            # if candidate_fe.yearOfGraduation is not None and '-' in candidate_fe.yearOfGraduation:
            #     candidate_fe.yearOfGraduation = candidate_fe.yearOfGraduation.split('-')[1]
            #     logger.warning(f"FIX: year of graduation date coming from llm is of form MM-YYYY, should be YYYY, {education.end_date}")
        
        education_fe = CandidateQualificationFrontEnd(
            qualification=education.degree_level,
            university=education.institution,
            fieldOfStudy=education.degree_field,
            # location=education.location,
            startDate=education.start_date,
            endDate=education.end_date,
            latestQualification=is_current,
            # TODO Find if this is the current education
        )
        logger.debug(f"Adding education_fe: {education_fe}")
        candidate_fe.candidateQualifications.append(education_fe)
    except Exception as err:
        logger.error(
            f"Exception while inserting education: {err}\n "
        )
        raise err


def update_candidate_frontend_service(candidate_fe: CandidateFrontEnd):
    """Send the frontend with candidate update.

    NOTE: In case of error it just logs the error and returns false.
    """
    try:

        logger.debug(
            f"update_candidate_frontend_service candidate:{candidate_fe}"
        )

        data_dict = candidate_fe.model_dump()
        for key, value in list(data_dict.items()):

            # Delete keys whose value is null or "" or 'null'
            if isinstance(value, (str, object, dict)) and not check_str_not_null(
                value
            ):
                logger.info(f"deleting {key}")
                del data_dict[key]
        data = json.dumps(data_dict)
        logger.debug(f"job_application:{candidate_fe}")
        logger.debug(f"data_dict:{data_dict}")

        url = f"{config.FRONT_END_URL}/api/candidates"
        
        logger.info(f"Post Candidate case: url: {url}")
        response = requests.post(url, json=data)
        logger.info(f"response: {response.content} status: {response.status_code}")
        response.raise_for_status()
        return True
    except Exception as err:
        # Log the error and continue
        # TODO: Should we log in database
        logger.error(err)
        logger.error(traceback.format_exc())
        return False


def update_ja_frontend_service(
        client_job_application_id: int,
        job_application_fe: JobApplicationFrontEnd,):
    """Send the frontend with status update.

    NOTE: In case of error it just logs the error and returns false.
    """
    try:
        logger.debug(
            f"update_ja_frontend_service client_job_application_id:{client_job_application_id} job_application_fe:{job_application_fe}"
        )
        if job_application_fe is None:
            raise Exception(f"Jobapplication is not populated or None")

        # This states need to match in front end as well.
        assert job_application_fe.processingStatus in ["INIT", "SUBMITTED", "WORKING", "PROCESSED", "ERROR"]
        job_application_fe.resumeUrl = None
        job_application_fe.candidateExperiences = None
        job_application_fe.candidateQualifications = None
        job_application_fe.candidateSkills = None
        
        data_dict = job_application_fe.model_dump()
        for key, value in list(data_dict.items()):

            # Delete keys whose value is null or "" or 'null'
            if isinstance(value, (str, object, dict)) and not check_str_not_null(
                value
            ):
                logger.info(f"deleting {key}")
                del data_dict[key]
        data = json.dumps(data_dict)
        logger.debug(f"job_application:{job_application_fe}")
        logger.debug(f"client_job_application_id:{client_job_application_id}")
        logger.debug(f"data_dict:{data_dict}")

        # NOTE: Currently since we are using same put api in front end for
        # job app update and update from backend (from here).
        # If we pass the resumeUrl front end will end up calling
        # backend again creating an infinite loop. So check and assert here.
        assert "resumeUrl" not in data_dict

        url = f"{config.FRONT_END_URL}/api/jobApplications/{client_job_application_id}"
        
        logger.info(f"calling {url} with {data}")
        headers = {"Content-Type": "application/json"}

        response = requests.put(url, data=data, headers=headers)
        logger.info(f"response: {response.content} status: {response.status_code}")
        response.raise_for_status()
        return True
    except Exception as err:
        # Log the error and continue
        # TODO: Should we log in database
        logger.error(traceback.format_exc())

        logger.error(err)
        return False

def update_screening_result_frontend_service(
        json_data):
    """Send the frontend with status update.

    NOTE: In case of error it just logs the error and returns false.
    """
    try:
        # This states need to match in front end as well.
        logger.debug(f"json_resp: {json_data}")

       

        url = f"{config.FRONT_END_URL}/api/interviews/screeningInterview/screeningResult"
        data = json.dumps(json_data)
        logger.info(f"calling {url} with {data}")
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=json_data)
        logger.info(f"response: {response.content} status: {response.status_code}")
        response.raise_for_status()
        return True
    except Exception as err:
        # Log the error and continue
        # TODO: Should we log in database
        logger.error(traceback.format_exc())

        logger.error(err)
        return False