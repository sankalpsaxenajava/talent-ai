from intai.schemas.candidate_fe import CandidateFrontEnd
from intai.schemas.job_application_fe import JobApplicationFrontEnd
from .test_db import (
    BackgroundTaskDb,
    BackgroundTaskTypeEnum,
    global_test_get_job_application,
    global_test_get_job_posting_for_ja,
)
from intai.models.models import (
    SessionLocal,
    JobPostingDb,
    JobApplicationDb,
    SkillDb,
    JobApplicationSkillDb,
    JobPostingSkillDb,
    JobApplicationDetailDb,
    JobApplicationProjectDb,
    JobApplicationAddressDb,
    JobApplicationAwardDb,
    JobApplicationCertificationDb,
    JobApplicationCertificationSkillDb,
    JobApplicationEducationDb,
    JobApplicationExperienceDb,
    JobApplicationInterestDb,
    JobApplicationLanguageDb,
    JobApplicationPublicationDb,
    JobApplicationScoreDb,
    JobApplicationVolunteerDb,
)

from intai.workers.job_application_worker import JobApplicationWorker
from intai.workers.job_posting_worker import JobPostingWorker
from icecream import ic
import json
from dotenv import load_dotenv

from subprocess import Popen
from pathlib import Path
import os
import asyncio

# import requests


def delete_application_entities(session, company_id):
    JobApplicationAddressDb.delete_all(session, company_id)
    JobApplicationAwardDb.delete_all(session, company_id)
    JobApplicationCertificationSkillDb.delete_all(session, company_id)
    JobApplicationCertificationDb.delete_all(session, company_id)
    JobApplicationEducationDb.delete_all(session, company_id)
    JobApplicationExperienceDb.delete_all(session, company_id)
    JobApplicationInterestDb.delete_all(session, company_id)
    JobApplicationLanguageDb.delete_all(session, company_id)
    JobApplicationProjectDb.delete_all(session, company_id)
    JobApplicationPublicationDb.delete_all(session, company_id)
    JobApplicationVolunteerDb.delete_all(session, company_id)
    JobApplicationScoreDb.delete_all(session, company_id)
    JobApplicationDb.delete_all(session, company_id)
    JobApplicationDetailDb.delete_all(session, company_id)

