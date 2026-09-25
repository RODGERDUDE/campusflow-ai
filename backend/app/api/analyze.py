"""
CampusFlow AI — Analyze route.

The single MVP endpoint: POST /api/v1/analyze (design §3.2, §11). This handler
is intentionally thin — it accepts the validated request and delegates all work
to analysis_service.run(). It contains no business logic.
"""

from fastapi import APIRouter

from app.schemas.request import AnalyzeRequest
from app.schemas.response import AnalyzeResponse
from app.services import analysis_service

router = APIRouter(prefix="/api/v1")


@router.post("/analyze", response_model=AnalyzeResponse, status_code=200)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze an announcement for a student and return the personalized result."""
    return await analysis_service.run(request)
