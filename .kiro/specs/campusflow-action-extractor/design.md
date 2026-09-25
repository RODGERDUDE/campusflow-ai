# Spec: campusflow-action-extractor — Technical Design

**Version:** 1.0 (Draft)
**Status:** Ready for Review
**Traceable to:** requirements.md v1.0 (Final)

---

## 1. Overview

### 1.1 Purpose

CampusFlow AI transforms a college announcement into a personalized, actionable
result for a specific student. The system extracts structured information from
the announcement using an LLM, then deterministically computes whether the
announcement is relevant to the student's profile, and generates a personalized
checklist when applicable.

The core differentiating design principle: **relevance is computed by the backend
using deterministic logic, not trusted from the LLM**. The LLM performs
extraction only.

### 1.2 MVP Architecture Summary

```
Browser (React + Vite + TypeScript)
  │
  │  POST /api/v1/analyze
  │  { announcement_text, student_profile }
  │
  ▼
FastAPI Backend (Python 3.11+)
  ├─ Pydantic: validate request
  ├─ ai_service: build prompt → call Gemini → validate response
  ├─ relevance_service: compute relevance_status deterministically
  ├─ checklist_service: build checklist based on relevance_status
  └─ Return JSON response
  │
  ▼
Browser: render PersonalizedDecisionSummary + Checklist + Deadlines
```

### 1.3 Main Request/Response Flow

1. Student fills in profile (saved to localStorage) and pastes an announcement.
2. Frontend validates both inputs; if valid, sends `POST /api/v1/analyze`.
3. Frontend sets loading state; submit button disabled.
4. Backend validates request via Pydantic (HTTP 422 on failure).
5. Backend calls `ai_service.analyze(announcement_text)`.
6. `ai_service` constructs a structured prompt, calls Gemini, validates the
   JSON response against the `AIExtractionResult` Pydantic model.
7. Backend calls `relevance_service.compute(extraction, student_profile)`.
8. Backend calls `checklist_service.build(extraction, relevance_status)`.
9. Backend assembles and returns the full `AnalyzeResponse` (HTTP 200).
10. Frontend clears loading state, renders decision summary, checklist, deadlines,
    and priority. Student can mark checklist items complete.

---

## 2. Architecture

### 2.1 Frontend

**Stack:** React 18, Vite, TypeScript

- Single-page application served from `frontend/`.
- All HTTP calls go through `src/services/api.ts`. No component calls `fetch`
  or `axios` directly.
- Student profile is persisted in `localStorage` under the key
  `campusflow_profile`. No backend session or auth.
- Component state (loading, error, results, checklist completion) is managed
  with React `useState` and `useEffect`. No Redux or external state library.
- TypeScript interfaces for all API shapes live in `src/types/index.ts`.

### 2.2 Backend

**Stack:** Python 3.11+, FastAPI, Pydantic v2

- Single FastAPI application in `backend/`.
- Strict layer separation: routes → services → schemas. No business logic in
  route handlers.
- All configuration (API key, model name, CORS origin) read from environment
  variables via `python-dotenv`.
- No database in MVP. No announcement history stored.

### 2.3 AI Provider

**Provider:** Google Gemini (via `google-generativeai` SDK)
**Model:** configured via `GEMINI_MODEL` environment variable

- All LLM interaction is isolated in `backend/app/services/ai_service.py`.
- The interface exposed by `ai_service` is provider-agnostic. Switching to
  OpenAI requires changes only inside `ai_service.py`.
- JSON mode (or explicit JSON schema in the prompt) is used to request
  structured output. Free-text parsing is never used.

### 2.4 Pydantic Validation

Two validation stages:

1. **Request validation**: `AnalyzeRequest` schema validates `announcement_text`
   (50–10,000 chars) and `student_profile` (all five fields present and valid)
   before any AI call is made. FastAPI raises HTTP 422 automatically.

2. **AI output validation**: `AIExtractionResult` schema validates the LLM
   response before it is used for any computation. Failures raise `AI_PARSE_ERROR`.

### 2.5 Student Profile — localStorage only

- The student profile is submitted with every request and discarded after use.
- It is never written to any backend data store.
- No user accounts, sessions, or authentication tokens are issued.

### 2.6 No Announcement History

The backend does not persist announcements or analysis results. There is no
database in the MVP. This is explicitly out of scope (Section 3.2 of requirements).

---

## 3. Components

### 3.1 Frontend Components

**`AnnouncementInput`**
Renders the text area for pasting the announcement. Enforces 50–10,000 character
constraint with live character count and validation message. Trims whitespace
before passing to the controller.

**`StudentProfileForm`**
Renders and manages the five profile fields (Name, Department, Specialization,
Year, Section). Loads saved values from localStorage on mount. Saves to
localStorage on change. Validates all fields are non-empty before allowing
analysis submission.

**`AnalyzeController`** (page-level logic, not a visible component)
Orchestrates the analysis flow: validates both inputs, calls `api.analyze()`,
manages loading/error/result state, passes results to display components.
Disables submit during in-flight requests.

**`LoadingState`**
Full-area loading spinner shown from the moment the request is sent until a
response arrives or an error occurs.

**`ErrorState`**
Displays a user-friendly error message. Shows a "Try Again" button. Never
exposes raw error objects or stack traces. Handles network errors, backend
errors, and frontend timeout (30s).

