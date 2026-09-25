// CampusFlow AI — Error state.
//
// Shows a user-friendly error message and a "Try Again" button (FR-03, FR-13,
// AC-07, AC-08, design §3.1). It renders only the plain message string it is
// given — never a raw error object, stack trace, HTTP status code, or error
// code field.

import styles from "./ErrorState.module.css";

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className={styles.wrapper} role="alert">
      <p className={styles.message}>{message}</p>
      <button type="button" className={styles.button} onClick={onRetry}>
        Try Again
      </button>
    </div>
  );
}
