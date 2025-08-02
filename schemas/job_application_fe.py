from pydantic import BaseModel, Field
from typing import Optional

from intai.schemas.candidate_fe import CandidateFrontEnd


class JobApplicationFrontEnd(CandidateFrontEnd):
    """JobApplication class represents the JobApplication object."""

    __job_applications__ = []

    model_config = {
        "extra": "forbid",
    }
    score: Optional[str] = Field(
        default="", description="score of the job application"
    )
    scoreSummary: Optional[str] = Field(
        default="", description="summary of the score"
    )

    
    @classmethod
    def create_copy(cls, other: CandidateFrontEnd) -> 'JobApplicationFrontEnd':
        return cls(
            companyId=other.companyId,
            firstName=other.firstName,
            lastName=other.lastName,
            resumeUrl=other.resumeUrl,
            location=other.location,
            email=other.email,
            phone=other.phone,
            yearsOfExperience=other.yearsOfExperience,
            linkedInUrl=other.linkedInUrl,
            peopleManagement=other.peopleManagement,
            spokenLanguages=other.spokenLanguages,
            technicalTools=other.technicalTools,
            yearOfGraduation=other.yearOfGraduation,
            latestDegree=other.latestDegree,
            latestInstitution=other.latestInstitution,
            candidateQualifications=other.candidateQualifications,
            candidateExperiences=other.candidateExperiences,
            candidateSkills=other.candidateSkills,
            expectedCompensation=other.expectedCompensation,
            currentCompensation=other.currentCompensation,
            noticePeriodInDays=other.noticePeriodInDays,
            currentCompany=other.currentCompany,
            currentDesignation=other.currentDesignation,
        )
    

