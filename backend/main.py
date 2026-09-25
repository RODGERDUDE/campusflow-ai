"""
CampusFlow AI — FastAPI application entry point.

For development:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import config

app = FastAPI(
    title="CampusFlow AI",
    description="Transforms college announcements into personalized, actionable checklists.",
    version="1.0.0",
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
