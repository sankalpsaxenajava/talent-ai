"""
Chatbot Model File.

This file represents an incoming Chatbot model
implemented using pydantic.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class JobPostingChat(BaseModel):
    """Job posting Chatbot request object"""

    __chatbot_requests__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    client_job_id: int = Field(
        ..., description="Client job id for this job in conversation"
    )
    conversation_id: str = Field(
        ...,
        description="Conversation Id for this request",
    )
    user_query: str = Field(..., description="User query for this request")
