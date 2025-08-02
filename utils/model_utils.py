"""This file contains the helper functions to interact with JobApplication and Candidate models."""

import json
from loguru import logger

from intai.ml.scoring_utils import get_skill_score_job
from intai.models.models import (
    JobApplicationAddressDb,
    JobApplicationAwardDb,
    JobApplicationCertificationDb,
    JobApplicationCertificationSkillDb,
    JobApplicationDetailDb,
    JobApplicationEducationDb,
    JobApplicationExperienceDb,
    JobApplicationInterestDb,
    JobApplicationLanguageDb,
    JobApplicationProjectDb,
    JobApplicationPublicationDb,
    JobApplicationSkillDb,
    JobApplicationVolunteerDb,
    SkillDb,
)
from intai.schemas.candidate_fe import CandidateFrontEnd, CandidateSkillFrontEnd
from intai.schemas.job_application import JobApplicationDetail, JobApplicationExperience
from intai.utils.fe_utils import (
    populate_candidate_basics,
    populate_education_fe,
    populate_experience_fe,
)
from intai.utils.json_data_utils import (
    ja_get_address_from_json,
    ja_get_awards_from_json,
    ja_get_certifications_from_json,
    ja_get_details_from_json,
    ja_get_education_from_json,
    ja_get_experience_from_json,
    ja_get_interests_from_json,
    ja_get_languages_from_json,
    ja_get_projects_from_json,
    ja_get_publications_from_json,
    ja_get_volunteers_from_json,
)

def populate_skills_fe(candidate_fe: CandidateFrontEnd, skill_score_dict: dict[str, float]) -> None:
    """Populate the skills fe.

    skill_score_dict is a dict with skill as key and score as value."""

    for skill in skill_score_dict.keys():
        score = round(skill_score_dict[skill] * 5)
        skill_fe = CandidateSkillFrontEnd(name=skill, proficiency=score)
        candidate_fe.candidateSkills.append(skill_fe)
        logger.debug(f"skill_fe: {skill_fe}")
        
def insert_experience_skills(db, candidate_fe: CandidateFrontEnd, company_id:int, jad_id: int,  experience_skills: list[JobApplicationExperience]):
        """Insert the skills into the skill table as well as ja_skills."""

        try:
            logger.debug(f"skills input json: {experience_skills}")
            skills = experience_skills.keys()

            logger.debug(f"skills from json: {skills}")
            # filter out the ones already in db.
            existing_skills = SkillDb.get_skills(db, company_id, skills)

            existing_skill_names = [x.skill_name for x in existing_skills]
            logger.debug(f"existing skills from db: {existing_skill_names}")
            new_skills = [x for x in skills if x not in existing_skill_names]
            logger.debug(f"new skills from this session {new_skills}")

            skills_list = list(zip(new_skills, new_skills))
            SkillDb.insert_skills_no_duplicates(session=db, company_id=company_id, skills_list=skills_list)

            # Now insert the skills in Ja_skills table.
            # NOTE: we need to insert all skills in ja_skills table not just the new skills.

            skill_score_dict = get_skill_score_job(skills=skills)
            populate_skills_fe(candidate_fe=candidate_fe, skill_score_dict=skill_score_dict)
            logger.debug(f"skill score dict is {skill_score_dict}")
            JobApplicationSkillDb.insert_many(session= db, company_id=company_id, jad_id=jad_id, skills_score=skill_score_dict)

            return new_skills
        except Exception as err:
            logger.error(
                f"Exception while inserting experience skills: {err}"
            )
            raise err


def insert_applicant_entities(db,
                              jad_id: int,
                              entities,
                              resume_url: str,
                              company_id: int) -> tuple[CandidateFrontEnd, JobApplicationDetail]:
    """Insert the applicant json_data tables."""
    logger.info(f"insert_applicant_entities: {entities} url: { resume_url} company_id: {company_id}")
    try:
        assert entities and len(entities) > 0
        json_entities = json.loads(entities)
        jad_detail_db = update_job_application_detail(db=db, jad_id=jad_id, json_entities=json_entities, json_basics=None, company_id=company_id)
        logger.debug(f"jad_detail_db: {jad_detail_db}")
        jad_id = jad_detail_db.id
        candidate_fe = populate_candidate_basics(company_id=company_id, resume_url=resume_url, jad_detail_db=jad_detail_db)        
        insert_addresses(db, json_entities, jad_id, company_id, candidate_fe)
        insert_experiences_and_skills(db, json_entities, jad_id, company_id, candidate_fe)
        insert_educations(db, json_entities, jad_id, company_id, candidate_fe)
        insert_languages(db, json_entities, jad_id, company_id)
        insert_certifications(db, json_entities, jad_id, company_id)
        insert_projects(db, json_entities, jad_id, company_id)
        insert_awards(db, json_entities, jad_id, company_id)
        insert_publications(db, json_entities, jad_id, company_id)
        insert_volunteers(db, json_entities, jad_id, company_id)
        insert_interests(db, json_entities, jad_id, company_id)
        return candidate_fe, jad_detail_db
    except Exception as err:
        logger.error(f"Exception while inserting applicant entities: {err}")
        raise err