**`PersonalizedDecisionSummary`**
The primary output panel. Appears at the top of the results section. Renders
the relevance status badge, relevance reason, and per-status content:
- RELEVANT: green badge, checklist, deadlines, priority
- NOT RELEVANT: neutral badge, explanation, no checklist
- NEEDS REVIEW (UNCERTAIN): amber badge, advisory message, no checklist

**`WhatChangedSection`**
Displays `analysis.summary` and `analysis.what_changed`.

**`AffectedGroupsSection`**
Displays `analysis.affected_groups` in readable form. Shows `ambiguous_raw_text`
when dimensions are ambiguous, to help the student understand the NEEDS REVIEW result.

**`DeadlineSection`**
Displays each deadline in `analysis.deadlines`. Shows `original_date_text` for
display; uses normalized `date` for sorting if available. Does not show deadlines
as obligations when status is UNCERTAIN.

**`RequiredActionsSection`**
Displays `analysis.required_actions`. Only shown when status is RELEVANT.

**`Checklist`**
Renders `checklist` items with checkboxes. Manages completion state in component
state (not persisted). Each item shows `description` and `deadline_text`.
Only rendered when `relevance_status` is `"RELEVANT"`.

**`PriorityDisplay`**
Shows `analysis.priority` as a colour-coded badge (High=red, Medium=amber,
Low=green) alongside `analysis.priority_reason`.

### 3.2 Backend Components

**`api/analyze.py`** — Route handler
Single route: `POST /api/v1/analyze`. Accepts `AnalyzeRequest`, delegates to
`analysis_service.run()`, returns `AnalyzeResponse`. Contains no business logic.

**`schemas/request.py`** — Request schemas
- `StudentProfile`: name, department, specialization, year (int 1–4), section
- `AnalyzeRequest`: announcement_text (str, min 50, max 10000), student_profile

**`schemas/ai_output.py`** — AI extraction schema
- `DeadlineItem`: label, date (str|None), original_date_text, description
- `RequiredActionItem`: action, by (str|None), original_by_text (str|None), details (str|None)
- `AffectedGroups`: departments, specializations, years, sections (each: list)
- `AIExtractionResult`: summary, what_changed, affected_groups, ambiguous_dimensions,
  ambiguous_raw_text, deadlines, required_actions, priority, priority_reason

**`schemas/response.py`** — Response schemas
- `ChecklistItem`: id, description, deadline (str|None), deadline_text (str|None), completed
- `RelevanceResult`: relevance_status, relevance_reason
- `AnalyzeResponse`: analysis (AIExtractionResult), relevance (RelevanceResult), checklist

**`services/ai_service.py`** — AI provider interface
Builds the structured prompt, calls Gemini, parses and validates the JSON
response into `AIExtractionResult`. Raises `AIProviderError` on provider
failure, `AIParseError` on validation failure. Provider-agnostic interface.

**`services/prompt_builder.py`** — Prompt construction
Builds the system instruction and user message sent to the model. Contains the
JSON schema definition, all semantic rules (ambiguity, date, priority), and
extraction-only instructions.

**`services/relevance_service.py`** — Relevance computation
Implements the deterministic relevance algorithm from FR-06. Takes
`AIExtractionResult` and `StudentProfile`, returns `RelevanceResult`.

**`services/checklist_service.py`** — Checklist generation
Takes `AIExtractionResult` and `relevance_status`, returns `list[ChecklistItem]`.
Returns `[]` for NOT_RELEVANT and UNCERTAIN.

**`services/analysis_service.py`** — Orchestration
Calls ai_service → relevance_service → checklist_service in sequence.
Assembles the final `AnalyzeResponse`. Catches and translates errors.

**`core/config.py`** — Configuration
Reads `GEMINI_API_KEY`, `GEMINI_MODEL`, `CORS_ORIGIN` from environment.

**`core/exceptions.py`** — Custom exceptions
`AIProviderError`, `AIParseError` with HTTP status codes and error codes.

**`main.py`** — FastAPI app entry point
Creates the FastAPI app, configures CORS, registers the router.

---

## 4. Data Models

All models are Pydantic v2. Fields match the approved API contract exactly.

### 4.1 Request Models

```python
class StudentProfile(BaseModel):
    name: str
    department: str
    specialization: str
    year: int = Field(ge=1, le=4)
    section: str

class AnalyzeRequest(BaseModel):
    announcement_text: str = Field(min_length=50, max_length=10000)
    student_profile: StudentProfile
```

### 4.2 AI Extraction Output Models

```python
class DeadlineItem(BaseModel):
    label: str
    date: str | None          # YYYY-MM-DD or None
    original_date_text: str   # always preserved
    description: str

class RequiredActionItem(BaseModel):
    action: str
    by: str | None            # YYYY-MM-DD or None
    original_by_text: str | None
    details: str | None

class AffectedGroups(BaseModel):
    departments: list[str | int]     # ["CSE"] | ["all"] | []
    specializations: list[str | int] # ["AI"]  | ["all"] | []
    years: list[int | str]           # [2]     | ["all"] | []
    sections: list[str | int]        # ["A"]   | ["all"] | []

class PriorityEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class AIExtractionResult(BaseModel):
    summary: str
    what_changed: str
    affected_groups: AffectedGroups
    ambiguous_dimensions: list[str] = []    # safe to default
    ambiguous_raw_text: dict[str, str] = {} # safe to default
    deadlines: list[DeadlineItem]
    required_actions: list[RequiredActionItem]
    priority: PriorityEnum
    priority_reason: str
```

**Validation notes:**
- `ambiguous_dimensions` and `ambiguous_raw_text` may default to empty if absent
  (safe default per FR-12).
