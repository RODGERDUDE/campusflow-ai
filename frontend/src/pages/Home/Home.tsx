// CampusFlow AI — Home page.
//
// The main single-page layout: a profile sidebar plus a main announcement area
// with placeholder sections for the profile form, announcement input, and
// results (design §15, §16). This is the skeleton only — state variables are
// declared here, but no behavior (handlers, API calls) is wired up yet.

import { useState } from "react";

import type {
  AnalyzeResponse,
  ChecklistItem,
  StudentProfile,
} from "../../types";
import styles from "./Home.module.css";

function Home() {
  // Student profile (loaded/edited later; null until provided).
  const [profile] = useState<StudentProfile | null>(null);
  // Raw announcement text pasted by the student.
  const [announcementText] = useState<string>("");
  // Whether an analysis request is in flight.
  const [isLoading] = useState<boolean>(false);
  // User-friendly error message, or null when there is no error.
  const [error] = useState<string | null>(null);
  // The analysis result from the backend, or null before/after a reset.
  const [result] = useState<AnalyzeResponse | null>(null);
  // Checklist items with frontend-only completion state.
  const [checklist] = useState<ChecklistItem[]>([]);

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <section className={styles.section} aria-label="Student profile">
          {/* Placeholder: StudentProfileForm (T-18) */}
          <h2>Your Profile</h2>
          <p>{profile ? profile.name : "No profile saved yet."}</p>
        </section>
      </aside>

      <main className={styles.main}>
        <section className={styles.section} aria-label="Announcement input">
          {/* Placeholder: AnnouncementInput (T-20) */}
          <h2>Announcement</h2>
          <p>{announcementText ? "Announcement entered." : "Paste an announcement to begin."}</p>
        </section>

        <section className={styles.section} aria-label="Analysis results">
          {/* Placeholder: results (decision summary at top), loading, error */}
          <h2>Results</h2>
          {isLoading && <p>Analysing…</p>}
          {error && <p>{error}</p>}
          {result && <p>Analysis ready.</p>}
          {checklist.length > 0 && <p>{checklist.length} checklist item(s).</p>}
        </section>
      </main>
    </div>
  );
}

export default Home;
