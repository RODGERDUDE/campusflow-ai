"""
CampusFlow AI — Checklist generation.

Builds the personalized checklist from the AI-extracted required actions
(design §10). This is deterministic, backend-controlled logic:

  RELEVANT     -> one checklist item per required action
  NOT_RELEVANT -> [] (no items)
  UNCERTAIN    -> [] (no items — never assume actions from ambiguous eligibility)

Checklist completion is tracked on the frontend only, so every item is created
with completed=False. Deadlines are copied straight from the extracted action:
the normalized date (YYYY-MM-DD or None) and the original wording. No dates or
years are invented here.
"""

from app.schemas.ai_output import AIExtractionResult
from app.schemas.response import ChecklistItem, RelevanceStatusEnum


def build(
    extraction: AIExtractionResult,
    relevance_status: RelevanceStatusEnum,
) -> list[ChecklistItem]:
    """Build the checklist for a given relevance status (design §10.1)."""
    # Only RELEVANT announcements produce checklist items.
    if relevance_status is not RelevanceStatusEnum.RELEVANT:
        return []

    items: list[ChecklistItem] = []
    for idx, action in enumerate(extraction.required_actions):
        items.append(
            ChecklistItem(
                id=f"item-{idx}",
                description=action.action,
                deadline=action.by,  # YYYY-MM-DD or None, as extracted
                deadline_text=action.original_by_text,  # original wording
                completed=False,
            )
        )

    # If there were no required actions, this is [] and the frontend shows
    # "No specific actions required."
    return items