- `years` in specific lists: a custom validator coerces string integers to `int`
  and rejects values outside 1–4.
- After parsing, a cross-field validator checks: every entry in
  `ambiguous_dimensions` has a key in `ambiguous_raw_text`, and every `[]`
  dimension is in `ambiguous_dimensions`.

### 4.3 Response Models

```python
class RelevanceStatusEnum(str, Enum):
    RELEVANT = "RELEVANT"
    NOT_RELEVANT = "NOT_RELEVANT"
    UNCERTAIN = "UNCERTAIN"

class RelevanceResult(BaseModel):
    relevance_status: RelevanceStatusEnum
    relevance_reason: str

class ChecklistItem(BaseModel):
    id: str
    description: str
    deadline: str | None       # YYYY-MM-DD or None
    deadline_text: str | None  # original wording for display
    completed: bool = False

class AnalyzeResponse(BaseModel):
    analysis: AIExtractionResult
    relevance: RelevanceResult
    checklist: list[ChecklistItem]
```

### 4.4 TypeScript Interfaces (Frontend)

```typescript
// src/types/index.ts

export interface StudentProfile {
  name: string;
  department: string;
  specialization: string;
  year: number;
  section: string;
}

export interface DeadlineItem {
  label: string;
  date: string | null;
  original_date_text: string;
  description: string;
}

export interface RequiredActionItem {
  action: string;
  by: string | null;
  original_by_text: string | null;
  details: string | null;
}

export interface AffectedGroups {
  departments: (string | number)[];
  specializations: (string | number)[];
  years: (string | number)[];
  sections: (string | number)[];
}

export type RelevanceStatus = "RELEVANT" | "NOT_RELEVANT" | "UNCERTAIN";
export type Priority = "High" | "Medium" | "Low";

export interface Analysis {
  summary: string;
  what_changed: string;
  affected_groups: AffectedGroups;
  ambiguous_dimensions: string[];
  ambiguous_raw_text: Record<string, string>;
  deadlines: DeadlineItem[];
  required_actions: RequiredActionItem[];
  priority: Priority;
  priority_reason: string;
}

export interface RelevanceResult {
  relevance_status: RelevanceStatus;
  relevance_reason: string;
}

export interface ChecklistItem {
  id: string;
  description: string;
  deadline: string | null;
  deadline_text: string | null;
  completed: boolean;
}

export interface AnalyzeResponse {
  analysis: Analysis;
  relevance: RelevanceResult;
  checklist: ChecklistItem[];
}

export interface ApiError {
  detail: string;
  code: string;
}
```

---

## 5. Affected Groups and Ambiguity Design

### 5.1 Canonical Semantics (from FR-05)

| Dimension value | Meaning | Backend treatment |
|-----------------|---------|------------------|
| `["all"]` | Announcement explicitly places no restriction on this dimension | Always passes — every student matches |
| `["CSE", "ECE"]` | Announcement explicitly targets these values only | Student's value must be in this list (case-insensitive) |
| `[]` | AI could not determine a reliable value | Dimension is ambiguous; MUST also appear in `ambiguous_dimensions` |

**`ambiguous_dimensions`**: list of dimension names the AI flagged as unresolvable.
Must be `[]` if nothing is ambiguous.

**`ambiguous_raw_text`**: maps each ambiguous dimension name to the original
wording from the announcement. Must be `{}` if nothing is ambiguous.

### 5.2 Schema Consistency Rules (enforced by Pydantic cross-field validator)

```
for each dimension in [departments, specializations, years, sections]:
    if affected_groups[dimension] == []:
        assert dimension in ambiguous_dimensions        # else AI_PARSE_ERROR
    if dimension in ambiguous_dimensions:
        assert dimension in ambiguous_raw_text          # else AI_PARSE_ERROR
        assert affected_groups[dimension] == []         # else AI_PARSE_ERROR
```

### 5.3 What the Backend Does NOT Do

- Does not default a missing `affected_groups` key to `["all"]` or `[]`.
- Does not interpret `["all"]` as ambiguous.
- Does not interpret `[]` as "no students" (zero-match); it means "indeterminate".
- Does not modify `ambiguous_raw_text` values — they are passed through as-is.

---

## 6. Relevance Algorithm

### 6.1 Pseudocode

```python
def compute_relevance(
    extraction: AIExtractionResult,
    profile: StudentProfile
) -> RelevanceResult:

    dimensions = {
        "departments":     profile.department,
        "specializations": profile.specialization,
        "years":           profile.year,
        "sections":        profile.section,
    }

    failed_dimensions = []
    uncertain_dimensions = []

    for dim_name, student_value in dimensions.items():
        dim_values = getattr(extraction.affected_groups, dim_name)

        if dim_name in extraction.ambiguous_dimensions:
            uncertain_dimensions.append(dim_name)

        elif dim_values == ["all"]:
            pass  # passes unconditionally

        elif student_value_in(student_value, dim_values):
            pass  # passes — student's value is explicitly listed

        else:
            failed_dimensions.append(dim_name)  # explicit exclusion

    # Priority order: exclusion beats ambiguity beats all-pass
    if failed_dimensions:
        status = RelevanceStatusEnum.NOT_RELEVANT
        reason = build_not_relevant_reason(failed_dimensions, dimensions, extraction)

    elif uncertain_dimensions:
        status = RelevanceStatusEnum.UNCERTAIN
        reason = build_uncertain_reason(uncertain_dimensions, extraction)

    else:
        status = RelevanceStatusEnum.RELEVANT
        reason = build_relevant_reason(dimensions, extraction)

    return RelevanceResult(relevance_status=status, relevance_reason=reason)
```

