# CampusFlow AI — Project Overview

## What It Is

CampusFlow AI is a hackathon project that helps college students cut through
long, confusing institutional announcements and understand exactly what they
need to do — and by when.

Students paste or upload an announcement. The AI analyzes it and produces a
personalized, actionable checklist based on the student's profile.

---

## The Problem

College announcements are:
- Too long and dense to read quickly
- Written for all students, not any particular one
- Easy to miss deadlines buried inside them
- Often unclear about what action is actually required

---

## The Solution

CampusFlow AI extracts structured information from announcements:

| Field | Description |
|---|---|
| What changed | The core change or update being announced |
| Who is affected | Which departments, years, sections, or specializations |
| Important dates | All deadlines and key dates mentioned |
| Required actions | Concrete steps a student must take |
| Priority | How urgent or important this announcement is |

It then cross-references the extracted data against the student's profile to
determine relevance and generate a personalized checklist.

---

## Student Profile

Each student has a profile with:
- **Department** (e.g., Computer Science, Mechanical Engineering)
- **Specialization** (e.g., AI/ML, Cybersecurity)
- **Year** (1st, 2nd, 3rd, 4th)
- **Section** (e.g., A, B, C)

The AI uses this profile to filter irrelevant announcements and tailor the
checklist to only what applies to that specific student.

---

## MVP Scope (v1)

1. Notice input — paste text or upload a document
2. AI analysis — structured extraction via LLM
3. Student relevance detection — does this apply to this student?
4. Deadline extraction — all dates and deadlines identified
5. Action extraction — concrete required steps
6. Priority — urgency classification (High / Medium / Low)
7. Personalized checklist — final output tailored to the student

---

## Future Features (Post-MVP)

- Deadline reminders and notification system
- Calendar integration (Google Calendar, iCal export)
- Action tracking (mark items complete)
- Announcement history per student
- Full dashboard with analytics
- Multi-announcement management

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Python 3.11+ + FastAPI |
| AI | OpenAI GPT-4o or Google Gemini 1.5 Pro |
| Database | SQLite (MVP) → PostgreSQL (production upgrade) |
| ORM | SQLAlchemy |
| API format | REST + JSON |

---

## Project Structure (Planned)

```
CampusFlow/
├── frontend/          # React + Vite app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/  # API calls
│   │   └── types/     # TypeScript interfaces
│   └── ...
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic + AI integration
│   │   └── core/      # Config, DB setup
│   └── ...
├── .kiro/
│   └── steering/
└── README.md
```
