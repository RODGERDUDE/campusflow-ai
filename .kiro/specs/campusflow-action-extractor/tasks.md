# Spec: campusflow-action-extractor — Implementation Tasks

**Version:** 1.0
**Status:** Ready for Implementation
**Traceable to:** requirements.md v1.0 (Final), design.md v1.0

---

## How to use this file

Work through tasks in phase order. Each task is self-contained and small enough
to implement in one Kiro session. Complete all tasks in a phase before starting
the next. Mark tasks complete as you go.

---

## Phase 1 — Project Setup

### T-01 — Initialise the backend Python project

**What to implement:**
- Create the `backend/` directory structure:
  ```
  backend/
  ├── main.py
  ├── requirements.txt
  ├── .env.example
  └── app/
      ├── __init__.py
      ├── api/
      │   └── __init__.py
      ├── schemas/
      │   └── __init__.py
      ├── services/
      │   └── __init__.py
      └── core/
          └── __init__.py
  ```
- Create `requirements.txt` with pinned versions:
  ```
  fastapi==0.111.0
  uvicorn[standard]==0.29.0
  pydantic==2.7.1
  python-dotenv==1.0.1
  google-generativeai==0.5.4
  ```
- Create `backend/.env.example`:
  ```
  GEMINI_API_KEY=your_key_here
  GEMINI_MODEL=gemini-1.5-pro
  CORS_ORIGIN=http://localhost:5173
  ```
- Create a minimal `main.py` that starts FastAPI with a health check route
  (`GET /health` returns `{"status": "ok"}`).

**Files involved:**
`backend/main.py`, `backend/requirements.txt`, `backend/.env.example`,
all `__init__.py` files

**Requirements satisfied:** FR-03 (backend foundation), design §2.2, §16

**Dependencies:** none

---

### T-02 — Configure backend settings and CORS

**What to implement:**
- Create `backend/app/core/config.py` that reads these env vars:
  - `GEMINI_API_KEY` (required, raises error if missing)
  - `GEMINI_MODEL` (required, never hardcoded)
  - `CORS_ORIGIN` (defaults to `http://localhost:5173`)
- Add CORS middleware to `main.py` using `CORS_ORIGIN` from config.
- Create `backend/.env` (not committed) by copying `.env.example` and filling
  in actual values.
- Add `.env` and `.env.example` entries to `backend/.gitignore`.

**Files involved:**
`backend/app/core/config.py`, `backend/main.py`, `backend/.gitignore`

**Requirements satisfied:** FR-03 (security — API key backend-only), design §12

**Dependencies:** T-01

---

### T-03 — Initialise the frontend React + Vite + TypeScript project

**What to implement:**
- Run `npm create vite@latest frontend -- --template react-ts` from the
  `CampusFlow/` root.
- Install Axios: `npm install axios`.
- Install ESLint + Prettier (already included by Vite template; verify config).
- Create `frontend/.env`:
  ```
  VITE_API_BASE_URL=http://localhost:8000
  ```
- Add `frontend/.env` to `.gitignore`.
- Delete the default Vite boilerplate content from `App.tsx` and `index.css`.
  Replace with a minimal skeleton: `<div>CampusFlow AI</div>`.
- Verify the dev server starts with `npm run dev`.

**Files involved:**
`frontend/` (entire scaffolded directory), `frontend/.env`, `.gitignore`

**Requirements satisfied:** FR-01, FR-03 (frontend foundation), design §2.1, §16

**Dependencies:** none (parallel with T-01)

---

### T-04 — Create shared TypeScript types

**What to implement:**
- Create `frontend/src/types/index.ts` with all interfaces from design §4.4:
  - `StudentProfile`
  - `DeadlineItem`
  - `RequiredActionItem`
  - `AffectedGroups`
  - `RelevanceStatus` (union type)
  - `Priority` (union type)
  - `Analysis`
  - `RelevanceResult`
  - `ChecklistItem`
  - `AnalyzeResponse`
  - `ApiError`

**Files involved:**
`frontend/src/types/index.ts`

**Requirements satisfied:** FR-04, FR-05, FR-06, FR-09, FR-13, design §4.4

**Dependencies:** T-03

---

## Phase 2 — Backend Foundation

### T-05 — Create custom exceptions

