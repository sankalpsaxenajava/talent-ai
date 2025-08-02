"""
Job Posting Model File.

This file represents an incoming Job Posting model
implemented using pydantic.
"""

from pydantic import BaseModel, Field
from typing import Optional


class JobPosting(BaseModel):
    """JobPosting class represents the JobPosting object."""

    __job_postings__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    client_job_id: int = Field(
        ..., description="JobId from front end or client (ATS etc.)."
    )
    job_posting_doc_url: str = Field(..., description="Url for job posting document")
    min_salary: Optional[float] = Field(default=None, description="Min Salary")
    max_salary: Optional[float] = Field(default=None, description="Max Salary")
    filtering_criteria: Optional[str] = Field(
        default=None,
        description="Filtering Criteria specified by hiring team to"
        "provide hard requirements to meet.",
    )
    is_update: Optional[bool] = Field(
        default=False, description="Whether this is update or insert"
    )
