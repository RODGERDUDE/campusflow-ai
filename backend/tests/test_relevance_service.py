"""
Unit tests for the deterministic relevance service (design §17.1).

Covers the relevance algorithm and reason text (FR-06, FR-07). No Gemini calls;
no GEMINI_API_KEY.
"""

from app.schemas.ai_output import AIExtractionResult
from app.schemas.request import StudentProfile
from app.schemas.response import RelevanceStatusEnum
from app.services import relevance_service


PROFILE = StudentProfile(
    name="Ananya", department="CSE", specialization="AI", year=2, section="A"
)


def make_extraction(
    departments,
    specializations,
    years,
    sections,
    ambiguous_dimensions=None,
    ambiguous_raw_text=None,
):
    """Build a valid AIExtractionResult with the given affected_groups."""
    return AIExtractionResult(
        summary="s",
        what_changed="w",
        affected_groups={
            "departments": departments,
            "specializations": specializations,
            "years": years,
            "sections": sections,
        },
        ambiguous_dimensions=ambiguous_dimensions or [],
        ambiguous_raw_text=ambiguous_raw_text or {},
        deadlines=[],
        required_actions=[],
        priority="Medium",
        priority_reason="r",
    )


def test_all_dimensions_all_is_relevant_for_any_profile():
    ext = make_extraction(["all"], ["all"], ["all"], ["all"])
    other = StudentProfile(
        name="X", department="ME", specialization="Robotics", year=4, section="Z"
    )
    result = relevance_service.compute(ext, other)
    assert result.relevance_status == RelevanceStatusEnum.RELEVANT


def test_exact_match_all_dimensions_is_relevant():
    ext = make_extraction(["CSE"], ["AI"], [2], ["A"])
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.RELEVANT
    # Reason references the matched profile values.
    assert "CSE" in result.relevance_reason
    assert "AI" in result.relevance_reason


def test_one_dimension_mismatch_is_not_relevant():
    ext = make_extraction(["ECE"], ["AI"], [2], ["A"])
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.NOT_RELEVANT
    # Reason names the failing dimension.
    assert "department" in result.relevance_reason.lower()


def test_one_dimension_ambiguous_rest_pass_is_uncertain():
    ext = make_extraction(
        [],
        ["all"],
        ["all"],
        ["all"],
        ambiguous_dimensions=["departments"],
        ambiguous_raw_text={"departments": "engineering students"},
    )
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.UNCERTAIN
    # Reason quotes the ambiguous wording.
    assert "engineering students" in result.relevance_reason


def test_mismatch_plus_ambiguity_is_not_relevant_exclusion_wins():
    ext = make_extraction(
        ["ECE"],
        [],
        ["all"],
        ["all"],
        ambiguous_dimensions=["specializations"],
        ambiguous_raw_text={"specializations": "selected students"},
    )
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.NOT_RELEVANT


def test_multiple_ambiguous_is_uncertain():
    ext = make_extraction(
        [],
        [],
        ["all"],
        ["all"],
        ambiguous_dimensions=["departments", "specializations"],
        ambiguous_raw_text={
            "departments": "engineering students",
            "specializations": "selected students",
        },
    )
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.UNCERTAIN


def test_case_insensitive_string_match_is_relevant():
    ext = make_extraction(["cse"], ["ai"], [2], ["a"])
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.RELEVANT


def test_year_integer_match_is_relevant():
    ext = make_extraction(["all"], ["all"], [1, 2, 3], ["all"])
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.RELEVANT


def test_year_integer_no_match_is_not_relevant():
    ext = make_extraction(["all"], ["all"], [1, 3, 4], ["all"])
    result = relevance_service.compute(ext, PROFILE)
    assert result.relevance_status == RelevanceStatusEnum.NOT_RELEVANT
    assert "year" in result.relevance_reason.lower()