**What to implement:**
- Create `backend/app/core/exceptions.py` with:
  - `AIParseError(Exception)` — carries `message: str`, `code = "AI_PARSE_ERROR"`
  - `AIProviderError(Exception)` — carries `message: str`, `code = "AI_PROVIDER_ERROR"`
- Register FastAPI exception handlers in `main.py` that return the standard
  error shape `{"detail": ..., "code": ...}`:
  - `AIParseError` → HTTP 500
  - `AIProviderError` → HTTP 500
  - Generic `Exception` fallback → HTTP 500, generic message (no stack trace)

**Files involved:**
`backend/app/core/exceptions.py`, `backend/main.py`

**Requirements satisfied:** FR-12, FR-13, design §13

**Dependencies:** T-01, T-02

---

### T-06 — Create request Pydantic schemas

**What to implement:**
- Create `backend/app/schemas/request.py` with:
  - `StudentProfile`: name (str), department (str), specialization (str),
    year (int, ge=1, le=4), section (str)
  - `AnalyzeRequest`: announcement_text (str, min_length=50, max_length=10000),
    student_profile (StudentProfile)
- All fields are required (no defaults).

**Files involved:**
`backend/app/schemas/request.py`

**Requirements satisfied:** FR-01, FR-02, FR-03, design §4.1

**Dependencies:** T-01

---

### T-07 — Create AI extraction output Pydantic schemas

**What to implement:**
- Create `backend/app/schemas/ai_output.py` with all models from design §4.2:
  - `DeadlineItem`
  - `RequiredActionItem`
  - `AffectedGroups` with a `@model_validator` that:
    - Coerces string integers in `years` to `int`
    - Rejects year values outside 1–4
  - `PriorityEnum` (str enum: High, Medium, Low)
  - `AIExtractionResult` with a `@model_validator` that:
    - Checks every `[]` dimension also appears in `ambiguous_dimensions`
    - Checks every entry in `ambiguous_dimensions` has a key in `ambiguous_raw_text`
    - Checks every entry in `ambiguous_dimensions` maps to a `[]` dimension
    - Rejects `["all", "CSE"]` mixed lists
  - `ambiguous_dimensions` defaults to `[]` if absent (safe default)
  - `ambiguous_raw_text` defaults to `{}` if absent (safe default)

**Files involved:**
`backend/app/schemas/ai_output.py`

**Requirements satisfied:** FR-05, FR-08, FR-10, FR-11, FR-12, design §4.2, §5

**Dependencies:** T-01

---

### T-08 — Create response Pydantic schemas

**What to implement:**
- Create `backend/app/schemas/response.py` with:
  - `RelevanceStatusEnum` (str enum: RELEVANT, NOT_RELEVANT, UNCERTAIN)
  - `RelevanceResult`: relevance_status (RelevanceStatusEnum), relevance_reason (str)
  - `ChecklistItem`: id (str), description (str), deadline (str|None),
    deadline_text (str|None), completed (bool, default False)
  - `AnalyzeResponse`: analysis (AIExtractionResult), relevance (RelevanceResult),
    checklist (list[ChecklistItem])
- Note: `AnalyzeResponse` has NO `announcement_id` field.

**Files involved:**
`backend/app/schemas/response.py`

**Requirements satisfied:** FR-06, FR-09, FR-13, design §4.3

**Dependencies:** T-07

---

## Phase 3 — AI Extraction and Validation

### T-09 — Build the AI prompt

**What to implement:**
- Create `backend/app/services/prompt_builder.py` with:
  - `SYSTEM_PROMPT` constant containing the full system instruction from
    design §7.2, including:
    - Extraction-only instruction (no relevance computation)
    - `affected_groups` rules (`["all"]` vs `[]` semantics)
    - Date rules (no invented years, relative dates → null)
    - Priority rules (date proximity vs urgency language)
    - Ambiguous language examples
    - Complete JSON output schema
  - `build_user_message(announcement_text: str) -> str` function that wraps
    the announcement in the `ANNOUNCEMENT:` prefix
  - The student profile is NOT included in the prompt

**Files involved:**
`backend/app/services/prompt_builder.py`

**Requirements satisfied:** FR-04, FR-05, FR-08, FR-10, FR-11, design §7

**Dependencies:** T-07

---

### T-10 — Implement the AI service

