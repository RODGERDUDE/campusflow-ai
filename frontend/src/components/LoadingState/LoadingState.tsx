// CampusFlow AI — Loading state.
//
// A centered spinner shown while an analysis request is in flight (FR-03,
// design §3.1). No additional content.

import styles from "./LoadingState.module.css";

export function LoadingState() {
  return (
    <div className={styles.wrapper} role="status" aria-live="polite">
      <div className={styles.spinner} aria-hidden="true" />
      <p className={styles.message}>Analysing your announcement...</p>
    </div>
  );
}
