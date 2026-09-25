"""
CampusFlow AI — AI extraction output schemas.

Pydantic v2 models that validate the LLM's JSON response before it is used for
any computation (design §4.2, §5). Validation failures here surface as
AI_PARSE_ERROR (see FR-12). The AI performs extraction only; relevance is
computed by the backend, so these models contain no relevance fields.
"""

from enum import Enum

from pydantic import BaseModel, model_validator

# The four affected-group dimension names, in a fixed order.
_DIMENSIONS = ("departments", "specializations", "years", "sections")


class DeadlineItem(BaseModel):
    """A single deadline extracted from the announcement."""

    label: str
    date: str | None  # YYYY-MM-DD or None
    original_date_text: str  # always preserved
    description: str


class RequiredActionItem(BaseModel):
    """A single required student action extracted from the announcement."""

    action: str
    by: str | None  # YYYY-MM-DD or None
    original_by_text: str | None
    details: str | None


class AffectedGroups(BaseModel):
    """Who the announcement targets, one list per dimension.

    Each dimension is a specific list (e.g. ["CSE"]), the sentinel ["all"],
    or [] (indeterminate — must be flagged ambiguous on the parent model).
    """

    departments: list[str | int]
    specializations: list[str | int]
    years: list[int | str]
    sections: list[str | int]

    @model_validator(mode="after")
    def _coerce_and_check_years(self) -> "AffectedGroups":
        """Coerce string-integer years to int and reject values outside 1-4.

        The ["all"] sentinel and [] are left untouched.
        """
        coerced: list[int | str] = []
        for value in self.years:
            if value == "all":
                coerced.append(value)
                continue
            # Coerce string integers like "2" to 2.
            if isinstance(value, str):
                stripped = value.strip()
                if not stripped.lstrip("-").isdigit():
                    raise ValueError(f"Invalid year value: {value!r}")
                value = int(stripped)
            if isinstance(value, int) and not (1 <= value <= 4):
                raise ValueError(f"Year value out of range (1-4): {value!r}")
            coerced.append(value)
        self.years = coerced
        return self


class PriorityEnum(str, Enum):
    """Priority classification. Any other value is AI_PARSE_ERROR."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class AIExtractionResult(BaseModel):
    """The complete, validated output of the AI extraction pass (design §4.2)."""

    summary: str
    what_changed: str
    affected_groups: AffectedGroups
    ambiguous_dimensions: list[str] = []  # safe default per FR-12
    ambiguous_raw_text: dict[str, str] = {}  # safe default per FR-12
    deadlines: list[DeadlineItem]
    required_actions: list[RequiredActionItem]
    priority: PriorityEnum
    priority_reason: str

    @model_validator(mode="after")
    def _check_affected_group_consistency(self) -> "AIExtractionResult":
        """Enforce the schema consistency rules from design §5.2 / FR-12."""
        for dim in _DIMENSIONS:
            values = getattr(self.affected_groups, dim)

            # ["all"] must be exactly the single sentinel — no mixed lists.
            if "all" in values and values != ["all"]:
                raise ValueError(
                    f"Dimension '{dim}' mixes 'all' with specific values: {values!r}"
                )

            # An empty dimension MUST be flagged as ambiguous.
            if values == [] and dim not in self.ambiguous_dimensions:
                raise ValueError(
                    f"Dimension '{dim}' is empty but not in ambiguous_dimensions"
                )

        for dim in self.ambiguous_dimensions:
            # Every ambiguous dimension must have raw text recorded.
            if dim not in self.ambiguous_raw_text:
                raise ValueError(
                    f"Ambiguous dimension '{dim}' has no entry in ambiguous_raw_text"
                )
            # Every ambiguous dimension must map to a [] dimension value.
            if dim not in _DIMENSIONS:
                raise ValueError(f"Unknown ambiguous dimension: {dim!r}")
            if getattr(self.affected_groups, dim) != []:
                raise ValueError(
                    f"Ambiguous dimension '{dim}' is not empty ([]) in affected_groups"
                )

        return self
