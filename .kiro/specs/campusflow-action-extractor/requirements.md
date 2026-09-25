# Spec: campusflow-action-extractor — Requirements

**Version:** 1.0 (Final)
**Status:** Approved
**Spec type:** MVP Feature Spec

---

## 1. Purpose

This spec defines the complete requirements for the CampusFlow AI MVP — a system
that transforms college announcements into personalized, actionable checklists
based on a student's profile.

The core differentiating feature is **personalized relevance detection**: the
system must explicitly determine whether a given announcement actually requires
something from a specific student, and explain why or why not.

This is not a generic summarizer. The product answers the question:
*"Does this notice actually require something from ME?"*

---

## 2. Background

### 2.1 Problem Statement

College announcements are long, dense, and written for large student populations.
Students must manually read through entire notices to determine whether they are
even affected — then identify what action they need to take, and by when. This
causes missed deadlines, missed registrations, and general confusion.

### 2.2 Illustrative Examples

**Example A — RELEVANT:**
- Student: Dept=CSE, Spec=AI, Year=2, Section=A
- Notice: "All second-year CSE AI students must register for the AI certification
  examination before September 30."
- `relevance_status: "RELEVANT"`
- `relevance_reason`: "This applies to you because you are a 2nd-year CSE AI student."
- Checklist: one item — "Register for the AI certification examination"
- Deadline: September 30 (date: null, original_date_text: "September 30")
- Priority: determined from urgency language "must register"

**Example B — NOT_RELEVANT:**
- Student: Dept=CSE, Spec=AI, Year=2, Section=A
- Notice: "All first-year ECE students must submit their laboratory records."
- `relevance_status: "NOT_RELEVANT"`
- `relevance_reason`: "This notice applies to 1st-year ECE students. Your profile
  is 2nd-year CSE AI, Section A."
- Checklist: empty

**Example C — UNCERTAIN:**
- Student: Dept=CSE, Spec=AI, Year=2, Section=A
- Notice: "All eligible students must register for the placement drive by October 15."
- `relevance_status: "UNCERTAIN"`
- `relevance_reason`: "This announcement refers to 'eligible students' but does not
  define eligibility criteria. Your eligibility cannot be determined automatically.
  Please check with your department or faculty office."
- Checklist: empty

---

## 3. Scope

### 3.1 In Scope (MVP)

- Announcement text input (paste)
- Student profile creation and persistence (localStorage)
- AI-powered structured extraction from announcement text
- What-changed extraction
- Affected student group extraction
- Personalized relevance detection with reasoning (RELEVANT / NOT_RELEVANT / UNCERTAIN)
- Deadline extraction with original wording preservation
- Required action extraction
- Priority classification
- Personalized checklist generation
- Checklist item completion tracking — mark as done, frontend state only,
  no server-side persistence
- Loading state during AI processing
- Error messaging when analysis fails

### 3.2 Out of Scope (Post-MVP)

- User authentication and accounts
- Notification and reminder system
- Google Calendar or iCal integration
- Announcement history and dashboard
- File/document upload (PDF, image, OCR)
- Voice input
- Analytics and reporting
- Admin panel
- College-wide announcement ingestion pipeline
- Multi-device profile sync
- Persistent server-side announcement storage
- Redis, microservices, or unnecessary paid infrastructure

---

## 4. Functional Requirements

### FR-01 — Announcement Input

- The system MUST allow a student to paste plain text into a text area.
- The input field MUST accept between 50 and 10,000 characters.
- Submission MUST be blocked if the input is empty or fewer than 50 characters.
- A clear validation message MUST be shown when input is invalid.
- Leading and trailing whitespace MUST be trimmed before the text is sent to the backend.

### FR-02 — Student Profile

- The system MUST allow a student to create and save a profile containing:
  Name, Department, Specialization, Year (1–4), Section.
- All five fields are required. Submission MUST be blocked if any field is empty.
- The profile MUST be persisted in the browser's localStorage under the key
  `campusflow_profile`.
- The profile MUST be automatically loaded on page load if it already exists
  in localStorage.
- The student MUST be able to edit and update their profile at any time.
- The profile MUST be sent to the backend as part of every analysis request.
- The profile MUST NOT be stored server-side. It is used only for the duration
  of a single analysis request and then discarded.

### FR-03 — AI Analysis Trigger

- The system MUST send the announcement text and student profile to
  `POST /api/v1/analyze` on form submission.
- A loading indicator MUST be displayed while the backend is processing.
- The submit button MUST be disabled while a request is in flight to prevent
  duplicate submissions.
- The backend MUST validate that `announcement_text` is a non-empty string and
  that the student profile contains all five required fields before calling the
  AI service. Validation failures return HTTP 422 before the AI is ever called.

**Security (integrated into FR-03):**
- The `GEMINI_API_KEY` MUST be stored only in `backend/.env` and MUST never be
  sent to or exposed in the frontend.