**What to implement:**
- Create `backend/app/services/ai_service.py` with:
  - `async def analyze(announcement_text: str) -> AIExtractionResult`
  - Inside:
    1. Read `config.GEMINI_API_KEY` and `config.GEMINI_MODEL`
    2. Initialise `genai.GenerativeModel` with `response_mime_type="application/json"`
       and `system_instruction=SYSTEM_PROMPT`
    3. Call `model.generate_content(build_user_message(announcement_text))`
    4. Parse `response.text` with `AIExtractionResult.model_validate_json()`
    5. On `google.api_core.exceptions.GoogleAPIError` → raise `AIProviderError`
    6. On `pydantic.ValidationError` → raise `AIParseError`
    7. Log the raw AI response at DEBUG level (no student profile data in logs)
- The model name comes from `config.GEMINI_MODEL` — never hardcoded.

**Files involved:**
`backend/app/services/ai_service.py`

**Requirements satisfied:** FR-03 (security), FR-04, FR-12, design §7.4, §12

**Dependencies:** T-02, T-07, T-09

---

## Phase 4 — Deterministic Relevance Engine

### T-11 — Implement the relevance service

**What to implement:**
- Create `backend/app/services/relevance_service.py` with:
  - `def compute(extraction: AIExtractionResult, profile: StudentProfile) -> RelevanceResult`
  - Implement the exact algorithm from design §6.1:
    1. For each dimension (departments, specializations, years, sections):
       - If dimension in `ambiguous_dimensions` → UNCERTAIN contributor
       - Elif `["all"]` → passes
       - Elif student value in dim list (case-insensitive for strings) → passes
       - Else → FAIL contributor (NOT_RELEVANT)
    2. Priority: any FAIL → NOT_RELEVANT; any UNCERTAIN → UNCERTAIN; else RELEVANT
  - Implement `build_relevant_reason`, `build_not_relevant_reason`,
    `build_uncertain_reason` helper functions that produce plain-English strings
  - Relevant reason names matched dimensions
  - Not-relevant reason names the failing dimension and contrasts values
  - Uncertain reason quotes `ambiguous_raw_text` and advises manual verification

**Files involved:**
`backend/app/services/relevance_service.py`

**Requirements satisfied:** FR-06, FR-07, design §6

**Dependencies:** T-06, T-07, T-08

---

## Phase 5 — Checklist and Priority Logic

### T-12 — Implement the checklist service

**What to implement:**
- Create `backend/app/services/checklist_service.py` with:
  - `def build(extraction: AIExtractionResult, relevance_status: RelevanceStatusEnum) -> list[ChecklistItem]`
  - If `relevance_status` is NOT_RELEVANT or UNCERTAIN → return `[]`
  - If RELEVANT → build from `extraction.required_actions`:
    - `id = f"item-{idx}"`
    - `description = action.action`
    - `deadline = action.by` (YYYY-MM-DD or None)
    - `deadline_text = action.original_by_text`
    - `completed = False`
  - If `required_actions` is empty → return `[]`
    (frontend will show "No specific actions required")

**Files involved:**
`backend/app/services/checklist_service.py`

**Requirements satisfied:** FR-09, design §10

**Dependencies:** T-07, T-08

---

### T-13 — Implement the analysis orchestration service

**What to implement:**
- Create `backend/app/services/analysis_service.py` with:
  - `async def run(request: AnalyzeRequest) -> AnalyzeResponse`
  - Calls in sequence:
    1. `extraction = await ai_service.analyze(request.announcement_text)`
    2. `relevance = relevance_service.compute(extraction, request.student_profile)`
    3. `checklist = checklist_service.build(extraction, relevance.relevance_status)`
    4. Return `AnalyzeResponse(analysis=extraction, relevance=relevance, checklist=checklist)`
  - All exceptions from `ai_service` propagate up; the route handler's FastAPI
    exception handlers catch them.

**Files involved:**
`backend/app/services/analysis_service.py`

**Requirements satisfied:** FR-03, FR-04, FR-06, FR-09, design §3.2

**Dependencies:** T-10, T-11, T-12

---

## Phase 6 — API Integration

### T-14 — Create the analyze route

**What to implement:**
- Create `backend/app/api/analyze.py` with:
  - `router = APIRouter(prefix="/api/v1")`
  - `POST /analyze` route:
    - Accepts `AnalyzeRequest` (FastAPI handles 422 automatically)
    - Calls `await analysis_service.run(request)`
    - Returns `AnalyzeResponse` with HTTP 200
    - Contains NO business logic
