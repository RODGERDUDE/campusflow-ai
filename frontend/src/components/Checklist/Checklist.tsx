// CampusFlow AI — Personalized checklist.
//
// Renders the checklist items with checkboxes (FR-09, AC-06, design §3.1,
// §10.2). Completion is frontend-only: toggling a checkbox calls onToggle(id)
// and the parent updates its state — nothing is ever sent back to the backend.
// The parent only renders this when relevance_status === "RELEVANT". When there
// are no items, the finalized empty-state message is shown.

import type { ChecklistItem } from "../../types";
import styles from "./Checklist.module.css";

interface ChecklistProps {
  items: ChecklistItem[];
  onToggle: (id: string) => void;
}

export function Checklist({ items, onToggle }: ChecklistProps) {
  if (items.length === 0) {
    return <p className={styles.empty}>No specific actions required.</p>;
  }

  return (
    <div className={styles.section} aria-label="Checklist">
      <ul className={styles.list}>
        {items.map((item) => (
          <li
            key={item.id}
            className={`${styles.item} ${item.completed ? styles.completed : ""}`}
          >
            <input
              type="checkbox"
              id={`checklist-${item.id}`}
              checked={item.completed}
              onChange={() => onToggle(item.id)}
              aria-label={`Mark "${item.description}" as ${item.completed ? "incomplete" : "complete"}`}
            />
            <label htmlFor={`checklist-${item.id}`}>
              <span className={styles.description}>{item.description}</span>
              {item.deadline_text && (
                <span className={styles.deadline}>Due: {item.deadline_text}</span>
              )}
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
