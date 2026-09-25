# CampusFlow AI — Decision Log

This file records the major architectural and product decisions made for
CampusFlow AI. Each entry explains what was decided, why, and any constraints
or trade-offs acknowledged at the time.

Decisions recorded here are **locked** unless explicitly revisited and updated
in this file. Do not deviate from them during implementation without a new entry.

---

## D-001 — Project Root

**Decision:** The existing `CampusFlow/` folder is the project root.

**Rationale:** All code, configuration, and documentation lives under this
single directory. No monorepo tooling is used for MVP.

**Status:** Locked

---

## D-002 — AI Provider: Gemini as Default

**Decision:** Google Gemini is the initial and default AI provider, accessed
via the `google-generativeai` Python SDK. The exact model is selected through
the `GEMINI_MODEL` environment variable, not hardcoded.

**Rationale:** Gemini offers a generous free tier suitable for a hackathon,
avoids paid infrastructure costs, and supports structured JSON output natively.
Keeping the model configurable via env var allows upgrading or switching models
without touching application code.

**Status:** Locked

---

## D-003 — Provider-Agnostic AI Layer

**Decision:** The AI service layer (`ai_service.py`) exposes a provider-agnostic
interface. All Gemini-specific code is encapsulated inside that single file.

**Rationale:** Switching to OpenAI or another provider requires changes only
inside `ai_service.py`. The rest of the backend never imports Gemini-specific types.

**Status:** Locked

---

## D-004 — No Authentication for MVP

**Decision:** There is no user authentication, login, or session management in the MVP.

**Rationale:** Authentication adds significant complexity out of scope for a
hackathon MVP. The focus is on the core AI-powered analysis and checklist feature.

**Constraint:** Any user can access the app and submit any announcement.
Acceptable for a demo context.

**Future:** Authentication will be added post-MVP when user accounts are needed.

**Status:** Locked

---

## D-005 — Student Profile in localStorage

**Decision:** The student profile (name, department, specialization, year, section)
is stored in the browser's `localStorage` under the key `campusflow_profile`.

**Rationale:** Without authentication there is no server-side user identity.
localStorage is the simplest persistent store available for MVP.

**Trade-off:** Profile is browser/device-specific and not shared across devices.
Acceptable for hackathon demo purposes.

**Future:** When authentication is added, the profile migrates to a server-side
user record.

**Status:** Locked

---

## D-006 — SQLite for MVP Database

**Decision:** SQLite (via `aiosqlite` + SQLAlchemy async engine) is the database
for MVP.

**Rationale:** Zero infrastructure setup. Suitable for single-user demo use.
File-based, no separate DB process to manage.

**Constraint:** Schema and ORM code must use only PostgreSQL-compatible SQLAlchemy
constructs. No SQLite-specific pragmas or syntax in application code.

**Future:** Upgrading to PostgreSQL requires only changing `DATABASE_URL` in `.env`.

**Status:** Locked

---

## D-007 — Online AI Only (No Offline / Local Models)

**Decision:** The MVP uses only cloud-based AI (Gemini API). No local model
inference (Ollama, llama.cpp, etc.) is supported.

**Rationale:** Local models add setup complexity, hardware requirements, and
latency concerns that are out of scope for a hackathon MVP.

**Status:** Locked

---

## D-008 — No Unnecessary Paid Infrastructure

**Decision:** The MVP uses no paid cloud services. No AWS, GCP compute, Azure,
Vercel Pro, Supabase paid tier, etc.

**Rationale:** This is a hackathon project. The only acceptable external cost is
API usage on a free tier (Gemini free tier covers this).

**Status:** Locked

---

## D-009 — Target AI Response Time: 5–10 Seconds

**Decision:** The acceptable AI processing time for a single announcement analysis
is approximately 5–10 seconds end-to-end.

**Rationale:** Cloud LLM inference for a moderately sized prompt typically falls in
this range. The frontend should show a loading state during this window.

**Constraint:** If a real announcement exceeds the model's context window, it must
be truncated or chunked — not silently dropped.

**Status:** Locked

---

## D-010 — Personalized Relevance Detection is the Core Differentiator

**Decision:** The primary feature that distinguishes CampusFlow AI from a generic
announcement summarizer is personalized relevance detection: the system explicitly
determines whether an announcement applies to a specific student based on their
profile, and filters the checklist accordingly.

**Rationale:** This is the product's main value proposition. Every implementation
decision about the AI prompt, the extraction schema, and the checklist generation
must serve this goal.

**Status:** Locked

---

## D-011 — Kiro Specs for Requirements, Design, and Tasks

**Decision:** All significant features are built using Kiro's Spec workflow:
requirements → design → implementation tasks.

**Rationale:** Specs provide a structured, reviewable artifact for each feature
before implementation begins. This keeps the build disciplined and traceable,
which is especially important under hackathon time pressure.

**Status:** Locked

---

## D-012 — Kiro Agent Hooks for Automated Validation

**Decision:** Kiro Agent Hooks will be used to automate useful validation and
testing workflows (e.g., linting on save, running tests after task completion).

**Rationale:** Hooks catch issues early without manual intervention, reducing
debugging time during a time-constrained hackathon build.

**Status:** Locked
