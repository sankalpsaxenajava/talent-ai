"""
Job Application Model File.

This file represents an incoming Job Application model
implemented using pydantic.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class JobApplicationInput(BaseModel):
    """JobApplication class represents the JobApplication object."""

    __job_applications__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    client_job_application_id: int = Field(
        ...,
        description="Job Application Id from front end or client",
    )
    client_job_id: int = Field(
        ..., description="JobId from front end or client (ATS etc.)."
    )
    resume_doc_url: str = Field(..., description="Url for resume")
    candidate_email: Optional[EmailStr] = Field(
        default=None, description="Email of the Candidate."
    )
    is_update: Optional[bool] = Field(
        default=False, description="Whether this is update operation or not."
    )

class JobApplication(JobApplicationInput):
    """JobApplication class represents the JobApplication object."""

    __job_applications__ = []

    model_config = {
        "extra": "forbid",
    }

    jad_id: Optional[int] = Field(default=None, description="JobApplicationDetailId")
   


class Candidate(BaseModel):
    """Candidate class represents the Candidate object."""

    __candidates__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    jad_id: Optional[int] = Field(None, description="JobApplicationDetailId")
    client_candidate_id: int = Field(
        ...,
        description="Candidate Id from front end or client",
    )
    resume_doc_url: str = Field(..., description="Url for resume")
    candidate_email: Optional[EmailStr] = Field(
        default=None, description="Email of the Candidate."
    )
    is_update: Optional[bool] = Field(
        default=False, description="Whether this is update operation or not."
    )

class JobApplicationDetail(BaseModel):
    """JobApplicationDetail class represents the JobApplication object."""

    __job_applications__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    summary: Optional[str] = Field(
        None,
        description="Job Application Id from front end or client",
    )
    experience_years: Optional[float] = Field(None, description="Experience in years.")
    software_skills: Optional[str] = Field(
        None, description="Software and Programming Skills."
    )
    avg_tenure_org_years: Optional[float] = Field(
        None, description="Average tenure in org in number of years."
    )
    avg_tenure_role_years: Optional[float] = Field(
        None, description="Average tenure in role in number of years."
    )
    num_promotions: Optional[int] = Field(
        None, description="Number of promotions or role changes."
    )
    num_awards: Optional[int] = Field(None, description="Number of awards.")
    num_published_papers: Optional[int] = Field(None, description="Number of awards.")
    num_patents: Optional[int] = Field(None, description="Number of patents.")
    num_conf_presentations: Optional[int] = Field(
        None, description="Number of presentation in conferences."
    )
    cert_education_new_domain: Optional[bool] = Field(
        None, description="If there is a certificate or education in new domain."
    )
    applicant_name: Optional[str] = Field(None, description="Name of applicant")
    applicant_resume_email: Optional[str] = Field(
        None, description="applicant email from resume."
    )
    applicant_resume_phone: Optional[str] = Field(
        None, description="Phone from resume."
    )
    applicant_resume_linkedin: Optional[str] = Field(
        None, description="Linked in from resume."
    )
    current_salary: Optional[float] = Field(None, description="Current salary.")
    expected_salary: Optional[float] = Field(None, description="Expected salary.")
    notice_period: Optional[int] = Field(None, description="Notice Period")
    gender: Optional[str] = Field(None, description="Gender")


class JobApplicationAddress(BaseModel):
    """JobApplicationDetail class represents the JobApplication object."""

    __job_application_addresses__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    city: Optional[str] = Field(
        None,
        description="City for this address",
    )
    state: Optional[str] = Field(
        None,
        description="State for this address",
    )
    country: Optional[str] = Field(
        None,
        description="Country for this address",
    )
    full_address: Optional[str] = Field(
        None,
        description="Full Address.",
    )


class JobApplicationAward(BaseModel):
    """JobApplicationAward class represents the JobApplicationAward object."""

    __job_application_awards__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    title: str = Field(
        ...,
        description="Title for award",
    )
    date_award: Optional[str] = Field(
        None,
        description="String date for this award",
    )
    award_authority: Optional[str] = Field(
        None,
        description="Award given by this authority.",
    )


class JobApplicationExperience(BaseModel):
    """JobApplicationExperience class."""

    __job_application_experiences__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    title: Optional[str] = Field(
        None,
        description="Title for experience",
    )
    experience_company: Optional[str] = Field(
        None,
        description="Name of company for this experience.",
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date at this company",
    )
    end_date: Optional[str] = Field(
        None,
        description="End date at this company",
    )

    description: Optional[str] = Field(
        None,
        description="Description of this experience",
    )
    industry: Optional[str] = Field(
        None,
        description="Industry for this experience.",
    )
    location: Optional[str] = Field(
        None,
        description="Location for this experince and company",
    )

    team_lead_experience: Optional[int] = Field(
        None,
        description="if there was any lead experience",
    )
    years_experience: Optional[float] = Field(
        None,
        description="if there was any lead experience",
    )
    employment_type: Optional[str] = Field(
        None,
        description="Type of employment.",
    )


class JobApplicationEducation(BaseModel):
    """JobApplicationEducation class."""

    __job_application_educations__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    institution: Optional[str] = Field(
        None,
        description="Institution for this education",
    )
    degree_level: Optional[str] = Field(
        None,
        description="Name of degree for this education.",
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date at this education",
    )
    end_date: Optional[str] = Field(
        None,
        description="End date at this education",
    )

    degree_field: Optional[str] = Field(
        None,
        description="Field for this degree.",
    )


class JobApplicationLanguage(BaseModel):
    """JobApplicationLanguage class."""

    __job_application_languages__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    language_name: Optional[str] = Field(
        None,
        description="Name of this language",
    )
    fluency_level: Optional[str] = Field(
        None,
        description="Fluency level for this language.",
    )


class JobApplicationProject(BaseModel):
    """JobApplicationProject class."""

    __job_application_projects__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    title: str = Field(
        ...,
        description="Title of project",
    )

    start_date: Optional[str] = Field(
        None,
        description="Start date at this project",
    )
    end_date: Optional[str] = Field(
        None,
        description="End date at this project",
    )

    tech_stack: Optional[str] = Field(
        None,
        description="Technology stack for this project",
    )
    public_urls: Optional[str] = Field(
        None,
        description="Public urls for this project",
    )


class JobApplicationScore(BaseModel):
    """JobApplicationScore class."""

    __job_application_scores__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    bucket: Optional[str] = Field(
        None,
        description="Bucket for this application",
    )
    score: Optional[float] = Field(
        None, descriptor="Score for the application for job."
    )
    factor_score: Optional[float] = Field(
        None, descriptor="Factor Score for the application for job."
    )
    factor_explanation: Optional[str] = Field(
        None, descriptor="Factor reasoning and explanation for the score."
    )
    factor_calculation: Optional[str] = Field(
        None, descriptor="Factor reasoning calculation for the score."
    )
    factor_summary: Optional[str] = Field(None, descriptor="Factor Score Summary")
    match_percent: Optional[float] = Field(
        None, descriptor="Matching percentage for this application "
    )
    learnability: Optional[bool] = Field(None, descriptor="learnability")
    matching_skills: Optional[str] = Field(None, descriptor="Matching skills with job")
    industry_match: Optional[bool] = Field(
        None, descriptor="Does industry matches with job"
    )
    title_match: Optional[bool] = Field(None, descriptor="Does title matches with job")


class JobApplicationSkill(BaseModel):
    """JobApplicationSkill class."""

    __job_application_skills__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    skill_name: Optional[str] = Field(
        None,
        description="Name of the skill",
    )
    score: Optional[float] = Field(None, descriptor="Score for the skill")


class JobApplicationCertification(BaseModel):
    """JobApplicationCertification class."""

    __job_application_certifications__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    title: Optional[str] = Field(
        None,
        description="Title of certificate",
    )

    issue_date: Optional[str] = Field(
        None,
        description="Issue date at this certificate",
    )

    issue_authority: Optional[str] = Field(
        None,
        description="Authority which issued this certificate.",
    )


class JobApplicationCertificationSkill(BaseModel):
    """JobApplicationCertificationSkill class."""

    __job_application_certification_skills__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    skill_name: Optional[str] = Field(
        None,
        description="Name of the skill",
    )


class JobApplicationPublication(BaseModel):
    """JobApplicationPublication class."""

    __job_application_publications__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    title: Optional[str] = Field(
        None,
        description="Title of publication",
    )

    publisher: Optional[str] = Field(
        None,
        description="publisher",
    )
    issue_date: Optional[str] = Field(
        None,
        description="Issue date at this publication",
    )

    description: Optional[str] = Field(
        None,
        description="Description of this publication",
    )


class JobApplicationInterest(BaseModel):
    """JobApplicationInterest class."""

    __job_application_interests__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    title: Optional[str] = Field(
        None,
        description="Title of Interest",
    )


class JobApplicationVolunteer(BaseModel):
    """JobApplicationVolunteer class."""

    __job_application_volunteers__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    organization: Optional[str] = Field(
        None,
        description="Organization for this volunteering.",
    )

    position: Optional[str] = Field(
        None,
        description="Position for this volunteer",
    )

    start_date: Optional[str] = Field(
        None,
        description="Start date at this volunteering job.",
    )
    end_date: Optional[str] = Field(
        None,
        description="End date at this volunteering job.",
    )
