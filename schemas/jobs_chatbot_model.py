"""
JobsChatbot Model File.

This file represents an incoming JobsChatbot model
implemented using pydantic.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class JobsChat(BaseModel):
    """Job posting Chatbot request object"""

    __chatbot_requests__ = []

    model_config = {
        "extra": "forbid",
    }

    company_id: int = Field(..., description="CompanyId for Intalent Client")
    conversation_id: str = Field(
        ...,
        description="Conversation Id for this request",
    )
    user_query: str = Field(..., description="User query for this request")
