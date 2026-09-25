"""
Integration tests for POST /api/v1/analyze (design §17.2).

Uses FastAPI's TestClient with the AI extraction layer PATCHED, so tests are
deterministic and NO real Gemini call is made. Placeholder env values only —
the real GEMINI_API_KEY is never required, used, or exposed.
"""

import os

# Placeholder env so app.core.config imports cleanly. NOT real credentials.
os.environ.setdefault("GEMINI_API_KEY", "test-placeholder-not-a-real-key")
os.environ.setdefault("GEMINI_MODEL", "test-model-placeholder")

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import main
from app.core import config
from app.core.exceptions import AIParseError, AIProviderError
from app.schemas.ai_output import (
    AffectedGroups,
    AIExtractionResult,
    DeadlineItem,
    PriorityEnum,
    RequiredActionItem,
)

client = TestClient(main.app, raise_server_exceptions=False)

# Where the endpoint reaches the AI layer (analysis_service imports ai_service).
AI_ANALYZE_PATH = "app.services.analysis_service.ai_service.analyze"

VALID_BODY = {
    "announcement_text": (
        "All second-year CSE AI students must register for the AI certification "
        "examination before September 30."
    ),
    "student_profile": {
        "name": "Ananya",
        "department": "CSE",
        "specialization": "AI",
        "year": 2,
        "section": "A",
    },
}


def sample_extraction() -> AIExtractionResult:
    """A deterministic extraction the mocked AI layer returns."""
    return AIExtractionResult(
        summary="Second-year CSE AI students must register for an AI exam.",
        what_changed="A new mandatory AI certification examination.",
        affected_groups=AffectedGroups(
            departments=["CSE"], specializations=["AI"], years=[2], sections=["all"]
        ),
        ambiguous_dimensions=[],
        ambiguous_raw_text={},
        deadlines=[
            DeadlineItem(
                label="Registration deadline",
                date=None,
                original_date_text="September 30",
                description="Last date to register.",
            )
        ],
        required_actions=[
            RequiredActionItem(
                action="Register for the AI certification examination",
                by=None,
                original_by_text="September 30",
                details=None,
            )
        ],
        priority=PriorityEnum.HIGH,
        priority_reason="Urgency language: 'must register'.",
    )


def test_valid_request_returns_200_with_correct_shape():
    with patch(AI_ANALYZE_PATH, new=AsyncMock(return_value=sample_extraction())):
        response = client.post("/api/v1/analyze", json=VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    # Response shape is exactly analysis / relevance / checklist.
    assert set(data.keys()) == {"analysis", "relevance", "checklist"}
    assert data["relevance"]["relevance_status"] in {
        "RELEVANT",
        "NOT_RELEVANT",
        "UNCERTAIN",
    }


def test_response_has_no_announcement_id():
    with patch(AI_ANALYZE_PATH, new=AsyncMock(return_value=sample_extraction())):
        response = client.post("/api/v1/analyze", json=VALID_BODY)
    data = response.json()
    assert "announcement_id" not in data
    assert "announcement_id" not in data["analysis"]


def test_provider_error_returns_500_with_code():
    with patch(
        AI_ANALYZE_PATH,
        new=AsyncMock(side_effect=AIProviderError("provider down")),
    ):
        response = client.post("/api/v1/analyze", json=VALID_BODY)
    assert response.status_code == 500
    assert response.json()["code"] == "AI_PROVIDER_ERROR"


def test_parse_error_returns_500_with_code():
    with patch(
        AI_ANALYZE_PATH,
        new=AsyncMock(side_effect=AIParseError("bad json")),
    ):
        response = client.post("/api/v1/analyze", json=VALID_BODY)
    assert response.status_code == 500
    assert response.json()["code"] == "AI_PARSE_ERROR"


def test_announcement_too_short_returns_422():
    body = {
        "announcement_text": "too short",
        "student_profile": VALID_BODY["student_profile"],
    }
    # No AI call should happen; Pydantic rejects first.
    response = client.post("/api/v1/analyze", json=body)
    assert response.status_code == 422


def test_missing_profile_field_returns_422():
    profile = {k: v for k, v in VALID_BODY["student_profile"].items() if k != "section"}
    body = {
        "announcement_text": VALID_BODY["announcement_text"],
        "student_profile": profile,
    }
    response = client.post("/api/v1/analyze", json=body)
    assert response.status_code == 422


def test_cors_header_present_for_configured_origin():
    with patch(AI_ANALYZE_PATH, new=AsyncMock(return_value=sample_extraction())):
        response = client.post(
            "/api/v1/analyze",
            json=VALID_BODY,
            headers={"Origin": config.CORS_ORIGIN},
        )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == config.CORS_ORIGIN
    )