- Register the router in `main.py`.
- Remove or keep the health check from T-01 (keep it — useful for debugging).

**Files involved:**
`backend/app/api/analyze.py`, `backend/main.py`

**Requirements satisfied:** FR-03, FR-13, design §3.2, §11

**Dependencies:** T-05, T-13

---

### T-15 — Manual end-to-end backend smoke test

**What to implement:**
- Start the backend with `uvicorn main:app --reload` from `backend/`.
- Use `curl` or a REST client to send a valid `POST /api/v1/analyze` request
  with a real announcement and student profile.
- Verify:
  - HTTP 200 response with correct shape
  - `relevance_status` is one of RELEVANT / NOT_RELEVANT / UNCERTAIN
  - No `announcement_id` in response
  - Checklist is `[]` for NOT_RELEVANT
  - `original_date_text` preserved when no year given
- Also test:
  - Announcement text under 50 chars → HTTP 422
  - Missing profile field → HTTP 422
  - Invalid year (e.g., 5) → HTTP 422

**Files involved:** none (verification only)

**Requirements satisfied:** FR-01, FR-02, FR-03, FR-13, AC-01, AC-02, AC-09

**Dependencies:** T-14

---

## Phase 7 — Frontend Setup

### T-16 — Create the Axios API service

**What to implement:**
- Create `frontend/src/services/api.ts` with:
  - An Axios instance with:
    - `baseURL: import.meta.env.VITE_API_BASE_URL`
    - `timeout: 30000` (30 seconds — frontend timeout per FR-03)
  - `export async function analyzeAnnouncement(announcementText: string, profile: StudentProfile): Promise<AnalyzeResponse>`
    - Calls `POST /api/v1/analyze`
    - On Axios timeout error → throws with a timeout-specific message
    - On HTTP error response → throws with `response.data.detail` and `response.data.code`
    - On network error → throws with a generic connectivity message

**Files involved:**
`frontend/src/services/api.ts`

**Requirements satisfied:** FR-03 (frontend security — no direct Gemini calls),
FR-03 (30s timeout), design §2.1, §14

**Dependencies:** T-04

---

### T-17 — Create the App layout and Home page skeleton

**What to implement:**
- Update `frontend/src/App.tsx` to render a `<Home />` page component.
- Create `frontend/src/pages/Home/Home.tsx` with:
  - Two-column or stacked layout: profile sidebar + main announcement area
  - Placeholder sections for: profile form, announcement input, results
  - All state variables declared: `profile`, `announcementText`, `isLoading`,
    `error`, `result`, `checklist` (per design §15)
  - No logic yet — just the layout shell and state declarations

**Files involved:**
`frontend/src/App.tsx`, `frontend/src/pages/Home/Home.tsx`

**Requirements satisfied:** FR-15 (decision summary at top of results), design §15, §16

**Dependencies:** T-03, T-04

---

## Phase 8 — Student Profile and localStorage

### T-18 — Build the StudentProfileForm component

**What to implement:**
- Create `frontend/src/components/StudentProfileForm/StudentProfileForm.tsx`:
  - Five inputs: Name (text), Department (text), Specialization (text),
    Year (number, 1–4), Section (text)
  - All fields required
  - On mount: load from `localStorage.getItem("campusflow_profile")` and
    pre-populate if present
  - On change: save to `localStorage.setItem("campusflow_profile", JSON.stringify(...))`
  - Expose `onProfileChange(profile: StudentProfile)` callback prop
  - Block submission if any field is empty (show inline validation message)
  - Year input: validate 1–4, show error if outside range

**Files involved:**
`frontend/src/components/StudentProfileForm/StudentProfileForm.tsx`

**Requirements satisfied:** FR-02, AC-04, AC-05, design §3.1

**Dependencies:** T-04, T-17

---

### T-19 — Connect profile form to Home page

**What to implement:**
- Wire `StudentProfileForm` into `Home.tsx`:
  - On `onProfileChange`, update `profile` state in Home
  - On page load, read profile from localStorage and set initial state
  - Profile is passed to `analyzeAnnouncement()` on submission
- Verify localStorage round-trip: fill in profile, refresh page, values reload.

**Files involved:**
`frontend/src/pages/Home/Home.tsx`

**Requirements satisfied:** FR-02, AC-04, design §15.2

**Dependencies:** T-18

