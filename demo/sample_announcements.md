# CampusFlow AI — Demo Announcements

Paste these into the app during the demo. They exercise the three relevance
outcomes. Use this demo student profile for all three:

- **Department:** CSE
- **Specialization:** AI
- **Year:** 2
- **Section:** A

---

## 1. RELEVANT

> All second-year CSE AI students must register for the AI certification
> examination before September 30. Registration is mandatory and opens on the
> college portal this week. Late registrations will not be accepted.

**Expected (AC-01):**
- Decision summary: **RELEVANT**
- A personalized checklist with a registration action
- Deadline shown as `September 30` (original wording preserved — no invented year)
- Priority displayed with its reason

---

## 2. NOT_RELEVANT

> All first-year ECE students must submit their laboratory records to the
> department office by the end of this week. Records submitted after the
> deadline will incur a penalty.

**Expected (AC-02):**
- Decision summary: **NOT RELEVANT**
- Message that the announcement does not apply to your profile
- No checklist

---

## 3. UNCERTAIN (displayed as NEEDS REVIEW)

> All eligible students must register for the upcoming placement drive by
> October 15. Eligibility will be communicated separately. Interested students
> should keep their documents ready.

**Expected (AC-12):**
- Decision summary: **NEEDS REVIEW**
- Advisory to verify with your department or faculty office
- No checklist (eligibility is undefined, so no actions are assumed)

---

### Notes

- These are plain-text announcements pasted into the announcement box (50–10,000
  characters). Leading/trailing whitespace is trimmed before analysis.
- Actual AI extraction may phrase the summary/what-changed differently; the
  **relevance outcome** and the presence/absence of a checklist are what each
  scenario demonstrates.
