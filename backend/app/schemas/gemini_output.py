"""
CampusFlow AI — Gemini provider-facing structured-output schema.

This module exists ONLY to shape the JSON schema we hand to the Gemini
Developer API via `response_schema`. It intentionally avoids constructs the
Gemini Developer API rejects — most importantly open-ended maps
(`dict[str, str]`), which Pydantic renders as `additionalProperties` (only
supported in Enterprise Agent Platform mode).

The public/authoritative contract lives in `ai_output.AIExtractionResult` and is
NOT changed. After Gemini returns a `GeminiExtraction`, we convert it to the
public dict shape and validate it with `AIExtractionResult`, so all existing
validation still runs and the external contract is unchanged.
"""

from enum import Enum

from pydantic import BaseModel


class GeminiDeadlineItem(BaseModel):
    """Deadline item — mirrors ai_output.DeadlineItem (fixed fields only)."""

    label: str
    date: str | None = None
    original_date_text: str
    description: str


class GeminiRequiredActionItem(BaseModel):
    """Required action — mirrors ai_output.RequiredActionItem (fixed fields)."""

    action: str
    by: str | None = None
    original_by_text: str | None = None
    details: str | None = None


class GeminiAffectedGroups(BaseModel):
    """Affected groups — four fixed list fields (no open maps)."""

    departments: list[str] = []
    specializations: list[str] = []
    years: list[int] = []
    sections: list[str] = []


class GeminiAmbiguousRawText(BaseModel):
    """Original wording per ambiguous dimension.

    Uses fixed optional fields for the only four supported dimensions instead of
    an arbitrary dict/map, so the generated schema contains NO
    `additionalProperties`.
    """

    departments: str | None = None
    specializations: str | None = None
    years: str | None = None
    sections: str | None = None


class GeminiPriorityEnum(str, Enum):
    """Priority — same allowed values as the public schema."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class GeminiExtraction(BaseModel):
    """Gemini-facing structured-output model (Developer-API-compatible).

    No cross-field validators here — this is a transport shape. Real validation
    happens after conversion to the public AIExtractionResult model.
    """

    summary: str
    what_changed: str
    affected_groups: GeminiAffectedGroups
    ambiguous_dimensions: list[str] = []
    ambiguous_raw_text: GeminiAmbiguousRawText = GeminiAmbiguousRawText()
    deadlines: list[GeminiDeadlineItem] = []
    required_actions: list[GeminiRequiredActionItem] = []
    priority: GeminiPriorityEnum
    priority_reason: str

    def to_public_dict(self) -> dict:
        """Convert to the public AIExtractionResult input shape.

        The fixed-field ambiguous_raw_text object becomes a plain dict with only
        the dimensions that actually carry wording (non-None), matching the
        public `dict[str, str]` contract.
        """
        raw = self.ambiguous_raw_text
        ambiguous_raw_text = {
            dim: getattr(raw, dim)
            for dim in ("departments", "specializations", "years", "sections")
            if getattr(raw, dim) is not None
        }
        return {
            "summary": self.summary,
            "what_changed": self.what_changed,
            "affected_groups": {
                "departments": list(self.affected_groups.departments),
                "specializations": list(self.affected_groups.specializations),
                "years": list(self.affected_groups.years),
                "sections": list(self.affected_groups.sections),
            },
            "ambiguous_dimensions": list(self.ambiguous_dimensions),
            "ambiguous_raw_text": ambiguous_raw_text,
            "deadlines": [d.model_dump() for d in self.deadlines],
            "required_actions": [a.model_dump() for a in self.required_actions],
            "priority": self.priority.value,
            "priority_reason": self.priority_reason,
        }
