"""
CampusFlow AI — FastAPI application entry point.

For development:
    uvicorn main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analyze
from app.core import config
from app.core.exceptions import AIParseError, AIProviderError

app = FastAPI(
    title="CampusFlow AI",
    description="Transforms college announcements into personalized, actionable checklists.",
    version="1.0.0",
)


@app.exception_handler(AIParseError)
async def ai_parse_error_handler(request: Request, exc: AIParseError) -> JSONResponse:
    """Return HTTP 500 with the standard error shape for AI parse failures."""
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(AIProviderError)
async def ai_provider_error_handler(
    request: Request, exc: AIProviderError
) -> JSONResponse:
    """Return HTTP 500 with the standard error shape for AI provider failures."""
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Fallback for unexpected errors. Returns a generic message, no stack trace."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "code": "INTERNAL_SERVER_ERROR",
        },
    )

# CORS — allow the frontend dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.CORS_ORIGIN],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint. Returns OK when the server is running."""
    return {"status": "ok"}


# Register the analyze route (POST /api/v1/analyze).
app.include_router(analyze.router)
