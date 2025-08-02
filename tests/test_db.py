""" Test the database crud operations here."""

from intai.models.models import (
    JobConversationChatDb,
    SessionLocal,
    JobApplicationDb,
    JobPostingDb,
    JobApplicationDetailDb,
    JobApplicationAddressDb,
    JobApplicationAwardDb,
    JobApplicationCertificationDb,
    JobApplicationCertificationSkillDb,
    JobApplicationEducationDb,
    JobApplicationExperienceDb,
    JobApplicationProjectDb,
    JobApplicationInterestDb,
    JobApplicationLanguageDb,
    JobApplicationPublicationDb,
    JobApplicationVolunteerDb,
    JobPostingSkillDb,
    JobApplicationSkillDb,
    JobApplicationScoreDb,
    SkillDb,
    BackgroundTaskDb,
    BackgroundTaskTypeEnum,
    CompanyDb,
    CandidateDb
)
from intai.schemas.job_posting import JobPosting
from intai.schemas.company import Company
from intai.schemas.job_application import (
    Candidate,
    JobApplication,
    JobApplicationDetail,
    JobApplicationAddress,
    JobApplicationAward,
    JobApplicationCertification,
    JobApplicationCertificationSkill,
    JobApplicationEducation,
    JobApplicationExperience,
    JobApplicationInterest,
    JobApplicationScore,
    JobApplicationLanguage,
    JobApplicationProject,
    JobApplicationPublication,
    JobApplicationVolunteer,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import select, delete
from icecream import ic
from sqlalchemy.orm import joinedload
import pytest
import msgpack

Base = declarative_base()

COMPANY_ID_JA_TEST = 1009
COMPANY_ID_JP_TEST = 1010


def global_test_get_job_posting(session):
    return JobPosting(
        company_id=COMPANY_ID_JP_TEST,
        client_job_id=99,
        job_posting_doc_url="http://localhost:9229/jp.docx",
        filtering_criteria="",
    )


def global_test_get_job_posting_for_ja(session):
    return JobPosting(
        company_id=COMPANY_ID_JA_TEST,
        client_job_id=99,
        job_posting_doc_url="http://localhost:9229/jp.docx",
        filtering_criteria="",
    )


def global_test_get_job_application(session):
    return JobApplication(
        company_id=COMPANY_ID_JA_TEST,
        client_job_application_id=100,
        client_job_id=99,
        resume_doc_url="http://localhost:9229/ja.pdf",
        candidate_email="test@west.com",
    )

def global_test_get_candidate(session):
    return Candidate(
        company_id=COMPANY_ID_JA_TEST,
        client_candidate_id=100,
        resume_doc_url="http://localhost:9229/ja.pdf",
        candidate_email="test@west.com"
    )


class BaseTestJobPostingDb:
    def setup_class(self):
        ic("setup_class is being called **** ")
        self.session = SessionLocal()
        self.valid_job_posting = global_test_get_job_posting(self.session)
        self.company_id = self.valid_job_posting.company_id
        self.valid_job_posting_db = JobPostingDb(self.valid_job_posting)
        self.valid_job_posting_db.ideal_candidate_score = 2

    def teardown_class(self):
        ic("Tearing Down now *********")
        JobPostingDb.delete_all(self.session, self.company_id)
        self.session.close()


def delete_application_entities_db(session, company_id, client_job_application_id):
    JobApplicationVolunteerDb.delete_all(session, company_id)
    JobApplicationInterestDb.delete_all(session, company_id)
    JobApplicationPublicationDb.delete_all(session, company_id)
    JobApplicationCertificationSkillDb.delete_all(session, company_id)
    JobApplicationCertificationDb.delete_all(session, company_id)
    JobApplicationProjectDb.delete_all(session, company_id)
    JobApplicationLanguageDb.delete_all(session, company_id)
    JobApplicationEducationDb.delete_all(session, company_id)
    JobApplicationExperienceDb.delete_all(session, company_id)
    JobApplicationAwardDb.delete_all(session, company_id)
    JobApplicationAddressDb.delete_all(session, company_id)
    JobApplicationDetailDb.delete_all(session, company_id)
    JobApplicationScoreDb.delete_all(session, company_id)
    session.execute(
        delete(JobApplicationDb).where(
            JobApplicationDb.client_job_application_id == client_job_application_id
        )
    )


def delete_candidate_entities_db(session, company_id, client_candidate_id):
    ic(f"company_id: {company_id}, client_candidate_id: {client_candidate_id}")
    JobApplicationVolunteerDb.delete_all(session, company_id)
    JobApplicationInterestDb.delete_all(session, company_id)
    JobApplicationPublicationDb.delete_all(session, company_id)
    JobApplicationCertificationSkillDb.delete_all(session, company_id)
    JobApplicationCertificationDb.delete_all(session, company_id)
    JobApplicationProjectDb.delete_all(session, company_id)
    JobApplicationLanguageDb.delete_all(session, company_id)
    JobApplicationEducationDb.delete_all(session, company_id)
    JobApplicationExperienceDb.delete_all(session, company_id)
    JobApplicationAwardDb.delete_all(session, company_id)
    JobApplicationAddressDb.delete_all(session, company_id)
    JobApplicationDetailDb.delete_all(session, company_id)
    session.execute(
        delete(CandidateDb).where(
            CandidateDb.client_candidate_id == client_candidate_id
        )
    )

class BaseTestJobApplicationDb:
    def setup_class(self):
        ic("setup_class JobApplication  is being called **** ")
        self.session = SessionLocal()
        # Create JobPostingDb in database
        self.valid_job_posting = JobPosting(
            company_id=2,
            client_job_id=98,
            job_posting_doc_url="http://localhost:9229/jp.docx",
            filtering_criteria="",
        )
        self.valid_job_posting_db = JobPostingDb(self.valid_job_posting)
        self.session.add(self.valid_job_posting_db)
        self.session.commit()

        self.valid_job_application = JobApplication(
            resume_doc_url="http://localhost:9229/ja.pdf",
            company_id=self.valid_job_posting.company_id,
            client_job_application_id=99,
            client_job_id=self.valid_job_posting.client_job_id,
            candidate_email="test@west.com",
        )

        ic(f"JobApplication Posting.Id is {self.valid_job_posting_db.id}")
        self.valid_job_application_db = JobApplicationDb(
            self.valid_job_application, self.valid_job_posting_db.id
        )

    def teardown_class(self):
        ic("Tearing Down for JobApplication now *********")
        company_id = self.valid_job_posting.company_id
        session = self.session
        delete_application_entities_db(
            session, company_id, self.valid_job_application_db.client_job_application_id
        )

        self.session.execute(
            delete(JobPostingDb).where(
                JobPostingDb.client_job_id == self.valid_job_posting_db.client_job_id
            )
        )
        self.session.commit()
        self.session.close()


class TestJobPostingDb(BaseTestJobPostingDb):
    def test_job_posting_db_valid(self):
        ic("test_job_posting_db_valid")
        self.session.add(self.valid_job_posting_db)
        self.session.commit()
        self.company_id = self.valid_job_posting_db.company_id
        actual = self.session.scalars(
            select(JobPostingDb).where(JobPostingDb.client_job_id == 99)
        ).first()
        ic(actual)
        assert actual.job_posting_doc_url == "http://localhost:9229/jp.docx"
        JobPostingDb.delete_all(self.session, self.company_id)

    def test_job_posting_db_upsert(self):
        ic("test_job_posting_db_valid")

        self.valid_job_posting_db.insert_job_posting(self.session)
        self.company_id = self.valid_job_posting_db.company_id
        ic(self.valid_job_posting_db)
        assert self.valid_job_posting_db.id > 0

        actual = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting_db.client_job_id
        )
        ic(actual)
        assert actual.job_posting_doc_url == "http://localhost:9229/jp.docx"

        dup_jp = JobPosting(
            company_id=self.valid_job_posting_db.company_id,
            client_job_id=self.valid_job_posting_db.client_job_id,
            job_posting_doc_url="http://www.google.com/jp.docx",
            filtering_criteria="Filter",
        )
        dup_jp_db = JobPostingDb(dup_jp)

        with pytest.raises(Exception):
            dup_jp_db.insert_job_posting(self.session)

        JobPostingDb.delete_all(self.session, self.company_id)
        # actual_jp_db = JobPostingDb.get_job_posting(
        #     self.session, self.company_id, self.valid_job_posting_db.client_job_id
        # )
        # ic(actual_jp_db)
        # assert actual_jp_db.job_posting_doc_url == "http://www.google.com/jp.docx"
        # assert actual_jp_db.filtering_criteria == "Filter"

    def test_job_posting_update_ideal_score(self):
        ic("test_job_posting_update_ideal_score")
        self.valid_job_posting_db.insert_job_posting(self.session)

        self.valid_job_posting_db.update_ideal_candidate_score(self.session, 9.88)
        actual = self.session.scalars(
            select(JobPostingDb).where(JobPostingDb.client_job_id == 99)
        ).first()
        ic(actual)
        assert actual.ideal_candidate_score == 9.88
        JobPostingDb.delete_all(self.session, self.company_id)

    def test_job_posting_get_jp(self):
        ic("test_job_posting_db_valid")
        self.valid_job_posting_db.insert_job_posting(self.session)
        actual = JobPostingDb.get_job_posting(
            self.session, self.company_id, self.valid_job_posting_db.client_job_id
        )

        ic(actual)
        assert actual.job_posting_doc_url == "http://localhost:9229/jp.docx"
        JobPostingDb.delete_all(self.session, self.company_id)

    def test_job_posting_delete_entities(self):
        """Delete the job posting and jobpostingskill entities"""
        ic("test_job_posting_delete_entities")
        ic("test_job_posting_db_valid")
        ic(f"Valid Job Posting Db: {self.valid_job_posting_db}")
        self.valid_job_posting_db.insert_job_posting(self.session)
        self.session.commit()
        job_posting_id = self.valid_job_posting_db.id
        client_job_id = self.valid_job_posting_db.client_job_id
        self.company_id = self.valid_job_posting_db.company_id
        actual = self.session.scalars(
            select(JobPostingDb).where(JobPostingDb.client_job_id == 99)
        ).first()
        ic(actual)
        valid_skill_db = SkillDb(
            company_id=self.company_id,
            standard_skill_name="Software Engineer",
            skill_name="Software Engg.",
        )
        self.session.add(valid_skill_db)
        self.session.commit()
        ic(f"SkillId for skill is {valid_skill_db.id}")
        valid_job_posting_skill_db = JobPostingSkillDb(
            company_id=2, job_posting_id=99, score=2.23, skill_id=valid_skill_db.id
        )
        self.session.add(valid_job_posting_skill_db)
        self.session.commit()

        JobPostingDb.delete_entities(self.session, self.company_id, client_job_id)

        actual = JobPostingDb.get_job_posting(
            self.session, self.company_id, client_job_id
        )

        ic(actual)
        assert actual is None

        actual_skills = JobPostingSkillDb.get_job_posting_skills(
            self.session, self.company_id, job_posting_id
        )

        ic(actual_skills)
        assert actual_skills is None or len(actual_skills) == 0

        JobPostingDb.delete_all(self.session, self.company_id)


