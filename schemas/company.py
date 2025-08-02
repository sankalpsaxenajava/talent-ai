"""
Company Model File.

This file represents an incoming Company model
implemented using pydantic.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Company(BaseModel):
    """Company class represents the JobPosting object."""

    __companies__ = []

    model_config = {
        "extra": "forbid",
    }

    id: int = Field(..., description="CompanyId for Intalent Client")
    filtering_criteria: Optional[str] = Field(
        default=None,
        description="Filtering Criteria specified by hiring team to"
        "provide hard requirements to meet.",
    )
    name: Optional[str] = Field(default=None, description="Company Name")
    context_doc: Optional[str] = Field(
        default=None, description="Context Document for Company"
    )