---

## Phase 9 — Announcement Analysis UI

### T-20 — Build the AnnouncementInput component

**What to implement:**
- Create `frontend/src/components/AnnouncementInput/AnnouncementInput.tsx`:
  - `<textarea>` with placeholder "Paste your college announcement here..."
  - Live character count display: "X / 10,000 characters"
  - Validation: min 50 chars, max 10,000 chars
  - Shows inline error message if under 50 chars on submit attempt
  - Trims whitespace before passing value up
  - Props: `value`, `onChange`, `disabled` (disabled during loading)

**Files involved:**
`frontend/src/components/AnnouncementInput/AnnouncementInput.tsx`

**Requirements satisfied:** FR-01, AC-01, design §3.1

**Dependencies:** T-04, T-17

---

### T-21 — Build the submit controller in Home

**What to implement:**
- In `Home.tsx`, implement the submit handler:
  - Validate: profile complete, announcement ≥ 50 chars
  - If invalid: show validation errors, do NOT call API
  - If valid:
    - Set `isLoading = true`, `error = null`, `result = null`
    - Disable submit button
    - Call `analyzeAnnouncement(announcementText.trim(), profile)`
    - On success: set `result`, set `checklist = result.checklist`, `isLoading = false`
    - On error: set `error` message, `isLoading = false`
  - Re-enable submit button after promise settles

**Files involved:**
`frontend/src/pages/Home/Home.tsx`

**Requirements satisfied:** FR-03, AC-07, AC-10, EC-09, design §3.1, §15

**Dependencies:** T-16, T-19, T-20

---

## Phase 10 — Results, Decision Summary and Checklist

### T-22 — Build the PersonalizedDecisionSummary component

**What to implement:**
- Create `frontend/src/components/PersonalizedDecisionSummary/PersonalizedDecisionSummary.tsx`:
  - Props: `relevance: RelevanceResult`
  - Displays the status badge:
    - RELEVANT → green badge, label "RELEVANT"
    - NOT_RELEVANT → neutral/grey badge, label "NOT RELEVANT"
    - UNCERTAIN → amber badge, label "NEEDS REVIEW" (NOT "UNCERTAIN")
  - Displays `relevance_reason` below the badge
  - For NOT_RELEVANT: shows "This announcement does not apply to your profile.
    No action is required from you."
  - For UNCERTAIN: shows "We could not determine whether this applies to you.
    Please verify with your department or faculty office before taking any action."
  - This component is placed at the TOP of the results section

**Files involved:**
`frontend/src/components/PersonalizedDecisionSummary/PersonalizedDecisionSummary.tsx`

**Requirements satisfied:** FR-15, AC-15, AC-16, AC-17, AC-18, design §3.1

**Dependencies:** T-04

---

### T-23 — Build the WhatChangedSection and DeadlineSection components

**What to implement:**
- Create `frontend/src/components/WhatChangedSection/WhatChangedSection.tsx`:
  - Props: `summary: string`, `whatChanged: string`
  - Displays both fields clearly labelled

- Create `frontend/src/components/DeadlineSection/DeadlineSection.tsx`:
  - Props: `deadlines: DeadlineItem[]`, `showAsObligations: boolean`
  - If `showAsObligations` is false (UNCERTAIN), display with a disclaimer
    "These deadlines may or may not apply to you. Verify before acting."
  - Always displays `original_date_text` (never the raw YYYY-MM-DD)
  - If `deadlines` is empty, renders nothing

**Files involved:**
`frontend/src/components/WhatChangedSection/WhatChangedSection.tsx`,
`frontend/src/components/DeadlineSection/DeadlineSection.tsx`

**Requirements satisfied:** FR-08, FR-15, design §3.1

**Dependencies:** T-04

---

### T-24 — Build the PriorityDisplay component

**What to implement:**
- Create `frontend/src/components/PriorityDisplay/PriorityDisplay.tsx`:
  - Props: `priority: Priority`, `priorityReason: string`
  - Colour-coded badge: High=red, Medium=amber, Low=green
  - Displays `priorityReason` below the badge
  - Only shown when `relevance_status` is RELEVANT

**Files involved:**
`frontend/src/components/PriorityDisplay/PriorityDisplay.tsx`

**Requirements satisfied:** FR-11, FR-15, design §3.1

**Dependencies:** T-04

---

### T-25 — Build the Checklist component

