from pydantic import BaseModel, EmailStr, Field
from typing import Optional
class ScreeningRequest(BaseModel):
    """Screening Reqeuest  request object"""

    __screening_requests__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    job_posting_id: int = Field(
        ...,
        description="job_posting Id for this request",
    )
    job_application_id: int = Field(..., description="Job Application Id this request")
    screening_focus_area: str = Field(..., description="Focus Area for Screening Interview")


class ScreeningScoreRequest(BaseModel):
    """Screening Score  request object"""

    __screening_requests__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    job_posting_id: int = Field(
        ...,
        description="job_posting Id for this request",
    )
    job_application_id: int = Field(..., description="Job Application Id this request")
    screening_id: int = Field(..., description="Screening Id this request")
    transcript: str = Field(..., description="Transcript of the interview")
    screening_focus_area: str = Field(..., description="Focus Area for Screening Interview")