class TestJobPostingSkillsDb:
    def setup_class(self):
        ic("setup_class is being called **** ")
        self.session = SessionLocal()
        self.company_id = 2

    def create_skill_entities(self):
        self.valid_skill_db = SkillDb(
            company_id=self.company_id,
            standard_skill_name="Software Engineer",
            skill_name="Software Engg.",
        )
        self.session.add(self.valid_skill_db)
        self.session.commit()
        ic(f"SkillId for skill is {self.valid_skill_db.id}")
        self.valid_job_posting_skill_db = JobPostingSkillDb(
            company_id=2, job_posting_id=99, score=2.23, skill_id=self.valid_skill_db.id
        )

    def delete_skill_entities(self):
        JobPostingSkillDb.delete_all(self.session, self.company_id)
        JobApplicationSkillDb.delete_all(self.session, self.company_id)
        SkillDb.delete_all(self.session, self.company_id)

    def teardown_class(self):
        ic("Tearing Down now *********")
        SkillDb.delete_all(self.session, self.company_id)
        self.session.commit()
        self.session.close()

    def test_job_posting_skills_db_valid(self):
        ic("testing the job posting skills db")
        self.create_skill_entities()

        self.session.add(self.valid_job_posting_skill_db)
        self.session.commit()
        actual = (
            # self.session.query(JobPostingSkillDb, SkillDb)
            # .filter(SkillDb.id == JobPostingSkillDb.skill_id)
            # .filter(SkillDb.standard_skill_name == "Software Engineer")
            # .first()
            self.session.query(JobPostingSkillDb)
            .options(joinedload(JobPostingSkillDb.skill))
            .join(SkillDb)
            .filter(SkillDb.standard_skill_name == "Software Engineer")
            .first()
        )
        ic(actual.skill)
        assert actual.skill.id > 0
        self.delete_skill_entities()

    def test_job_posting_skills_db_insert_skills_score(self):
        ic("Testing the job posting skills insert skills score")

        self.create_skill_entities()

        ocaml_skill_db = SkillDb(
            company_id=self.company_id,
            standard_skill_name="Ocaml",
            skill_name="Ocaml",
        )
        self.session.add(ocaml_skill_db)
        self.session.commit()

        skill_cum_score = {
            "Software Engg.": 1.25,
            "Ocaml": 1.87,
        }

        # Insert the job posting skills scorek
        JobPostingSkillDb.insert_many(
            self.session,
            self.company_id,
            self.valid_job_posting_skill_db.job_posting_id,
            skill_cum_score,
        )

        actual = (
            self.session.query(JobPostingSkillDb)
            .options(joinedload(JobPostingSkillDb.skill))
            .join(SkillDb)
            .filter(SkillDb.standard_skill_name == "Ocaml")
            .first()
        )
        ic(actual)
        ic(actual.skill)
        assert actual.skill.id > 0
        assert actual.score == 1.87

        # Delete all JobPostingSkill
        self.delete_skill_entities()

    def test_skill_db_insert_new_skills_jp(self):
        ic("testing the job posting skills db")

        self.create_skill_entities()

        # NOTE: Skills db is inserted with a single row of "Software Engg."
        # as standard skill name.

        skill_names_ip = ["Software Engg.", "Java", "Golang", "Ocaml"]

        skills_list = list(zip(skill_names_ip, skill_names_ip))

        SkillDb.insert_skills_no_duplicates(
            self.session, self.valid_skill_db.company_id, skills_list
        )

        actual_skills_list = SkillDb.get_skills(
            self.session, self.valid_skill_db.company_id, None
        )

        ic(actual_skills_list)
        assert len(actual_skills_list) == 4

        # Delete all JobPostingSkill
        self.delete_skill_entities()