**What to implement:**
- Create `frontend/src/components/Checklist/Checklist.tsx`:
  - Props: `items: ChecklistItem[]`, `onToggle: (id: string) => void`
  - If `items` is empty: displays "No specific actions required."
  - For each item: renders a checkbox + description + `deadline_text` (if present)
  - Clicking checkbox calls `onToggle(item.id)`
  - Completed items show strikethrough styling
  - Only rendered by parent when `relevance_status === "RELEVANT"`

**Files involved:**
`frontend/src/components/Checklist/Checklist.tsx`

**Requirements satisfied:** FR-09, AC-06, design §3.1, §10.2

**Dependencies:** T-04

---

### T-26 — Assemble the full results view in Home

**What to implement:**
- In `Home.tsx`, when `result` is non-null, render in this order:
  1. `<PersonalizedDecisionSummary relevance={result.relevance} />`
  2. `<WhatChangedSection summary={result.analysis.summary} whatChanged={result.analysis.what_changed} />`
  3. `<DeadlineSection deadlines={result.analysis.deadlines} showAsObligations={result.relevance.relevance_status === "RELEVANT"} />`
  4. If RELEVANT: `<PriorityDisplay priority={result.analysis.priority} priorityReason={result.analysis.priority_reason} />`
  5. If RELEVANT: `<Checklist items={checklist} onToggle={toggleItem} />`
- Implement `toggleItem` in Home per design §10.2
- Results section MUST NOT be visible while `isLoading` is true

**Files involved:**
`frontend/src/pages/Home/Home.tsx`

**Requirements satisfied:** FR-09, FR-15, AC-01, AC-02, AC-06, design §15

**Dependencies:** T-22, T-23, T-24, T-25

---

## Phase 11 — Error, Loading, and Timeout Handling

### T-27 — Build LoadingState and ErrorState components

**What to implement:**
- Create `frontend/src/components/LoadingState/LoadingState.tsx`:
  - A centered spinner with the message "Analysing your announcement..."
  - No additional content

- Create `frontend/src/components/ErrorState/ErrorState.tsx`:
  - Props: `message: string`, `onRetry: () => void`
  - Displays the user-friendly error message (never a raw error object)
  - Shows a "Try Again" button that calls `onRetry`
  - Does NOT show stack traces, HTTP status codes, or `code` fields to the user

**Files involved:**
`frontend/src/components/LoadingState/LoadingState.tsx`,
`frontend/src/components/ErrorState/ErrorState.tsx`

**Requirements satisfied:** FR-03 (loading state), FR-03 (timeout), FR-13
(error handling), AC-07, AC-08, design §3.1

**Dependencies:** T-04

---

### T-28 — Wire LoadingState and ErrorState into Home

**What to implement:**
- In `Home.tsx`, conditionally render:
  - When `isLoading`: show `<LoadingState />`, hide results and form submit area
  - When `error` is non-null: show `<ErrorState message={error} onRetry={clearError} />`
  - `clearError` resets `error` to null and re-enables the form
- Verify: timeout after 30 seconds shows the timeout error message (test by
  temporarily setting timeout to 2s in `api.ts`).

**Files involved:**
`frontend/src/pages/Home/Home.tsx`

**Requirements satisfied:** FR-03, AC-07, AC-08, EC-09, design §13

**Dependencies:** T-27, T-21

---

## Phase 12 — Testing and Integration

### T-29 — Write backend unit tests for schemas

**What to implement:**
- Create `backend/tests/test_schemas.py` covering:
  - `AnalyzeRequest` validation:
    - Text < 50 chars → `ValidationError`
    - Text > 10,000 chars → `ValidationError`
    - Year = 0 or 5 → `ValidationError`
    - Missing profile field → `ValidationError`
    - Valid input → passes
  - `AIExtractionResult` cross-field validation:
    - `[]` dimension not in `ambiguous_dimensions` → `ValidationError`
    - Dimension in `ambiguous_dimensions` missing from `ambiguous_raw_text` → `ValidationError`
    - `ambiguous_dimensions` absent → defaults to `[]`
    - `years: ["2"]` → coerced to `[2]`
    - `years: [5]` → `ValidationError`
    - `["all", "CSE"]` in any dimension → `ValidationError`
    - `priority: "Critical"` → `ValidationError`
  - Run with `pytest backend/tests/`

