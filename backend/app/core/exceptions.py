"""
CampusFlow AI — Custom application exceptions.

These exceptions represent failures in the AI extraction pipeline. FastAPI
exception handlers (registered in main.py) translate them into the standard
error response shape: {"detail": ..., "code": ...}.
"""


class AIParseError(Exception):
    """Raised when the AI response cannot be parsed into the expected schema."""

    code = "AI_PARSE_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AIProviderError(Exception):
    """Raised when the AI provider is unreachable or returns an error."""

    code = "AI_PROVIDER_ERROR"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
