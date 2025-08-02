"""JobApplicationDb SQL model."""

import os
import timeit
import traceback
from dotenv import load_dotenv
from enum import Enum as PyEnum
from sqlalchemy import (
    LargeBinary,
    DateTime,
    ForeignKey,
    String,
    Text,
    delete,
    insert,
    select,
    update,
    Enum,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import (
    declarative_base,
    joinedload,
    sessionmaker,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from typing import List, Optional
from sqlalchemy.sql import func
from intai.schemas.job_application import (
    Candidate,
    JobApplication,
    JobApplicationDetail,
    JobApplicationAddress,
    JobApplicationAward,
    JobApplicationExperience,
    JobApplicationEducation,
    JobApplicationLanguage,
    JobApplicationProject,
    JobApplicationSkill,
    JobApplicationCertification,
    JobApplicationCertificationSkill,
    JobApplicationPublication,
    JobApplicationInterest,
    JobApplicationVolunteer,
    JobApplicationScore,
)
from intai.schemas.company import Company
from intai.schemas.job_posting import JobPosting
from loguru import logger

Base = declarative_base()


class CompanyDb(Base):
    """
    Company SQL model.

    Contains the main entry from api to
    save the work.
    """

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    context_doc: Mapped[Optional[str]] = mapped_column(Text)

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, company: Company):
        """Initialize the companyDb from Company model."""


        self.id = company.id
        self.name = company.name
        self.context_doc = company.context_doc

    def __repr__(self):
        """Represent string format of the JobPostingDb."""
        return "<CompanyDb: id:{}; name:{}>".format(self.id, self.name)

    def insert_company(self, session):
        """Insert the company in database."""

        try:
            from sqlalchemy.dialects.mysql import insert

            stmt = insert(CompanyDb).values(
                id=self.id,
                name=self.name,
                context_doc=self.context_doc,
            )
            result = session.execute(stmt)
            session.commit()
            if result is not None and len(result.inserted_primary_key) > 0:
                logger.debug(result.inserted_primary_key[0])
                self.id = result.inserted_primary_key[0]
            else:
                raise Exception(f"Insert failed for company: {self}")

        except Exception as err:
            logger.error(f"error insert_company {err}")
            raise err

    def update_company(
        self,
        session,
        context_doc=None,
        name=None,
    ):
        """Update the company in database."""

        try:
            logger.debug(self)
            assert self.id is not None
            val = {}
            if context_doc is not None:
                val["context_doc"] = context_doc
            if name is not None:
                val["name"] = name

            logger.debug(val)
            logger.debug(self.id)
            if len(val) > 0:
                stmt = update(CompanyDb).where(CompanyDb.id == self.id).values(val)
                session.execute(stmt)
                session.commit()
            else:
                raise Exception("len of query for update is 0")
        except Exception as err:
            logger.error(f"error update_company {err}")
            raise err

    @classmethod
    def get_company(cls, session, company_id):
        """Get company for company id."""
        logger.debug(f"{company_id} ")
        try:
            stmt = select(CompanyDb).filter(CompanyDb.id == company_id)
            logger.debug(f"{stmt}")
            result = session.execute(stmt).first()
            logger.debug(f"{result} {result.__class__}")
            return result[0] if result and len(result) > 0 else None

        except Exception as err:
            logger.error(f"{err}")
            raise err

    @classmethod
    def delete(cls, session, company_id: int):
        try:
            logger.info(f"Deleting entity company company_id: {company_id}")
            session.execute(delete(CompanyDb).where(CompanyDb.id == company_id))
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err


class JobPostingDb(Base):
    """
    Job Posting SQL model.

    Contains the main entry from api to
    save the work.
    """

    __tablename__ = "job_postings"
    __table_args__ = (
        UniqueConstraint("company_id", "client_job_id", name="uix_ci_cji"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    client_job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    job_posting_doc_url: Mapped[str] = mapped_column(String(2048))
    parsed_jd: Mapped[Optional[str]] = mapped_column(Text)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    ideal_candidate_score: Mapped[Optional[float]]
    # Filtering Criteria for this job
    filtering_criteria: Mapped[Optional[str]] = mapped_column(String(255))
    min_salary: Mapped[Optional[float]]
    max_salary: Mapped[Optional[float]]
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    status: Mapped[Optional[str]] = mapped_column(String(32))
    job_applications: Mapped[List["JobApplicationDb"]] = relationship(
        back_populates="job_posting"
    )

    def __init__(self, job_posting: JobPosting):
        """Initialize the JobPostingDb from JobPosting."""
        self.company_id = job_posting.company_id
        self.client_job_id = job_posting.client_job_id
        self.job_posting_doc_url = job_posting.job_posting_doc_url
        self.filtering_criteria = job_posting.filtering_criteria
        self.min_salary = job_posting.min_salary
        self.max_salary = job_posting.max_salary

    def __repr__(self):
        """Represent string format of the JobPostingDb."""
        return "<JobPostingDb: company_id:{}; id: {}, job_posting_doc_url: {}, ideal_candidate_score: {}, status: {}>".format(
            self.company_id,
            self.id,
            self.job_posting_doc_url,
            self.ideal_candidate_score,
            self.status,
        )

    def insert_job_posting(self, session):
        """Insert the job posting in database.

        NOTE: If the client_job_id, company_id already exists then
        this will perform an update.
        """

        try:
            from sqlalchemy.dialects.mysql import insert

            stmt = insert(JobPostingDb).values(
                company_id=self.company_id,
                client_job_id=self.client_job_id,
                job_posting_doc_url=self.job_posting_doc_url,
                parsed_jd=self.parsed_jd,
                extracted_text=self.extracted_text,
                ideal_candidate_score=self.ideal_candidate_score,
                filtering_criteria=self.filtering_criteria,
                min_salary=self.min_salary,
                max_salary=self.max_salary,
                status=self.status,
            )
            # stmt = stmt.on_duplicate_key_update(
            #     job_posting_doc_url=self.job_posting_doc_url,
            #     parsed_jd=self.parsed_jd,
            #     extracted_text=self.extracted_text,
            #     ideal_candidate_score=self.ideal_candidate_score,
            #     filtering_criteria=self.filtering_criteria,
            #     min_salary=self.min_salary,
            #     max_salary=self.max_salary,
            #     status=self.status,
            # )
            result = session.execute(stmt)
            session.commit()
            if result is not None and len(result.inserted_primary_key) > 0:
                logger.debug(result.inserted_primary_key[0])
                self.id = result.inserted_primary_key[0]
            else:
                raise Exception(f"Insert failed for posting: {self}")

        except Exception as err:
            logger.error(f"error insert_job_posting {err}")
            raise err

    def update_job_posting(
        self,
        session,
        parsed_jd=None,
        extracted_text=None,
        score=None,
        filtering_criteria=None,
        status=None,
    ):
        """Update the job posting in database."""

        try:
            logger.debug(self)
            assert self.id is not None
            val = {}
            if extracted_text is not None:
                val["extracted_text"] = extracted_text
            if parsed_jd is not None:
                val["parsed_jd"] = parsed_jd
            if score is not None:
                val["score"] = score
            if filtering_criteria is not None:
                val["filtering_criteria"] = filtering_criteria
            if status is not None:
                val["status"] = status

            logger.debug(val)
            logger.debug(self.id)
            if len(val) > 0:
                stmt = (
                    update(JobPostingDb).where(JobPostingDb.id == self.id).values(val)
                )
                session.execute(stmt)
                session.commit()
            else:
                raise Exception("len of query for update is 0")
        except Exception as err:
            logger.error(f"error update_job_posting {err}")
            raise err

    def update_ideal_candidate_score(self, session, score: float):
        """Update the ideal candidate score for this job posting."""
        try:
            stmt = (
                update(JobPostingDb)
                .where(JobPostingDb.id == self.id)
                .values(ideal_candidate_score=score)
            )
            session.execute(stmt)
            session.commit()
        except Exception as err:
            logger.error(f"error update ideal candidate score {err}")
            raise err

    @classmethod
    def get_job_posting(cls, session, company_id, client_job_id):
        """Get job posting for company and client-job-id."""
        logger.trace(f"{company_id} {client_job_id}")
        try:
            stmt = (
                select(JobPostingDb)
                .filter(JobPostingDb.company_id == company_id)
                .filter(JobPostingDb.client_job_id == client_job_id)
            )
            logger.trace(f"{stmt}")
            result = session.execute(stmt).first()
            logger.debug(f"{result} {result.__class__}")
            return result[0] if result and len(result) > 0 else None

        except Exception as err:
            logger.error(f"{err}")
            raise err

    @classmethod
    def delete(cls, session, company_id: int, job_posting_id: int):
        try:
            logger.info(
                f"Deleting entity JobPostingDb company_id: {company_id}; ja_id: {job_posting_id}"
            )
            session.execute(
                delete(JobPostingDb)
                .where(JobPostingDb.company_id == company_id)
                .where(JobPostingDb.id == job_posting_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_entities(cls, session, company_id: int, client_job_id: int):
        """Delete JobPosting and JobPostingSkills for this client_job_id.

        Also delete all the job applications which exist for this job posting.
        """
        try:
            logger.info(
                f"Deleting job posting entities: cid: {company_id}, cjid: {client_job_id}"
            )
            existing_job_posting_db = JobPostingDb.get_job_posting(
                session, company_id, client_job_id
            )
            if existing_job_posting_db:
                job_posting_id: int = existing_job_posting_db.id
                JobApplicationDb.delete_entities_for_job_posting(
                    session, company_id, client_job_id
                )
                JobPostingSkillDb.delete(session, company_id, job_posting_id)
                JobPostingDb.delete(session, company_id, job_posting_id)
            else:
                logger.error(
                    f"Existing JobPostingDb not found for update case: [cid: {company_id}], [cj_id: {client_job_id}]"
                )

        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        try:
            session.execute(
                delete(JobPostingDb).where(JobPostingDb.company_id == company_id)
            )
            session.commit()

        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationDb(Base):
    """
    Job Application SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint("company_id", "client_job_application_id", name="uix_ci_cjai"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int]
    client_job_application_id: Mapped[int]
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    jad_id: Mapped[int] = mapped_column(ForeignKey("ja_details.id"))

    # TODO #B: Can candidate email be null?
    candidate_email: Mapped[Optional[str]] = mapped_column(String(255))
    resume_doc_url: Mapped[str] = mapped_column(String(2048))

    # Parsed Resume JSON
    parsed_resume: Mapped[Optional[str]] = mapped_column(Text)

    # Extracted Text Data from Resume File
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)

    # TODO #B: Confirm if this is needed
    # scored_unique_skills = mapped_column(str)
    status: Mapped[Optional[str]] = mapped_column(String(32))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_posting: Mapped["JobPostingDb"] = relationship(
        back_populates="job_applications"
    )
    job_application_detail: Mapped[Optional["JobApplicationDetailDb"]] = relationship(
        back_populates="job_application"
    )
    job_application_score: Mapped[Optional["JobApplicationScoreDb"]] = relationship(
        back_populates="job_application"
    )

    def __init__(self, job_application: JobApplication, job_posting_id: int):
        """Initialize the JobApplicationDb from JobApplication."""
        self.company_id = job_application.company_id
        self.client_job_id = job_application.client_job_id
        self.client_job_application_id = job_application.client_job_application_id
        self.resume_doc_url = job_application.resume_doc_url
        self.job_posting_id = job_posting_id

    def __repr__(self):
        """Represent string format of the JobApplicationDb."""
        return "<JobApplicationDb: company_id:{}; id: {}; client_job_application_id: {}, job_posting_id: {}; status: {}; candidate_email: {}>".format(
            self.company_id,
            self.id,
            self.client_job_application_id,
            self.job_posting_id,
            self.status,
            self.candidate_email,
        )

    def insert_job_application(self, session):
        """Insert the job application in database.

        NOTE: If the client_job_application_id, company_id already exists then
        this will perform an update.
        """

        try:
            from sqlalchemy.dialects.mysql import insert
            start_time = timeit.default_timer()

            
            

            stmt = insert(JobApplicationDb).values(
                company_id=self.company_id,
                client_job_application_id=self.client_job_application_id,
                job_posting_id=self.job_posting_id,
                candidate_email=self.candidate_email,
                resume_doc_url=self.resume_doc_url,
                parsed_resume=self.parsed_resume,
                extracted_text=self.extracted_text,
                status=self.status,
            )
            # stmt = stmt.on_duplicate_key_update(
            #     candidate_email=self.candidate_email,
            #     resume_doc_url=self.resume_doc_url,
            #     parsed_resume=self.parsed_resume,
            #     extracted_text=self.extracted_text,
            #     status=self.status,
            # )
            result = session.execute(stmt)
            session.commit()
            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"oooooo=====( Execution time inserting job application is: {execution_time} seconds )===ooooo")
            if result is not None and len(result.inserted_primary_key) > 0:
                logger.debug(result.inserted_primary_key[0])
                self.id = result.inserted_primary_key[0]
            else:
                logger.error(f"Insert failed for application: {self}")
        except Exception as err:
            logger.error(str(err))
            raise err

    def update_job_application(
        self,
        session,
        jad_id = None,
        parsed_resume=None,
        extracted_text=None,
        resume_doc_url=None,
        candidate_email=None,
        status=None,
    ):
        """Update the job application in database."""
        val = {}
        if jad_id is not None:
            val["jad_id"] = jad_id
        if extracted_text is not None:
            val["extracted_text"] = extracted_text
        if parsed_resume is not None:
            val["parsed_resume"] = parsed_resume
        if resume_doc_url is not None:
            val["resume_doc_url"] = resume_doc_url
        if candidate_email is not None:
            val["candidate_email"] = candidate_email
        if status is not None:
            val["status"] = status

        logger.debug(val)
        try:
            if len(val) > 0:
                stmt = (
                    update(JobApplicationDb)
                    .where(JobApplicationDb.id == self.id)
                    .values(val)
                )
                session.execute(stmt)
                session.commit()
                logger.debug(self)
            else:
                raise Exception("len of query for update is 0.")
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, job_application_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationDb entity company_id: {company_id}; ja_id: {job_application_id}"
            )
            session.execute(
                delete(JobApplicationDb)
                .where(JobApplicationDb.company_id == company_id)
                .where(JobApplicationDb.id == job_application_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_entities_for_job_posting(
        cls, session, company_id: int, client_job_id: int
    ):
        """Delete all job application entities for client job id."""
        try:
            logger.info(
                "Deleting all job application entities for job_posting. cid:{company_id}, cjid: {client_job_id}"
            )
            # Find all the job applications for this job posting id.
            job_applications = JobApplicationDb.get_job_application_for_posting(
                session, company_id, client_job_id
            )
            logger.info(job_applications)

            if job_applications is not None:
                for job_application in job_applications:
                    logger.info(job_application)
                    cjaid = job_application.client_job_application_id
                    logger.info(cjaid)
                    JobApplicationDb.delete_entities(session, company_id, cjaid)
            else:
                logger.info("no Job applications found for this job posting.")

        except Exception as err:
            logger.error(str(err))
            logger.error(traceback.format_exc())
            raise err

    @classmethod
    def delete_entities(cls, session, company_id: int, client_job_application_id: int):
        """Delete all the jobapplication entities for this ja."""
        logger.info(
            f"Deleting job applications for company_id: {company_id}; ja_id: {client_job_application_id}"
        )

        try:
            existing_job_application_db = JobApplicationDb.get_job_application(
                session, company_id, client_job_application_id
            )
            if existing_job_application_db:
                job_application_id: int = existing_job_application_db.id
                jad_id: int = existing_job_application_db.jad_id

                JobApplicationScoreDb.delete(session, company_id, job_application_id)
                JobApplicationDb.delete(session, company_id, job_application_id)
                JobApplicationDetailDb.delete(session, company_id, jad_id=jad_id)
            else:
                logger.error(
                    f"Existing Job ApplicationDb not found for update case: [cid: {company_id}], [cja_id: {client_job_application_id}]"
                )
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        try:
            session.execute(
                delete(JobApplicationDb).where(
                    JobApplicationDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_application(cls, session, company_id, client_job_application_id):
        """Get the job application for client-job-application_id."""
        logger.debug(
            f"{company_id} for job application client id: {client_job_application_id}"
        )
        try:
            stmt = (
                select(JobApplicationDb)
                .filter(JobApplicationDb.company_id == company_id)
                .filter(
                    JobApplicationDb.client_job_application_id
                    == client_job_application_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).first()
            logger.debug(f"{result} {result.__class__}")
            return result[0] if result and len(result) > 0 else None
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_application_for_posting(cls, session, company_id, client_job_id):
        """Get the job application for the company and client-job-id."""
        logger.debug(f"{company_id} for job posting client id: {client_job_id}")
        try:
            job_posting_db = JobPostingDb.get_job_posting(
                session, company_id, client_job_id
            )
            logger.debug(f"{job_posting_db}")
            stmt = (
                select(JobApplicationDb)
                .filter(JobApplicationDb.company_id == company_id)
                .filter(JobApplicationDb.job_posting_id == job_posting_db.id)
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationDetailDb(Base):
    """
    Job Application Details SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_details"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    company_id: Mapped[int]
    applicant_name: Mapped[Optional[str]] = mapped_column(String(256))
    applicant_resume_email: Mapped[Optional[str]] = mapped_column(String(255))
    applicant_resume_phone: Mapped[Optional[str]] = mapped_column(String(32))
    applicant_resume_linkedin: Mapped[Optional[str]] = mapped_column(String(1024))
    current_salary: Mapped[Optional[float]]
    expected_salary: Mapped[Optional[float]]
    notice_period: Mapped[Optional[int]]
    gender: Mapped[Optional[str]] = mapped_column(String(16))

    summary: Mapped[Optional[str]] = mapped_column(Text)
    experience_years: Mapped[Optional[float]]
    software_skills: Mapped[Optional[str]] = mapped_column(Text)

    num_promotions: Mapped[Optional[int]]
    # Avg. Tenure in organization in years
    avg_tenure_org_years: Mapped[Optional[float]]
    # Avg. Tenure in role in years
    avg_tenure_role_years: Mapped[Optional[float]]
    num_awards: Mapped[Optional[int]]
    cert_education_new_domain: Mapped[Optional[bool]]
    significant_skill_change: Mapped[Optional[int]]
    num_published_papers: Mapped[Optional[int]]
    num_patents: Mapped[Optional[int]]
    num_conf_presentations: Mapped[Optional[int]]

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application: Mapped["JobApplicationDb"] = relationship(
        back_populates="job_application_detail"
    )
    candidate: Mapped["CandidateDb"] = relationship(
        back_populates="candidate_detail"
    )
    job_application_address: Mapped["JobApplicationAddressDb"] = relationship(
        back_populates="job_application_detail"
    )

    job_application_awards: Mapped[Optional[List["JobApplicationAwardDb"]]] = (
        relationship(back_populates="job_application_detail")
    )

    job_application_experiences: Mapped[
        Optional[List["JobApplicationExperienceDb"]]
    ] = relationship(back_populates="job_application_detail")

    job_application_educations: Mapped[Optional[List["JobApplicationEducationDb"]]] = (
        relationship(back_populates="job_application_detail")
    )

    job_application_languages: Mapped[Optional[List["JobApplicationLanguageDb"]]] = (
        relationship(back_populates="job_application_detail")
    )

    job_application_projects: Mapped[Optional[List["JobApplicationProjectDb"]]] = (
        relationship(back_populates="job_application_detail")
    )

    job_application_certifications: Mapped[
        Optional[List["JobApplicationCertificationDb"]]
    ] = relationship(back_populates="job_application_detail")

    job_application_publications: Mapped[
        Optional[List["JobApplicationPublicationDb"]]
    ] = relationship(back_populates="job_application_detail")

    job_application_interests: Mapped[Optional[List["JobApplicationInterestDb"]]] = (
        relationship(back_populates="job_application_detail")
    )

    job_application_volunteers: Mapped[Optional[List["JobApplicationVolunteerDb"]]] = (
        relationship(back_populates="job_application_detail")
    )
    

    def __init__(
        self,
        job_application_detail: JobApplicationDetail,
    ):
        """Initialize the JobApplicationDb from JobApplication."""
       
        if (job_application_detail):
            self.company_id = job_application_detail.company_id
            self.applicant_name = job_application_detail.applicant_name
            self.num_promotions = job_application_detail.num_promotions

            self.applicant_resume_email = job_application_detail.applicant_resume_email
            self.applicant_resume_phone = job_application_detail.applicant_resume_phone
            self.applicant_resume_linkedin = (
                job_application_detail.applicant_resume_linkedin
            )
            self.current_salary = job_application_detail.current_salary
            self.expected_salary = job_application_detail.expected_salary
            self.notice_period = job_application_detail.notice_period
            self.gender = job_application_detail.gender
            self.summary = job_application_detail.summary
            self.experience_years = job_application_detail.experience_years
            self.software_skills = job_application_detail.software_skills
            self.avg_tenure_org_years = job_application_detail.avg_tenure_org_years
            self.avg_tenure_role_years = job_application_detail.avg_tenure_role_years
            self.num_awards = job_application_detail.num_awards
            self.num_published_papers = job_application_detail.num_published_papers
            self.num_conf_presentations = job_application_detail.num_conf_presentations
            self.cert_education_new_domain = (
                job_application_detail.cert_education_new_domain
            )
        else: 
            logger.warning("JobApplicationDetailDb: job_application_detail is None")


    def __repr__(self):
        """Represent string format of the JobApplicationDb."""
        ret = "<JobApplicationDetailDb: company_id:{}; name: {}; email: {}; summary: {}; experience: {}; software_skills:{}; avg. org tenure: {}; avg role tenure:{}>"
        return ret.format(
            self.company_id,
            self.applicant_name,
            self.applicant_resume_email,
            self.summary,
            self.experience_years,
            self.software_skills,
            self.avg_tenure_org_years,
            self.avg_tenure_role_years,
        )

    @classmethod
    def get_by_id(cls, session, id):
        """Get the job application detail by id."""
        try:
            logger.info(f"Getting job application detail by id: {id}")
            return (
                session.query(JobApplicationDetailDb)
                .filter(JobApplicationDetailDb.id == id)
                .first()
            )
        except Exception as err:
            logger.error(str(err))
            raise err
        
    def insert(self, session):
        """Insert the job application detail in database."""
        try:
            logger.info(f"Inserting {self}")
            session.add(self)
            session.flush()
            session.commit()
            if self.id is None:
                logger.error(f"Insert failed for candidate: {self}")
            else:
                logger.warning(f"JAD ID: {self.id}")

        except Exception as err:
            logger.error(str(err))
            raise err

    def update(self, session, job_application_detail):
        """Update the job application detail in database."""
        try:
            logger.debug(f"self: {self}\n job_application_detail: {job_application_detail}")
            
            
            assert self.id is not None
            val = {}
            for attr, value in job_application_detail.__dict__.items():
                if hasattr(self, attr) and getattr(self, attr) != value and value is not None:
                    logger.debug(f"Updating {attr} from {getattr(self, attr)} to {value}")
                    val[attr] = value

            logger.debug(val)
            logger.debug(self.id)
            if len(val) > 0:
                stmt = (
                    update(JobApplicationDetailDb).where(JobApplicationDetailDb.id == self.id).values(val)
                )
                session.execute(stmt)
                session.commit()
                logger.info(f"Updated JAD ID: {self.id} Updated:{self}")
            else:
                raise Exception("No changes to update")
        except Exception as err:
            logger.error(f"Error updating job application detail: {err}")
            raise err


    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        """Delete the jobapplicationdetail based on jad_id."""
        try:
            logger.info(
                f"Deleting JobApplicationDetailDb entity company_id: {company_id}; ja_id: {jad_id}"
            )

            JobApplicationAddressDb.delete(session, company_id, jad_id)
            JobApplicationAwardDb.delete(session, company_id, jad_id)
            JobApplicationCertificationDb.delete(
                session, company_id, jad_id
            )
            JobApplicationEducationDb.delete(
                session, company_id, jad_id
            )
            JobApplicationExperienceDb.delete(
                session, company_id, jad_id
            )
            JobApplicationInterestDb.delete(session, company_id, jad_id)
            JobApplicationLanguageDb.delete(session, company_id, jad_id)
            JobApplicationProjectDb.delete(session, company_id, jad_id)
            JobApplicationPublicationDb.delete(
                session, company_id, jad_id
            )
            JobApplicationVolunteerDb.delete(
                session, company_id, jad_id
            )
            JobApplicationSkillDb.delete(session, company_id, jad_id)

            session.execute(
                delete(JobApplicationDetailDb)
                .where(JobApplicationDetailDb.company_id == company_id)
                .where(JobApplicationDetailDb.id == jad_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_by_candidate(cls, session, company_id: int, candidate_id: int):
        """Delete by Candidate."""
        try:
            logger.info(
                f"Deleting JobApplicationDetailDb entity company_id: {company_id}; cd_id: {candidate_id}"
            )
            session.execute(
                delete(JobApplicationDetailDb)
                .where(JobApplicationDetailDb.company_id == company_id)
                .where(JobApplicationDetailDb.candidate_id == candidate_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all jobapplicationdetails"""
        try:
            session.execute(
                delete(JobApplicationDetailDb).where(
                    JobApplicationDetailDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_application_detail(cls, session, company_id, jad_id):
        """Get the job application detail for the company and jad_id."""
        try:
            logger.debug(f"{company_id} {jad_id}")
            stmt = (
                select(JobApplicationDetailDb)
                .filter(JobApplicationDetailDb.company_id == company_id)
                .filter(JobApplicationDetailDb.id == jad_id)
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).first()
            logger.debug(f"{result} {result.__class__}")
            return result[0] if result and len(result) > 0 else None
        except Exception as err:
            logger.error(str(err))
            raise err


class CandidateDb(Base):
    """
    Candidate SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "candidates"
    # __table_args__ = (
    #     UniqueConstraint("company_id", "client_candidate_id", name="uix_ci_cci"),
    # )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int]
    jad_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ja_details.id"), nullable=True)
    client_candidate_id: Mapped[Optional[int]]

    # TODO #B: Can candidate email be null?
    candidate_email: Mapped[Optional[str]] = mapped_column(String(255))
    resume_doc_url: Mapped[Optional[str]] = mapped_column(String(2048))

    # Parsed Resume JSON
    parsed_resume: Mapped[Optional[str]] = mapped_column(Text)

    # Extracted Text Data from Resume File
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)

    # TODO #B: Confirm if this is needed
    status: Mapped[Optional[str]] = mapped_column(String(32))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    candidate_detail: Mapped[Optional["JobApplicationDetailDb"]] = relationship(
        back_populates="candidate"
    )

    def __init__(self, candidate: Candidate):
        """Initialize the CandidateDb from Candidate."""
        self.company_id = candidate.company_id
        self.jad_id = candidate.jad_id
        self.client_candidate_id = candidate.client_candidate_id
        self.resume_doc_url = candidate.resume_doc_url

    def __repr__(self):
        """Represent string format of the CandidateDb."""
        return "<CandidateDb: company_id:{}; id: {}; client_candidate_id: {}, status: {}; candidate_email: {}>".format(
            self.company_id,
            self.id,
            self.client_candidate_id,
            self.status,
            self.candidate_email,
        )

    def insert_candidate(self, session):
        """Insert the candidate in database.

        NOTE: If the client_candidate_id, company_id already exists then
        this will perform an update.
        """
        try:
            from sqlalchemy.dialects.mysql import insert

            stmt = insert(CandidateDb).values(
                company_id=self.company_id,
                jad_id=self.jad_id,
                client_candidate_id=self.client_candidate_id,
                candidate_email=self.candidate_email,
                resume_doc_url=self.resume_doc_url,
                parsed_resume=self.parsed_resume,
                extracted_text=self.extracted_text,
                status=self.status,
            )
            # stmt = stmt.on_duplicate_key_update(
            #     candidate_email=self.candidate_email,
            #     resume_doc_url=self.resume_doc_url,
            #     parsed_resume=self.parsed_resume,
            #     extracted_text=self.extracted_text,
            #     status=self.status,
            # )
            result = session.execute(stmt)
            session.commit()
            if result is not None and len(result.inserted_primary_key) > 0:
                logger.debug(result.inserted_primary_key[0])
                self.id = result.inserted_primary_key[0]
            else:
                logger.error(f"Insert failed for candidate: {self}")
        except Exception as err:
            logger.error(str(err))
            raise err

    def update_candidate(
        self,
        session,
        jad_id=None,
        parsed_resume=None,
        extracted_text=None,
        resume_doc_url=None,
        candidate_email=None,
        status=None,
    ):
        """Update the candidate in database."""
        val = {}
        if jad_id is not None:
            val["jad_id"] = jad_id
        if extracted_text is not None:
            val["extracted_text"] = extracted_text
        if parsed_resume is not None:
            val["parsed_resume"] = parsed_resume
        if resume_doc_url is not None:
            val["resume_doc_url"] = resume_doc_url
        if candidate_email is not None:
            val["candidate_email"] = candidate_email
        if status is not None:
            val["status"] = status

        logger.trace(val)
        try:
            if len(val) > 0:
                stmt = (
                    update(CandidateDb)
                    .where(CandidateDb.id == self.id)
                    .values(val)
                )
                session.execute(stmt)
                session.commit()
            else:
                raise Exception("len of query for update is 0.")
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, candidate_id: int):
        """Delete the Candidate object."""
        try:
            logger.info(
                f"Deleting CandidateDb entity company_id: {company_id}; candidate_id: {candidate_id}"
            )
            session.execute(
                delete(CandidateDb)
                .where(CandidateDb.company_id == company_id)
                .where(CandidateDb.id == candidate_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err


    @classmethod
    def delete_entities(cls, session, company_id: int, client_candidate_id: int):
        """Delete all the candidate entities for this candidate."""
        logger.info(
            f"Deleting candidates for company_id: {company_id}; candidate_id: {client_candidate_id}"
        )

        try:
            existing_candidate_db = CandidateDb.get_candidate(
                session, company_id, client_candidate_id
            )
            logger.warning(existing_candidate_db)
            if existing_candidate_db:
                candidate_id: int = existing_candidate_db.id

                CandidateDb.delete(session, company_id, candidate_id)
                JobApplicationDetailDb.delete(session, company_id, existing_candidate_db.jad_id)
            else:
                logger.error(
                    f"Existing CandidateDb not found for update case: [cid: {company_id}], [cc_id: {client_candidate_id}]"
                )
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        try:
            session.execute(
                delete(CandidateDb).where(
                    CandidateDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_candidate(cls, session, company_id, client_candidate_id):
        """Get the candidate for client-candidate_id."""
        logger.debug(
            f"{company_id} for candidate client id: {client_candidate_id}"
        )
        try:
            stmt = (
                select(CandidateDb)
                .filter(CandidateDb.company_id == company_id)
                .filter(
                    CandidateDb.client_candidate_id
                    == client_candidate_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).first()
            logger.debug(f"{result} {result.__class__}")
            return result[0] if result and len(result) > 0 else None
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationAddressDb(Base):
    """
    Job Application Addresses SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    city: Mapped[Optional[str]] = mapped_column(String(512))
    state: Mapped[Optional[str]] = mapped_column(String(512))
    country: Mapped[Optional[str]] = mapped_column(String(512))
    full_address: Mapped[Optional[str]] = mapped_column(String(2048))

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_address"
    )

    def __init__(
        self, job_application_address: JobApplicationAddress, jad_id: int
    ):
        """Initialize the JobApplicationAddressDb from JobApplicationAddress."""
        self.jad_id = jad_id
        self.company_id = job_application_address.company_id
        self.city = job_application_address.city
        self.state = job_application_address.state
        self.country = job_application_address.country
        self.full_address = job_application_address.full_address

    def __repr__(self):
        """Represent string format of the JobApplicationAddressDb."""
        ret = "<JobApplicationAddressDb: company_id:{}; id:{} jad_id: {}; city: {}; state: {}; country:{}; full_address:{}>"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.city,
            self.state,
            self.country,
            self.full_address,
        )

    def insert_job_application_address(self, session):
        """Insert the job application address in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationAddressDb entity company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationAddressDb)
                .where(JobApplicationAddressDb.company_id == company_id)
                .where(JobApplicationAddressDb.jad_id == jad_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        try:
            session.execute(
                delete(JobApplicationAddressDb).where(
                    JobApplicationAddressDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_address_by_jad(cls, session, company_id, jad_id):
        """Get the job application address for the company and jad_id"""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationAddressDb)
                .filter(JobApplicationAddressDb.company_id == company_id)
                .filter(
                    JobApplicationAddressDb.jad_id == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).first()
            logger.debug(f"{result} {result.__class__}")
            return result[0] if result and len(result) > 0 else None
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationAwardDb(Base):
    """
    Job Application Award SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_awards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    title: Mapped[Optional[str]] = mapped_column(String(512))
    date_award: Mapped[Optional[str]] = mapped_column(String(128))
    award_authority: Mapped[Optional[str]] = mapped_column(String(128))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_awards"
    )

    def __init__(
        self, job_application_award: JobApplicationAward, jad_id: int
    ):
        """Initialize the JobApplicationAwardDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_award.company_id
        self.title = job_application_award.title
        self.date_award = job_application_award.date_award
        self.award_authority = job_application_award.award_authority

    def __repr__(self):
        """Represent string format of the JobApplicationAwardDb."""
        ret = "<JobApplicationAwardDb: company_id:{}; id:{}"
        "jad_id: {}; title: {}; date_award: {};"
        " authority:{}>"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.title,
            self.date_award,
            self.award_authority,
        )

    def insert_job_application_award(self, session):
        """Insert the job application award in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationAwardDb entity company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationAwardDb)
                .where(JobApplicationAwardDb.company_id == company_id)
                .where(JobApplicationAwardDb.jad_id == jad_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        try:
            session.execute(
                delete(JobApplicationAwardDb).where(
                    JobApplicationAwardDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_awards_by_jad(cls, session, company_id, jad_id):
        """Get the job application award for the company and jad_id"""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationAwardDb)
                .filter(JobApplicationAwardDb.company_id == company_id)
                .filter(JobApplicationAwardDb.jad_id == jad_id)
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationExperienceDb(Base):
    """
    Job Application Experience SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_experiences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    title: Mapped[Optional[str]] = mapped_column(String(256))
    experience_company: Mapped[Optional[str]] = mapped_column(String(256))
    start_date: Mapped[Optional[str]] = mapped_column(String(128))
    end_date: Mapped[Optional[str]] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(String(256))
    location: Mapped[Optional[str]] = mapped_column(String(256))
    team_lead_experience: Mapped[Optional[int]]
    years_experience: Mapped[Optional[float]]
    employment_type: Mapped[Optional[str]] = mapped_column(String(128))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_experiences"
    )

    def __init__(
        self,
        job_application_experience: JobApplicationExperience,
        jad_id: int,
    ):
        """Initialize the JobApplicationExperienceDb from JobApplication."""
        self.jad_id = jad_id
        self.title = job_application_experience.title
        self.company_id = job_application_experience.company_id
        self.experience_company = job_application_experience.experience_company
        self.start_date = job_application_experience.start_date
        self.end_date = job_application_experience.end_date
        self.industry = job_application_experience.industry
        self.description = job_application_experience.description
        self.location = job_application_experience.location
        self.team_lead_expeirnce = job_application_experience.team_lead_experience
        self.years_experience = job_application_experience.years_experience

    def __repr__(self):
        """Represent string format of the JobApplicationExperienceDb."""
        ret = "<JobApplicationExperienceDb: [company_id]:{}; [id]:{} [jad_id]: {}; [title]: {}, [experience_company]: {}; [description]: {}; [industry]:{}>"

        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.title,
            self.experience_company,
            self.description,
            self.industry,
        )

    def insert_job_application_experience(self, session):
        """Insert the job application experience in database."""
        logger.debug(self)
        try:
            start_time = timeit.default_timer()

            session.add(self)
            session.commit()
            end_time = timeit.default_timer()
            execution_time = end_time - start_time
            logger.warning(f"oooooo=====( Execution time inserting app experience is: {execution_time} seconds )===ooooo")
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationExperienceDb entity company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationExperienceDb)
                .where(JobApplicationExperienceDb.company_id == company_id)
                .where(
                    JobApplicationExperienceDb.jad_id == jad_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the experiences for this company."""
        try:
            session.execute(
                delete(JobApplicationExperienceDb).where(
                    JobApplicationExperienceDb.company_id == company_id
                )
            )
            session.commit()

        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_experience_by_jad(
        cls, session, company_id, jad_id, limit=0
    ):
        """Get the job application experience for the company and jad_id."""
        logger.debug(f"cid: {company_id} jad:{jad_id} limit:{limit}")
        try:
            stmt = (
                select(JobApplicationExperienceDb)
                .filter(JobApplicationExperienceDb.company_id == company_id)
                .filter(
                    JobApplicationExperienceDb.jad_id == jad_id
                )
            )
            if limit > 0:
                stmt = stmt.limit(limit)

            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationEducationDb(Base):
    """
    Job Application Education SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_educations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    institution: Mapped[Optional[str]] = mapped_column(String(128))
    start_date: Mapped[Optional[str]] = mapped_column(String(128))
    end_date: Mapped[Optional[str]] = mapped_column(String(128))
    degree_level: Mapped[Optional[str]] = mapped_column(String(1024))
    degree_field: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_educations"
    )

    def __init__(
        self,
        job_application_education: JobApplicationEducation,
        jad_id: int,
    ):
        """Initialize the JobApplicationExperienceDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_education.company_id
        self.institution = job_application_education.institution
        self.start_date = job_application_education.start_date
        self.end_date = job_application_education.end_date
        self.degree_level = job_application_education.degree_level
        self.degree_field = job_application_education.degree_field

    def __repr__(self):
        """Represent string format of the JobApplicationEducationDb."""
        ret = "<JobApplicationEducationDb: company_id:{}; id:{} jad_id: {}; institurion: {}; degree_level: {}; degree_field:{}; start_date: {}; end_date: {}>"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.institution,
            self.degree_level,
            self.degree_field,
            self.start_date,
            self.end_date,
        )

    def insert_job_application_education(self, session):
        """Insert the job application education in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationEducationDb entity company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationEducationDb)
                .where(JobApplicationEducationDb.company_id == company_id)
                .where(
                    JobApplicationEducationDb.jad_id == jad_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the educations for this company."""
        try:
            session.execute(
                delete(JobApplicationEducationDb).where(
                    JobApplicationEducationDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_application_educations(cls, session, company_id, jad_id):
        """Get the job application education for the company and jad_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationEducationDb)
                .filter(JobApplicationEducationDb.company_id == company_id)
                .filter(
                    JobApplicationEducationDb.jad_id == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationLanguageDb(Base):
    """
    Job Application Language SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_languages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    language_name: Mapped[Optional[str]] = mapped_column(String(128))
    fluency_level: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_languages"
    )

    def __init__(
        self, job_application_language: JobApplicationLanguage, jad_id: int
    ):
        """Initialize the JobApplicationLanguageDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_language.company_id
        self.language_name = job_application_language.language_name
        self.fluency_level = job_application_language.fluency_level

    def __repr__(self):
        """Represent string format of the JobApplicationLanguageDb"""
        ret = "<JobApplicationLanguageDb: company_id:{}; id:{} jad_id: {}; language: {}; fluency_level: {};"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.language_name,
            self.fluency_level,
        )

    def insert_job_application_language(self, session):
        """Insert the job application language in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the languages for this company."""
        try:
            session.execute(
                delete(JobApplicationLanguageDb).where(
                    JobApplicationLanguageDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationLanguageDb entity company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationLanguageDb)
                .where(JobApplicationLanguageDb.company_id == company_id)
                .where(
                    JobApplicationLanguageDb.jad_id == jad_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_language_by_jad(cls, session, company_id, jad_id):
        """Get the job application language for the company and jad_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationLanguageDb)
                .filter(JobApplicationLanguageDb.company_id == company_id)
                .filter(
                    JobApplicationLanguageDb.jad_id == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationProjectDb(Base):
    """
    Job Application ProjectDb SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    title: Mapped[Optional[str]] = mapped_column(String(512))
    start_date: Mapped[Optional[str]] = mapped_column(String(128))
    end_date: Mapped[Optional[str]] = mapped_column(String(128))
    tech_stack: Mapped[Optional[str]] = mapped_column(String(2048))
    public_urls: Mapped[Optional[str]] = mapped_column(String(2048))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_projects"
    )

    def __init__(
        self, job_application_project: JobApplicationProject, jad_id: int
    ):
        """Initialize the JobApplicationProjectDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_project.company_id
        self.title = job_application_project.title
        self.start_date = job_application_project.start_date
        self.end_date = job_application_project.end_date
        self.tech_stack = job_application_project.tech_stack
        self.public_urls = job_application_project.public_urls

    def __repr__(self):
        """Represent string format of the JobApplicationProjectDb."""
        ret = "<JobApplicationProjectDb: company_id:{}; id:{} jad_id: {}; title: {}; tech_stack: {}; public_urls:{}>"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.title,
            self.tech_stack,
            self.public_urls,
        )

    def insert_job_application_project(self, session):
        """Insert the job application project in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()

        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the projects for this company."""
        try:
            session.execute(
                delete(JobApplicationProjectDb).where(
                    JobApplicationProjectDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationProjectDb entity company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationProjectDb)
                .where(JobApplicationProjectDb.company_id == company_id)
                .where(JobApplicationProjectDb.jad_id == jad_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_projects_by_jad(cls, session, company_id, jad_id):
        """Get the job application project for the company and jad_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationProjectDb)
                .filter(JobApplicationProjectDb.company_id == company_id)
                .filter(
                    JobApplicationProjectDb.jad_id == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationCertificationDb(Base):
    """
    Job Application CertificationDb SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    title: Mapped[Optional[str]] = mapped_column(String(512))
    issue_date: Mapped[Optional[str]] = mapped_column(String(128))
    issue_authority: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_certifications"
    )

    certification_skills: Mapped["JobApplicationCertificationSkillDb"] = relationship(
        back_populates="job_application_certification"
    )

    def __init__(
        self,
        job_application_certification: JobApplicationCertification,
        jad_id: int,
    ):
        """Initialize the JobApplicationCertificationDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_certification.company_id
        self.title = job_application_certification.title
        self.issue_date = job_application_certification.issue_date
        self.issue_authority = job_application_certification.issue_authority

    def __repr__(self):
        """Represent string format of the JobApplicationCertificationDb."""
        ret = "<JobApplicationCertificationDb: company_id:{}; id:{} jad_id: {}; title: {}; issue_date: {}; issue_authority:{}>"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.title,
            self.issue_date,
            self.issue_authority,
        )

    def insert_job_application_certification(self, session):
        """Insert the job application certification in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the certifications for this company."""
        try:
            session.execute(
                delete(JobApplicationCertificationDb).where(
                    JobApplicationCertificationDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationCertificationDb entity company_id: {company_id}; ja_id: {jad_id}"
            )
            certifications = (
                JobApplicationCertificationDb.get_job_application_certification(
                    session, company_id, jad_id
                )
            )
            # for each certification delete certification skill as well.
            for cert in certifications:
                JobApplicationCertificationSkillDb.delete(session, company_id, cert.id)

            session.execute(
                delete(JobApplicationCertificationDb)
                .where(JobApplicationCertificationDb.company_id == company_id)
                .where(
                    JobApplicationCertificationDb.jad_id
                    == jad_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_application_certification(cls, session, company_id, jad_id):
        """Get the job application certification for the company and jad_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationCertificationDb)
                .filter(JobApplicationCertificationDb.company_id == company_id)
                .filter(
                    JobApplicationCertificationDb.jad_id
                    == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationCertificationSkillDb(Base):
    """
    Job Application CertificationSkillDb SQL model.

    Contains the main entry from api to
    save the work
    TODO #C: Should we have a foreign key with skills table here.
    """

    __tablename__ = "ja_certification_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    certification_id: Mapped[int] = mapped_column(ForeignKey("ja_certifications.id"))
    company_id: Mapped[int]

    skill_name: Mapped[Optional[str]] = mapped_column(String(512))

    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_certification: Mapped["JobApplicationCertificationDb"] = (
        relationship(back_populates="certification_skills")
    )

    def __init__(
        self,
        certification_skill: JobApplicationCertificationSkill,
        certification_id: int,
    ):
        """Initialize the JobApplicationCertificationSkillDb from JobApplication."""
        self.certification_id = certification_id
        self.company_id = certification_skill.company_id
        self.skill_name = certification_skill.skill_name

    def __repr__(self):
        """Represent string format of the JobApplicationCertificationSkillDb."""
        ret = "<JobApplicationCertificationSkillDb: company_id:{}; id:{} certification_id: {}; skill_name:{}>"
        return ret.format(
            self.company_id,
            self.id,
            self.certification_id,
            self.skill_name,
        )

    def insert_job_application_certification_skill(self, session):
        """Insert the job application certificationskill in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    def get_dict(self):
        """Provide this class as a dictionary."""
        return {
            "company_id": self.company_id,
            "skill_name": self.skill_name,
            "certification_id": self.certification_id,
        }

    @classmethod
    def insert_many(
        cls,
        session,
        company_id: int,
        certification_db: JobApplicationCertificationDb,
        cert_skills_list: list[str],
    ):
        """Insert list of job application certification skills into database.

        This assumes certification was inserted into certification table.

        """
        logger.debug(f"{company_id}, {certification_db}, {cert_skills_list}")
        # For each skill in cert_skills_list build a JobApplicationCertificationSkill
        # object and add it
        jac_skills = []
        try:

            for skill_name in cert_skills_list:
                logger.debug(f"{skill_name} {certification_db.id}")
                cert_skill = JobApplicationCertificationSkill(
                    company_id=company_id,
                    skill_name=skill_name,
                )
                jac_skill = JobApplicationCertificationSkillDb(
                    certification_skill=cert_skill,
                    certification_id=certification_db.id,
                )
                jac_skills.append(jac_skill.get_dict())

            logger.debug(f"Job Cert Skills dictionary to insert:\n {jac_skills}")

            # Insert the skills to JobApplicationCertificationSkills db
            if len(jac_skills) > 0:
                stmt = insert(JobApplicationCertificationSkillDb).values(jac_skills)
                session.execute(stmt)
                session.commit()
            else:
                logger.debug("No new skills to insert as length is 0")
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the certificationskills for this company."""
        try:
            session.execute(
                delete(JobApplicationCertificationSkillDb).where(
                    JobApplicationCertificationSkillDb.company_id == company_id
                )
            )
            session.commit()

        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, certification_id: int):
        try:
            logger.info(
                f"Deleting JobApplicationCertificationSkillDb entity company_id: {company_id}; certification_id: {certification_id}"
            )
            session.execute(
                delete(JobApplicationCertificationSkillDb)
                .where(JobApplicationCertificationSkillDb.company_id == company_id)
                .where(
                    JobApplicationCertificationSkillDb.certification_id
                    == certification_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_skills_by_jad(cls, session, company_id, jad_id):
        """Get the job application certificationskill for the application with
        company and application_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationCertificationSkillDb)
                .join(JobApplicationCertificationDb)
                .filter(JobApplicationCertificationSkillDb.company_id == company_id)
                .filter(
                    JobApplicationCertificationDb.jad_id
                    == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_skills_by_certificate(cls, session, company_id, certification_id):
        """Get the job application certificationskill for the application with
        company and certification_id."""
        logger.debug(f"{company_id} {certification_id}")
        try:
            stmt = (
                select(JobApplicationCertificationSkillDb)
                .join(JobApplicationCertificationDb)
                .filter(JobApplicationCertificationSkillDb.company_id == company_id)
                .filter(
                    JobApplicationCertificationSkillDb.certification_id
                    == certification_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationPublicationDb(Base):
    """
    Job Application PublicationDb SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_publications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    title: Mapped[Optional[str]] = mapped_column(String(512))
    issue_date: Mapped[Optional[str]] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_publications"
    )

    def __init__(
        self,
        job_application_publication: JobApplicationPublication,
        jad_id: int,
    ):
        """Initialize the JobApplicationPublicationDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_publication.company_id
        self.title = job_application_publication.title
        self.issue_date = job_application_publication.issue_date
        self.description = job_application_publication.description

    def __repr__(self):
        """Represent string format of the JobApplicationCertificationDb"""
        ret = "<JobApplicationPublicationDb: company_id:{}; id:{} jad_id: {}; title: {}; issue_date: {}; description:{}>"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.title,
            self.issue_date,
            self.description,
        )

    def insert_job_application_publication(self, session):
        """Insert the job application publication in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the publications for this company."""
        try:
            session.execute(
                delete(JobApplicationPublicationDb).where(
                    JobApplicationPublicationDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting entity JobApplicationPublicationDb company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationPublicationDb)
                .where(JobApplicationPublicationDb.company_id == company_id)
                .where(
                    JobApplicationPublicationDb.jad_id == jad_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_application_publications(cls, session, company_id, jad_id):
        """Get the job application publication for the company and jad_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationPublicationDb)
                .filter(JobApplicationPublicationDb.company_id == company_id)
                .filter(
                    JobApplicationPublicationDb.jad_id == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationInterestDb(Base):
    """
    Job Application InterestDb SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_interests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    title: Mapped[Optional[str]] = mapped_column(String(512))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_interests"
    )

    def __init__(
        self, job_application_interest: JobApplicationInterest, jad_id: int
    ):
        """Initialize the JobApplicationInterestDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_interest.company_id
        self.title = job_application_interest.title

    def __repr__(self):
        """Represent string format of the JobApplicationInterestDb."""
        ret = "<JobApplicationInterestDb: company_id:{}; id:{} jad_id: {}; title: {};"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.title,
        )

    def insert_job_application_interest(self, session):
        """Insert the job application interest in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the interests for this company."""
        try:
            session.execute(
                delete(JobApplicationInterestDb).where(
                    JobApplicationInterestDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting entity JobApplicationInterestDb company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationInterestDb)
                .where(JobApplicationInterestDb.company_id == company_id)
                .where(
                    JobApplicationInterestDb.jad_id == jad_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_interests_by_jad(cls, session, company_id, jad_id):
        """Get the job application interest for the company and jad_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationInterestDb)
                .filter(JobApplicationInterestDb.company_id == company_id)
                .filter(
                    JobApplicationInterestDb.jad_id == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationVolunteerDb(Base):
    """
    Job Application VolunteerDb SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_volunteers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jad_id: Mapped[int] = mapped_column(
        ForeignKey("ja_details.id")
    )
    company_id: Mapped[int]

    organization: Mapped[Optional[str]] = mapped_column(String(512))
    position: Mapped[Optional[str]] = mapped_column(String(512))
    start_date: Mapped[Optional[str]] = mapped_column(String(128))
    end_date: Mapped[Optional[str]] = mapped_column(String(128))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application_detail: Mapped["JobApplicationDetailDb"] = relationship(
        back_populates="job_application_volunteers"
    )

    def __init__(
        self,
        job_application_volunteer: JobApplicationVolunteer,
        jad_id: int,
    ):
        """Initialize the JobApplicationInterestDb from JobApplication."""
        self.jad_id = jad_id
        self.company_id = job_application_volunteer.company_id
        self.organization = job_application_volunteer.organization
        self.position = job_application_volunteer.position
        self.start_date = job_application_volunteer.start_date
        self.end_date = job_application_volunteer.end_date

    def __repr__(self):
        """Represent string format of the JobApplicationVolunteerDb."""
        ret = "<JobApplicationVolunteerDb: company_id:{}; id:{} jad_id: {}; organizaiton: {}; position: {}"
        return ret.format(
            self.company_id,
            self.id,
            self.jad_id,
            self.organization,
            self.position,
        )

    def insert_job_application_volunteer(self, session):
        """Insert the job application volunteer in database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the volunteers for this company."""
        try:
            session.execute(
                delete(JobApplicationVolunteerDb).where(
                    JobApplicationVolunteerDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting entity JobApplicationVolunteerDb company_id: {company_id}; ja_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationVolunteerDb)
                .where(JobApplicationVolunteerDb.company_id == company_id)
                .where(
                    JobApplicationVolunteerDb.jad_id == jad_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_volunteers_by_jad(cls, session, company_id, jad_id):
        """Get the job application volunteer for the company and jad_id."""
        logger.debug(f"{company_id} {jad_id}")
        try:
            stmt = (
                select(JobApplicationVolunteerDb)
                .filter(JobApplicationVolunteerDb.company_id == company_id)
                .filter(
                    JobApplicationVolunteerDb.jad_id == jad_id
                )
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class SkillDb(Base):
    """
    Skill Sql Model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int]

    # Skill name from job posting or resume.
    skill_name: Mapped[str] = mapped_column(String(128))
    standard_skill_name: Mapped[Optional[str]] = mapped_column(String(128))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_posting_skills: Mapped[Optional[List["JobPostingSkillDb"]]] = relationship(
        back_populates="skill"
    )
    job_application_skills: Mapped[Optional[List["JobApplicationSkillDb"]]] = (
        relationship(back_populates="skill")
    )

    def __init__(self, company_id: int, skill_name: str, standard_skill_name: str):
        """Initialize the JobApplicationDb from JobApplication."""
        self.company_id = company_id
        self.skill_name = skill_name
        self.standard_skill_name = standard_skill_name

    def __repr__(self):
        """Represent string format of the JobApplicationDb."""
        return "<SkillDb: company_id:{}; id: {}; skill_name: {}; standard_skill_name: {}>".format(
            self.company_id, self.id, self.skill_name, self.standard_skill_name
        )

    def get_dict(self):
        """Provide this class as a dictionary."""
        return {
            "company_id": self.company_id,
            "skill_name": self.skill_name,
            "standard_skill_name": self.standard_skill_name,
        }

    @classmethod
    def get_skills(cls, session, company_id: int, filter_skills: [str]):
        """Get skills by company_id.

        filter_skills is list of skill names.
        If filter_skills is passed it will return only skills
        in db from that filter.
        TODO #D: Move these methods to the schema classes instead.
        """
        logger.debug(filter_skills)
        try:
            stmt = select(SkillDb).filter(SkillDb.company_id == company_id)
            if filter_skills is not None and len(filter_skills) > 0:
                stmt = stmt.filter(SkillDb.skill_name.in_(filter_skills))
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            return result
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_skills_by_ids(cls, session, company_id: int, filter_skills: [str]):
        """Get skills by company_id.

        If filter_skills is passed it will return only skills
        in db from that filter.
        TODO: Move these methods to the schema classes instead.
        """
        logger.debug(filter_skills)
        try:
            stmt = select(SkillDb).filter(SkillDb.company_id == company_id)
            if filter_skills is not None and len(filter_skills) > 0:
                stmt = stmt.filter(SkillDb.skill_name.in_(filter_skills))
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            return result
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id: int):
        """Delete skills by company_id."""
        try:
            session.execute(delete(SkillDb).where(SkillDb.company_id == company_id))
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def insert_skills_no_duplicates(
        cls, session, company_id: int, skills_list: [(str, str)]
    ):
        """Insert skills tuples (skillname, standard_skill_name).

        NOTE: If skill name is already in data base it doesn't inserts it.
        """
        # Filter skills already in Db.
        # logger.debug(skills_list)

        try:
            skill_names_ip = [x for (x, y) in skills_list]
            # logger.debug(f"Skill Names: {skill_names_ip}")
            duplicates = (
                session.query(SkillDb)
                # .options(load_only(SkillDb.skill_name))
                .filter(SkillDb.skill_name.in_(skill_names_ip))
                .filter(SkillDb.company_id == company_id)
                .all()
            )

            duplicate_skills = [x.skill_name for x in duplicates]

            # logger.debug(f"Duplicate skills: {duplicate_skills}")
            # Filter out the duplicates from skills_names_to_insert
            skills_to_insert = [
                (x, y) for (x, y) in skills_list if x not in duplicate_skills
            ]

            # logger.debug(f"New Skills to insert (non-duplicates): {skills_to_insert}")

            # Skills is of type List of dictionary representation of SkillDb
            skills = []
            for skill_name, standard_skill_name in skills_to_insert:
                skill = SkillDb(company_id, skill_name, standard_skill_name)
                skills.append(skill.get_dict())

            # logger.debug(skills)

            # Insert the skills to Skills db
            if len(skills) > 0:
                stmt = insert(SkillDb).values(skills)
                session.execute(stmt)
                session.commit()
            else:
                logger.warning(
                    f"No new skills to insert as length is 0. company_id: {company_id} skills: {skills_list}"
                )

        except Exception as err:
            logger.error(str(err))
            raise err


class JobPostingSkillDb(Base):
    """
    Job Posting Skills SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "jp_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int]

    # TODO #D: Do we need a foreign key here for some reason.
    job_posting_id: Mapped[int]
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))

    score: Mapped[float]
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    skill: Mapped["SkillDb"] = relationship(back_populates="job_posting_skills")

    def __init__(
        self,
        company_id: int,
        job_posting_id: int,
        score: float,
        skill_id: int,
    ):
        """Initialize the JobPostingSkillDb."""
        self.company_id = company_id
        self.job_posting_id = job_posting_id
        self.score = score
        self.skill_id = skill_id

    def __repr__(self):
        """Represent string format of the JobPostingSkillDb."""
        return (
            "<JobPostingSkillDb: company_id:{}; id: {}; job_posting_id: {};"
            " score: {}, skill_id: {}>".format(
                self.company_id, self.id, self.job_posting_id, self.score, self.skill_id
            )
        )

    def get_dict(self):
        """Provide this class as a dictionary."""
        return {
            "company_id": self.company_id,
            "job_posting_id": self.job_posting_id,
            "skill_id": self.skill_id,
            "score": self.score,
        }

    @classmethod
    def get_job_posting_skills(cls, session, company_id: int, job_posting_id: int):
        """Get jobpostingskills by company_id and job postingid.

        If filter_skills is passed it will return only skills
        in db from that filter.
        TODO #D: Move these methods to the schema classes instead.
        """
        # logger.debug(f"get_job_posting_skills: {company_id}")
        try:

            # TODO #B: Need to do this commit as without it read after write is not working
            # Even though there is a commit after previous write. Need to do some debugging
            stmt = (
                select(JobPostingSkillDb)
                .filter(JobPostingSkillDb.company_id == company_id)
                .filter(JobPostingSkillDb.job_posting_id == job_posting_id)
            )
            # logger.debug(f"{stmt} {company_id}")
            result = session.execute(stmt).all()
            # logger.debug(f"{result}")
            return [r[0] for r in result]
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def insert_many(
        cls, session, company_id: int, job_posting_id: int, skills_score: {str: float}
    ):
        """Insert list of job posting skills into database.

        This assumes skills were inserted into skills table.

        """
        logger.trace(f"{company_id}, {job_posting_id}, {skills_score}")
        # For each skill in skills-score build a JobPostingSkill object and add it
        # jp_skills is a list of dictionary of JobPostingSkillDb values
        jp_skills = []

        try:
            # TODO #D Just select skill name and id that we need here.
            skill_names_ip = skills_score.keys()
            skill_stmt = (
                select(SkillDb)
                .filter(SkillDb.skill_name.in_(skill_names_ip))
                .filter(SkillDb.company_id == company_id)
            )
            result = session.execute(skill_stmt).all()
            skills_db_list = [r[0] for r in result]
            # logger.debug(f"{skills_db_list}")

            for skill_name in skill_names_ip:
                skill_db_matching = [
                    x.id for x in skills_db_list if x.skill_name == skill_name
                ]
                if len(skill_db_matching) == 0:
                    raise Exception(
                        f"SkillDb: Skill name not found in skill_db. {skill_name}"
                    )
                skill_id = skill_db_matching[0]
                # logger.debug(f"{skill_name} {skill_id}")
                jp_skill = JobPostingSkillDb(
                    company_id=company_id,
                    job_posting_id=job_posting_id,
                    score=skills_score[skill_name],
                    skill_id=skill_id,
                )
                jp_skills.append(jp_skill.get_dict())

            # logger.debug(f"Job Skills dictionary to insert:\n {jp_skills}")

            # Insert the skills to JobPostingSkills db
            if len(jp_skills) > 0:
                stmt = insert(JobPostingSkillDb).values(jp_skills)
                session.execute(stmt)
                session.commit()
            else:
                logger.debug("No new skills to insert as length is 0")
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id: int):
        """Delete job posting skills by company_id."""
        try:
            session.execute(
                delete(JobPostingSkillDb).where(
                    JobPostingSkillDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, job_posting_id: int):
        try:
            logger.info(
                f"Deleting entity JobPostingSkillDb company_id: {company_id}; jp_id: {job_posting_id}"
            )
            session.execute(
                delete(JobPostingSkillDb)
                .where(JobPostingSkillDb.company_id == company_id)
                .where(JobPostingSkillDb.job_posting_id == job_posting_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationSkillDb(Base):
    """
    Job Application Skills SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int]

    # TODO #C: Add a column and relationship to Experience table.
    # TODO #C: Do we need a foreign key here for some reason.
    jad_id: Mapped[int]
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))

    score: Mapped[float]
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    skill: Mapped["SkillDb"] = relationship(back_populates="job_application_skills")

    def __init__(
        self,
        company_id: int,
        jad_id: int,
        score: float,
        skill_id: int,
    ):
        """Initialize the JobPostingSkillDb."""
        self.company_id = company_id
        self.jad_id = jad_id
        self.score = score
        self.skill_id = skill_id

    def __repr__(self):
        """Represent string format of the JobApplicationDb."""
        return (
            "<JobPostingSkillDb: company_id:{}; id: {}; jad_id: {};"
            " score: {}, skill_id: {}>".format(
                self.company_id,
                self.id,
                self.jad_id,
                self.score,
                self.skill_id,
            )
        )

    @classmethod
    def insert_many(
        cls,
        session,
        company_id: int,
        jad_id: int,
        skills_score: {str: float},
    ):
        """Insert list of job application skills into database.

        This assumes skills were inserted into skills table.

        """
        logger.debug(f"{company_id}, {jad_id}, {skills_score}")
        # For each skill in skills-score build a JobApplicationSkill object and add it
        # jp_skills is a list of dictionary of JobApplicationSkillDb values
        ja_skills = []

        try:
            # TODO #D Just select skill name and id that we need here.
            skill_names_ip = skills_score.keys()
            skill_stmt = (
                select(SkillDb)
                .filter(SkillDb.skill_name.in_(skill_names_ip))
                .filter(SkillDb.company_id == company_id)
            )
            result = session.execute(skill_stmt).all()
            skills_db_list = [r[0] for r in result]
            logger.debug(f"{skills_db_list}")

            for skill_name in skill_names_ip:
                skill_db_matching = [
                    x.id for x in skills_db_list if x.skill_name == skill_name
                ]
                if len(skill_db_matching) == 0:
                    raise Exception(
                        f"SkillDb: Skill name not found in skill_db. {skill_name}"
                    )
                skill_id = skill_db_matching[0]
                logger.debug(f"{skill_name} {skill_id}")
                ja_skill = JobApplicationSkillDb(
                    company_id=company_id,
                    jad_id=jad_id,
                    score=skills_score[skill_name],
                    skill_id=skill_id,
                )
                ja_skills.append(ja_skill.get_dict())

            logger.debug(f"Job Skills dictionary to insert:\n {ja_skills}")

            # Insert the skills to JobPostingSkills db
            if len(ja_skills) > 0:
                stmt = insert(JobApplicationSkillDb).values(ja_skills)
                session.execute(stmt)
                session.commit()
            else:
                logger.debug("No new skills to insert as length is 0")
        except Exception as err:
            logger.error(str(err))
            raise err

    def get_dict(self):
        """Provide this class as a dictionary."""
        return {
            "company_id": self.company_id,
            "jad_id": self.jad_id,
            "skill_id": self.skill_id,
            "score": self.score,
        }

    @classmethod
    def delete_all(cls, session, company_id: int):
        """Delete job application skills by company_id."""
        try:
            session.execute(
                delete(JobApplicationSkillDb).where(
                    JobApplicationSkillDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, jad_id: int):
        try:
            logger.info(
                f"Deleting entity JobApplicationSkillDb company_id: {company_id}; jp_id: {jad_id}"
            )
            session.execute(
                delete(JobApplicationSkillDb)
                .where(JobApplicationSkillDb.company_id == company_id)
                .where(JobApplicationSkillDb.jad_id == jad_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_skills_by_jad(
        cls, session, company_id: int, jad_id: int
    ):
        """Get jobapplicationstingskills by company_id.

        Returns List of JobApplicationSkill

        If filter_skills is passed it will return only skills
        in db from that filter.
        TODO #D: Move these methods to the schema classes instead.
        """
        logger.trace(f"get_skills_by_jad: {company_id}")
        try:
            stmt = (
                select(JobApplicationSkillDb)
                .options(joinedload(JobApplicationSkillDb.skill))
                .join(SkillDb)
                .filter(JobApplicationSkillDb.company_id == company_id)
                .filter(JobApplicationSkillDb.jad_id == jad_id)
            )
            logger.debug(f"{stmt} {company_id} {jad_id}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            ja_skills = []
            for ja_skill_db in result:
                ja_skill = JobApplicationSkill(
                    company_id=ja_skill_db.company_id,
                    skill_name=ja_skill_db.skill.skill_name,
                    score=ja_skill_db.score,
                )
                ja_skills.append(ja_skill)

            return ja_skills
        except Exception as err:
            logger.error(str(err))
            raise err


class JobApplicationScoreDb(Base):
    """
    Job Application SQL model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "ja_scores"

    job_application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id"), primary_key=True
    )
    company_id: Mapped[int]
    score: Mapped[Optional[float]]
    factor_score: Mapped[Optional[float]]
    factor_explanation: Mapped[Optional[str]] = mapped_column(Text)
    factor_summary: Mapped[Optional[str]] = mapped_column(Text)
    factor_calculation: Mapped[Optional[str]] = mapped_column(Text)
    bucket: Mapped[Optional[str]] = mapped_column(String(8))
    match_percent: Mapped[Optional[float]]
    learnability: Mapped[Optional[bool]]
    industry_match: Mapped[Optional[bool]]
    title_match: Mapped[Optional[bool]]
    matching_skills: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())
    job_application: Mapped[Optional["JobApplicationDb"]] = relationship(
        back_populates="job_application_score"
    )

    def __init__(self, ja_score: JobApplicationScore, job_application_id: int):
        """Initialize the JobApplicationScoreDb from JobApplication."""
        self.company_id = ja_score.company_id
        if ja_score.score is not None:
            self.score = ja_score.score
        if ja_score.match_percent is not None:
            self.match_percent = ja_score.match_percent
        if ja_score.learnability is not None:
            self.learnability = ja_score.learnability
        if ja_score.industry_match is not None:
            self.industry_match = ja_score.industry_match
        if ja_score.title_match is not None:
            self.title_match = ja_score.title_match
        if ja_score.matching_skills is not None:
            self.matching_skills = ja_score.matching_skills
        if ja_score.bucket is not None:
            self.bucket = ja_score.bucket
        self.job_application_id = job_application_id
        if ja_score.factor_score is not None:
            self.factor_score = ja_score.factor_score
        if ja_score.factor_explanation is not None:
            self.factor_explanation = ja_score.factor_explanation
        if ja_score.factor_calculation is not None:
            self.factor_calculation = ja_score.factor_calculation
        if ja_score.factor_summary is not None:
            self.factor_summary = ja_score.factor_summary

    def __repr__(self):
        """Represent string format of the JobApplicationScoreDb."""
        return "<JobApplicationScoreDb: company_id:{}; job_application_id: {}; score: {}; factor_summary: {}; factor_score: {}; factor_explain: {}; factor calc: {}; industry_match: {}; title_match: {}; bucket: {}; matching_skills: {}>".format(
            self.company_id,
            self.job_application_id,
            self.score,
            self.factor_summary,
            self.factor_score,
            self.factor_explanation,
            self.factor_calculation,
            self.industry_match,
            self.title_match,
            self.bucket,
            self.matching_skills,
        )

    def insert_job_application_score(self, session):
        """Insert the job application score in database. On Duplicate it will update the score, bucket etc."""
        logger.trace(self)
        from sqlalchemy.dialects.mysql import insert

        try:

            stmt = insert(JobApplicationScoreDb).values(
                job_application_id=self.job_application_id,
                company_id=self.company_id,
                score=self.score,
                bucket=self.bucket,
                factor_score=self.factor_score,
                factor_explanation=self.factor_explanation,
                factor_calculation=self.factor_calculation,
                factor_summary=self.factor_summary,
                match_percent=self.match_percent,
                learnability=self.learnability,
                industry_match=self.industry_match,
                title_match=self.title_match,
                matching_skills=self.matching_skills,
            )
            stmt = stmt.on_duplicate_key_update(
                score=self.score,
                factor_score=self.factor_score,
                bucket=self.bucket,
                factor_explanation=self.factor_explanation,
                factor_calculation=self.factor_calculation,
                factor_summary=self.factor_summary,
                match_percent=self.match_percent,
                learnability=self.learnability,
                industry_match=self.industry_match,
                title_match=self.title_match,
                matching_skills=self.matching_skills,
            )
            result = session.execute(stmt)
            session.commit()
            if result is not None and len(result.inserted_primary_key) > 0:
                logger.debug(result.inserted_primary_key[0])
                self.id = result.inserted_primary_key[0]
            else:
                logger.error(f"Insert failed for application score: {self}")
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the application scores with companyid."""
        try:
            session.execute(
                delete(JobApplicationScoreDb).where(
                    JobApplicationScoreDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete(cls, session, company_id: int, job_application_id: int):
        try:
            logger.info(
                f"Deleting entity JobApplicationScoreDb company_id: {company_id}; jp_id: {job_application_id}"
            )
            session.execute(
                delete(JobApplicationScoreDb)
                .where(JobApplicationScoreDb.company_id == company_id)
                .where(JobApplicationScoreDb.job_application_id == job_application_id)
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_application_score(cls, session, company_id, job_application_id):
        """Get the job application score for the company and job_application_id."""
        logger.debug(f"{company_id} {job_application_id}")
        try:
            stmt = (
                select(JobApplicationScoreDb)
                .filter(JobApplicationScoreDb.company_id == company_id)
                .filter(JobApplicationScoreDb.job_application_id == job_application_id)
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} ")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err


class BackgroundTaskTypeEnum(PyEnum):
    """Describes the type of the background Task."""

    JobPosting = 1
    JobApplication = 2
    Candidate = 3
    Invalid = 0


class BackgroundTaskDb(Base):
    """
    Background Task model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "bg_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int]

    message: Mapped[Optional[str]] = mapped_column(String(2048))
    message_type: Mapped[BackgroundTaskTypeEnum] = mapped_column(
        Enum(BackgroundTaskTypeEnum)
    )
    status: Mapped[Optional[str]] = mapped_column(String(256))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def __init__(
        self,
        company_id: int,
        message: str,
        message_type: BackgroundTaskTypeEnum,
    ):
        """Initialize the BackgroundTask."""
        self.company_id = company_id
        self.message = message
        self.message_type = message_type
        self.status = "INIT"

    def __repr__(self):
        """Represent string format of the BackgroundTask."""
        ret = "<BackgroundTaskDb: company_id:{}; id:{}, message: {}, status: {}, message_type: {}>"
        return ret.format(
            self.company_id,
            self.id,
            self.message,
            self.status,
            self.message_type,
        )

    def insert_background_task(self, session):
        """Insert the background task database."""
        logger.debug(self)
        try:
            session.add(self)
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the background task for this company."""
        try:
            session.execute(
                delete(BackgroundTaskDb).where(
                    BackgroundTaskDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_background_tasks(cls, session, company_id):
        """Get the job application volunteer for the company and job_application_id."""
        logger.debug(f"{company_id} ")
        try:
            stmt = select(BackgroundTaskDb).filter(
                BackgroundTaskDb.company_id == company_id
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_background_task(cls, session, task_id: int):
        """Get the background task by its ID."""
        logger.debug(f"Fetching background task with ID: {task_id}")
        try:
            result = session.get(BackgroundTaskDb, task_id)
            logger.debug(f"Result: {result}")
            return result
        except Exception as err:
            logger.error(f"Error fetching background task: {str(err)}")
            raise err


    @classmethod
    def update_background_task(cls, session, task_id: int, status: str):
        """Update the background task status in database."""
        if task_id == 0:
            logger.warning("Task id is invalid (taskid: 0)")
            return
        logger.debug(f"Updating bg task {task_id} with status {status}")
        try:

            # NOTE: keeping dictionary here in case we want to update many values in future.
            val = {}
            val["status"] = status

            logger.debug(val)
            stmt = (
                update(BackgroundTaskDb)
                .where(BackgroundTaskDb.id == task_id)
                .values(val)
            )
            logger.debug(stmt)
            session.execute(stmt)
            session.commit()
            tasks = BackgroundTaskDb.get_background_task(session, task_id)
            logger.debug(f"Getting Updated task {tasks}")

        except Exception as err:
            # Log the error and continue
            # TODO #B: Should we log in database
            logger.error(f"Exception while updating bg task {err}")
            raise err


class JobConversationChatDb(Base):
    """
    Background Task model.

    Contains the main entry from api to
    save the work
    """

    __tablename__ = "cb_jobs"
    __table_args__ = (
        UniqueConstraint("company_id", "conversation_id", name="uix_jcc_ci_ci"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int]
    conversation_id: Mapped[str] = mapped_column(String(128))
    # client_job_id: Mapped[int]
    # client_candidate_id: Mapped[int]

    result: Mapped[Optional[str]] = mapped_column(String(2048))
    message: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    status: Mapped[Optional[str]] = mapped_column(String(256))
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def __init__(
        self,
        company_id: int,
        message: bytes,
        # client_job_id: int,
        conversation_id: int,
        # client_candidate_id: int,
    ):
        """Initialize the BackgroundTask."""
        self.company_id = company_id
        self.message = message
        # self.client_job_id = client_job_id
        self.conversation_id = conversation_id
        # self.client_candidate_id = client_candidate_id
        self.status = "INIT"

    def __repr__(self):
        """Represent string format of the JobConversationChatDb."""
        ret = "<JobConversationChatDb: company_id:{}; id:{}, conversation_id: {}, result: {}, message: {}, status: {}>"
        return ret.format(
            self.company_id,
            self.id,
            self.conversation_id,
            # self.client_job_id,
            self.result,
            self.message,
            self.status,
        )

    def insert_job_conversation_chat(self, session):
        """Insert the covnersation in  database."""
        logger.debug(self)
        from sqlalchemy.dialects.mysql import insert

        try:

            stmt = insert(JobConversationChatDb).values(
                company_id=self.company_id,
                conversation_id=self.conversation_id,
                result=self.result,
                message=self.message,
                status=self.status,
            )
            stmt = stmt.on_duplicate_key_update(
                result=self.result,
                message=self.message,
                status=self.status,
            )
            result = session.execute(stmt)
            session.commit()
            if result is not None and len(result.inserted_primary_key) > 0:
                logger.debug(result.inserted_primary_key[0])
                self.id = result.inserted_primary_key[0]
            else:
                logger.error(f"Insert failed for JobConversationChatDb: {self}")
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def delete_all(cls, session, company_id):
        """Delete all the conversation chat for this company."""
        try:
            session.execute(
                delete(JobConversationChatDb).where(
                    JobConversationChatDb.company_id == company_id
                )
            )
            session.commit()
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def get_job_conversation_chat(cls, session, company_id, conversation_id):
        """Get the conversation chat given the conversation id and company_id"""
        logger.debug(f"{company_id} {conversation_id}")
        try:
            stmt = (
                select(JobConversationChatDb)
                .filter(JobConversationChatDb.company_id == company_id)
                .filter(JobConversationChatDb.conversation_id == conversation_id)
            )
            logger.debug(f"{stmt}")
            result = session.execute(stmt).scalars().all()
            logger.debug(f"{result} {result.__class__}")
            return result[0] if len(result) > 0 else None
        except Exception as err:
            logger.error(str(err))
            raise err

    @classmethod
    def update_job_conversation_chat(
        cls,
        session,
        company_id: int,
        conversation_id: int,
        status: str,
        result: str,
        message: bytes,
    ):
        """Update the conversation in database."""
        if conversation_id == 0:
            logger.warning("conversation id is invalid (0)")
            return

        try:

            # NOTE: keeping dictionary here in case we want to update many values in future.
            val = {}
            if result is not None:
                val["result"] = result
            if message is not None:
                val["message"] = message
            if status is not None:
                val["status"] = status

            logger.debug(val)

            # logger.debug(val)
            stmt = (
                update(JobConversationChatDb)
                .where(JobConversationChatDb.company_id == company_id)
                .where(JobConversationChatDb.conversation_id == conversation_id)
                .values(val)
            )
            session.execute(stmt)
            session.commit()

        except Exception as err:
            # Log the error and continue
            # TODO #B: Should we log in database
            logger.error(f"Exception while updating JobConverastionChatDb {err}")
            raise err


# TODO #B: Should we remove this from here and move to migration scripts.

load_dotenv()
db_conn_str = os.getenv("DB_CONNECTION_STR")
assert db_conn_str
print(db_conn_str)

engine = create_engine(
    db_conn_str,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
    #isolation_level="READ COMMITTED"
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

