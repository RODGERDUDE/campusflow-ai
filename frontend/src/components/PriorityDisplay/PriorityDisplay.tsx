// CampusFlow AI — Priority display.
//
// Shows the announcement's priority as a colour-coded badge with the backend's
// explanation (FR-11, FR-15, design §3.1). Priority values are preserved
// exactly (High / Medium / Low) and priorityReason is shown verbatim — no
// values are invented or reinterpreted. The parent only renders this when the
// relevance status is RELEVANT (assembled in T-26).

import type { Priority } from "../../types";
import styles from "./PriorityDisplay.module.css";

// Colour class per priority value: High=red, Medium=amber, Low=green.
const BADGE_CLASS: Record<Priority, string> = {
  High: styles.high,
  Medium: styles.medium,
  Low: styles.low,
};

interface PriorityDisplayProps {
  priority: Priority;
  priorityReason: string;
}

export function PriorityDisplay({
  priority,
  priorityReason,
}: PriorityDisplayProps) {
  return (
    <div className={styles.wrapper} aria-label="Priority">
      <span className={`${styles.badge} ${BADGE_CLASS[priority]}`}>
        {priority}
      </span>
      <p className={styles.reason}>{priorityReason}</p>
    </div>
  );
}