- The frontend MUST communicate only with the backend API. It MUST NOT call the
  Gemini API or any other AI provider directly.
- All backend request bodies MUST be validated via Pydantic schemas before
  processing begins.
- The student profile submitted in the request body MUST NOT be persisted
  server-side. It is used only for the duration of the current analysis request.
- `.env` files MUST be listed in `.gitignore` and MUST never be committed to
  version control.

**Performance (integrated into FR-03):**
- The `/api/v1/analyze` endpoint MUST target a response time of 5–10 seconds
  under normal conditions.
- The absolute maximum acceptable response time is 15 seconds.
- The frontend MUST display a loading indicator from the moment the form is
  submitted until a response is received or an error occurs.
- The frontend MUST disable the submit button for the entire duration of an
  in-flight request to prevent duplicate submissions.
- A request that has not received a response within 30 seconds MUST be treated
  as timed out by the frontend. The frontend MUST display a timeout error message
  and re-enable the submit button.

### FR-04 — Structured AI Extraction

The AI service MUST return a single structured JSON response for every analysis
request. This response is the complete output of the AI extraction pass.
The following fields MUST be present:

| Field | Description | Authoritative requirement |
|-------|-------------|--------------------------|
| `summary` | One-sentence plain-English summary | FR-04 |
| `what_changed` | Core change or update being announced | FR-04 |
| `affected_groups` | Who the announcement targets | FR-05 |
| `ambiguous_dimensions` | Dimensions the AI could not determine reliably | FR-05 |
| `ambiguous_raw_text` | Original wording for each ambiguous dimension | FR-05 |
| `deadlines` | All dates and deadlines extracted | FR-08 |
| `required_actions` | All required student actions extracted | FR-10 |
| `priority` | Urgency classification: High, Medium, or Low | FR-11 |
| `priority_reason` | Explanation of the priority assignment | FR-11 |

- `summary` MUST be a non-null, non-empty string.
- `what_changed` MUST be a non-null, non-empty string. If no specific change can
  be determined, it MUST be a best-effort description, not an empty string.
- Relevance determination (`relevance_status`, `relevance_reason`) is NOT part of
  the AI output. It is computed by the backend service after extraction. See FR-06
  and FR-07.
- Detailed semantic rules for each field are in the authoritative FRs listed above.
  FR-04 does not redefine those rules.

### FR-05 — Affected Student Extraction

> **This section is the single authoritative definition of the `affected_groups`
> schema, `ambiguous_dimensions`, and `ambiguous_raw_text`. All other sections
> that reference these fields defer to this section.**

#### Canonical `affected_groups` schema

```json
{
  "affected_groups": {
    "departments":     ["CSE", "ECE"]  |  ["all"]  |  [],
    "specializations": ["AI", "DS"]    |  ["all"]  |  [],
    "years":           [1, 2]          |  ["all"]  |  [],
    "sections":        ["A", "B"]      |  ["all"]  |  []
  },
  "ambiguous_dimensions": ["years"],
  "ambiguous_raw_text": {
    "years": "senior students"
  }
}
```

**Canonical meaning of each dimension value:**

| Value | Meaning |
|-------|---------|
| `["all"]` | The announcement explicitly places NO restriction on this dimension. Every student passes. |
| Specific list (e.g., `["CSE", "ECE"]`) | The announcement explicitly targets only these values. |
| `[]` | This dimension is ambiguous/indeterminate. MUST also appear in `ambiguous_dimensions`. |

**Rules:**

- Each of the four dimensions (`departments`, `specializations`, `years`,
  `sections`) MUST be present in the AI response as a non-null list.
- `["all"]` MUST only be used when the announcement genuinely and explicitly
  places no restriction on that dimension. It is a deliberate positive signal —
  not a fallback for missing or uncertain information.
- `[]` MUST only be used when the dimension also appears in `ambiguous_dimensions`.
  A non-ambiguous dimension MUST never be `[]`.
- `["all"]` and `[]` are mutually exclusive. A dimension cannot be both.
- The AI MUST NOT use `["all"]` for an ambiguous dimension. If the announcement
  says "senior students" without defining the year, `years` MUST be `[]` (not
  `["all"]`), added to `ambiguous_dimensions`, and recorded in `ambiguous_raw_text`.
- The AI MUST NOT invent specific values for an ambiguous dimension (e.g., guessing
  `[3, 4]` for "senior students").
- `years` values in specific lists are integers (1, 2, 3, 4), not strings.
- `ambiguous_dimensions` MUST be present in every AI response. It is an empty
  list `[]` when no dimensions are ambiguous.
- `ambiguous_raw_text` MUST be present in every AI response. It is an empty
  object `{}` when no dimensions are ambiguous.
- A dimension name in `ambiguous_dimensions` MUST have a corresponding entry
  in `ambiguous_raw_text`.
- The backend MUST NOT default a missing `affected_groups` dimension to `["all"]`
  or `[]`. A missing dimension is always `AI_PARSE_ERROR`.