class TestJobApplicationWorker:
    def setup_class(self):
        ic("Running python web server")
        load_dotenv()

        # TODO: Get the path from os.env
        self.test_server = Popen(
            [
                "python",
                "-m",
                "http.server",
                "-d",
                os.getenv("TEST_DATA_FOLDER"),
                "-b",
                "127.0.0.1",
                "9229",
            ]
        )
        import time
        time.sleep(2)

        ic("Server running for local test docs")
        self.session = SessionLocal()
        self.valid_job_posting = global_test_get_job_posting_for_ja(self.session)
        jp_worker = JobPostingWorker(self.valid_job_posting, self.session)
        jp_worker.run()
        ic(jp_worker.jobPostingDb)
        self.valid_job_application = global_test_get_job_application(self.session)
        self.valid_job_posting_db = jp_worker.jobPostingDb
        ic(self.valid_job_posting_db)
        self.valid_job_application_db = JobApplicationDb(
            self.valid_job_application, self.valid_job_posting_db.id
        )
        self.company_id = self.valid_job_posting.company_id
        self.valid_job_posting_db.ideal_candidate_score = 2
        ic(self.valid_job_application_db)
        assert self.valid_job_application_db is not None

    def teardown_class(self):
        ic(self.test_server.kill())
        delete_application_entities(self.session, self.company_id)
        JobPostingDb.delete_all(self.session, self.company_id)

        JobApplicationSkillDb.delete_all(self.session, self.company_id)
        JobPostingSkillDb.delete_all(self.session, self.company_id)
        SkillDb.delete_all(self.session, self.company_id)
        BackgroundTaskDb.delete_all(self.session, self.company_id)

    def test_extract_entities(self):
        """Test extract entities for job application."""
        ic("test_extract_entities")
        worker = JobApplicationWorker(self.valid_job_application, self.session)
        worker._load_job()
        asyncio.run(worker._save_db_and_extract_text(False))
        asyncio.run(worker._get_score_summay_and_basics())
        actual_entities = ""
        ic(f"Entities: {actual_entities}")
        actual_ja = JobApplicationDb.get_job_application_for_posting(
            self.session, self.company_id, self.valid_job_posting.client_job_id
        )[0]
        ic(f"actual_ja: {actual_ja}")
        assert actual_ja.status == "Extracted Entities"
        assert len(actual_ja.extracted_text) > 0
        assert len(actual_ja.parsed_resume) > 0
        delete_application_entities(self.session, self.company_id)

    def test_calculate_save_ranking(self):
        """Test calculation of ranking."""
        ic("test calculate save ranking")
        ic(self.valid_job_application)

        # populate the job posting with parsed info
        # Parse and Store the skills infor in jp_skills table
        actual_jp = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting_db.client_job_id
        )
        ic(f"actual_jp jd: {actual_jp}")
        ic(f"actual_jp jd: {actual_jp.parsed_jd}")

        worker = JobApplicationWorker(self.valid_job_application, self.session)

        worker.insert_update_entity(is_update=False)
        actual_entities = worker.extract_save_entities()
        ic(f"Entities: {actual_entities}")
        worker.update_applicant_entities(actual_entities)

        worker.calculate_save_ranking()
        jafe = worker.job_application_fe
        ic(jafe)
        assert jafe.location == "Ahmedabad, Gujarat"
        score = float(jafe.score)
        assert score > 0
        delete_application_entities(self.session, self.company_id)

    def test_update_applicant_entities(self):
        """Test update of ja details."""
        ic("*****" * 10)
        ic("test update ja details")
        ic("*****" * 10)
        ic(self.valid_job_application)

        # populate the job posting with parsed info
        # Parse and Store the skills infor in jp_skills table
        actual_jp = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting_db.client_job_id
        )
        ic(f"actual_jp jd: {actual_jp}")
        ic(f"actual_jp jd: {actual_jp.parsed_jd}")

        worker = JobApplicationWorker(self.valid_job_application, self.session)
        entities_path = Path(os.getenv("TEST_DATA_FOLDER"), "ja_entities.json")
        assert entities_path.exists()
        f = entities_path.open()
        entities = f.read()
        ic(entities)
        worker.insert_update_entity(is_update=False)
        #actual_entities = worker.extract_save_entities()
        #ic(f"Entities: {actual_entities}")
        worker._update_applicant_entities(self.session, jad_id = worker.job_application.jad_id, entities=entities)
        jafe = worker.job_application_fe
        ic(jafe)

        # check data exists in db
        actual_jad = JobApplicationDetailDb.get_job_application_detail(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(f"{actual_jad}")
        assert len(actual_jad.applicant_name) > 0
        assert actual_jad.applicant_name == "Ishan Shukla"
        assert actual_jad.applicant_resume_email == "ishanshuklaa@gmail.com"
        #assert actual_jad.applicant_resume_linkedin == "linkedin.com/in/ishan"

        assert actual_jad.experience_years > 0
        assert actual_jad.avg_tenure_org_years > 0
        assert actual_jad.avg_tenure_role_years > 0

        actual_address = JobApplicationAddressDb.get_address_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_address)
        assert actual_address.city != None and len(actual_address.city) > 0
        assert actual_address.city == "Ahmedabad"
        assert actual_address.state == "Gujarat"
        assert actual_address.country == "India"

        # Test experience and skills

        actual_experiences = JobApplicationExperienceDb.get_experience_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_experiences)
        # ic(skill_score_dict)
        assert actual_experiences is not None
        actual_experience = actual_experiences[0]
        assert actual_experience.title != None and len(actual_experience.title) > 0
        assert actual_experience.title == "Sr. Executive-Costing"

        actual_ja_skills = JobApplicationSkillDb.get_skills_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_ja_skills)
        skill_names = [sk.skill_name for sk in actual_ja_skills]
        ic(skill_names)
        actual_skill_name = skill_names[0]
        ic(actual_skill_name)
        assert len(actual_skill_name) > 0
        assert actual_skill_name == "Costing"

        # Test for education
        actual_educations = JobApplicationEducationDb.get_job_application_educations(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_educations)
        assert actual_educations != None and len(actual_educations) > 0
        actual_education = actual_educations[0]
        assert (
            actual_education.institution == "The Institute of Cost Accountants of India"
        )
        assert actual_education.degree_level == "Certification"
        assert actual_education.degree_field == "ICAI Final"

        # TODO #A Test for language
        actual_languages = JobApplicationLanguageDb.get_language_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_languages)
        assert actual_languages != None and len(actual_languages) > 0
        actual_language = actual_languages[0]
        assert actual_language.language_name == "English"
        assert actual_language.fluency_level == "Fluent"

        # Test for certification

        actual_certifications = (
            JobApplicationCertificationDb.get_job_application_certification(
                self.session, self.company_id, worker.job_application.jad_id
            )
        )

        ic(actual_certifications)
        assert actual_certifications is not None
        actual_certification = actual_certifications[0]
        assert (
            actual_certification.title != None and len(actual_certification.title) > 0
        )
        assert actual_certification.title == "ICAI Final"

        actual_jac_skills = (
            JobApplicationCertificationSkillDb.get_skills_by_certificate(
                self.session, self.company_id, actual_certification.id
            )
        )

        ic(actual_jac_skills)
        expected_cert_skill_name = "Costing"
        actual_cert_skills = [
            x for x in actual_jac_skills if x.skill_name == expected_cert_skill_name
        ]
        assert actual_cert_skills is not None and len(actual_cert_skills) > 0
        ic(actual_cert_skills)

        # TODO #D Test for projects. Use a job application which populates projects.

        actual_projects = JobApplicationProjectDb.get_projects_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_projects)
        assert actual_projects != None and len(actual_projects) > 0
        actual_project = actual_projects[0]
        assert actual_project.title == "SAP S/4 HANA Implementation"

        # TODO #D Test for awards. Use a job application which has an award
        actual_awards = JobApplicationAwardDb.get_awards_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_awards)
        assert actual_awards != None and len(actual_awards) > 0
        actual_award = actual_awards[0]
        assert actual_award.title == "Award 1"
        assert actual_award.award_authority == "Awarder"

        # TODO #D Test for Interests. use a job application with interests. use a job application with interests.
        actual_interests = JobApplicationInterestDb.get_interests_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_interests)
        assert actual_interests != None and len(actual_interests) > 0
        actual_interest = actual_interests[0]
        assert actual_interest.title == "Sports"

        # TODO #D Test for Publications. Use a test case with publications.
        actual_publications = (
            JobApplicationPublicationDb.get_job_application_publications(
                self.session, self.company_id, worker.job_application.jad_id
            )
        )

        ic(actual_publications)
        assert actual_publications != None and len(actual_publications) > 0
        actual_publication = actual_publications[0]
        assert actual_publication.title == "Publication 1"

        # TODO #A Test for Volunteers
        actual_volunteers = JobApplicationVolunteerDb.get_volunteers_by_jad(
            self.session, self.company_id, worker.job_application.jad_id
        )

        ic(actual_volunteers)
        assert actual_volunteers != None and len(actual_volunteers) > 0
        actual_volunteer = actual_volunteers[0]
        assert actual_volunteer.position == "Director"
        delete_application_entities(self.session, self.company_id)

    def test_run(self):
        """Test running of jobapplicationworker."""
        ic("****************************************************************")
        ic("test update run")
        ic("****************************************************************")
        ic(self.valid_job_application)

        # populate the job posting with parsed info
        # Parse and Store the skills infor in jp_skills table
        actual_jp = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting_db.client_job_id
        )
        ic(f"actual_jp jd: {actual_jp}")
        ic(f"actual_jp jd: {actual_jp.parsed_jd}")

        bg_task = BackgroundTaskDb(
            self.valid_job_application.company_id,
            message="Message",
            message_type=BackgroundTaskTypeEnum.JobApplication,
        )
        bg_task.insert_background_task(self.session)
        ic(bg_task)
        import timeit

        worker = JobApplicationWorker(self.valid_job_application, task_id=bg_task.id)

        timer = timeit.Timer(lambda: worker.run())
        execution_time = timer.timeit(1)

        print(f"********* Execution time: {execution_time} seconds *********")

        with SessionLocal() as session:
            actual_jad = JobApplicationDb.get_job_application_for_posting(
            session, self.company_id, self.valid_job_posting_db.client_job_id
            )[0]

            ic(f"{actual_jad}")
            assert actual_jad.status == "PROCESSED"
            actual_bg_tasks = BackgroundTaskDb.get_background_tasks(
                session, self.company_id
            )
            print(actual_bg_tasks)
            actual_bg_task = actual_bg_tasks[0]
            ic(actual_bg_task)
            assert actual_bg_task.status == "COMPLETED FE ERROR"

            BackgroundTaskDb.delete_all(session, self.company_id)
            delete_application_entities(session, self.company_id)

    def test_adjust_factor_score(self):
        """Test factor adjusting of score"""
        ic("test_adjust_factor_score")
        worker = JobApplicationWorker(self.valid_job_application, self.session)
        base_path = os.getenv("TEST_DATA_FOLDER")
        jd_file_path = os.path.join(base_path, "parsed_jd.json")
        jd_file = open(jd_file_path)
        jd_json = json.load(jd_file)
        ic(jd_json)
        factor_score = 82
        factor_file_path = os.path.join(base_path, "factor_response.json")
        factor_file = open(factor_file_path)
        factor_json = json.load(factor_file)
        ic(factor_json)

        actual_score = worker.get_adjusted_factor_score(factor_score, factor_json, jd_json)
        ic(actual_score)
        assert actual_score == 72


class TestJobApplicationFE:
    def test_application_fe(self):
        "Test Setting up applciation FE"
        candidate_fe = CandidateFrontEnd(
            companyId=1,
            firstName = "Shahrukh",
            lastName = "Khan",
            email = "shahrukh@gmail.com",
            phone = "1234567890",
            resumeUrl = "https://www.google.com",
            yearsOfExperience = 10,
            linkedInUrl = "https://www.linkedin.com",
            peopleManagement = True,
            spokenLanguages = "English",
            technicalTools = "Python, Java",
            yearOfGraduation = "2010",
            latestDegree = "Bachelor of Science in Computer Science",
            latestInstitution = "University of California, Berkeley",
            #noticePeriodInDays = 30,

        )

        job_application_fe = JobApplicationFrontEnd.create_copy(candidate_fe)
        ic(job_application_fe)
        assert job_application_fe.firstName == "Shahrukh"
        assert job_application_fe.yearOfGraduation == "2010"
        ic(job_application_fe.json())
