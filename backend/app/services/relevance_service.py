"""
CampusFlow AI — Deterministic relevance computation.

Compares the AI-extracted affected_groups against the student's profile and
decides whether the announcement is RELEVANT, NOT_RELEVANT, or UNCERTAIN
(design §6). This logic is fully deterministic and lives in backend code — the
LLM is never asked to compute personalized relevance.

Precedence (design §6.2):
  1. Any non-ambiguous dimension mismatch  -> NOT_RELEVANT (exclusion wins)
  2. Otherwise any ambiguous dimension     -> UNCERTAIN
  3. Otherwise                             -> RELEVANT
"""

from app.schemas.ai_output import AIExtractionResult
from app.schemas.request import StudentProfile
from app.schemas.response import RelevanceResult, RelevanceStatusEnum

# Maps each affected_groups dimension to the student profile attribute it checks.
_DIMENSION_TO_PROFILE_ATTR = {
    "departments": "department",
    "specializations": "specialization",
    "years": "year",
    "sections": "section",
}

# Human-readable labels for reason strings.
_DIMENSION_LABEL = {
    "departments": "department",
    "specializations": "specialization",
    "years": "year",
    "sections": "section",
}


def _student_value_in(student_value: object, dim_values: list) -> bool:
    """Return True if the student's value is in the dimension's list.

    Case-insensitive comparison for strings; direct equality for integers
    (e.g. year). Handles mixed str/int lists safely.
    """
    for value in dim_values:
        if isinstance(student_value, str) and isinstance(value, str):
            if student_value.strip().lower() == value.strip().lower():
                return True
        elif student_value == value:
            return True
    return False


def compute(
    extraction: AIExtractionResult, profile: StudentProfile
) -> RelevanceResult:
    """Compute the relevance of an announcement for a specific student."""
    failed_dimensions: list[str] = []
    uncertain_dimensions: list[str] = []
    matched_dimensions: list[str] = []

    for dim_name, profile_attr in _DIMENSION_TO_PROFILE_ATTR.items():
        student_value = getattr(profile, profile_attr)
        dim_values = getattr(extraction.affected_groups, dim_name)

        if dim_name in extraction.ambiguous_dimensions:
            uncertain_dimensions.append(dim_name)
        elif dim_values == ["all"]:
            matched_dimensions.append(dim_name)
        elif _student_value_in(student_value, dim_values):
            matched_dimensions.append(dim_name)
        else:
            failed_dimensions.append(dim_name)

    # Precedence: explicit exclusion beats ambiguity beats all-pass.
    if failed_dimensions:
        status = RelevanceStatusEnum.NOT_RELEVANT
        reason = build_not_relevant_reason(failed_dimensions, profile, extraction)
    elif uncertain_dimensions:
        status = RelevanceStatusEnum.UNCERTAIN
        reason = build_uncertain_reason(uncertain_dimensions, extraction)
    else:
        status = RelevanceStatusEnum.RELEVANT
        reason = build_relevant_reason(profile)

    return RelevanceResult(relevance_status=status, relevance_reason=reason)


def build_relevant_reason(profile: StudentProfile) -> str:
    """Plain-English reason naming the student's matched profile (design §6.3)."""
    return (
        f"This applies to you because you are a Year {profile.year} "
        f"{profile.department} {profile.specialization} student in "
        f"Section {profile.section}."
    )


def build_not_relevant_reason(
    failed_dimensions: list[str],
    profile: StudentProfile,
    extraction: AIExtractionResult,
) -> str:
    """Plain-English reason naming the failing dimension(s) and contrasting values."""
    parts: list[str] = []
    for dim_name in failed_dimensions:
        label = _DIMENSION_LABEL[dim_name]
        target = getattr(extraction.affected_groups, dim_name)
        student_value = getattr(profile, _DIMENSION_TO_PROFILE_ATTR[dim_name])
        target_text = ", ".join(str(v) for v in target)
        parts.append(
            f"the {label} targets [{target_text}] but your {label} is "
            f"{student_value}"
        )
    detail = "; ".join(parts)
    return (
        f"This announcement does not apply to your profile because {detail}. "
        f"No action is required from you."
    )


def build_uncertain_reason(
    uncertain_dimensions: list[str], extraction: AIExtractionResult
) -> str:
    """Plain-English reason quoting the ambiguous wording and advising verification."""
    parts: list[str] = []
    for dim_name in uncertain_dimensions:
        label = _DIMENSION_LABEL[dim_name]
        raw = extraction.ambiguous_raw_text.get(dim_name, "")
        if raw:
            parts.append(f"the {label} is described as '{raw}'")
        else:
            parts.append(f"the {label} could not be determined")
    detail = "; ".join(parts)
    return (
        f"We could not determine whether this applies to you because {detail}. "
        f"Please verify with your department or faculty office before taking "
        f"any action."
    )
