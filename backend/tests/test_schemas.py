"""
Unit tests for the request and AI-output schemas (design §17.1).

Covers AnalyzeRequest validation (FR-01, FR-02) and AIExtractionResult
cross-field validation (FR-05, FR-12). No Gemini calls; no GEMINI_API_KEY.
"""

import pytest
from pydantic import ValidationError

from app.schemas.ai_output import AffectedGroups, AIExtractionResult
from app.schemas.request import AnalyzeRequest


# --- Fixtures / helpers -------------------------------------------------------

VALID_PROFILE = {
    "name": "Ananya",
    "department": "CSE",
    "specialization": "AI",
    "year": 2,
    "section": "A",
}

# 50-10,000 chars.
VALID_TEXT = "x" * 60


def make_extraction(**overrides):
    """Build a valid AIExtractionResult payload, applying any overrides."""
    data = {
        "summary": "s",
        "what_changed": "w",
        "affected_groups": {
            "departments": ["all"],
            "specializations": ["all"],
            "years": ["all"],
            "sections": ["all"],
        },
        "ambiguous_dimensions": [],
        "ambiguous_raw_text": {},
        "deadlines": [],
        "required_actions": [],
        "priority": "High",
        "priority_reason": "r",
    }
    data.update(overrides)
    return data


# --- AnalyzeRequest validation (FR-01, FR-02) --------------------------------


def test_valid_request_passes():
    req = AnalyzeRequest(announcement_text=VALID_TEXT, student_profile=VALID_PROFILE)
    assert req.student_profile.year == 2


def test_text_too_short_rejected():
    with pytest.raises(ValidationError):
        AnalyzeRequest(announcement_text="x" * 10, student_profile=VALID_PROFILE)


def test_text_too_long_rejected():
    with pytest.raises(ValidationError):
        AnalyzeRequest(announcement_text="x" * 10001, student_profile=VALID_PROFILE)


def test_year_zero_rejected():
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            announcement_text=VALID_TEXT,
            student_profile={**VALID_PROFILE, "year": 0},
        )


def test_year_five_rejected():
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            announcement_text=VALID_TEXT,
            student_profile={**VALID_PROFILE, "year": 5},
        )


def test_missing_profile_field_rejected():
    bad_profile = {k: v for k, v in VALID_PROFILE.items() if k != "section"}
    with pytest.raises(ValidationError):
        AnalyzeRequest(announcement_text=VALID_TEXT, student_profile=bad_profile)


# --- AIExtractionResult cross-field validation (FR-05, FR-12) ----------------


def test_valid_all_dimensions_passes():
    model = AIExtractionResult(**make_extraction())
    assert model.priority.value == "High"


def test_empty_dimension_not_in_ambiguous_rejected():
    with pytest.raises(ValidationError):
        AIExtractionResult(
            **make_extraction(
                affected_groups={
                    "departments": [],
                    "specializations": ["all"],
                    "years": ["all"],
                    "sections": ["all"],
                },
            )
        )


def test_ambiguous_dimension_missing_raw_text_rejected():
    with pytest.raises(ValidationError):
        AIExtractionResult(
            **make_extraction(
                affected_groups={
                    "departments": [],
                    "specializations": ["all"],
                    "years": ["all"],
                    "sections": ["all"],
                },
                ambiguous_dimensions=["departments"],
                ambiguous_raw_text={},
            )
        )


def test_ambiguous_dimensions_defaults_to_empty_when_absent():
    data = make_extraction()
    del data["ambiguous_dimensions"]
    del data["ambiguous_raw_text"]
    model = AIExtractionResult(**data)
    assert model.ambiguous_dimensions == []
    assert model.ambiguous_raw_text == {}


def test_year_string_is_coerced_to_int():
    groups = AffectedGroups(
        departments=["CSE"], specializations=["AI"], years=["2"], sections=["A"]
    )
    assert groups.years == [2]


def test_year_out_of_range_rejected():
    with pytest.raises(ValidationError):
        AffectedGroups(
            departments=["CSE"], specializations=["AI"], years=[5], sections=["A"]
        )


def test_mixed_all_list_rejected():
    with pytest.raises(ValidationError):
        AIExtractionResult(
            **make_extraction(
                affected_groups={
                    "departments": ["all", "CSE"],
                    "specializations": ["all"],
                    "years": ["all"],
                    "sections": ["all"],
                },
            )
        )


def test_invalid_priority_rejected():
    with pytest.raises(ValidationError):
        AIExtractionResult(**make_extraction(priority="Critical"))
