# CampusFlow AI — Development Rules

These rules apply to all code written for this project. Follow them consistently
across both frontend and backend.

---

## General Rules

- **MVP first.** Build the minimal thing that works before adding polish or extras.
  Do not add features not listed in the current scope unless explicitly asked.
- **No premature abstraction.** Avoid over-engineering. Add abstraction only when
  duplication or complexity clearly demands it.
- **Explicit over implicit.** Favor readable, obvious code over clever shortcuts.
- **One responsibility per module.** Each file/module should do one clear thing.
- **Environment config stays in .env files.** Never hardcode API keys, secrets,
  or environment-specific values in source code.

---

## Frontend Rules (React + Vite + TypeScript)

- Use **TypeScript** for all frontend code. No plain `.js` files in `src/`.
- Define explicit types/interfaces for all API responses and shared data shapes.
  Place them in `src/types/`.
- Use **functional components** only. No class components.
- Use **React hooks** for all state and side-effect logic.
- API calls live in `src/services/`. Components do not call `fetch` or `axios` directly.
- Use **Axios** for HTTP requests (not the Fetch API directly).
- Keep components small and focused. If a component exceeds ~150 lines, consider splitting it.
- No inline styles. Use CSS modules or Tailwind (decide before starting UI work).
- Accessibility: all interactive elements must have appropriate ARIA labels and
  keyboard support.

---

## Backend Rules (Python + FastAPI)

- Use **Python 3.11+** features where appropriate.
- Use **Pydantic v2** for all request/response schemas.
- Use **SQLAlchemy 2.x** with the async engine for database access.
- Organize code into layers:
  - `api/` — route handlers only, thin logic, delegate to services
  - `services/` — business logic, AI calls, data processing
  - `models/` — SQLAlchemy ORM models
  - `schemas/` — Pydantic input/output models
  - `core/` — config, database setup, dependencies
- Never put business logic inside route handlers.
- Use **dependency injection** (FastAPI `Depends`) for DB sessions and shared dependencies.
- All database operations go through SQLAlchemy. No raw SQL strings unless
  performance requires it and it is clearly documented.
- Return consistent error shapes across all endpoints:
  ```json
  { "detail": "Human-readable message", "code": "ERROR_CODE" }
  ```
- Use HTTP status codes correctly:
  - `200` for successful reads
  - `201` for successful creates
  - `422` for validation errors (FastAPI handles this automatically)
  - `404` for not found
  - `500` for unexpected server errors

---

## AI Integration Rules

- All AI calls are isolated in `backend/app/services/ai_service.py`.
  No other layer calls the LLM directly.
- The AI service must be provider-agnostic at the interface level. The implementation
  can target OpenAI or Gemini, but the calling code should not care which one.
- Always use **structured output / JSON mode** when the LLM supports it.
  Never parse free-text LLM responses with regex.
- Define the expected output schema (Pydantic) before writing the prompt.
  The prompt should instruct the model to match that schema.
- Handle LLM errors gracefully. If the AI call fails, return a clear error to the
  frontend — do not crash the request.
- Log all AI inputs and outputs at DEBUG level for development tracing.
  Sanitize any PII before logging in production.

---

## Database Rules

- Start with **SQLite** for the MVP. The schema must be designed so that switching
  to PostgreSQL requires only a connection string change — no SQLite-specific syntax.
- Use **Alembic** for all schema migrations. Never modify the database directly.
- Table names are **snake_case plural** (e.g., `student_profiles`, `announcements`).
- All tables have:
  - `id` — integer primary key, auto-increment
  - `created_at` — UTC timestamp, set on insert
  - `updated_at` — UTC timestamp, updated on every write
- Foreign keys must be defined explicitly in the model.

---

## API Design Rules

- Base path: `/api/v1/`
- Use **nouns** for resource names, not verbs: `/announcements`, not `/getAnnouncement`
- Endpoint naming follows REST conventions:
  - `GET /resource` — list
  - `POST /resource` — create
  - `GET /resource/{id}` — retrieve one
  - `PUT /resource/{id}` — full update
  - `PATCH /resource/{id}` — partial update
  - `DELETE /resource/{id}` — delete
- All endpoints return JSON.
- Include CORS configuration from day one so the frontend can call the backend
  during development.

---

## Code Style

### Python
- Follow **PEP 8**. Use `ruff` for linting and formatting.
- Type-annotate all function signatures.
- Docstrings on all public functions and classes (one-line summary minimum).

### TypeScript / React
- Follow standard ESLint + Prettier config (set up via Vite template defaults).
- Use `const` by default; only use `let` when reassignment is needed.
- Prefer named exports over default exports for components and utilities.
  (Exception: page-level components may use default exports for router compatibility.)

---

## Git Rules

- Branch naming: `feature/<short-description>`, `fix/<short-description>`
- Commit messages follow the format: `type: short description`
  - Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `style`, `test`
  - Example: `feat: add announcement analysis endpoint`
- Never commit `.env` files or secrets.
- `main` branch always contains working code.

---

## What Not to Build Yet (Post-MVP Only)

- User authentication / login system
- Notification system
- Calendar integration
- Action tracking / completion marking
- Announcement history / dashboard
- Multi-user / multi-tenant support
