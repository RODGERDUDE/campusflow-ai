"""
CampusFlow AI — Response schemas.

Pydantic v2 models for the /api/v1/analyze success response (design §4.3).
The relevance status is computed by the backend, not the AI. There is
intentionally NO announcement_id field — the MVP does not persist announcements.
"""

from enum import Enum

from pydantic import BaseModel

from app.schemas.ai_output import AIExtractionResult


class RelevanceStatusEnum(str, Enum):
    """Backend-computed relevance outcome for the student."""

    RELEVANT = "RELEVANT"
    NOT_RELEVANT = "NOT_RELEVANT"
    UNCERTAIN = "UNCERTAIN"


class RelevanceResult(BaseModel):
    """Whether the announcement applies to the student, with a plain-English reason."""

    relevance_status: RelevanceStatusEnum
    relevance_reason: str


class ChecklistItem(BaseModel):
    """A single actionable item in the personalized checklist."""

    id: str
    description: str
    deadline: str | None  # YYYY-MM-DD or None
    deadline_text: str | None  # original wording for display
    completed: bool = False


class AnalyzeResponse(BaseModel):
    """The full response body for POST /api/v1/analyze (no announcement_id)."""

    analysis: AIExtractionResult
    relevance: RelevanceResult
    checklist: list[ChecklistItem]