**Files involved:**
`backend/tests/__init__.py`, `backend/tests/test_schemas.py`

**Requirements satisfied:** FR-01, FR-02, FR-05, FR-12, design §17.1

**Dependencies:** T-06, T-07

---

### T-30 — Write backend unit tests for relevance service

**What to implement:**
- Create `backend/tests/test_relevance_service.py` covering all cases from
  design §17.1:
  - All `["all"]` → RELEVANT for any profile
  - Exact match all dimensions → RELEVANT
  - One dimension mismatch → NOT_RELEVANT
  - One dimension ambiguous (in `ambiguous_dimensions`), rest pass → UNCERTAIN
  - One dimension fails, another ambiguous → NOT_RELEVANT (exclusion wins)
  - Multiple ambiguous → UNCERTAIN
  - Case-insensitive match ("cse" matches ["CSE"]) → RELEVANT
  - Year integer match (profile.year=2 matches [2]) → RELEVANT
  - Verify `relevance_reason` content references correct dimension names

**Files involved:**
`backend/tests/test_relevance_service.py`

**Requirements satisfied:** FR-06, FR-07, AC-01, AC-02, AC-12, AC-13, AC-14,
EC-15, design §17.1

**Dependencies:** T-11

---

### T-31 — Write backend unit tests for checklist service

**What to implement:**
- Create `backend/tests/test_checklist_service.py` covering:
  - NOT_RELEVANT → `[]`
  - UNCERTAIN → `[]`
  - RELEVANT + 2 actions → list length 2
  - RELEVANT + 0 actions → `[]`
  - `deadline_text` copied from `original_by_text`
  - `deadline` copied from `by` (YYYY-MM-DD or None)
  - `completed` always False on creation

**Files involved:**
`backend/tests/test_checklist_service.py`

**Requirements satisfied:** FR-09, EC-02, EC-08, design §17.1

**Dependencies:** T-12

---

### T-32 — Write backend integration test for the analyze endpoint

**What to implement:**
- Create `backend/tests/test_analyze_endpoint.py` using FastAPI's `TestClient`:
  - Valid request with mocked `ai_service.analyze` → HTTP 200, correct response shape
  - `ai_service` raises `AIProviderError` → HTTP 500 + `"code": "AI_PROVIDER_ERROR"`
  - `ai_service` raises `AIParseError` → HTTP 500 + `"code": "AI_PARSE_ERROR"`
  - Announcement too short → HTTP 422
  - Missing profile field → HTTP 422
  - Verify response has NO `announcement_id` field
  - Verify CORS header present for configured origin

**Files involved:**
`backend/tests/test_analyze_endpoint.py`

**Requirements satisfied:** FR-13, AC-08, AC-09, AC-19, design §17.2

**Dependencies:** T-14, T-29

---

### T-33 — Full frontend-to-backend integration test

**What to implement:**
- Run both backend (`uvicorn`) and frontend (`npm run dev`) simultaneously.
- Manually test the three golden-path scenarios:

  **Scenario A (RELEVANT):**
  - Profile: Dept=CSE, Spec=AI, Year=2, Section=A
  - Announcement: "All second-year CSE AI students must register for the AI
    certification examination before September 30."
  - Expected: RELEVANT banner, checklist item, deadline with
    `original_date_text="September 30"`, no invented year

  **Scenario B (NOT_RELEVANT):**
  - Same profile
  - Announcement: "All first-year ECE students must submit their laboratory records."
  - Expected: NOT RELEVANT banner, no checklist

  **Scenario C (UNCERTAIN):**
  - Same profile
  - Announcement: "All eligible students must register for the placement drive
    by October 15."
  - Expected: NEEDS REVIEW banner, no checklist, advisory message

- Also verify: submit button disabled during request, loading spinner visible,
  Try Again button appears on network error.

**Files involved:** none (manual verification)

**Requirements satisfied:** AC-01, AC-02, AC-12, AC-15, AC-16, AC-17

**Dependencies:** T-26, T-28

---

## Phase 13 — Final UI Polish and Demo Preparation

### T-34 — Style the decision summary panel

**What to implement:**
- Apply styles to `PersonalizedDecisionSummary` so the three states are visually
  distinct at a glance:
  - RELEVANT: green left-border or background tint, green badge
  - NOT RELEVANT: grey/neutral treatment, grey badge
  - NEEDS REVIEW: amber left-border or background tint, amber badge
