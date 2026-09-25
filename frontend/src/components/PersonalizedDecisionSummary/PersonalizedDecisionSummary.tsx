// CampusFlow AI — Personalized decision summary.
//
// The primary output panel, shown at the TOP of the results section (FR-15,
// AC-15..AC-18, design §3.1). It maps the backend relevance status to a
// display label and badge colour WITHOUT changing the underlying enum value,
// and shows the plain-English reason plus a per-status advisory message.

import type { RelevanceResult, RelevanceStatus } from "../../types";
import styles from "./PersonalizedDecisionSummary.module.css";

// Display mapping (data/state keeps the original enum value untouched):
//   RELEVANT      -> "RELEVANT"
//   NOT_RELEVANT  -> "NOT RELEVANT"
//   UNCERTAIN     -> "NEEDS REVIEW"
const DISPLAY: Record<
  RelevanceStatus,
  { label: string; badgeClass: string; advisory?: string }
> = {
  RELEVANT: {
    label: "RELEVANT",
    badgeClass: styles.relevant,
  },
  NOT_RELEVANT: {
    label: "NOT RELEVANT",
    badgeClass: styles.notRelevant,
    advisory:
      "This announcement does not apply to your profile. No action is required from you.",
  },
  UNCERTAIN: {
    label: "NEEDS REVIEW",
    badgeClass: styles.needsReview,
    advisory:
      "We could not determine whether this applies to you. Please verify with your department or faculty office before taking any action.",
  },
};

interface PersonalizedDecisionSummaryProps {
  relevance: RelevanceResult;
}

export function PersonalizedDecisionSummary({
  relevance,
}: PersonalizedDecisionSummaryProps) {
  const display = DISPLAY[relevance.relevance_status];

  return (
    <div className={styles.panel} aria-label="Decision summary">
      <span className={`${styles.badge} ${display.badgeClass}`}>
        {display.label}
      </span>
      <p className={styles.reason}>{relevance.relevance_reason}</p>
      {display.advisory && <p className={styles.advisory}>{display.advisory}</p>}
    </div>
  );
}
