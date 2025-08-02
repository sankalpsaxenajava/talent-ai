"""
Job Posting Skill Model File.

This file represents an incoming Job Posting model
implemented using pydantic.
"""

from pydantic import BaseModel, Field
from typing import Optional


class JobPostingSkill(BaseModel):
    """JobPostingSkill class represents the JobPostingSkill object."""

    __job_posting_skills__ = []

    model_config = {
        "extra": "forbid",
    }

    job_posting_doc_url: str = Field(..., description="Url for job posting document")
    company_id: int = Field(..., description="CompanyId for Intalent Client")
    job_posting_id: int = Field(..., description="JobPostingId .")
    score: Optional[float] = Field(
        ...,
        description="Score for this skill for this job.",
    )


class Skill(BaseModel):
    """Skill Master Class."""

    __skills__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    id: int = Field(..., description="SkillId for this Skill.")
    skill_name: Optional[str] = (Field(..., description="name of the skill"),)
    standardized_skill_name: Optional[str] = Field(
        ..., description="standardized skill"
    )