- The panel MUST appear at the top of the results section, clearly above all
  other result content.
- Use CSS Modules or Tailwind (whichever was chosen during T-03 setup).

**Files involved:**
`frontend/src/components/PersonalizedDecisionSummary/PersonalizedDecisionSummary.tsx`
and its CSS/style file

**Requirements satisfied:** FR-15, AC-18, design §3.1

**Dependencies:** T-22

---

### T-35 — Style the checklist and priority components

**What to implement:**
- Style `Checklist.tsx`:
  - Completed items: strikethrough text, dimmed/greyed appearance
  - Uncompleted items: normal text, visible checkbox
  - Deadline text displayed in a smaller, secondary style
- Style `PriorityDisplay.tsx`:
  - High: red badge
  - Medium: amber badge
  - Low: green badge
- Ensure all interactive elements (checkboxes, retry button, submit) have ARIA
  labels for accessibility.

**Files involved:**
`frontend/src/components/Checklist/Checklist.tsx`,
`frontend/src/components/PriorityDisplay/PriorityDisplay.tsx`
and their CSS/style files

**Requirements satisfied:** FR-09, FR-11, FR-15, NFR-02 (accessibility),
design §3.1

**Dependencies:** T-24, T-25

---

### T-36 — Create a README with setup and run instructions

**What to implement:**
- Create `README.md` at the project root with:
  - Project description (one paragraph)
  - Prerequisites: Node.js 18+, Python 3.11+, a Gemini API key
  - Backend setup:
    ```
    cd backend
    pip install -r requirements.txt
    cp .env.example .env  # add your GEMINI_API_KEY and GEMINI_MODEL
    uvicorn main:app --reload
    ```
  - Frontend setup:
    ```
    cd frontend
    npm install
    # create .env with VITE_API_BASE_URL=http://localhost:8000
    npm run dev
    ```
  - Note: `GEMINI_MODEL` must be set in `backend/.env` — not hardcoded

**Files involved:**
`README.md`

**Requirements satisfied:** design §16, DECISIONS.md D-002 (model via env var)

**Dependencies:** T-15, T-33

---

### T-37 — Demo preparation checklist

**What to implement:**
- Prepare three demo announcements to paste during the demo:
  1. A RELEVANT announcement (specific year, dept, specialization)
  2. A NOT_RELEVANT announcement (different year or department)
  3. An UNCERTAIN announcement (vague group like "eligible students")
- Save these as a file `demo/sample_announcements.md` at the project root.
- Do a final run-through of all three scenarios and confirm the UI output
  matches the expected results from AC-01, AC-02, AC-12.
- Verify `.env` files are NOT committed to git.
- Verify no `announcement_id` in any response.

**Files involved:**
`demo/sample_announcements.md`

**Requirements satisfied:** AC-01, AC-02, AC-12, AC-19, design §17.4

**Dependencies:** T-33, T-36

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | T-01 – T-04 | Project setup (backend + frontend scaffolding, types) |
| 2 | T-05 – T-08 | Backend foundation (exceptions, request/response schemas) |
| 3 | T-09 – T-10 | AI extraction (prompt builder, AI service) |
| 4 | T-11 | Relevance engine |
| 5 | T-12 – T-13 | Checklist + orchestration |
| 6 | T-14 – T-15 | API route + smoke test |
| 7 | T-16 – T-17 | Frontend setup (Axios service, App layout) |
| 8 | T-18 – T-19 | Student profile + localStorage |
| 9 | T-20 – T-21 | Announcement input + submit controller |
| 10 | T-22 – T-26 | Results display (decision summary, checklist, deadlines, priority) |
| 11 | T-27 – T-28 | Loading + error + timeout states |
| 12 | T-29 – T-33 | Backend unit tests + integration tests |
| 13 | T-34 – T-37 | UI polish, README, demo prep |

**Total tasks: 37**

---

## Implementation boundaries (what these tasks do NOT include)

- No authentication or user accounts
- No server-side student profile storage
- No announcement history or database
- No notifications or reminders
- No calendar integration
- No file upload or OCR
- No Redis, Celery, or task queues
- No PostgreSQL (no database at all in MVP)
- No microservices
- No paid infrastructure beyond Gemini free tier
- No multi-device profile sync

---

*Implementation tasks are complete. Begin with T-01 and proceed in phase order.*
