"""
Tests for the Gemini provider-facing structured-output schema.

The Gemini Developer API rejects `additionalProperties` (open maps). These tests
confirm the Gemini-facing schema contains NO `additionalProperties` anywhere and
that a provider result converts into a valid public AIExtractionResult. No
Gemini calls; no GEMINI_API_KEY.
"""

import json

from app.schemas.ai_output import AIExtractionResult
from app.schemas.gemini_output import (
    GeminiAffectedGroups,
    GeminiAmbiguousRawText,
    GeminiExtraction,
)


def _contains_additional_properties(node) -> bool:
    """Recursively check a JSON-schema-like structure for additionalProperties."""
    if isinstance(node, dict):
        if "additionalProperties" in node:
            return True
        return any(_contains_additional_properties(v) for v in node.values())
    if isinstance(node, list):
        return any(_contains_additional_properties(v) for v in node)
    return False


def test_gemini_pydantic_schema_has_no_additional_properties():
    schema = GeminiExtraction.model_json_schema()
    assert not _contains_additional_properties(schema), (
        "GeminiExtraction JSON schema must not contain additionalProperties"
    )


def test_gemini_sdk_transformed_schema_has_no_additional_properties():
    """The schema the SDK actually sends must also be free of the keyword."""
    from google.genai import _transformers as t  # type: ignore

    schema_obj = t.t_schema(None, GeminiExtraction)
    # Serialize the SDK Schema object to a plain dict and scan it.
    dumped = schema_obj.model_dump(exclude_none=True)
    dumped_json = json.loads(json.dumps(dumped, default=str))
    assert not _contains_additional_properties(dumped_json), (
        "SDK-transformed Gemini schema must not contain additionalProperties"
    )


def test_provider_result_converts_to_valid_public_model():
    provider = GeminiExtraction(
        summary="s",
        what_changed="w",
        affected_groups=GeminiAffectedGroups(
            departments=["CSE"], specializations=["AI"], years=[2], sections=[]
        ),
        ambiguous_dimensions=["sections"],
        ambiguous_raw_text=GeminiAmbiguousRawText(sections="all interested students"),
        deadlines=[],
        required_actions=[],
        priority="High",
        priority_reason="r",
    )
    public = AIExtractionResult.model_validate(provider.to_public_dict())
    # The fixed-field object became a dict with only the non-None dimension.
    assert public.ambiguous_raw_text == {"sections": "all interested students"}
    assert public.ambiguous_dimensions == ["sections"]
    assert public.affected_groups.sections == []
    assert public.priority.value == "High"


def test_public_dict_omits_none_ambiguous_entries():
    provider = GeminiExtraction(
        summary="s",
        what_changed="w",
        affected_groups=GeminiAffectedGroups(
            departments=["all"], specializations=["all"], years=[], sections=["all"]
        ),
        ambiguous_dimensions=["years"],
        ambiguous_raw_text=GeminiAmbiguousRawText(years="senior students"),
        priority="Medium",
        priority_reason="r",
    )
    data = provider.to_public_dict()
    assert data["ambiguous_raw_text"] == {"years": "senior students"}
    # Unset dimensions must not leak through as null entries.
    assert "departments" not in data["ambiguous_raw_text"]
    public = AIExtractionResult.model_validate(data)
    assert public.affected_groups.years == []