def update_job_application_detail(db, jad_id, json_entities, json_basics, company_id):
    """Update the job application detail table."""
    logger.debug(f"jad_id: {jad_id}, json_entities: {json_entities}, json_basics: {json_basics}")
    ja_detail: JobApplicationDetail = ja_get_details_from_json(json_entities, json_basics, company_id)
    logger.debug(f"ja_detail from ja_get_details_from_json is: {ja_detail}")
    ja_detail_db = JobApplicationDetailDb.get_by_id(session=db, id=jad_id)
    logger.warning(f"ja_detail_db after getting by id is: {ja_detail_db}")
    ja_detail_db.update(db, job_application_detail=ja_detail)
    logger.debug(f"ja_detail_db after update: {ja_detail_db}")
    return ja_detail_db

def insert_addresses(db, json_entities, jad_id, company_id, candidate_fe):
    addresses = ja_get_address_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(addresses)
    location = ""
    for address in addresses:
        address_db = JobApplicationAddressDb(job_application_address=address, jad_id=jad_id)
        address_db.insert_job_application_address(db)
        if address.city is not None and address.city != "null":
            location = address.city
        if address.state is not None and address.state != "null":
            if len(location) > 0:
                location = location + ", "
            location = location + address.state
        #candidate_fe.location = location

def insert_experiences_and_skills(db, json_entities, jad_id, company_id, candidate_fe):
    experiences, experience_skills = ja_get_experience_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(f"Experiences: {experiences} \n Experience Skills: {experience_skills}")
    current_company = ""
    current_designation = ""
    previous_companies = ""
    previous_industries = ""
    team_leading_experience = ""
    if experiences is not None:
        for experience in experiences:
            experience_db = JobApplicationExperienceDb(job_application_experience=experience, jad_id=jad_id)
            experience_db.insert_job_application_experience(session=db)
            is_current = False
            if len(current_company) > 0:
                previous_companies += experience.experience_company + ", " if experience.experience_company is not None else previous_companies
                if len(previous_industries) == 0 and experience.industry:
                    previous_industries = experience.industry
            if len(current_company) == 0:
                is_current = True
                current_company = experience.experience_company
                if len(previous_industries) == 0 and experience.industry:
                    previous_industries = experience.industry
            if len(current_designation) == 0:
                current_designation = experience.title
            if len(team_leading_experience) == 0 and team_leading_experience == "False":
                team_leading_experience = experience.team_lead_experience if experience.team_lead_experience else team_leading_experience
            populate_experience_fe(candidate_fe=candidate_fe, experience=experience, is_current=is_current)
    insert_experience_skills(db=db, candidate_fe=candidate_fe, company_id=company_id, jad_id=jad_id, experience_skills=experience_skills)

def insert_educations(db, json_entities, jad_id, company_id, candidate_fe):
    educations = ja_get_education_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(educations)
    is_current = True
    if educations is not None:
        for education in educations:
            education_db = JobApplicationEducationDb(job_application_education=education, jad_id=jad_id)
            education_db.insert_job_application_education(session=db)
            populate_education_fe(candidate_fe=candidate_fe, education=education, is_current=is_current)
            is_current = False

def insert_languages(db, json_entities, jad_id, company_id):
    languages = ja_get_languages_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(languages)
    if languages is not None:
        for language in languages:
            language_db = JobApplicationLanguageDb(job_application_language=language, jad_id=jad_id)
            language_db.insert_job_application_language(session=db)

def insert_certifications(db, json_entities, jad_id, company_id):
    certifications, certs_skills_dict = ja_get_certifications_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(f"Certification:{certifications} \n Cert skill: {certs_skills_dict}")
    if certifications is not None:
        for certification in certifications:
            certification_db = JobApplicationCertificationDb(job_application_certification=certification, jad_id=jad_id)
            certification_db.insert_job_application_certification(session=db)
            cert_skills_list = certs_skills_dict[certification_db.title]
            logger.debug(f"certication list for {certification_db.title} is {cert_skills_list}")
            if cert_skills_list is not None and len(cert_skills_list) > 0:
                JobApplicationCertificationSkillDb.insert_many(session=db, company_id=company_id, certification_db=certification_db, cert_skills_list=cert_skills_list)

def insert_projects(db, json_entities, jad_id, company_id):
    projects = ja_get_projects_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(projects)
    if projects is not None:
        for project in projects:
            project_db = JobApplicationProjectDb(job_application_project=project, jad_id=jad_id)
            project_db.insert_job_application_project(session=db)

def insert_awards(db, json_entities, jad_id, company_id):
    awards = ja_get_awards_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(awards)
    if awards is not None:
        for award in awards:
            award_db = JobApplicationAwardDb(award, jad_id=jad_id)
            award_db.insert_job_application_award(session=db)

def insert_publications(db, json_entities, jad_id, company_id):
    publications = ja_get_publications_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(publications)
    if publications is not None:
        for publication in publications:
            publication_db = JobApplicationPublicationDb(job_application_publication=publication, jad_id=jad_id)
            publication_db.insert_job_application_publication(session=db)

def insert_volunteers(db, json_entities, jad_id, company_id):
    volunteers = ja_get_volunteers_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(volunteers)
    if volunteers is not None:
        for volunteer in volunteers:
            volunteer_db = JobApplicationVolunteerDb(job_application_volunteer=volunteer, jad_id=jad_id)
            volunteer_db.insert_job_application_volunteer(session=db)

def insert_interests(db, json_entities, jad_id, company_id):
    interests = ja_get_interests_from_json(json_data=json_entities, company_id=company_id)
    logger.debug(interests)
    if interests is not None:
        for interest in interests:
            interest_db = JobApplicationInterestDb(job_application_interest=interest, jad_id=jad_id)
            interest_db.insert_job_application_interest(session=db)
