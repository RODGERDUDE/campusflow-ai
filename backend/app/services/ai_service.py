"""
CampusFlow AI — AI provider interface.

Isolates all LLM interaction (design §7.4, §12). This is the only module that
imports the Gemini SDK; the interface exposed here is provider-agnostic, so
switching providers requires changes only inside this file.

The AI performs extraction only. The student profile is never sent to the model
and never logged. The Gemini API key is read from config and is never logged.
"""

import logging

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.core import config
from app.schemas.ai_output import AIExtractionResult
from app.services.prompt_builder import SYSTEM_PROMPT, build_user_message

logger = logging.getLogger(__name__)


async def analyze(announcement_text: str) -> AIExtractionResult:
    """Send an announcement to Gemini and return validated structured output.

    Raises:
        AIProviderError: the Gemini API was unreachable or returned an error.
        AIParseError: the model's response failed schema validation.
    """
    # Local import so the exception classes stay in one place and to avoid any
    # circular-import risk with the app package.
    from app.core.exceptions import AIParseError, AIProviderError

    # Provider-specific call, isolated in its own try/except so that only
    # genuine provider/network failures become AIProviderError.
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,  # never hardcoded
            contents=build_user_message(announcement_text),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
    except errors.APIError as exc:
        # Do not include the API key or student data in the message.
        raise AIProviderError("The AI service is currently unavailable.") from exc

    raw_json = response.text

    # Log the raw AI response for development tracing. No student profile data
    # is ever present here, and the API key is not logged.
    logger.debug("Raw AI response: %s", raw_json)

    # Validate the model output against the expected schema before returning it.
    try:
        return AIExtractionResult.model_validate_json(raw_json)
    except ValidationError as exc:
        raise AIParseError(
            "The AI service returned data that could not be understood."
        ) from exc
