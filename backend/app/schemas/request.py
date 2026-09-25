"""
CampusFlow AI — Request schemas.

Pydantic v2 models that validate the incoming /api/v1/analyze request body
before any AI call is made (design §4.1). All fields are required.
"""

from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    """A student's profile, submitted with every analysis request."""

    name: str
    department: str
    specialization: str
    year: int = Field(ge=1, le=4)
    section: str


class AnalyzeRequest(BaseModel):
    """The request body for POST /api/v1/analyze."""

    announcement_text: str = Field(min_length=50, max_length=10000)
    student_profile: StudentProfile