**`student_value_in(student_value, dim_values)`**: performs case-insensitive
string comparison for string dimensions; direct integer equality for `years`.

### 6.2 Decision Flow

```
For each dimension (departments, specializations, years, sections):
    │
    ├─ Is this dimension in ambiguous_dimensions?
    │       YES → mark as UNCERTAIN_CONTRIBUTOR
    │
    ├─ Is dim_values == ["all"]?
    │       YES → PASS
    │
    ├─ Is student's value in dim_values? (case-insensitive)
    │       YES → PASS
    │
    └─ Otherwise → FAIL_CONTRIBUTOR

After evaluating all four dimensions:
    │
    ├─ Any FAIL_CONTRIBUTOR? → NOT_RELEVANT  (explicit exclusion wins)
    │
    ├─ Any UNCERTAIN_CONTRIBUTOR? → UNCERTAIN
    │
    └─ All PASS → RELEVANT
```

### 6.3 Relevance Reason Generation

The `relevance_reason` is a plain-English string built from the algorithm result:

- **RELEVANT**: Names the matched dimensions. E.g.: *"This applies to you because
  you are a 2nd-year CSE AI student in Section A."*
- **NOT_RELEVANT**: Names the failing dimension and contrasts profile vs. target.
  E.g.: *"This notice targets 1st-year ECE students. Your profile: Year 2, CSE."*
- **UNCERTAIN**: Quotes `ambiguous_raw_text` for each uncertain dimension and
  advises verification. E.g.: *"The announcement refers to 'senior students' —
  it is unclear which year this maps to. Please verify manually."*

---

## 7. AI Prompt Design

### 7.1 Strategy

The prompt instructs the model to perform **extraction and classification only**.
Relevance computation is explicitly stated as the backend's responsibility —
the model MUST NOT attempt to determine whether the announcement is relevant to
the student.

### 7.2 System / Instruction Prompt

```
You are an information extraction assistant for a college announcement analysis
system. Your job is to extract structured data from a college announcement and
return it as valid JSON matching the schema below.

RULES:
1. Extract only. Do not determine whether the announcement is relevant to any
   student. Relevance is computed by the backend.
2. Return ONLY valid JSON. No explanations, no markdown, no extra text.
3. All required fields must be present. Do not omit any field.

AFFECTED_GROUPS RULES:
- Use ["all"] ONLY when the announcement EXPLICITLY states no restriction on a
  dimension (e.g., "all students", "the entire college").
- Use [] for a dimension when you CANNOT reliably determine the target group
  without guessing. Add the dimension name to ambiguous_dimensions and record
  the original wording in ambiguous_raw_text.
- Do NOT use ["all"] as a fallback when the group is unclear.
- Do NOT invent specific values. If you cannot determine the year, do not guess
  [3, 4] — use [] instead.
- years values must be integers (1, 2, 3, or 4). Not strings.

DATE RULES:
- Normalize dates to YYYY-MM-DD ONLY when the year is explicitly stated in the
  announcement. Set date to null otherwise.
- Do NOT invent a year. "September 30" without a year → date: null,
  original_date_text: "September 30".
- Relative expressions ("next Monday", "tomorrow", "in two weeks") → date: null,
  original_date_text: [exact original wording].
- Always preserve the exact original wording in original_date_text.

PRIORITY RULES:
- If a deadline date is provided (non-null): use date proximity.
  Within 7 days = High. Within 30 days = Medium. Beyond 30 days = Low.
- If no reliable date is available: infer from urgency language.
  "immediately", "urgent", "mandatory by", "last chance" = High.
  "should complete", "please ensure", "recommended" = Medium.
  "for your information", "optional" = Low.
  No signals present = Medium.
- Explain in priority_reason whether you used date proximity or urgency language,
  and quote the relevant signal.

AMBIGUOUS LANGUAGE EXAMPLES (always use [] for these unless the announcement
defines them explicitly):
- "senior students", "junior students", "eligible students",
  "selected students", "engineering students"

OUTPUT SCHEMA:
{
  "summary": "string",
  "what_changed": "string",
  "affected_groups": {
    "departments": ["string"] | ["all"] | [],
    "specializations": ["string"] | ["all"] | [],
    "years": [integer] | ["all"] | [],
    "sections": ["string"] | ["all"] | []
  },
  "ambiguous_dimensions": ["string"],
  "ambiguous_raw_text": { "dimension_name": "original wording" },
  "deadlines": [
    {
      "label": "string",
      "date": "YYYY-MM-DD or null",
      "original_date_text": "string",
      "description": "string"
    }
  ],
  "required_actions": [
    {
      "action": "string",
      "by": "YYYY-MM-DD or null",
      "original_by_text": "string or null",
      "details": "string or null"
    }
  ],
  "priority": "High" | "Medium" | "Low",
  "priority_reason": "string"
}
```

### 7.3 User Message

```
ANNOUNCEMENT:
{announcement_text}
```

The student profile is NOT included in the AI prompt. The model does not need
it — relevance is computed by the backend after extraction.

### 7.4 API Call

```python
model = genai.GenerativeModel(
    model_name=config.GEMINI_MODEL,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json"
    ),
    system_instruction=SYSTEM_PROMPT,
)
response = model.generate_content(user_message)
raw_json = response.text
result = AIExtractionResult.model_validate_json(raw_json)
```

