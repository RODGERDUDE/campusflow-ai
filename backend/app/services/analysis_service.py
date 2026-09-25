"""
CampusFlow AI — Analysis orchestration.

Ties the three stages together for a single analysis request (design §3.2):

  1. ai_service.analyze        -> structured extraction (LLM)
  2. relevance_service.compute -> deterministic relevance for the student
  3. checklist_service.build   -> personalized checklist

Exceptions raised by ai_service (AIProviderError / AIParseError) are NOT caught
here; they propagate to the route handler's FastAPI exception handlers.
"""

from app.schemas.request import AnalyzeRequest
from app.schemas.response import AnalyzeResponse
from app.services import ai_service, checklist_service, relevance_service


async def run(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run the full analysis pipeline and assemble the response."""
    extraction = await ai_service.analyze(request.announcement_text)
    relevance = relevance_service.compute(extraction, request.student_profile)
    checklist = checklist_service.build(extraction, relevance.relevance_status)

    return AnalyzeResponse(
        analysis=extraction,
        relevance=relevance,
        checklist=checklist,
    )
