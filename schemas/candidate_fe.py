"""Candidate Frontend model"""

from pydantic import BaseModel, Field
from typing import Optional


class CandidateSkillFrontEnd(BaseModel):
    """CandidateSkill class represents the CandidateSkill object."""

    __candidate_skills__ = []

    model_config = {
        "extra": "forbid",
    }
    name: Optional[str] = Field(default="", description="name of the candidate skill")
    proficiency: Optional[int] = Field(
        default=5, description="proficiency of the candidate skill"
    )


class CandidateExperienceFrontEnd(BaseModel):
    """CandidateExperience class represents the CandidateExperience object."""

    __candidate_experiences__ = []
    designation: Optional[str] = Field(
        default="", description="designation of the candidate experience"
    )
    companyName: Optional[str] = Field(
        default="", description="company name of the candidate experience"
    )
    location: Optional[str] = Field(
        default="", description="location of the candidate experience"
    )
    startDate: Optional[str] = Field(
        default="", description="start date of the candidate experience"
    )
    endDate: Optional[str] = Field(
        default="", description="end date of the candidate experience"
    )
    currentlyEmployedAt: Optional[bool] = Field(
        default=False, description="currently employed at the company"
    )


class CandidateQualificationFrontEnd(BaseModel):
    """CandidateQualification class represents the CandidateQualification object."""

    __candidate_qualifications__ = []

    model_config = {
        "extra": "forbid",
    }
    qualification: Optional[str] = Field(
        default="", description="Qualification For this candidate"
    )
    university: Optional[str] = Field(
        default="", description="university of the candidate qualification"
    )
    fieldOfStudy: Optional[str] = Field(
        default="", description="field of study for the candidate qualification"
    )
    location: Optional[str] = Field(
        default="", description="location for the candidate qualification"
    )

    startDate: Optional[str] = Field(
        default="", description="Start Date for the candidate qualification"
    )

    endDate: Optional[str] = Field(
        default="", description="End Date for the candidate qualification"
    )

    latestQualification: Optional[bool] = Field(
        default=False,
        description="Is latest qualification for the candidate qualification",
    )


class CandidateFrontEnd(BaseModel):
    """Candidate class represents the Candidate object."""

    __candidates__ = []

    model_config = {
        "extra": "forbid",
    }

    companyId: int = Field(..., description="CompanyId for Intalent Client")
    firstName: Optional[str] = Field(
        default="", description="first name of the candidate"
    )
    lastName: Optional[str] = Field(
        default="", description="last name of the candidate"
    )
    resumeUrl: Optional[str] = Field(default="", description="Url of the candidate")
    location: Optional[str] = Field(
        default="", description="location of the candidate"
    )
    email: Optional[str] = Field(default="", description="Email of the candidate")
    phone: Optional[str] = Field(default="", description="Phone of the candidate")
    yearsOfExperience: Optional[float] = Field(
        default=0, description="Total years of experience for this candidate"
    )
    linkedInUrl: Optional[str] = Field(
        default="", description="Linkedin Url of the candidate"
    )
    peopleManagement: Optional[bool] = Field(
        default=False, description="If they have people management experience"
    )
    spokenLanguages: Optional[str] = Field(
        default="", description="Spoken languages  of the candidate"
    )
    technicalTools: Optional[str] = Field(
        default="", description="Technical tools of the candidate"
    )
    yearOfGraduation: Optional[str] = Field(default="", description="Year of graduation")
    currentCompany: Optional[str] = Field(
        default="", description="Current company of the candidate"
    )
    currentDesignation: Optional[str] = Field(
        default="", description="Current designation of the candidate"
    )

    latestDegree: Optional[str] = Field(default="", description="Latest Degree")
    latestInstitution: Optional[str] = Field(
        default="", description="Latest Institution"
    )
    candidateQualifications: Optional[list[CandidateQualificationFrontEnd]] = Field(
        default=[], description="CandidateQualification of the candidate"
    )
    candidateExperiences: Optional[list[CandidateExperienceFrontEnd]] = Field(
        default=[], description="CandidateExperience of the candidate"
    )
    candidateSkills: Optional[list[CandidateSkillFrontEnd]] = Field(
        default=[], description="CandidateSkill of the candidate"
    )
    expectedCompensation: Optional[str] = Field(
        default="", description="Expected Compensation of the candidate"
    )
    currentCompensation: Optional[str] = Field(
        default="", description="Current Compensation of the candidate"
    )
    noticePeriodInDays: Optional[int] = Field(
        default=0, description="Notice Period of the candidate in Days"
    )
    processingStatus: Optional[str] = Field(
        default="", description="Status for the frontend"
    )
    processingStatusProgress: Optional[int] = Field(
        default=0, description="Progress indicator for the frontend"
    )

    isBackendRequest: Optional[bool] = Field(
        default=True, description="Is this a backend request"
    )