class TestJobApplicationDb(BaseTestJobApplicationDb):

    def test_job_application_db_upsert(self):
        """Validate the insert and upsert functionality of JobApplicationDb.
        Currently duplication insert will raise an exception.

        """
        ic("test_job_application_db_upsert")
        self.valid_job_application_db.insert_job_application(self.session)
        company_id = self.valid_job_posting.company_id
        application_id = self.valid_job_application_db.id
        ic(application_id)

        actual = self.session.scalars(
            select(JobApplicationDb).where(
                JobApplicationDb.job_posting_id == self.valid_job_posting_db.id
            )
        ).first()
        ic(actual)
        assert actual.resume_doc_url == "http://localhost:9229/ja.pdf"

        dup_ja = JobApplication(
            company_id=company_id,
            client_job_id=self.valid_job_posting_db.client_job_id,
            client_job_application_id=self.valid_job_application_db.client_job_application_id,
            resume_doc_url="http://www.google.com/ja.docx",
        )
        dup_ja_db = JobApplicationDb(dup_ja, self.valid_job_posting_db.id)
        with pytest.raises(Exception):
            dup_ja_db.insert_job_application(self.session)

        JobApplicationDb.delete_all(self.session, company_id)

    def test_job_application_db_valid(self):
        ic("test_job_application_db_valid")
        self.valid_job_application_db.insert_job_application(self.session)
        company_id = self.valid_job_posting.company_id
        application_id = self.valid_job_application_db.id
        ic(application_id)

        actual = self.session.scalars(
            select(JobApplicationDb).where(
                JobApplicationDb.job_posting_id == self.valid_job_posting_db.id
            )
        ).first()
        ic(actual)
        assert actual.resume_doc_url == "http://localhost:9229/ja.pdf"

        self.valid_job_application_db.update_job_application(
            self.session,
            parsed_resume="ParsedResume",
            extracted_text="ExtractedText",
            status="Testing",
        )

        actuals = JobApplicationDb.get_job_application_for_posting(
            self.session,
            self.valid_job_posting.company_id,
            self.valid_job_posting.client_job_id,
        )
        actual = actuals[0]
        ic(actual)

        assert actual.parsed_resume == "ParsedResume"
        assert actual.extracted_text == "ExtractedText"
        assert actual.status == "Testing"

        valid_ja_detail = JobApplicationDetail(
            company_id=company_id,
            applicant_name="Test Applicant",
            # summary="Summary",
            applicant_resume_email="test@west.com",
            applicant_resume_linkedin="www.linkedin.com/tester",
            current_salary=100000,
            expected_salary=200000,
            notice_period=90,
            software_skills="Java, Ocaml, Sql, Python",
            avg_tenure_org_years=2,
            cert_education_new_domain=True,
            num_patents=2,
        )
        valid_ja_detail_db = JobApplicationDetailDb(
            valid_ja_detail
        )

        valid_ja_detail_db.insert(self.session)

        self.valid_job_application_db.update_job_application(
            self.session,
            jad_id=valid_ja_detail_db.id
        )
        valid_ja_detail.applicant_name = "TA2"
        valid_ja_detail_db.update(self.session, valid_ja_detail)
        actuals = JobApplicationDb.get_job_application_for_posting(
            self.session,
            self.valid_job_posting.company_id,
            self.valid_job_posting.client_job_id,
        )
        actual = actuals[0]
        assert actual.jad_id == valid_ja_detail_db.id
        actual_ja_detail = JobApplicationDetailDb.get_job_application_detail(
            session=self.session, company_id=company_id, jad_id=actual.jad_id
        )

        assert actual_ja_detail.applicant_resume_email == "test@west.com"
        assert actual_ja_detail.applicant_name == "TA2"

        # insert  and validate job address

        jad_id = actual_ja_detail.id
        ic(f"Jad id: {jad_id} jad: {actual_ja_detail}")

        valid_ja_address = JobApplicationAddress(
            company_id=company_id,
            city="Bareilly",
            state="UP",
            country="India",
            full_address="346/13, SS Nagar, Pilibhit Bypass, Bareilly, UP",
        )
        valid_ja_address_db = JobApplicationAddressDb(
            valid_ja_address, jad_id=jad_id
        )
        valid_ja_address_db.insert_job_application_address(self.session)

        actual_ja_address = JobApplicationAddressDb.get_address_by_jad(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_address)

        assert actual_ja_address.city == "Bareilly"

        # insert  and validate job award

        valid_ja_award = JobApplicationAward(
            company_id=company_id,
            title="Award 1",
            date_award="1 Jan 2023",
            award_authority="IEEE",
        )
        valid_ja_award_db = JobApplicationAwardDb(valid_ja_award, jad_id=jad_id)
        valid_ja_award_db.insert_job_application_award(self.session)

        actual_ja_awards = JobApplicationAwardDb.get_awards_by_jad(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_awards)
        assert len(actual_ja_awards) > 0
        actual_ja_award = actual_ja_awards[0]
        ic(actual_ja_award)

        assert actual_ja_award.title == "Award 1"

        # insert  and validate job experience

        valid_ja_experience = JobApplicationExperience(
            company_id=company_id,
            title="Sr. Engineer",
            experience_company="Expo",
            description="Description of expo",
            start_date="1/1/2023",
            end_date="1/1/2024",
            team_lead_experience=True,
            employment_type="FullTime",
            location="Delhi",
            years_experience=4,
            industry="Retail",
        )
        valid_ja_experience_db = JobApplicationExperienceDb(
            valid_ja_experience, jad_id=jad_id
        )
        valid_ja_experience_db.insert_job_application_experience(self.session)

        actual_ja_experiences = (
            JobApplicationExperienceDb.get_experience_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_experiences)

        assert len(actual_ja_experiences) > 0
        actual_ja_experience = actual_ja_experiences[0]
        ic(actual_ja_experience.__class__)
        ic(actual_ja_experience)
        assert actual_ja_experience.experience_company == "Expo"

        # insert  and validate job education

        valid_ja_education = JobApplicationEducation(
            company_id=company_id,
            institution="IET",
            degree_level="B.A.",
            degree_field="Arts",
        )
        valid_ja_education_db = JobApplicationEducationDb(
            valid_ja_education, jad_id=jad_id
        )
        valid_ja_education_db.insert_job_application_education(self.session)

        actual_ja_educations = JobApplicationEducationDb.get_job_application_educations(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_educations)

        assert len(actual_ja_educations) > 0
        actual_ja_education = actual_ja_educations[0]
        ic(actual_ja_education.__class__)
        ic(actual_ja_education)

        assert actual_ja_education.institution == "IET"

        # insert  and validate job language

        valid_ja_language = JobApplicationLanguage(
            company_id=company_id,
            language_name="Punjabi",
            fluency_level="Spoken",
        )
        valid_ja_language_db = JobApplicationLanguageDb(
            valid_ja_language, jad_id=jad_id
        )
        valid_ja_language_db.insert_job_application_language(self.session)

        actual_ja_languages = JobApplicationLanguageDb.get_language_by_jad(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_languages)
        assert len(actual_ja_languages) > 0
        actual_ja_language = actual_ja_languages[0]

        ic(actual_ja_language)

        assert actual_ja_language.language_name == "Punjabi"

        # insert  and validate job project

        valid_ja_project = JobApplicationProject(
            company_id=company_id,
            title="Hudson",
            tech_stack="C++, Assembly, Mainframes",
            public_urls="https://www.google.com",
        )
        valid_ja_project_db = JobApplicationProjectDb(
            valid_ja_project, jad_id=jad_id
        )
        valid_ja_project_db.insert_job_application_project(self.session)

        actual_ja_projects = JobApplicationProjectDb.get_projects_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        ic(actual_ja_projects)
        assert len(actual_ja_projects) > 0
        actual_ja_project = actual_ja_projects[0]

        ic(actual_ja_project)

        assert actual_ja_project.title == "Hudson"

        # insert  and validate job certification

        valid_ja_certification = JobApplicationCertification(
            company_id=company_id,
            title="AWS Certified",
            issue_date="Jan 1, 2023",
            issue_authority="Amazon",
        )
        valid_ja_certification_db = JobApplicationCertificationDb(
            valid_ja_certification, jad_id=jad_id
        )
        valid_ja_certification_db.insert_job_application_certification(self.session)

        actual_ja_certifications = (
            JobApplicationCertificationDb.get_job_application_certification(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_certifications)
        assert len(actual_ja_certifications) > 0
        actual_ja_certification = actual_ja_certifications[0]

        ic(actual_ja_certification)

        assert actual_ja_certification.title == "AWS Certified"

        # insert  and validate job certification skill

        valid_ja_certification_skill = JobApplicationCertificationSkill(
            company_id=company_id,
            skill_name="FST",
        )
        valid_ja_certification_skill_db = JobApplicationCertificationSkillDb(
            valid_ja_certification_skill, actual_ja_certification.id
        )
        valid_ja_certification_skill_db.insert_job_application_certification_skill(
            self.session
        )

        actual_ja_certification_skills = (
            JobApplicationCertificationSkillDb.get_skills_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_certification_skills)
        assert len(actual_ja_certification_skills) > 0
        actual_ja_certification_skill = actual_ja_certification_skills[0]
        ic(actual_ja_certification_skill)

        assert actual_ja_certification_skill.skill_name == "FST"

        # insert many certification skills
        cert_skills_insert = ["NLP", "SKIM"]
        JobApplicationCertificationSkillDb.insert_many(
            self.session, company_id, actual_ja_certification, cert_skills_insert
        )

        actual_many_ja_certification_skills = (
            JobApplicationCertificationSkillDb.get_skills_by_certificate(
                self.session, company_id, actual_ja_certification.id
            )
        )

        ic(actual_many_ja_certification_skills)
        assert len(actual_many_ja_certification_skills) > 1

        actual_many_ja_certification_skill = [
            x for x in actual_many_ja_certification_skills if x.skill_name == "SKIM"
        ]
        ic(actual_many_ja_certification_skill)

        assert (
            actual_many_ja_certification_skill is not None
            and len(actual_many_ja_certification_skill) > 0
        )

        # insert  and validate job publication

        valid_ja_publication = JobApplicationPublication(
            company_id=company_id,
            title="Patent",
            issue_date="Jan 1, 2023",
            description="Patent on how to write patents",
        )
        valid_ja_publication_db = JobApplicationPublicationDb(
            valid_ja_publication, jad_id=jad_id
        )
        valid_ja_publication_db.insert_job_application_publication(self.session)

        actual_ja_publications = (
            JobApplicationPublicationDb.get_job_application_publications(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_publications)
        assert len(actual_ja_publications) > 0
        actual_ja_publication = actual_ja_publications[0]
        ic(actual_ja_publication)

        assert actual_ja_publication.title == "Patent"

        # insert  and validate job interest

        valid_ja_interest = JobApplicationInterest(
            company_id=company_id,
            title="Sleeping",
        )
        valid_ja_interest_db = JobApplicationInterestDb(
            valid_ja_interest, jad_id=jad_id
        )
        valid_ja_interest_db.insert_job_application_interest(self.session)

        actual_ja_interests = JobApplicationInterestDb.get_interests_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        ic(actual_ja_interests)
        assert len(actual_ja_interests) > 0
        actual_ja_interest = actual_ja_interests[0]

        ic(actual_ja_interest)

        assert actual_ja_interest.title == "Sleeping"

        # insert  and validate job volunteer

        valid_ja_volunteer = JobApplicationVolunteer(
            company_id=company_id,
            organization="CRY",
            position="Chief Plumber",
        )
        valid_ja_volunteer_db = JobApplicationVolunteerDb(
            valid_ja_volunteer, jad_id=jad_id
        )
        valid_ja_volunteer_db.insert_job_application_volunteer(self.session)

        actual_ja_volunteers = JobApplicationVolunteerDb.get_volunteers_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        ic(actual_ja_volunteers)
        assert len(actual_ja_volunteers) > 0
        actual_ja_volunteer = actual_ja_volunteers[0]

        ic(actual_ja_volunteer)

        assert actual_ja_volunteer.organization == "CRY"

        # test delete_entities
        JobApplicationDb.delete_entities(
            self.session,
            company_id,
            self.valid_job_application_db.client_job_application_id,
        )
        actual_ja_address = JobApplicationAddressDb.get_address_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_address is None

        actual_ja_award = JobApplicationAwardDb.get_awards_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_award is None or len(actual_ja_award) == 0
        actual_ja_certification_skill = (
            JobApplicationCertificationSkillDb.get_skills_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )

        assert (
            actual_ja_certification_skill is None
            or len(actual_ja_certification_skill) == 0
        )

        actual_ja_certification = (
            JobApplicationCertificationDb.get_job_application_certification(
                self.session, company_id, jad_id=jad_id
            )
        )

        assert actual_ja_certification is None or len(actual_ja_certification) == 0
        actual_ja_address = JobApplicationAddressDb.get_address_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_address is None or len(actual_ja_address) == 0
        actual_ja_education = JobApplicationEducationDb.get_job_application_educations(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_education is None or len(actual_ja_education) == 0
        actual_ja_experience = (
            JobApplicationExperienceDb.get_experience_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )
        assert actual_ja_experience is None or len(actual_ja_experience) == 0
        actual_ja_interest = JobApplicationInterestDb.get_interests_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_interest is None or len(actual_ja_interest) == 0
        actual_ja_language = JobApplicationLanguageDb.get_language_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_language is None or len(actual_ja_language) == 0

        actual_ja_project = JobApplicationProjectDb.get_projects_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_project is None or len(actual_ja_project) == 0

        actual_ja_publication = (
            JobApplicationPublicationDb.get_job_application_publications(
                self.session, company_id, jad_id=jad_id
            )
        )
        assert actual_ja_publication is None or len(actual_ja_publication) == 0
        actual_ja_volunteer = JobApplicationVolunteerDb.get_volunteers_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_volunteer is None or len(actual_ja_volunteer) == 0
        actual_ja_skill = JobApplicationSkillDb.get_skills_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_skill is None or len(actual_ja_skill) == 0

        actual_ja_detail = JobApplicationDetailDb.get_job_application_detail(
            self.session, company_id, jad_id
        )
        assert actual_ja_detail is None
        actual_ja_score = JobApplicationScoreDb.get_job_application_score(
            self.session, company_id, application_id
        )
        assert actual_ja_score is None or len(actual_ja_score) == 0
        actual_ja = JobApplicationDb.get_job_application(
            self.session,
            company_id,
            self.valid_job_application_db.client_job_application_id,
        )
        assert actual_ja is None


class TestJobApplicationScoreDb(BaseTestJobApplicationDb):
    def test_job_application_score_db(self):
        ic("test_job_application_db_valid")
        self.valid_job_application_db.insert_job_application(self.session)
        company_id = self.valid_job_posting.company_id
        application_id = self.valid_job_application_db.id
        ic(application_id)
        ja_score = JobApplicationScore(
            company_id=company_id,
            bucket="A",
            score=2,
            factor_score=3.0,
            factor_explanation="Explain",
            factor_calculation="Calc",
            factor_summary="Summary",
            match_percent=9.2,
            learnability=True,
            industry_match=True,
            title_match=False,
            matching_skills="AWS, C#, Java",
        )
        ja_score_db = JobApplicationScoreDb(ja_score, application_id)
        ja_score_db.insert_job_application_score(self.session)
        actual_ja_score_db = JobApplicationScoreDb.get_job_application_score(
            self.session, company_id, application_id
        )
        ic(actual_ja_score_db[0])
        assert actual_ja_score_db[0].bucket == "A"
        ja_score_db.bucket = "C"
        ja_score_db.insert_job_application_score(self.session)
        actual_ja_score_db = JobApplicationScoreDb.get_job_application_score(
            self.session, company_id, application_id
        )
        ic(actual_ja_score_db[0])
        assert actual_ja_score_db[0].bucket == "C"
        assert actual_ja_score_db[0].factor_score == 3.0
        assert actual_ja_score_db[0].factor_explanation == "Explain"
        assert actual_ja_score_db[0].factor_calculation == "Calc"
        assert actual_ja_score_db[0].industry_match == True
        assert actual_ja_score_db[0].title_match == False
        assert actual_ja_score_db[0].factor_summary == "Summary"

class TestCandidateDb:

    def setup_class(self):
        ic("setup_class TestCandidateDb  is being called **** ")
        self.session = SessionLocal()

        self.valid_candidate = Candidate(
            resume_doc_url="http://localhost:9229/ja.pdf",
            company_id=2,
            client_candidate_id=99,
            candidate_email="test@west.com",
        )
        self.valid_candidate_db = CandidateDb(self.valid_candidate)


    def teardown_class(self):
        ic("Tearing Down for JobApplication now *********")
        company_id = self.valid_candidate_db.company_id
        session = self.session
        ic(self.valid_candidate_db.client_candidate_id)
        delete_candidate_entities_db(
            session=session, company_id=company_id, client_candidate_id=self.valid_candidate_db.client_candidate_id
        )

        self.session.commit()
        self.session.close()

    @pytest.mark.skip(reason="Upsert is not valid because client_candidate_id can't be null")
    def test_candidatedb_upsert(self):
        """Validate the insert and upsert functionality of CandidateDb
        Currently duplication insert will raise an exception.

        """
        ic("test_candidate_db_upsert")
        self.valid_candidate_db.insert_candidate(self.session)
        company_id = self.valid_candidate.company_id
        candidate_id = self.valid_candidate_db.id
        ic(candidate_id)

        actual = self.session.scalars(
            select(CandidateDb).where(
                CandidateDb.id == self.valid_candidate_db.id
            )
        ).first()
        ic(actual)
        assert actual.resume_doc_url == "http://localhost:9229/ja.pdf"

        dup_ca = Candidate(
            company_id=company_id,
            client_candidate_id=self.valid_candidate_db.client_candidate_id,
            resume_doc_url="http://www.google.com/ja.docx",
        )
        dup_ca_db = CandidateDb(dup_ca)
        with pytest.raises(Exception):
            dup_ca_db.insert_candidate(self.session)

        CandidateDb.delete_all(self.session, company_id)

    def test_candidatedb_valid(self):
        # TODO: This is not done yet
        ic("test_candidate_db_valid")
        self.valid_candidate_db.insert_candidate(self.session)
        company_id = self.valid_candidate.company_id
        candidate_id = self.valid_candidate_db.id
        ic(candidate_id)

        actual = self.session.scalars(
            select(CandidateDb).where(
                CandidateDb.id == self.valid_candidate_db.id
            )
        ).first()
        ic(actual)
        assert actual.resume_doc_url == "http://localhost:9229/ja.pdf"

        self.valid_candidate_db.update_candidate(
            self.session,
            parsed_resume="ParsedResume",
            extracted_text="ExtractedText",
            status="Testing",
        )

        actual = CandidateDb.get_candidate(
            self.session,
            self.valid_candidate_db.company_id,
            self.valid_candidate_db.client_candidate_id,
        )
        ic(actual)

        assert actual.parsed_resume == "ParsedResume"
        assert actual.extracted_text == "ExtractedText"
        assert actual.status == "Testing"

        valid_ja_detail = JobApplicationDetail(
            company_id=company_id,
            applicant_name="Test Applicant",
            # summary="Summary",
            applicant_resume_email="test@west.com",
            applicant_resume_linkedin="www.linkedin.com/tester",
            current_salary=100000,
            expected_salary=200000,
            notice_period=90,
            software_skills="Java, Ocaml, Sql, Python",
            avg_tenure_org_years=2,
            cert_education_new_domain=True,
            num_patents=2,
        )
        valid_ja_detail_db = JobApplicationDetailDb(
            valid_ja_detail
        )

        valid_ja_detail_db.insert(self.session)

        self.valid_candidate_db.update_candidate(
            self.session,
            jad_id=valid_ja_detail_db.id
        )
        actual = CandidateDb.get_candidate(
            self.session,
            self.valid_candidate_db.company_id,
            self.valid_candidate.client_candidate_id
        )
        assert actual.jad_id == valid_ja_detail_db.id
        actual_ja_detail = JobApplicationDetailDb.get_job_application_detail(
            session=self.session, company_id=company_id, jad_id=actual.jad_id
        )

        assert actual_ja_detail.applicant_resume_email == "test@west.com"

        # insert  and validate job address
        jad_id = actual_ja_detail.id
        ic(f"Jad id: {jad_id} jad: {actual_ja_detail}")

        valid_ja_address = JobApplicationAddress(
            company_id=company_id,
            city="Bareilly",
            state="UP",
            country="India",
            full_address="346/13, SS Nagar, Pilibhit Bypass, Bareilly, UP",
        )
        valid_ja_address_db = JobApplicationAddressDb(
            valid_ja_address, jad_id=jad_id
        )
        valid_ja_address_db.insert_job_application_address(self.session)

        actual_ja_address = JobApplicationAddressDb.get_address_by_jad(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_address)

        assert actual_ja_address.city == "Bareilly"

        # insert  and validate job award

        valid_ja_award = JobApplicationAward(
            company_id=company_id,
            title="Award 1",
            date_award="1 Jan 2023",
            award_authority="IEEE",
        )
        valid_ja_award_db = JobApplicationAwardDb(valid_ja_award, jad_id=jad_id)
        valid_ja_award_db.insert_job_application_award(self.session)

        actual_ja_awards = JobApplicationAwardDb.get_awards_by_jad(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_awards)
        assert len(actual_ja_awards) > 0
        actual_ja_award = actual_ja_awards[0]
        ic(actual_ja_award)

        assert actual_ja_award.title == "Award 1"

        # insert  and validate job experience

        valid_ja_experience = JobApplicationExperience(
            company_id=company_id,
            title="Sr. Engineer",
            experience_company="Expo",
            description="Description of expo",
            start_date="1/1/2023",
            end_date="1/1/2024",
            team_lead_experience=True,
            employment_type="FullTime",
            location="Delhi",
            years_experience=4,
            industry="Retail",
        )
        valid_ja_experience_db = JobApplicationExperienceDb(
            valid_ja_experience, jad_id=jad_id
        )
        valid_ja_experience_db.insert_job_application_experience(self.session)

        actual_ja_experiences = (
            JobApplicationExperienceDb.get_experience_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_experiences)

        assert len(actual_ja_experiences) > 0
        actual_ja_experience = actual_ja_experiences[0]
        ic(actual_ja_experience.__class__)
        ic(actual_ja_experience)
        assert actual_ja_experience.experience_company == "Expo"

        # insert  and validate job education

        valid_ja_education = JobApplicationEducation(
            company_id=company_id,
            institution="IET",
            degree_level="B.A.",
            degree_field="Arts",
        )
        valid_ja_education_db = JobApplicationEducationDb(
            valid_ja_education, jad_id=jad_id
        )
        valid_ja_education_db.insert_job_application_education(self.session)

        actual_ja_educations = JobApplicationEducationDb.get_job_application_educations(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_educations)

        assert len(actual_ja_educations) > 0
        actual_ja_education = actual_ja_educations[0]
        ic(actual_ja_education.__class__)
        ic(actual_ja_education)

        assert actual_ja_education.institution == "IET"

        # insert  and validate job language

        valid_ja_language = JobApplicationLanguage(
            company_id=company_id,
            language_name="Punjabi",
            fluency_level="Spoken",
        )
        valid_ja_language_db = JobApplicationLanguageDb(
            valid_ja_language, jad_id=jad_id
        )
        valid_ja_language_db.insert_job_application_language(self.session)

        actual_ja_languages = JobApplicationLanguageDb.get_language_by_jad(
            self.session, company_id, jad_id=jad_id
        )

        ic(actual_ja_languages)
        assert len(actual_ja_languages) > 0
        actual_ja_language = actual_ja_languages[0]

        ic(actual_ja_language)

        assert actual_ja_language.language_name == "Punjabi"

        # insert  and validate job project

        valid_ja_project = JobApplicationProject(
            company_id=company_id,
            title="Hudson",
            tech_stack="C++, Assembly, Mainframes",
            public_urls="https://www.google.com",
        )
        valid_ja_project_db = JobApplicationProjectDb(
            valid_ja_project, jad_id=jad_id
        )
        valid_ja_project_db.insert_job_application_project(self.session)

        actual_ja_projects = JobApplicationProjectDb.get_projects_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        ic(actual_ja_projects)
        assert len(actual_ja_projects) > 0
        actual_ja_project = actual_ja_projects[0]

        ic(actual_ja_project)

        assert actual_ja_project.title == "Hudson"

        # insert  and validate job certification

        valid_ja_certification = JobApplicationCertification(
            company_id=company_id,
            title="AWS Certified",
            issue_date="Jan 1, 2023",
            issue_authority="Amazon",
        )
        valid_ja_certification_db = JobApplicationCertificationDb(
            valid_ja_certification, jad_id=jad_id
        )
        valid_ja_certification_db.insert_job_application_certification(self.session)

        actual_ja_certifications = (
            JobApplicationCertificationDb.get_job_application_certification(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_certifications)
        assert len(actual_ja_certifications) > 0
        actual_ja_certification = actual_ja_certifications[0]

        ic(actual_ja_certification)

        assert actual_ja_certification.title == "AWS Certified"

        # insert  and validate job certification skill

        valid_ja_certification_skill = JobApplicationCertificationSkill(
            company_id=company_id,
            skill_name="FST",
        )
        valid_ja_certification_skill_db = JobApplicationCertificationSkillDb(
            valid_ja_certification_skill, actual_ja_certification.id
        )
        valid_ja_certification_skill_db.insert_job_application_certification_skill(
            self.session
        )

        actual_ja_certification_skills = (
            JobApplicationCertificationSkillDb.get_skills_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_certification_skills)
        assert len(actual_ja_certification_skills) > 0
        actual_ja_certification_skill = actual_ja_certification_skills[0]
        ic(actual_ja_certification_skill)

        assert actual_ja_certification_skill.skill_name == "FST"

        # insert many certification skills
        cert_skills_insert = ["NLP", "SKIM"]
        JobApplicationCertificationSkillDb.insert_many(
            self.session, company_id, actual_ja_certification, cert_skills_insert
        )

        actual_many_ja_certification_skills = (
            JobApplicationCertificationSkillDb.get_skills_by_certificate(
                self.session, company_id, actual_ja_certification.id
            )
        )

        ic(actual_many_ja_certification_skills)
        assert len(actual_many_ja_certification_skills) > 1

        actual_many_ja_certification_skill = [
            x for x in actual_many_ja_certification_skills if x.skill_name == "SKIM"
        ]
        ic(actual_many_ja_certification_skill)

        assert (
            actual_many_ja_certification_skill is not None
            and len(actual_many_ja_certification_skill) > 0
        )

        # insert  and validate job publication

        valid_ja_publication = JobApplicationPublication(
            company_id=company_id,
            title="Patent",
            issue_date="Jan 1, 2023",
            description="Patent on how to write patents",
        )
        valid_ja_publication_db = JobApplicationPublicationDb(
            valid_ja_publication, jad_id=jad_id
        )
        valid_ja_publication_db.insert_job_application_publication(self.session)

        actual_ja_publications = (
            JobApplicationPublicationDb.get_job_application_publications(
                self.session, company_id, jad_id=jad_id
            )
        )

        ic(actual_ja_publications)
        assert len(actual_ja_publications) > 0
        actual_ja_publication = actual_ja_publications[0]
        ic(actual_ja_publication)

        assert actual_ja_publication.title == "Patent"

        # insert  and validate job interest

        valid_ja_interest = JobApplicationInterest(
            company_id=company_id,
            title="Sleeping",
        )
        valid_ja_interest_db = JobApplicationInterestDb(
            valid_ja_interest, jad_id=jad_id
        )
        valid_ja_interest_db.insert_job_application_interest(self.session)

        actual_ja_interests = JobApplicationInterestDb.get_interests_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        ic(actual_ja_interests)
        assert len(actual_ja_interests) > 0
        actual_ja_interest = actual_ja_interests[0]

        ic(actual_ja_interest)

        assert actual_ja_interest.title == "Sleeping"

        # insert  and validate job volunteer

        valid_ja_volunteer = JobApplicationVolunteer(
            company_id=company_id,
            organization="CRY",
            position="Chief Plumber",
        )
        valid_ja_volunteer_db = JobApplicationVolunteerDb(
            valid_ja_volunteer, jad_id=jad_id
        )
        valid_ja_volunteer_db.insert_job_application_volunteer(self.session)

        actual_ja_volunteers = JobApplicationVolunteerDb.get_volunteers_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        ic(actual_ja_volunteers)
        assert len(actual_ja_volunteers) > 0
        actual_ja_volunteer = actual_ja_volunteers[0]

        ic(actual_ja_volunteer)

        assert actual_ja_volunteer.organization == "CRY"

        # test delete_entities
        CandidateDb.delete_entities(
            self.session,
            company_id,
            self.valid_candidate_db.client_candidate_id)

        actual_ja_address = JobApplicationAddressDb.get_address_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_address is None
        return

        actual_ja_award = JobApplicationAwardDb.get_awards_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_award is None or len(actual_ja_award) == 0
        actual_ja_certification_skill = (
            JobApplicationCertificationSkillDb.get_skills_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )

        assert (
            actual_ja_certification_skill is None
            or len(actual_ja_certification_skill) == 0
        )

        actual_ja_certification = (
            JobApplicationCertificationDb.get_job_application_certification(
                self.session, company_id, jad_id=jad_id
            )
        )

        assert actual_ja_certification is None or len(actual_ja_certification) == 0
        actual_ja_address = JobApplicationAddressDb.get_address_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_address is None or len(actual_ja_address) == 0
        actual_ja_education = JobApplicationEducationDb.get_job_application_educations(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_education is None or len(actual_ja_education) == 0
        actual_ja_experience = (
            JobApplicationExperienceDb.get_experience_by_jad(
                self.session, company_id, jad_id=jad_id
            )
        )
        assert actual_ja_experience is None or len(actual_ja_experience) == 0
        actual_ja_interest = JobApplicationInterestDb.get_interests_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_interest is None or len(actual_ja_interest) == 0
        actual_ja_language = JobApplicationLanguageDb.get_language_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_language is None or len(actual_ja_language) == 0

        actual_ja_project = JobApplicationProjectDb.get_projects_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_project is None or len(actual_ja_project) == 0

        actual_ja_publication = (
            JobApplicationPublicationDb.get_job_application_publications(
                self.session, company_id, jad_id=jad_id
            )
        )
        assert actual_ja_publication is None or len(actual_ja_publication) == 0
        actual_ja_volunteer = JobApplicationVolunteerDb.get_volunteers_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_volunteer is None or len(actual_ja_volunteer) == 0
        actual_ja_skill = JobApplicationSkillDb.get_skills_by_jad(
            self.session, company_id, jad_id=jad_id
        )
        assert actual_ja_skill is None or len(actual_ja_skill) == 0

        actual_ja_detail = JobApplicationDetailDb.get_job_application_detail(
            self.session, company_id, jad_id
        )
        assert actual_ja_detail is None
        actual_ja_score = JobApplicationScoreDb.get_job_application_score(
            self.session, company_id, application_id
        )
        assert actual_ja_score is None or len(actual_ja_score) == 0
        actual_ja = JobApplicationDb.get_job_application(
            self.session,
            company_id,
            self.valid_job_application_db.client_job_application_id,
        )
        assert actual_ja is None
        CandidateDb.delete_all(self.session, self.valid_candidate_db.company_id)

class TestJobApplicationSkillsDb:
    def setup_class(self):
        ic("setup_class is being called **** ")
        self.session = SessionLocal()
        self.company_id = 2

    def create_skill_entities(self):
        self.valid_skill_db = SkillDb(
            company_id=self.company_id,
            standard_skill_name="App Engineer",
            skill_name="App Engineer",
        )
        self.session.add(self.valid_skill_db)
        self.session.commit()
        ic(f"SkillId for skill is {self.valid_skill_db.id}")
        self.valid_job_application_skill_db = JobApplicationSkillDb(
            company_id=2,
            jad_id=99,
            score=2.23,
            skill_id=self.valid_skill_db.id,
        )
        self.job_application_id = 99
        self.jad_id = 99

    def delete_skill_entities(self):
        JobPostingSkillDb.delete_all(self.session, self.company_id)
        JobApplicationSkillDb.delete_all(self.session, self.company_id)
        SkillDb.delete_all(self.session, self.company_id)

    def teardown_class(self):
        ic("Tearing Down now *********")
        JobPostingSkillDb.delete_all(self.session, self.company_id)
        JobApplicationSkillDb.delete_all(self.session, self.company_id)
        SkillDb.delete_all(self.session, self.company_id)
        self.session.commit()
        self.session.close()

    def test_job_application_skills_db_valid(self):
        ic("testing the job application skills db")
        self.create_skill_entities()

        self.session.add(self.valid_job_application_skill_db)
        self.session.commit()
        actual_ja_skills = JobApplicationSkillDb.get_skills_by_jad(
            self.session, self.company_id, self.jad_id
        )[0]
        ic(actual_ja_skills)
        assert len(actual_ja_skills.skill_name) > 0
        self.delete_skill_entities()

    def test_job_application_skills_db_insert_skills_score(self):
        ic("Testing the job application skills insert skills score")

        self.create_skill_entities()
        ocaml_skill_db = SkillDb(
            company_id=self.company_id,
            standard_skill_name="Ocaml",
            skill_name="Ocaml",
        )
        self.session.add(ocaml_skill_db)
        self.session.commit()

        skill_cum_score = {
            "App Engineer": 1.25,
            "Ocaml": 1.87,
        }

        # Insert the job application skills scores
        JobApplicationSkillDb.insert_many(
            self.session,
            self.company_id,
            self.valid_job_application_skill_db.jad_id,
            skill_cum_score,
        )

        actual = (
            self.session.query(JobApplicationSkillDb)
            .options(joinedload(JobApplicationSkillDb.skill))
            .join(SkillDb)
            .filter(SkillDb.standard_skill_name == "Ocaml")
            .first()
        )
        ic(actual)
        ic(actual.skill)
        assert actual.skill.id > 0
        assert actual.score == 1.87

        # Delete all JobApplicationSkill
        self.delete_skill_entities()

    def test_skill_db_insert_new_skills_ja(self):
        ic("testing the job application skills db")

        self.create_skill_entities()
        # NOTE: Skills db is inserted with a single row of "Software Engg."
        # as standard skill name.

        skill_names_ip = ["Software Engg.", "Java", "Golang", "OCAML"]

        skills_list = list(zip(skill_names_ip, skill_names_ip))

        SkillDb.insert_skills_no_duplicates(
            self.session, self.valid_skill_db.company_id, skills_list
        )

        actual_skills_list = SkillDb.get_skills(
            self.session, self.valid_skill_db.company_id, None
        )

        ic(actual_skills_list)
        ocaml_skill_actual = [x for x in actual_skills_list if x.skill_name == "OCAML"]
        ic(ocaml_skill_actual)
        assert len(ocaml_skill_actual) > 0
        # Delete all JobApplicationSkill
        self.delete_skill_entities()


class TestJobConversationChatDb:

    def setup_class(self):
        ic("setup_class is being called **** ")
        self.session = SessionLocal()
        self.company_id = 2
        self.job_chat = JobConversationChatDb(
            company_id=self.company_id,
            message=msgpack.packb({"key": 2, "message": "start"}),
            conversation_id=99,
        )

    def teardown_class(self):
        ic("Tearing Down now *********")
        JobConversationChatDb.delete_all(self.session, self.company_id)
        self.session.commit()
        self.session.close()

    def test_job_conversation_chat(self):
        ic("testing the job conversation chatbot db")

        self.job_chat.insert_job_conversation_chat(self.session)
        actual_job_chat = JobConversationChatDb.get_job_conversation_chat(
            session=self.session,
            company_id=self.company_id,
            conversation_id=self.job_chat.conversation_id,
        )
        ic(actual_job_chat)
        self.job_chat.status = "CHANGED"
        self.job_chat.insert_job_conversation_chat(self.session)
        actual_job_chat = JobConversationChatDb.get_job_conversation_chat(
            session=self.session,
            company_id=self.company_id,
            conversation_id=self.job_chat.conversation_id,
        )
        ic(actual_job_chat)
        ic(msgpack.unpackb(actual_job_chat.message))
        assert actual_job_chat.message == self.job_chat.message
        assert actual_job_chat.status == "CHANGED"
        JobConversationChatDb.delete_all(self.session, self.company_id)

        actual_job_chat_notfound = JobConversationChatDb.get_job_conversation_chat(
            session=self.session,
            company_id=99,
            conversation_id=1111,
        )
        ic(actual_job_chat)
        assert actual_job_chat_notfound is None


class TestBackgroundTasks:
    def setup_class(self):
        ic("setup_class is being called **** ")
        self.session = SessionLocal()
        self.company_id = 2
        self.job_posting = JobPosting(
            company_id=self.company_id,
            client_job_id=98,
            job_posting_doc_url="http://localhost:9229/jp.docx",
            filtering_criteria="",
        )

        self.job_application = JobApplication(
            resume_doc_url="http://localhost:9229/ja.pdf",
            company_id=self.job_posting.company_id,
            client_job_application_id=99,
            client_job_id=self.job_posting.client_job_id,
            candidate_email="test@west.com",
        )

    def teardown_class(self):
        ic("Tearing Down now *********")
        BackgroundTaskDb.delete_all(self.session, self.company_id)
        self.session.commit()
        self.session.close()

    def test_background_tasks_jp(self):
        ic("testing the bg tasks db")
        jp_str = str(self.job_posting)
        ic(jp_str)
        bg_task = BackgroundTaskDb(
            self.company_id,
            message=jp_str,
            message_type=BackgroundTaskTypeEnum.JobPosting,
        )
        ic(bg_task)
        bg_task.insert_background_task(self.session)
        actual_bg_task = BackgroundTaskDb.get_background_tasks(
            self.session, self.company_id
        )[0]
        ic(actual_bg_task)
        assert actual_bg_task.message == bg_task.message
        assert actual_bg_task.message_type == bg_task.message_type
        BackgroundTaskDb.delete_all(self.session, self.company_id)

    def test_background_tasks_ja(self):
        ja_str = str(self.job_application)
        ic(ja_str)
        bg_task = BackgroundTaskDb(
            self.company_id,
            message=ja_str,
            message_type=BackgroundTaskTypeEnum.JobApplication,
        )
        ic(bg_task)
        bg_task.insert_background_task(self.session)
        actual_bg_task = BackgroundTaskDb.get_background_tasks(
            self.session, self.company_id
        )[0]
        ic(actual_bg_task)
        assert actual_bg_task.message == bg_task.message
        assert actual_bg_task.message_type == bg_task.message_type
        BackgroundTaskDb.delete_all(self.session, self.company_id)


class TestCompany:
    def setup_class(self):
        ic("setup_class is being called **** ")
        self.session = SessionLocal()
        self.company = Company(id=2, name="TestCompany", context_doc="Context123")

    def teardown_class(self):
        ic("Tearing Down now *********")
        CompanyDb.delete(self.session, self.company.id)
        self.session.commit()
        self.session.close()

    def test_company(self):
        ic("testing the companydb")
        companyDb = CompanyDb(self.company)
        ic(companyDb)
        companyDb.insert_company(self.session)
        actual_company = CompanyDb.get_company(self.session, self.company.id)
        ic(actual_company)
        assert actual_company.name == self.company.name
        assert actual_company.context_doc == self.company.context_doc
        companyDb.update_company(self.session, context_doc="Context987")
        actual_company = CompanyDb.get_company(self.session, self.company.id)
        ic(actual_company)
        assert actual_company.context_doc == "Context987"