**Ambiguous language examples:**

The AI MUST flag a dimension as ambiguous (`[]` + entry in `ambiguous_dimensions`)
when the announcement uses language that cannot be reliably mapped to profile
fields without guessing. Examples:
- "senior students" — does not map reliably to a year unless defined in the announcement
- "junior students" — same
- "engineering students" — could mean a department, faculty, or stream
- "eligible students" — eligibility criteria not stated
- "selected students" — selection criteria not stated

If the same announcement defines the ambiguous term elsewhere (e.g., "senior
students, i.e., Year 3 and Year 4"), the AI MAY resolve it using that explicit
definition and set the dimension to specific values (not `[]`).

### FR-06 — Personalized Relevance Detection

- The backend MUST compare the extracted `affected_groups` against the submitted
  student profile.
- The system MUST produce a `relevance_status` field using exactly one of:
  `"RELEVANT"`, `"NOT_RELEVANT"`, or `"UNCERTAIN"`.
- The system MUST produce a `relevance_reason` string in plain English.

**Per-dimension matching logic:**

```
for each dimension in [departments, specializations, years, sections]:
    if dimension in ambiguous_dimensions:
        → cannot evaluate; contributes to UNCERTAIN
    else if affected_groups[dimension] == ["all"]:
        → passes
    else if student.profile[dimension] in affected_groups[dimension]:
        → passes (case-insensitive for strings)
    else:
        → fails; contributes to NOT_RELEVANT
```

**Overall status — priority order:**

1. If any non-ambiguous dimension **fails** → `"NOT_RELEVANT"` (explicit exclusion
   always takes precedence, even if other dimensions are ambiguous)
2. Else if any dimension is in `ambiguous_dimensions` → `"UNCERTAIN"`
3. Else all dimensions pass → `"RELEVANT"`

### FR-07 — Relevance Explanation

- `relevance_reason` MUST be present for all three statuses.
- The explanation MUST be in plain English, addressed to the student, and MUST
  reference specific profile values and announcement content.

**Per-status guidance:**

- **RELEVANT**: State which profile attributes matched. E.g.: *"This applies to
  you because you are a 2nd-year CSE AI student in Section A."*
- **NOT_RELEVANT**: Name the failing dimension and contrast profile vs. target.
  E.g.: *"This notice is for 1st-year ECE students. Your profile is 2nd-year
  CSE AI, Section A."*
- **UNCERTAIN**: Quote the ambiguous wording from `ambiguous_raw_text`, name the
  unresolvable dimension, and advise manual verification. E.g.: *"This announcement
  refers to 'eligible students' but does not define eligibility. Please check with
  your faculty office."*

### FR-08 — Deadline Extraction

- The AI MUST extract all dates and deadlines mentioned in the announcement into
  a `deadlines` list.
- Each deadline object MUST contain:
  - `label` (string): short name for the deadline (e.g., "Registration deadline")
  - `date` (string or null): ISO 8601 `YYYY-MM-DD` **only if the year can be
    determined reliably** from the announcement text; otherwise `null`
  - `original_date_text` (string): the original date wording exactly as it
    appears in the announcement — MUST always be preserved regardless of whether
    `date` is populated
  - `description` (string): additional context about the deadline
- The AI MUST NOT invent or guess a year when none is stated. If the announcement
  says "September 30" without specifying a year, `date` MUST be `null` and
  `original_date_text` MUST be `"September 30"`.
- A year is reliably determinable only if explicitly stated in the announcement
  (e.g., "September 30, 2026").
- Relative date expressions (e.g., "tomorrow", "next Monday", "in two weeks",
  "by end of this week") MUST be treated as non-normalizable unless the required
  reference date is explicitly available and reliable from the announcement text.
  When unavailable, `date` MUST be `null` and `original_date_text` MUST preserve
  the original wording exactly.
- If no deadlines are present, `deadlines` MUST be `[]`, never `null` or omitted.

### FR-09 — Checklist Generation Rules by Status

| `relevance_status` | Checklist behaviour |
|--------------------|-------------------|
| `"RELEVANT"` | Generate checklist from applicable `required_actions` and `deadlines`. If `required_actions` is empty, `checklist: []` and frontend shows "No specific actions required." |
| `"NOT_RELEVANT"` | `checklist` MUST be `[]`. No items generated. |
| `"UNCERTAIN"` | `checklist` MUST be `[]`. Backend MUST NOT invent or assume actions based on ambiguous eligibility. |

- Each checklist item MUST contain:
  - `id` (string): unique identifier within this result
  - `description` (string): what the student needs to do
  - `deadline` (string or null): associated date in `YYYY-MM-DD` format if reliably known, otherwise `null`
  - `deadline_text` (string or null): original date wording carried from the source deadline's `original_date_text`, for display purposes
  - `completed` (boolean): default `false`
- The frontend MUST render each checklist item with a checkbox.
- The student MUST be able to toggle any item between complete and incomplete.
- Checklist completion state is managed on the frontend only. It does NOT persist
  across page reloads in the MVP.

### FR-10 — Required Action Extraction

- The AI MUST extract all required student actions into a `required_actions` list.
- Each action object MUST contain:
  - `action` (string): plain-English description of what the student must do
  - `by` (string or null): deadline date in `YYYY-MM-DD` format if the year is
    reliably known; otherwise `null`
  - `original_by_text` (string or null): original date wording for this action's
    deadline as it appears in the announcement; `null` if no deadline was mentioned
  - `details` (string or null): additional context or instructions
- The AI MUST NOT invent a year for an action deadline when none is stated. Same
  rule as FR-08.
- If no required actions are present, `required_actions` MUST be `[]`, never
  `null` or omitted.

### FR-11 — Priority Classification

- The AI MUST assign a `priority` value of exactly one of: `"High"`, `"Medium"`,
  or `"Low"`.
- The AI MUST provide a `priority_reason` string explaining the assigned priority.
- `priority_reason` MUST state whether the priority was determined from date
  proximity or from urgency language in the text.

**When a reliable normalized date is available (`date` is non-null):**
- **High**: deadline within 7 days of the analysis date.
- **Medium**: deadline within 30 days of the analysis date.
- **Low**: deadline beyond 30 days, or no deadline.

**When the normalized date is null (year cannot be reliably determined):**
- The AI MUST NOT perform date arithmetic or invent a proximity calculation.
- Priority MUST be inferred from explicit urgency language and contextual signals:
  - High signals: "immediately", "urgent", "must complete before", "last chance",
    "failure to comply will result in", "mandatory by"
  - Medium signals: "should complete", "please ensure", "required before end of",
    "recommended"
  - Low signals: "for your information", "note that", "you may", "optional"
- If no urgency signals are present and the date is `null`, default to `"Medium"`.

- The backend MUST validate that `priority` is exactly one of `"High"`, `"Medium"`,
  `"Low"`. Any other value is `AI_PARSE_ERROR`.

### FR-12 — AI Output Validation

> The following rules validate the structure and consistency of the AI response.
> FR-12 does not redefine the semantic meaning of fields — those definitions live
> in their authoritative FRs (FR-05 for `affected_groups`, FR-08 for deadlines,
> FR-10 for actions, FR-11 for priority).

- All required fields (`summary`, `what_changed`, `affected_groups`,
  `ambiguous_dimensions`, `ambiguous_raw_text`, `deadlines`, `required_actions`,
  `priority`, `priority_reason`) MUST be present and non-null. Missing required
  field → `AI_PARSE_ERROR`.
- `priority` MUST be exactly one of `"High"`, `"Medium"`, `"Low"`. Any other
  value → `AI_PARSE_ERROR`.
- `affected_groups` MUST be present with all four keys: `departments`,
  `specializations`, `years`, `sections`. Missing key → `AI_PARSE_ERROR`.
- Each dimension value MUST be one of: non-empty specific list, `["all"]`, or
  `[]` only when the dimension is also in `ambiguous_dimensions`.
- A `[]` dimension NOT in `ambiguous_dimensions` → `AI_PARSE_ERROR`.
- A dimension in `ambiguous_dimensions` with a non-empty non-`["all"]` value
  → `AI_PARSE_ERROR`.
- `["all"]` is valid only as a single-element list containing exactly the string
  `"all"`. Mixed lists like `["all", "CSE"]` → `AI_PARSE_ERROR`.
- `years` values in specific lists MUST be integers (1–4). String year values MUST
  be coerced to integers. Values outside 1–4 → `AI_PARSE_ERROR`.
- `ambiguous_dimensions` MUST be a list. If **absent** from the AI response, the
  backend MAY default it to `[]`. Unlike a missing `affected_groups` dimension —
  which has no safe default — a missing `ambiguous_dimensions` field has an
  unambiguous interpretation: no dimensions are flagged as ambiguous. Defaulting
  to `[]` is therefore safe and does not mask a real error.
- `ambiguous_raw_text` MUST be an object. If absent, default to `{}` for the same
  reason.
- Every entry in `ambiguous_dimensions` MUST have a corresponding key in
  `ambiguous_raw_text`. A listed dimension with no raw text entry → `AI_PARSE_ERROR`.
- `relevance_status` MUST be exactly one of `"RELEVANT"`, `"NOT_RELEVANT"`,
  `"UNCERTAIN"`. Any other value is an internal logic error → HTTP 500.
- All LLM responses MUST be validated against the expected Pydantic schema before
  any data is returned to the frontend. AI output MUST NOT be forwarded raw.
- The backend MUST sanitize AI inputs and outputs before writing to logs. No
  student profile data should appear in plain-text logs.
- Validation failures MUST be logged at ERROR level with enough context to
  reproduce the issue.

### FR-13 — API Contract

> API keys and secrets are never included in any request or response from this
> endpoint. See FR-03 for the full security and performance requirements governing
> this endpoint.

#### MVP endpoint

The MVP contains exactly one API endpoint:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analyze` | Submit an announcement for AI analysis and receive the personalized result |

Announcement history endpoints (`GET /api/v1/announcements`,
`GET /api/v1/announcements/{id}`) are post-MVP. They require persistent
server-side announcement storage which is explicitly out of scope per Section 3.2.

#### `POST /api/v1/analyze`

**Request body:**

```json
{
  "announcement_text": "string (50–10,000 characters, required)",
  "student_profile": {
    "name":           "string (required)",
    "department":     "string (required)",
    "specialization": "string (required)",
    "year":           "integer 1–4 (required)",
    "section":        "string (required)"
  }
}
```

**Success response — HTTP 200 OK:**

```json
{
  "analysis": {
    "summary": "string",
    "what_changed": "string",
    "affected_groups": {
      "departments":     ["CSE"] | ["all"] | [],
      "specializations": ["AI"]  | ["all"] | [],
      "years":           [2]     | ["all"] | [],
      "sections":        ["A"]   | ["all"] | []
    },
    "ambiguous_dimensions": [],
    "ambiguous_raw_text": {},
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
    "priority": "High | Medium | Low",
    "priority_reason": "string"
  },
  "relevance": {
    "relevance_status": "RELEVANT | NOT_RELEVANT | UNCERTAIN",
    "relevance_reason": "string"
  },
  "checklist": [
    {
      "id": "string",
      "description": "string",
      "deadline": "YYYY-MM-DD or null",
      "deadline_text": "string or null",
      "completed": false
    }
  ]
}
```

The `affected_groups` object, `ambiguous_dimensions`, and `ambiguous_raw_text`
shown above follow the canonical schema defined in FR-05. The response example
illustrates the shape; FR-05 is authoritative for all semantic rules.

**Validation error — HTTP 422** (FastAPI/Pydantic automatic):

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "human-readable message",
      "type": "validation error type"
    }
  ]
}
```

**Application error — HTTP 400 / 500:**

```json
{
  "detail": "Human-readable description of what went wrong",
  "code": "ERROR_CODE"
}
```

**Error codes:**

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `AI_PARSE_ERROR` | 500 | AI response could not be parsed into the expected schema |
| `AI_PROVIDER_ERROR` | 500 | The AI provider returned an error or was unreachable |
| `ANNOUNCEMENT_TOO_SHORT` | 422 | Announcement text is under 50 characters (Pydantic field constraint) |
| `ANNOUNCEMENT_TOO_LONG` | 422 | Announcement text exceeds 10,000 characters (Pydantic field constraint) |
| `PROFILE_INCOMPLETE` | 422 | One or more student profile fields are missing or invalid |

> `ANNOUNCEMENT_TOO_SHORT` and `ANNOUNCEMENT_TOO_LONG` are enforced as Pydantic
> field constraints. FastAPI returns HTTP 422 automatically for Pydantic validation
> failures, consistent with the project's dev-rules.md convention. No
> application-level HTTP 400 is used for field validation.

### FR-14 — Edge Cases

The system MUST handle the following edge cases without crashing and with a
meaningful response:

| # | Edge Case | Expected Behaviour |
|---|-----------|-------------------|
| EC-01 | Announcement has no deadlines | `deadlines: []`; checklist items omit `deadline` or set it to `null`; no error |
| EC-02 | Announcement has no required actions | `required_actions: []`; `checklist: []` even if `relevance_status: "RELEVANT"`; frontend shows "No specific actions required" |
| EC-03 | Announcement explicitly affects all students | All four dimensions are `["all"]`. `ambiguous_dimensions: []`. `relevance_status: "RELEVANT"` for any profile |
| EC-04 | Announcement targets a different dept/year/spec | Mismatched dimension contains specific values excluding the student. `relevance_status: "NOT_RELEVANT"`. `relevance_reason` names the mismatch |
| EC-05 | Vague language, unresolvable (e.g., "eligible students") | Affected dimension(s) set to `[]`. Added to `ambiguous_dimensions`. `ambiguous_raw_text` records wording. `relevance_status: "UNCERTAIN"`. `checklist: []` |
| EC-06 | AI returns malformed JSON or missing required fields | Backend catches failure. Returns HTTP 500 with `AI_PARSE_ERROR`. Raw AI output not forwarded |
| EC-07 | AI provider is unavailable or returns an HTTP error | Backend catches exception. Returns HTTP 500 with `AI_PROVIDER_ERROR`. Server does not crash |
| EC-08 | `relevance_status: "RELEVANT"` but no actions extracted | `checklist: []`. Frontend shows "No specific actions required" |
| EC-09 | Student submits while first request is in flight | Submit button is disabled. Second click has no effect. No duplicate API call |
| EC-10 | Input boundary and validation cases (10,000-char limit; year outside 1–4; invalid priority value) | Validated by FR-01/FR-02 (input/profile), FR-03 (Pydantic), and FR-12 (AI output validation) respectively. Backend returns HTTP 422 or HTTP 500 with appropriate error code per FR-13 |
| EC-11 | Resolvable colloquial term (e.g., "senior students, i.e., Year 3 and 4") | AI resolves using explicit in-announcement definition. Dimension NOT in `ambiguous_dimensions`. Normal relevance evaluation proceeds |
| EC-12 | Multiple dimensions ambiguous simultaneously | All listed in `ambiguous_dimensions`, all mapped in `ambiguous_raw_text`. `relevance_status: "UNCERTAIN"`. `relevance_reason` addresses each |
| EC-13 | AI response missing one or more `affected_groups` keys | `AI_PARSE_ERROR`. Backend does not default missing key to `["all"]` or `[]` |
| EC-14 | AI returns `[]` for a dimension NOT in `ambiguous_dimensions` | Schema contradiction. `AI_PARSE_ERROR` |
| EC-15 | One dimension ambiguous, another explicitly excludes student | Explicit exclusion takes precedence. `relevance_status: "NOT_RELEVANT"` |

### FR-15 — Personalized Decision Summary

- The frontend MUST display a **personalized decision summary panel** as the
  primary output of every analysis.
- The panel MUST appear at the **top of the results section**, above all other
  result content. Scroll behaviour and fixed/sticky positioning are implementation
  details left to the design document.
- The panel MUST display the `relevance_status` using the following mapping:

| API `relevance_status` | UI display label |
|------------------------|-----------------|
| `"RELEVANT"` | **RELEVANT** |
| `"NOT_RELEVANT"` | **NOT RELEVANT** |
| `"UNCERTAIN"` | **NEEDS REVIEW** |

- `"NEEDS REVIEW"` is a frontend display-only label. The API continues to use
  `"UNCERTAIN"`. No fourth status is introduced.
- The panel MUST display a concise relevance explanation from `relevance_reason`.
- When the student's profile attributes are the deciding factor, the explanation
  MUST name them explicitly. Examples:
  - RELEVANT: *"Relevant because you are a 2nd-year CSE AI student."*
  - NOT RELEVANT: *"Not relevant because this notice applies to 1st-year ECE students."*
  - NEEDS REVIEW: *"Needs review because the announcement refers to 'senior students'
    without defining the year."*
- The three states MUST be visually distinct (e.g., green / neutral / amber).

**Per-status content rules:**

**RELEVANT:**
- Display RELEVANT label and `relevance_reason`.
- Display the personalized checklist if `checklist` is non-empty.
- Display all extracted deadlines.
- Display priority badge and `priority_reason`.
- If `checklist` is empty, display: *"No specific actions required."*

**NOT RELEVANT:**
- Display NOT RELEVANT label and `relevance_reason`.
- Display: *"This announcement does not apply to your profile. No action is
  required from you."*
- MUST NOT display a checklist.
- MAY display the raw extraction summary (collapsed by default).

**UNCERTAIN (displayed as NEEDS REVIEW):**
- Display NEEDS REVIEW label and `relevance_reason`.
- Display: *"We could not determine whether this applies to you. Please verify
  with your department or faculty office before taking any action."*
- MUST NOT display a checklist.
- MUST NOT present any inferred actions as required steps.
- MUST NOT present unverified deadlines as student obligations.
- MAY display the ambiguous wording from `ambiguous_raw_text` to help the student
  understand what is unclear.

---

## 5. Acceptance Criteria

All criteria use Given / When / Then format. All must pass for the MVP to be
considered complete.

### AC-01 — RELEVANT: undated deadline

**Given** a student: Dept=CSE, Spec=AI, Year=2, Section=A
**And** the announcement: *"All second-year CSE AI students must register for the
AI certification examination before September 30."*

**When** the student submits the announcement

**Then:**
- `relevance_status` is `"RELEVANT"`
- `relevance_reason` references the student's department, specialization, and year
- The checklist contains at least one item mentioning "register" and "AI certification"
- At least one deadline is present with `date: null` and
  `original_date_text: "September 30"` (no year is stated; no year is invented)
- `priority` is determined from urgency language (e.g., "must register"); the test
  MUST NOT assert a specific priority value without documenting the urgency signal
  identified
- `priority_reason` states that urgency language — not date proximity — was used
- The frontend displays the RELEVANT banner, the checklist, and the deadline text
- The submit button was disabled during processing and re-enabled after

### AC-02 — NOT_RELEVANT announcement

**Given** the same student: Dept=CSE, Spec=AI, Year=2, Section=A
**And** the announcement: *"All first-year ECE students must submit their
laboratory records by October 10."*

**When** the student submits the announcement

**Then:**
- `relevance_status` is `"NOT_RELEVANT"`
- `relevance_reason` explains the mismatch (year=1 vs student year=2 and/or
  dept=ECE vs CSE)
- `checklist` is `[]`
- The frontend displays the NOT RELEVANT banner with the reason
- No checklist is rendered

### AC-03 — Universal announcement with undated deadline

**Given** a student with any profile
**And** the announcement: *"The college will be closed on October 2nd for a
public holiday."*

**When** the student submits the announcement

**Then:**
- All four `affected_groups` dimensions are `["all"]`
- `ambiguous_dimensions` is `[]`
- `relevance_status` is `"RELEVANT"`
- `required_actions` is `[]`
- `checklist` is `[]`
- `deadlines` contains exactly one item with `date: null` and
  `original_date_text: "October 2nd"` (no year is invented)
- The frontend shows RELEVANT, the summary, the deadline text "October 2nd",
  and "No specific actions required"

### AC-04 — Profile persistence

**Given** a student has filled in and saved their profile

**When** the page is refreshed

**Then:**
- All five profile fields are pre-populated with the saved values
- No re-entry is required before submitting an announcement

### AC-05 — Profile required before analysis

**Given** a student has not completed their profile (one or more fields empty)

**When** the student attempts to submit an announcement

**Then:**
- Submission is blocked at the frontend
- A validation message identifies the missing field(s)
- No network request is made to the backend

### AC-05b — Structured extraction shape

**Given** any completed analysis

**Then:**
- The response contains all required fields: `summary`, `what_changed`,
  `affected_groups`, `ambiguous_dimensions`, `ambiguous_raw_text`, `deadlines`,
  `required_actions`, `priority`, `priority_reason`
- `affected_groups` contains exactly four keys: `departments`, `specializations`,
  `years`, `sections`
- Each dimension value is one of: non-empty specific list, `["all"]`, or `[]`
- A dimension with value `[]` also appears in `ambiguous_dimensions`
- No non-ambiguous dimension has value `[]`
- `ambiguous_dimensions` is present (may be `[]`)
- `ambiguous_raw_text` is present (may be `{}`)
- `years` values in specific lists are integers
- `deadlines` and `required_actions` are always arrays, never null
- `priority` is one of `"High"`, `"Medium"`, `"Low"`

### AC-06 — Checklist interaction

**Given** a completed analysis with `relevance_status: "RELEVANT"` and at least
one checklist item

**When** the student clicks a checklist item's checkbox

**Then:**
- The item is visually marked as complete (e.g., strikethrough, checked state)
- Clicking again unchecks it
- Other checklist items are unaffected
- Items generated per FR-09 are displayed correctly

### AC-07 — Loading state

**Given** the student has submitted a valid announcement

**When** the request is in flight

**Then:**
- A loading spinner is visible
- The submit button is disabled
- The results section is not visible

### AC-08 — AI provider failure

**Given** the backend cannot reach the Gemini API

**When** the student submits an announcement

**Then:**
- The backend returns HTTP 500 with code `AI_PROVIDER_ERROR`
- The frontend displays a user-friendly error message
- No stack trace is visible to the user
- A retry option is available
- Error handling per FR-12 is applied

### AC-09 — Malformed AI response

**Given** the AI returns a response that does not match the expected schema

**When** the backend attempts to parse the response

**Then:**
- The backend returns HTTP 500 with code `AI_PARSE_ERROR` per FR-12
- Raw AI output is not sent to the frontend
- The frontend displays a user-friendly error message with a retry option

### AC-10 — Duplicate submission prevention

**Given** a student has submitted an announcement and the request is in flight

**When** the student clicks the submit button again

**Then:**
- The button is disabled and the second click has no effect (per FR-03)
- Only one request is sent to the backend

### AC-11 — Ambiguous date: null path

**Given** an announcement containing: *"Register before September 30"* (no year)

**When** the AI extracts the deadlines

**Then:**
- The deadline object has `date: null`
- The deadline object has `original_date_text: "September 30"`
- The backend does not reject this — it is valid
- The frontend displays "September 30" to the student

### AC-11b — Full date: normalized path

**Given** the announcement: *"All second-year CSE AI students must register for
the AI certification examination before September 30, 2026."*
**And** a student: Dept=CSE, Spec=AI, Year=2, Section=A
**And** assumed analysis date: **September 24, 2026** (6 days before deadline —
within the 7-day High threshold)

**When** the student submits the announcement

**Then:**
- `relevance_status` is `"RELEVANT"`
- At least one deadline has `date: "2026-09-30"`
- That deadline has `original_date_text: "September 30, 2026"`
- The checklist item has `deadline: "2026-09-30"` and
  `deadline_text: "September 30, 2026"`
- `priority` is `"High"` (analysis date is within 7 days of the deadline)
- `priority_reason` states that the deadline is within 7 days of the analysis date
- If this test is run on a date more than 7 days before September 30, 2026,
  the expected priority is `"Medium"` and the test assertion MUST be updated.
  The assumed analysis date MUST always be documented.

### AC-12 — UNCERTAIN: ambiguous affected groups

**Given** the announcement: *"All eligible students must register for the
placement drive by October 15."*
**And** a student with any profile

**When** the student submits the announcement

**Then:**
- At least one dimension in `affected_groups` is `[]`
  (e.g., `"departments": []`)
- That dimension appears in `ambiguous_dimensions`
  (e.g., `["departments"]`)
- `ambiguous_raw_text` contains the entry
  (e.g., `{ "departments": "eligible students" }`)
- `["all"]` is NOT used for the ambiguous dimension
- `relevance_status` is `"UNCERTAIN"`
- `checklist` is `[]`
- `relevance_reason` quotes "eligible students" and advises manual verification
- The frontend displays the NEEDS REVIEW banner
- The frontend shows: *"We could not determine whether this applies to you.
  Please verify manually."*
- No checklist is rendered

### AC-13 — Resolvable colloquial term

**Given** the announcement: *"All senior students (Year 3 and Year 4) must
complete the exit survey by November 30, 2026."*
**And** a student with profile: Year=4

**When** the student submits the announcement

**Then:**
- The AI resolves "senior students" using the explicit definition "(Year 3 and 4)"
- `years` is `[3, 4]` (not `[]`)
- `years` is NOT in `ambiguous_dimensions`
- `relevance_status` is `"RELEVANT"` for Year 3 and Year 4 students
- `relevance_status` is `"NOT_RELEVANT"` for Year 1 and Year 2 students
- No NEEDS REVIEW banner is shown

### AC-14 — Explicit exclusion overrides ambiguity

**Given** the announcement: *"All eligible CSE students must attend.
ECE and ME students are not required."*
**And** a student: Dept=ECE

**When** the student submits the announcement

**Then:**
- `relevance_status` is `"NOT_RELEVANT"` (ECE is explicitly excluded)
- The ambiguity in "eligible" does not change the result — explicit exclusion
  takes precedence per FR-06
- `relevance_reason` references the explicit ECE exclusion
- `checklist` is `[]`

### AC-15 — RELEVANT decision summary display

**Given** an analysis with `relevance_status: "RELEVANT"`, non-empty checklist,
at least one deadline

**When** the results are rendered

**Then:**
- The decision summary panel is the first visible element in the results section
- The panel displays the label RELEVANT (green or positive treatment)
- `relevance_reason` is displayed
- The personalized checklist is visible below the panel
- At least one deadline is shown
- The priority badge is visible
- No advisory verification message is shown

### AC-16 — NOT RELEVANT decision summary display

**Given** an analysis with `relevance_status: "NOT_RELEVANT"`

**When** the results are rendered

**Then:**
- The decision summary panel is the first visible element in the results section
- The panel displays the label NOT RELEVANT (neutral or muted treatment)
- `relevance_reason` is displayed and references the specific mismatch
- The message "This announcement does not apply to your profile. No action is
  required from you." is shown
- No checklist is rendered

### AC-17 — UNCERTAIN decision summary display (NEEDS REVIEW)

**Given** an analysis with `relevance_status: "UNCERTAIN"`

**When** the results are rendered

**Then:**
- The decision summary panel is the first visible element in the results section
- The panel displays the label NEEDS REVIEW (amber or warning treatment) —
  NOT "UNCERTAIN"
- `relevance_reason` is displayed and quotes the ambiguous wording
- The advisory message is shown: *"We could not determine whether this applies
  to you. Please verify with your department or faculty office before taking
  any action."*
- No checklist is rendered
- No action items are presented as required steps

### AC-18 — Visual distinction between all three states

**Given** results for three announcements with statuses RELEVANT, NOT_RELEVANT,
and UNCERTAIN respectively

**When** a developer or tester views each result in turn

**Then:**
- Each decision summary panel is visually distinct from the other two
- RELEVANT, NOT RELEVANT, and NEEDS REVIEW cannot be mistaken for one another
  based on label text alone
- The colour or visual treatment of each state is consistent

### AC-19 — API key never exposed

**Given** the application is running

**When** a developer inspects all browser network requests, the frontend bundle,
and any client-side storage

**Then:**
- `GEMINI_API_KEY` is not present in any of those locations

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Compatibility | Frontend MUST work in the latest stable versions of Chrome, Firefox, and Edge |
| NFR-02 | Accessibility | All interactive elements MUST have appropriate ARIA labels and keyboard support |
| NFR-03 | Portability | Switching AI provider from Gemini to OpenAI MUST require changes only in `ai_service.py` |
| NFR-04 | Portability | Switching from SQLite to PostgreSQL MUST require only a `DATABASE_URL` change in `.env` |
| NFR-05 | Observability | Backend MUST log all AI requests and responses at DEBUG level |
| NFR-06 | Maintainability | No business logic in route handlers; all logic in the services layer |

---

*This requirements document covers the CampusFlow AI MVP.
Post-MVP features are documented in `project-overview.md` under Future Features.
Design document (design.md) and implementation tasks (tasks.md) to follow after
requirements approval.*
