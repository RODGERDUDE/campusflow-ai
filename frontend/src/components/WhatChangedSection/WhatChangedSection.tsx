// CampusFlow AI — What-changed section.
//
// Displays the announcement summary and the core change, each clearly labelled
// (design §3.1). Pure presentation from the analysis result.

import styles from "./WhatChangedSection.module.css";

interface WhatChangedSectionProps {
  summary: string;
  whatChanged: string;
}

export function WhatChangedSection({
  summary,
  whatChanged,
}: WhatChangedSectionProps) {
  return (
    <div className={styles.section} aria-label="What changed">
      <p className={styles.label}>Summary</p>
      <p className={styles.value}>{summary}</p>
      <p className={styles.label}>What changed</p>
      <p className={styles.value}>{whatChanged}</p>
    </div>
  );
}