If `model_validate_json` raises a `ValidationError`, the service raises
`AIParseError("AI_PARSE_ERROR")`.

---

## 8. Date Handling

### 8.1 Rules

| Scenario | `date` field | `original_date_text` |
|----------|-------------|----------------------|
| Full date stated: "September 30, 2026" | `"2026-09-30"` | `"September 30, 2026"` |
| Month/day only: "September 30" | `null` | `"September 30"` |
| Relative: "next Monday" | `null` | `"next Monday"` |
| Relative: "in two weeks" | `null` | `"in two weeks"` |
| No date mentioned | field omitted from item | n/a |

### 8.2 Checklist Item Date Fields

Each checklist item carries two date fields, sourced from the corresponding
`required_action` or `deadline`:

| Field | Source | Purpose |
|-------|--------|---------|
| `deadline` | `by` or `date` (YYYY-MM-DD or null) | Machine-readable; used for sorting |
| `deadline_text` | `original_by_text` or `original_date_text` | Human-readable display |

The frontend ALWAYS displays `deadline_text`. It uses `deadline` only if it
needs to sort items chronologically.

### 8.3 Backend Validation

The backend validates that `date` and `by` fields, when non-null, match the
pattern `^\d{4}-\d{2}-\d{2}$`. If a non-null value fails this pattern, it is
treated as `AI_PARSE_ERROR`.

---

## 9. Priority Design

### 9.1 Priority Determination (from FR-11)

```
Priority logic:

if any deadline has a reliable normalized date (non-null):
    days_until = (deadline_date - analysis_date).days
    if days_until <= 7:   priority = "High"
    elif days_until <= 30: priority = "Medium"
    else:                  priority = "Low"

else (all dates are null or no deadlines):
    scan announcement text for urgency signals:
    HIGH signals:   "immediately", "urgent", "must complete before",
                    "last chance", "failure to comply", "mandatory by"
    MEDIUM signals: "should complete", "please ensure",
                    "required before end of", "recommended"
    LOW signals:    "for your information", "note that", "you may", "optional"
    default:        "Medium" (no signals present)
```

### 9.2 Priority Reason

`priority_reason` must explicitly state:
- Which path was used: date proximity or urgency language
- The specific signal that drove the decision

Example: *"Priority set to High because the deadline (2026-09-30) is within
7 days of the analysis date."*
Example: *"Priority set to High based on urgency language: 'must complete before'."*

### 9.3 Analysis Date

The AI is instructed to use date proximity relative to the analysis date.
For MVP, the backend passes the current UTC date as context in the prompt if
needed for the date-proximity path. The AI does not independently determine
the current date.

---

## 10. Checklist Generation

### 10.1 Generation Logic

```python
def build_checklist(
    extraction: AIExtractionResult,
    relevance_status: RelevanceStatusEnum
) -> list[ChecklistItem]:

    if relevance_status in (NOT_RELEVANT, UNCERTAIN):
        return []

    # RELEVANT: build from required_actions
    items = []
    for idx, action in enumerate(extraction.required_actions):
        items.append(ChecklistItem(
            id=f"item-{idx}",
            description=action.action,
            deadline=action.by,
            deadline_text=action.original_by_text,
            completed=False
        ))

    # If no required_actions but there are deadlines, still return []
    # Frontend shows "No specific actions required."
    return items
```

### 10.2 Frontend Completion State

```typescript
// AnalyzeController manages checklist state locally
const [checklist, setChecklist] = useState<ChecklistItem[]>([]);

const toggleItem = (id: string) => {
  setChecklist(prev =>
    prev.map(item =>
      item.id === id ? { ...item, completed: !item.completed } : item
    )
  );
};
```

State lives in React component memory only. It is reset when a new analysis
is run or the page is refreshed.

---

## 11. API Contract

### 11.1 MVP Endpoint

**The MVP exposes exactly one endpoint:**

```
POST /api/v1/analyze
```

No history endpoints. No GET endpoints. No authentication endpoints.

### 11.2 Request

```json
{
  "announcement_text": "string (50–10,000 characters)",
  "student_profile": {
    "name": "string",
    "department": "string",
    "specialization": "string",
    "year": 2,
    "section": "A"
  }
}
```

### 11.3 Success Response — HTTP 200

```json
{
  "analysis": {
    "summary": "Second-year CSE AI students must register for an AI exam.",
    "what_changed": "A new mandatory AI certification examination has been introduced.",
    "affected_groups": {
      "departments": ["CSE"],
      "specializations": ["AI"],
      "years": [2],
      "sections": ["all"]
    },
    "ambiguous_dimensions": [],
    "ambiguous_raw_text": {},
    "deadlines": [
      {
        "label": "Registration deadline",
        "date": null,
        "original_date_text": "September 30",
        "description": "Last date to register for the AI certification examination"
      }
    ],
    "required_actions": [
      {
        "action": "Register for the AI certification examination",
        "by": null,
        "original_by_text": "September 30",
        "details": null
      }
    ],
    "priority": "High",
    "priority_reason": "Priority set to High based on urgency language: 'must register'."
  },
  "relevance": {
    "relevance_status": "RELEVANT",
    "relevance_reason": "This applies to you because you are a 2nd-year CSE AI student."
  },
  "checklist": [
    {
      "id": "item-0",
      "description": "Register for the AI certification examination",
      "deadline": null,
      "deadline_text": "September 30",
      "completed": false
    }
  ]
}
```

### 11.4 Validation Error — HTTP 422

