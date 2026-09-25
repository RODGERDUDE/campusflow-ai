"""
Unit tests for the checklist service (design §17.1).

Covers checklist generation rules by relevance status and field mapping
(FR-09, EC-02, EC-08). No Gemini calls; no GEMINI_API_KEY.
"""

from app.schemas.ai_output import AIExtractionResult
from app.schemas.response import RelevanceStatusEnum
from app.services import checklist_service


def make_extraction(required_actions):
    """Build a valid AIExtractionResult with the given required_actions."""
    return AIExtractionResult(
        summary="s",
        what_changed="w",
        affected_groups={
            "departments": ["all"],
            "specializations": ["all"],
            "years": ["all"],
            "sections": ["all"],
        },
        ambiguous_dimensions=[],
        ambiguous_raw_text={},
        deadlines=[],
        required_actions=required_actions,
        priority="Medium",
        priority_reason="r",
    )


TWO_ACTIONS = [
    {
        "action": "Register for the exam",
        "by": "2026-09-30",
        "original_by_text": "September 30, 2026",
        "details": None,
    },
    {
        "action": "Submit the form",
        "by": None,
        "original_by_text": "September 30",
        "details": "Bring your ID.",
    },
]


def test_not_relevant_returns_empty():
    ext = make_extraction(TWO_ACTIONS)
    assert checklist_service.build(ext, RelevanceStatusEnum.NOT_RELEVANT) == []


def test_uncertain_returns_empty():
    ext = make_extraction(TWO_ACTIONS)
    assert checklist_service.build(ext, RelevanceStatusEnum.UNCERTAIN) == []


def test_relevant_with_two_actions_returns_two_items():
    ext = make_extraction(TWO_ACTIONS)
    items = checklist_service.build(ext, RelevanceStatusEnum.RELEVANT)
    assert len(items) == 2
    assert items[0].id == "item-0"
    assert items[1].id == "item-1"
    assert items[0].description == "Register for the exam"


def test_relevant_with_no_actions_returns_empty():
    ext = make_extraction([])
    assert checklist_service.build(ext, RelevanceStatusEnum.RELEVANT) == []


def test_deadline_text_copied_from_original_by_text():
    ext = make_extraction(TWO_ACTIONS)
    items = checklist_service.build(ext, RelevanceStatusEnum.RELEVANT)
    assert items[0].deadline_text == "September 30, 2026"
    assert items[1].deadline_text == "September 30"


def test_deadline_copied_from_by():
    ext = make_extraction(TWO_ACTIONS)
    items = checklist_service.build(ext, RelevanceStatusEnum.RELEVANT)
    # Normalized date preserved when present, None when absent.
    assert items[0].deadline == "2026-09-30"
    assert items[1].deadline is None


def test_completed_initializes_to_false():
    ext = make_extraction(TWO_ACTIONS)
    items = checklist_service.build(ext, RelevanceStatusEnum.RELEVANT)
    assert all(item.completed is False for item in items)
