# CampusFlow AI — MVP Architecture

## Overview

CampusFlow AI is a two-tier web application: a React frontend and a FastAPI
backend. The backend handles all AI processing and data persistence. The
frontend is responsible only for presentation and user interaction.

---

## Frontend

**Stack:** React 18 + Vite + TypeScript

### Responsibilities
- Render the announcement input form (paste text or upload file)
- Manage and display the student profile
- Display the AI-generated analysis and personalized checklist
- Communicate with the backend exclusively through a dedicated API service layer

### Key Conventions
- All components are functional components using React hooks
- No component calls `fetch` or `axios` directly — all HTTP calls go through `src/services/`
- TypeScript interfaces for all API request/response shapes live in `src/types/`
- Student profile is persisted in **localStorage** (no backend auth required for MVP)

### Component Structure (Planned)

```
src/
├── components/
│   ├── AnnouncementInput/   # Paste or upload notice
│   ├── StudentProfile/      # View and edit profile fields
│   ├── AnalysisResult/      # Structured extraction display
│   └── Checklist/           # Personalized action checklist
├── pages/
│   └── Home/                # Main single-page layout
├── services/
│   └── api.ts               # All backend API calls
└── types/
    └── index.ts             # Shared TypeScript interfaces
```

---

## Backend

**Stack:** Python 3.11+ + FastAPI + SQLAlchemy + SQLite

### Responsibilities
- Receive announcement text from the frontend
- Call the AI service to extract structured data
- Persist announcements and analysis results
- Return structured JSON responses to the frontend

### Layer Separation

```
backend/app/
├── api/        # Route handlers — thin, delegate to services
├── services/   # Business logic, AI integration, data processing
├── models/     # SQLAlchemy ORM models (database tables)
├── schemas/    # Pydantic v2 request/response models
└── core/       # Config, database setup, shared dependencies
```

No business logic lives in `api/`. Route handlers receive a request, call a
service, and return the result.

### REST API

All endpoints are served under `/api/v1/`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analyze` | Submit announcement for AI analysis |
| GET | `/api/v1/announcements` | List past analyses |
| GET | `/api/v1/announcements/{id}` | Retrieve a specific analysis |

CORS is configured from day one to allow frontend dev server requests.

---

## AI Layer

**Default Provider:** Google Gemini (via `google-generativeai` SDK), with the exact model selected through the `GEMINI_MODEL` environment variable

### Design Principles
- All LLM calls are isolated in `backend/app/services/ai_service.py`
- The interface is **provider-agnostic** — calling code depends only on the
  service interface, not on Gemini-specific types
- Switching providers requires changes only inside `ai_service.py`
- Structured JSON output is always requested via the model's JSON mode or an
  explicit JSON schema in the prompt — never free-form text
- LLM responses are parsed directly into Pydantic models; no regex parsing

### Extraction Schema (AI Output)

The AI is instructed to return a JSON object conforming to this shape:

```json
{
  "summary": "One-sentence summary of the announcement",
  "what_changed": "Description of the core change or update",
  "affected_groups": {
    "departments": ["all | CS | ME | ..."],
    "years": ["all | 1 | 2 | 3 | 4"],
    "sections": ["all | A | B | ..."],
    "specializations": ["all | AI/ML | ..."]
  },
  "deadlines": [
    { "label": "Registration deadline", "date": "YYYY-MM-DD", "description": "..." }
  ],
  "required_actions": [
    { "action": "Submit form X", "by": "YYYY-MM-DD", "details": "..." }
  ],
  "priority": "High | Medium | Low",
  "priority_reason": "Why this priority was assigned"
}
```

### API Key Storage
- API keys are stored only in `.env` files
- Never committed to version control
- Accessed in code via `python-dotenv` and `os.getenv()`

---

## Database

**MVP:** SQLite via SQLAlchemy 2.x (async engine)
**Future upgrade:** PostgreSQL — connection string change only, no SQLite-specific syntax used

### Schema Conventions
- Table names: `snake_case` plural (e.g., `announcements`, `analysis_results`)
- Every table has: `id` (PK), `created_at` (UTC), `updated_at` (UTC)
- Migrations managed with Alembic

### Core Tables (MVP)

**announcements**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| raw_text | TEXT | Original announcement text |
| created_at | DATETIME | UTC |
| updated_at | DATETIME | UTC |

**analysis_results**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| announcement_id | INTEGER | FK → announcements.id |
| summary | TEXT | |
| what_changed | TEXT | |
| affected_groups | TEXT | JSON-serialized |
| deadlines | TEXT | JSON-serialized |
| required_actions | TEXT | JSON-serialized |
| priority | TEXT | High / Medium / Low |
| priority_reason | TEXT | |
| created_at | DATETIME | UTC |
| updated_at | DATETIME | UTC |

---

## Student Profile

The student profile is managed entirely on the frontend for MVP.

**Storage:** `localStorage` under the key `campusflow_profile`

**Fields:**

| Field | Type | Example |
|-------|------|---------|
| name | string | "Ananya Sharma" |
| department | string | "Computer Science" |
| specialization | string | "AI/ML" |
| year | number | 3 |
| section | string | "B" |

No authentication, no server-side user accounts in the MVP.

---

## Core Processing Flow

```
Student pastes / uploads announcement
        │
        ▼
Frontend sends POST /api/v1/analyze
  { announcement_text, student_profile }
        │
        ▼
Backend: save raw announcement to DB
        │
        ▼
AI Service: send announcement to Gemini
  → extract: summary, what_changed,
             affected_groups, deadlines,
             required_actions, priority
        │
        ▼
Backend: save analysis_result to DB
        │
        ▼
Backend: relevance check
  Compare affected_groups with student_profile
  → is_relevant: true/false
  → relevance_reason: explanation
        │
        ▼
Backend: build personalized checklist
  Filter required_actions and deadlines
  that apply to this student
        │
        ▼
Return full response to frontend
  { analysis, is_relevant, checklist }
        │
        ▼
Frontend renders:
  - Relevance banner
  - Structured extraction summary
  - Personalized checklist
```

---

## Environment Configuration

Each tier has its own `.env` file:

**backend/.env**
```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-pro
DATABASE_URL=sqlite+aiosqlite:///./campusflow.db
```

**frontend/.env**
```
VITE_API_BASE_URL=http://localhost:8000
```

Both `.env` files are listed in `.gitignore`.