```json
{
  "detail": [
    {
      "loc": ["body", "announcement_text"],
      "msg": "String should have at least 50 characters",
      "type": "string_too_short"
    }
  ]
}
```

### 11.5 Application Error — HTTP 500

```json
{
  "detail": "The AI service failed to parse the announcement. Please try again.",
  "code": "AI_PARSE_ERROR"
}
```

### 11.6 Error Code Table

| Code | HTTP | Trigger |
|------|------|---------|
| `AI_PARSE_ERROR` | 500 | LLM response fails Pydantic validation |
| `AI_PROVIDER_ERROR` | 500 | Gemini API unreachable or returns error |
| `ANNOUNCEMENT_TOO_SHORT` | 422 | Pydantic: text < 50 chars |
| `ANNOUNCEMENT_TOO_LONG` | 422 | Pydantic: text > 10,000 chars |
| `PROFILE_INCOMPLETE` | 422 | Pydantic: missing or invalid profile field |

---

## 12. Security Design

| Concern | Design decision |
|---------|----------------|
| Gemini API key | Stored only in `backend/.env`. Read via `os.getenv()`. Never in source code. |
| `.env` files | Listed in `.gitignore`. Never committed. |
| Frontend isolation | Frontend only calls `VITE_API_BASE_URL/api/v1/analyze`. No direct Gemini calls from browser. |
| Request validation | All inputs validated by Pydantic before any AI call. Invalid requests rejected at HTTP 422. |
| AI output trust | LLM responses validated against `AIExtractionResult` schema. Raw output never forwarded. |
| Student profile | Never persisted server-side. Discarded after single use. |
| Logging | AI prompts/responses logged at DEBUG. No student profile fields (name, dept, etc.) logged. |
| Secrets in responses | No API keys, internal paths, or stack traces in any HTTP response. |

---

## 13. Error Handling

### 13.1 Error Matrix

| Error | Where caught | HTTP response | Frontend display |
|-------|-------------|---------------|-----------------|
| Announcement < 50 chars | Pydantic / FR-01 | 422 | Inline validation message |
| Announcement > 10,000 chars | Pydantic / FR-01 | 422 | Inline validation message |
| Profile field missing | Pydantic / FR-02 | 422 | Inline validation message |
| Profile year outside 1–4 | Pydantic / FR-02 | 422 | Inline validation message |
| Gemini API unreachable | `ai_service` exception handler | 500 + `AI_PROVIDER_ERROR` | "Analysis service unavailable. Please try again." |
| Gemini returns non-JSON | `ai_service` Pydantic validator | 500 + `AI_PARSE_ERROR` | "Could not process the announcement. Please try again." |
| Gemini returns invalid schema | `ai_service` Pydantic validator | 500 + `AI_PARSE_ERROR` | same |
| Invalid `affected_groups` | Cross-field Pydantic validator | 500 + `AI_PARSE_ERROR` | same |
| Invalid `priority` value | Pydantic enum validator | 500 + `AI_PARSE_ERROR` | same |
| Invalid `relevance_status` | `relevance_service` guard | 500 | "Internal error. Please try again." |
| Frontend network timeout (30s) | `api.ts` axios timeout | — | "Request timed out. Please try again." |
| Unexpected backend error | FastAPI global exception handler | 500 | "An unexpected error occurred. Please try again." |

### 13.2 FastAPI Global Exception Handler

```python
@app.exception_handler(AIParseError)
async def ai_parse_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message, "code": "AI_PARSE_ERROR"}
    )

@app.exception_handler(AIProviderError)
async def ai_provider_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": exc.message, "code": "AI_PROVIDER_ERROR"}
    )
```

---

## 14. Performance

| Metric | Target | Maximum | Timeout |
|--------|--------|---------|---------|
| AI response time (end-to-end) | 5–10 s | 15 s | 30 s frontend |

### 14.1 Backend

- No caching, queuing, or async task runners in MVP.
- The `/api/v1/analyze` route is synchronous (or simple async with `await`).
- If Gemini exceeds 30 s, the frontend times out and shows a timeout message.
  The backend request may still complete — it is simply not delivered to the
  frontend in that case.

### 14.2 Frontend

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000, // 30 seconds
});
```

The submit button is disabled from the moment `api.analyze()` is called until
the promise settles (success, error, or timeout).

---

## 15. Frontend State Management

### 15.1 State Shape

```typescript
// In AnalyzeController / Home page component

const [profile, setProfile] = useState<StudentProfile | null>(null);
const [announcementText, setAnnouncementText] = useState("");
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const [result, setResult] = useState<AnalyzeResponse | null>(null);
const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
```

### 15.2 localStorage Profile

```typescript
// Load on mount
useEffect(() => {
  const saved = localStorage.getItem("campusflow_profile");
  if (saved) setProfile(JSON.parse(saved));
}, []);

