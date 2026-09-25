// CampusFlow AI — Home page.
//
// The main single-page layout: a profile sidebar plus a main announcement area
// with placeholder sections for the announcement input and results
// (design §15, §16). The student profile form (T-18) is wired in here: the
// profile is loaded from localStorage on page load and kept in Home state so it
// is ready to be passed to analyzeAnnouncement() on submission (T-21).

import { useState } from "react";

import { StudentProfileForm } from "../../components/StudentProfileForm/StudentProfileForm";
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
  const [announcementText] = useState<string>("");
  // Whether an analysis request is in flight.
  const [isLoading] = useState<boolean>(false);
  // User-friendly error message, or null when there is no error.
  const [error] = useState<string | null>(null);
  // The analysis result from the backend, or null before/after a reset.
  const [result] = useState<AnalyzeResponse | null>(null);
  // Checklist items with frontend-only completion state.
  const [checklist] = useState<ChecklistItem[]>([]);

  // Keep Home's profile state in sync when the form reports a valid profile.
  function handleProfileChange(nextProfile: StudentProfile) {
    setProfile(nextProfile);
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
          {/* Placeholder: AnnouncementInput (T-20) */}
          <h2>Announcement</h2>
          <p>
            {announcementText
              ? "Announcement entered."
              : "Paste an announcement to begin."}
          </p>
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
