# CampusFlow AI

CampusFlow AI turns long, dense college announcements into a personalized,
actionable checklist for a specific student. You paste an announcement and fill
in your profile (department, specialization, year, section); the backend uses
Google Gemini to extract structured information (what changed, who is affected,
deadlines, required actions, priority), then deterministically decides whether
the announcement is **relevant**, **not relevant**, or **needs review** for you
and generates a tailored checklist — so you know exactly what to do, and by when.

---

## Prerequisites

- **Node.js 18+**
- **Python 3.11+**
- **A Google Gemini API key**

---

## Backend setup

```
cd backend
pip install -r requirements.txt
cp .env.example .env  # add your GEMINI_API_KEY and GEMINI_MODEL
uvicorn main:app --reload
```

The backend runs at `http://localhost:8000`. Its single MVP endpoint is
`POST /api/v1/analyze`, plus a `GET /health` check.

> **Note:** `GEMINI_MODEL` must be set in `backend/.env` — the model name is
> never hardcoded in source. `backend/.env` is git-ignored; use
> `backend/.env.example` as the template.

---

## Frontend setup

```
cd frontend
npm install
# create .env with VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

The frontend dev server runs at `http://localhost:5173` and talks only to the
backend API (never to Gemini directly). Your student profile is stored in the
browser's `localStorage` — there is no login and no server-side profile storage.

---

## Environment variables

**backend/.env**

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
CORS_ORIGIN=http://localhost:5173
```

**frontend/.env**

```
VITE_API_BASE_URL=http://localhost:8000
```

Never commit `.env` files — they are listed in `.gitignore`. Only the
`.env.example` template is committed.