// Save on update
const saveProfile = (p: StudentProfile) => {
  setProfile(p);
  localStorage.setItem("campusflow_profile", JSON.stringify(p));
};
```

### 15.3 No External State Library

React `useState` and `useEffect` are sufficient for the MVP. Redux, Zustand,
or Context API are not introduced. State is lifted to the page-level component
and passed down as props.

---

## 16. File and Folder Structure

```
CampusFlow/
│
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── .env                          # VITE_API_BASE_URL
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── types/
│       │   └── index.ts              # All TypeScript interfaces
│       ├── services/
│       │   └── api.ts                # axios instance + analyzeAnnouncement()
│       ├── components/
│       │   ├── AnnouncementInput/
│       │   │   └── AnnouncementInput.tsx
│       │   ├── StudentProfileForm/
│       │   │   └── StudentProfileForm.tsx
│       │   ├── PersonalizedDecisionSummary/
│       │   │   └── PersonalizedDecisionSummary.tsx
│       │   ├── Checklist/
│       │   │   └── Checklist.tsx
│       │   ├── DeadlineSection/
│       │   │   └── DeadlineSection.tsx
│       │   ├── PriorityDisplay/
│       │   │   └── PriorityDisplay.tsx
│       │   ├── LoadingState/
│       │   │   └── LoadingState.tsx
│       │   └── ErrorState/
│       │       └── ErrorState.tsx
│       └── pages/
│           └── Home/
│               └── Home.tsx          # Page-level controller + layout
│
├── backend/
│   ├── .env                          # GEMINI_API_KEY, GEMINI_MODEL, CORS_ORIGIN
│   ├── requirements.txt
│   ├── main.py                       # FastAPI app, CORS, router
│   └── app/
│       ├── api/
│       │   └── analyze.py            # POST /api/v1/analyze route
│       ├── schemas/
│       │   ├── request.py            # AnalyzeRequest, StudentProfile
│       │   ├── ai_output.py          # AIExtractionResult and sub-models
│       │   └── response.py           # AnalyzeResponse, ChecklistItem, RelevanceResult
│       ├── services/
│       │   ├── ai_service.py         # Gemini call, prompt, response parsing
│       │   ├── prompt_builder.py     # System prompt + user message construction
│       │   ├── relevance_service.py  # Deterministic relevance algorithm
│       │   ├── checklist_service.py  # Checklist generation
│       │   └── analysis_service.py   # Orchestration
│       └── core/
│           ├── config.py             # Settings from env vars
│           └── exceptions.py         # AIParseError, AIProviderError
│
├── .kiro/
│   ├── steering/
│   │   ├── project-overview.md
│   │   └── dev-rules.md
│   └── specs/
│       └── campusflow-action-extractor/
│           ├── requirements.md
│           ├── design.md             # this file
│           └── tasks.md              # to be created
│
├── architecture.md
├── DECISIONS.md
└── README.md
```

---

## 17. Testing Strategy

### 17.1 Backend Unit Tests

**Input validation** (`test_request_validation.py`):
- Announcement text below 50 chars → HTTP 422
- Announcement text above 10,000 chars → HTTP 422
- Missing profile field → HTTP 422
- Profile year = 0 or 5 → HTTP 422
- Valid request → passes validation

**`AIExtractionResult` validation** (`test_ai_output_validation.py`):
- Missing `affected_groups` key → `ValidationError`
- `[]` dimension not in `ambiguous_dimensions` → `ValidationError`
- Dimension in `ambiguous_dimensions` missing from `ambiguous_raw_text` → `ValidationError`
- `priority` = `"Critical"` → `ValidationError`
- `years: ["2"]` → coerced to `[2]`
- `years: [5]` → `ValidationError`
- `["all", "CSE"]` in any dimension → `ValidationError`
- `ambiguous_dimensions` absent → defaults to `[]`
- `ambiguous_raw_text` absent → defaults to `{}`

**Relevance algorithm** (`test_relevance_service.py`):
- All `["all"]` → RELEVANT for any profile
- Matching dept, year, spec, section → RELEVANT
- Non-matching dept → NOT_RELEVANT
- Non-matching year → NOT_RELEVANT
- One dim ambiguous, rest match → UNCERTAIN
- One dim explicitly excludes + another ambiguous → NOT_RELEVANT (exclusion wins)
- Multiple dims ambiguous → UNCERTAIN
- Multiple dims fail → NOT_RELEVANT
- Case-insensitive match (student="cse", dim=["CSE"]) → RELEVANT

**Date handling** (`test_date_handling.py`):
- Full date "September 30, 2026" → `date: "2026-09-30"`, `original_date_text: "September 30, 2026"`
- Partial date "September 30" → `date: null`, `original_date_text: "September 30"`
- Relative "next Monday" → `date: null`, `original_date_text: "next Monday"`
- Invalid date format → `AI_PARSE_ERROR`

**Priority** (`test_priority_service.py`):
- Non-null date within 7 days → High
- Non-null date 8–30 days away → Medium
- Non-null date > 30 days → Low
- Null date + "urgent" in text → High
- Null date + "optional" in text → Low
- Null date + no signals → Medium

**Checklist generation** (`test_checklist_service.py`):
- RELEVANT + 2 required actions → checklist length 2
- RELEVANT + 0 required actions → `[]`
- NOT_RELEVANT → `[]`
- UNCERTAIN → `[]`
- `deadline_text` carried from `original_by_text`
- `deadline` carried from `by`

### 17.2 Backend Integration Tests

**API endpoint** (`test_analyze_endpoint.py`):
- Valid request with mocked AI → HTTP 200 with full response shape
- AI provider error → HTTP 500 + `AI_PROVIDER_ERROR`
- AI returns malformed JSON → HTTP 500 + `AI_PARSE_ERROR`
- Invalid request body → HTTP 422
- CORS headers present

### 17.3 Frontend Tests

**`StudentProfileForm`**:
- Renders all five fields
- Blocks submission on empty field
- Saves to localStorage on valid submit
- Loads from localStorage on mount

**`AnnouncementInput`**:
- Blocks submission under 50 chars
- Shows character count
- Trims whitespace before submission

**`PersonalizedDecisionSummary`**:
- Renders RELEVANT badge for RELEVANT status
- Renders NOT RELEVANT badge for NOT_RELEVANT status
- Renders NEEDS REVIEW badge (not "UNCERTAIN") for UNCERTAIN status
- Checklist absent for NOT_RELEVANT
- Checklist absent for UNCERTAIN
- Advisory message present for UNCERTAIN

**`Checklist`**:
- Renders checkboxes for each item
- Toggle marks item complete
- Toggle again unchecks item

### 17.4 Key Edge Cases from FR-14

| Edge case | Test |
|-----------|------|
| EC-05 (vague language) | Mock AI response with `ambiguous_dimensions: ["departments"]`, assert UNCERTAIN |
| EC-06 (malformed AI) | Mock AI raising exception, assert HTTP 500 + `AI_PARSE_ERROR` |
| EC-09 (duplicate submit) | Submit button disabled after first click, no second request |
| EC-13 (missing AG key) | Mock AI response missing `sections` key, assert `ValidationError` |
| EC-15 (exclusion + ambiguity) | Exclusion in years + ambiguity in depts, assert NOT_RELEVANT |

---

## 18. Traceability

| Requirement | Design component / section |
|-------------|---------------------------|
| FR-01 Announcement Input | `AnnouncementInput` component, `AnalyzeRequest.announcement_text` Pydantic field |
| FR-02 Student Profile | `StudentProfileForm`, `StudentProfile` Pydantic model, localStorage design (§15.2) |
| FR-03 AI Analysis Trigger | `AnalyzeController`, `api.ts`, `analyze.py` route, CORS, security design (§12), performance design (§14) |
| FR-04 Structured AI Extraction | `AIExtractionResult` model, `ai_service.py`, `prompt_builder.py`, AI prompt design (§7) |
| FR-05 Affected Student Extraction | `AffectedGroups` model, affected groups design (§5), Pydantic cross-field validators |
| FR-06 Personalized Relevance Detection | `relevance_service.py`, relevance algorithm (§6) |
| FR-07 Relevance Explanation | `relevance_service.py` reason builders, `RelevanceResult.relevance_reason` |
| FR-08 Deadline Extraction | `DeadlineItem` model, date handling design (§8), prompt date rules |
| FR-09 Checklist Generation Rules | `checklist_service.py`, checklist generation design (§10), `ChecklistItem` model |
| FR-10 Required Action Extraction | `RequiredActionItem` model, prompt action extraction rules |
| FR-11 Priority Classification | Priority design (§9), prompt priority rules, `PriorityEnum` |
| FR-12 AI Output Validation | `AIExtractionResult` Pydantic validators, cross-field validators, error handling (§13) |
| FR-13 API Contract | API contract design (§11), `AnalyzeResponse`, `analyze.py` route |
| FR-14 Edge Cases | Error handling matrix (§13.1), testing strategy edge cases (§17.4) |
| FR-15 Personalized Decision Summary | `PersonalizedDecisionSummary` component, status display mapping (§3.1) |

---

## 19. Design Decisions

| Decision | Rationale |
|----------|-----------|
| Gemini as default AI provider | Free tier available; no paid infrastructure needed for hackathon; supports JSON mode natively |
| Provider-agnostic `ai_service` interface | Switching to OpenAI requires changes only in `ai_service.py`; no other layer imports Gemini types |
| Backend-computed relevance (not LLM-computed) | LLM output is probabilistic and cannot be trusted for deterministic business logic; relevance must be reproducible and testable |
| Pydantic v2 for all validation | Single consistent validation layer; automatic HTTP 422 for request errors; catches AI output errors before they reach business logic |
| localStorage for student profile | No authentication needed for MVP; simplest browser-native persistence; profile is small and non-sensitive |
| No authentication in MVP | Adds significant complexity out of scope for a hackathon; the core differentiator (relevance detection) does not require user identity |
| No announcement history / no database | Persistent storage requires a data model, migrations, and retrieval endpoints all out of MVP scope; removing it eliminates a significant complexity surface |
| `[]` means ambiguous, `["all"]` means explicit no-restriction | Avoids the temptation to silently default ambiguous dimensions to "all students", which would produce false RELEVANT results |
| Separate `original_date_text` field | Normalizing all dates risks losing information when the year is unknown; preserving the original wording lets the frontend display what the announcement actually said |
| No Redux / no external state library | React `useState` is sufficient for a single-page form → result flow; introducing Redux adds boilerplate without benefit at this scale |
| No unnecessary paid infrastructure | Hackathon constraint; only the Gemini free tier API is used externally |

---

## 20. Implementation Boundaries

The following are explicitly **NOT** part of this design and MUST NOT be
implemented as part of the MVP:

- User authentication, registration, or login
- User accounts or sessions
- Server-side student profile storage
- Announcement storage or retrieval
- Announcement history endpoints (`GET /api/v1/announcements`, etc.)
- Notification or reminder system
- Google Calendar or iCal integration
- PDF, image, or OCR-based announcement input
- Voice input
- Analytics, reporting, or admin dashboard
- Redis, Celery, or any task queue
- Microservices or service mesh
- PostgreSQL (SQLite would be used if a DB were needed; no DB needed for MVP)
- Multi-user or multi-tenant support
- Any paid infrastructure beyond Gemini free tier API usage
- Mobile app or React Native

---

*This design document is directly traceable to requirements.md v1.0 (Final).
Implementation tasks (tasks.md) to be created after design review.*
