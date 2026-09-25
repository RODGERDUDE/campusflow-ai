// CampusFlow AI — Home page.
//
// The main single-page layout: a profile sidebar plus a main announcement area
// (design §15, §16). This page owns all analysis state and the submit
// controller (T-21): it validates inputs, calls the backend API service
// (never Gemini directly), and manages loading/error/result state. It also
// assembles the full results view (T-26) with relevance-specific rendering.

import { useState } from "react";

import {
  AnnouncementInput,
  MAX_LENGTH,
  MIN_LENGTH,
} from "../../components/AnnouncementInput/AnnouncementInput";
import { Checklist } from "../../components/Checklist/Checklist";
import { DeadlineSection } from "../../components/DeadlineSection/DeadlineSection";
import { PersonalizedDecisionSummary } from "../../components/PersonalizedDecisionSummary/PersonalizedDecisionSummary";
import { PriorityDisplay } from "../../components/PriorityDisplay/PriorityDisplay";
import { StudentProfileForm } from "../../components/StudentProfileForm/StudentProfileForm";
import { WhatChangedSection } from "../../components/WhatChangedSection/WhatChangedSection";
import { analyzeAnnouncement } from "../../services/api";
import type {
  AnalyzeResponse,
  ChecklistItem,
  StudentProfile,
} from "../../types";
import styles from "./Home.module.css";

const STORAGE_KEY = "campusflow_profile";

// Read a previously saved profile from localStorage (frontend-only, no auth).
function loadSavedProfile(): StudentProfile | null {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return null;
  try {
    return JSON.parse(saved) as StudentProfile;
  } catch {
    return null;
  }
}

function Home() {
  // Student profile — initialised from localStorage on page load.
  const [profile, setProfile] = useState<StudentProfile | null>(loadSavedProfile);
  // Raw announcement text pasted by the student.
  const [announcementText, setAnnouncementText] = useState<string>("");
  // Whether an analysis request is in flight.
  const [isLoading, setIsLoading] = useState<boolean>(false);
  // User-friendly error message, or null when there is no error.
  const [error, setError] = useState<string | null>(null);
  // The analysis result from the backend, or null before/after a reset.
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  // Checklist items with frontend-only completion state.
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);

  // Keep Home's profile state in sync when the form reports a valid profile.
  function handleProfileChange(nextProfile: StudentProfile) {
    setProfile(nextProfile);
  }

  async function handleSubmit() {
    // Trim immediately before validating and sending (FR-01).
    const trimmed = announcementText.trim();

    // Block submission on invalid input; show a validation error, no API call.
    if (!profile) {
      setError("Please fill in and save your profile before analysing.");
      return;
    }
    if (trimmed.length < MIN_LENGTH) {
      setError(`The announcement must be at least ${MIN_LENGTH} characters.`);
      return;
    }
    if (trimmed.length > MAX_LENGTH) {
      setError(
        `The announcement must be ${MAX_LENGTH.toLocaleString()} characters or fewer.`,
      );
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await analyzeAnnouncement(trimmed, profile);
      setResult(response);
      setChecklist(response.checklist);
    } catch (err) {
      // Show a user-visible message from the thrown Error.
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  // Toggle a checklist item's completed flag in frontend state only (design
  // §10.2). All other item fields are preserved and nothing is sent to the
  // backend.
  function toggleItem(id: string) {
    setChecklist((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, completed: !item.completed } : item,
      ),
    );
  }

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <section className={styles.section} aria-label="Student profile">
          <h2>Your Profile</h2>
          <StudentProfileForm onProfileChange={handleProfileChange} />
          <p>
            {profile
              ? `Saved profile: ${profile.name}`
              : "No profile saved yet."}
          </p>
        </section>
      </aside>

      <main className={styles.main}>
        <section className={styles.section} aria-label="Announcement input">
          <AnnouncementInput
            value={announcementText}
            onChange={setAnnouncementText}
            disabled={isLoading}
          />
          <button type="button" onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? "Analysing…" : "Analyse announcement"}
          </button>
        </section>

        <section className={styles.section} aria-label="Analysis results">
          <h2>Results</h2>
          {isLoading && <p>Analysing…</p>}
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
          {/* Results are hidden while a request is in flight. */}
          {!isLoading && result && (
            <>
              {/* PersonalizedDecisionSummary is always first (FR-15). */}
              <PersonalizedDecisionSummary relevance={result.relevance} />
              <WhatChangedSection
                summary={result.analysis.summary}
                whatChanged={result.analysis.what_changed}
              />
              <DeadlineSection
                deadlines={result.analysis.deadlines}
                showAsObligations={
                  result.relevance.relevance_status === "RELEVANT"
                }
              />
              {result.relevance.relevance_status === "RELEVANT" && (
                <>
                  <PriorityDisplay
                    priority={result.analysis.priority}
                    priorityReason={result.analysis.priority_reason}
                  />
                  <Checklist items={checklist} onToggle={toggleItem} />
                </>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default Home;
