// CampusFlow AI — Announcement input.
//
// A controlled <textarea> for pasting a college announcement (FR-01, AC-01,
// design §3.1). It shows a live character count and enforces the same limits as
// the backend (50-10,000 chars). The raw value is passed up so multi-word
// typing works naturally; leading/trailing whitespace is trimmed at the submit
// boundary (T-21) before sending to the backend. This component does not submit
// anything and never talks to Gemini; the submit controller lives in Home.

import styles from "./AnnouncementInput.module.css";

// Length limits mirror the backend AnalyzeRequest constraints exactly.
export const MIN_LENGTH = 50;
export const MAX_LENGTH = 10000;

interface AnnouncementInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function AnnouncementInput({
  value,
  onChange,
  disabled = false,
}: AnnouncementInputProps) {
  const length = value.length;
  const tooShort = length > 0 && length < MIN_LENGTH;

  function handleChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    // Pass the raw value up so multi-word typing (including spaces) works
    // naturally. Leading/trailing whitespace is trimmed at the submit boundary
    // (T-21) before the announcement is sent to the backend, per FR-01.
    onChange(event.target.value);
  }

  return (
    <div className={styles.wrapper}>
      <label htmlFor="announcement-input">Announcement</label>
      <textarea
        id="announcement-input"
        className={styles.textarea}
        placeholder="Paste your college announcement here..."
        value={value}
        maxLength={MAX_LENGTH}
        disabled={disabled}
        aria-required="true"
        aria-invalid={tooShort}
        aria-describedby="announcement-count announcement-error"
        onChange={handleChange}
      />
      <span id="announcement-count" className={styles.count}>
        {length.toLocaleString()} / {MAX_LENGTH.toLocaleString()} characters
      </span>
      {tooShort && (
        <span id="announcement-error" className={styles.error} role="alert">
          Please enter at least {MIN_LENGTH} characters.
        </span>
      )}
    </div>
  );
}
