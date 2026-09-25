// CampusFlow AI — Deadline section.
//
// Lists the deadlines extracted from the announcement (FR-08, FR-15,
// design §3.1). It always shows the original source wording
// (original_date_text) and never the raw normalized YYYY-MM-DD, so no invented
// or reformatted dates are ever surfaced. When the announcement is uncertain
// (showAsObligations = false), the deadlines are shown with a disclaimer rather
// than as firm obligations. Renders nothing when there are no deadlines.

import type { DeadlineItem } from "../../types";
import styles from "./DeadlineSection.module.css";

interface DeadlineSectionProps {
  deadlines: DeadlineItem[];
  showAsObligations: boolean;
}

export function DeadlineSection({
  deadlines,
  showAsObligations,
}: DeadlineSectionProps) {
  if (deadlines.length === 0) {
    return null;
  }

  return (
    <div className={styles.section} aria-label="Deadlines">
      <p className={styles.heading}>Important dates</p>
      {!showAsObligations && (
        <p className={styles.disclaimer}>
          These deadlines may or may not apply to you. Verify before acting.
        </p>
      )}
      <ul className={styles.list}>
        {deadlines.map((deadline, index) => (
          <li key={index} className={styles.item}>
            <div>
              <span className={styles.date}>{deadline.original_date_text}</span>
              {deadline.label ? ` — ${deadline.label}` : ""}
            </div>
            {deadline.description && (
              <div className={styles.description}>{deadline.description}</div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
