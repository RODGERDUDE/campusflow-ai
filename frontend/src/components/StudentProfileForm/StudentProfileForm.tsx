// CampusFlow AI — Student profile form.
//
// Collects the five profile fields and persists them to localStorage under the
// key "campusflow_profile" (FR-02, design §3.1). Profile handling is entirely
// frontend-only: no backend persistence, no authentication. When the profile
// is complete and valid, the parent is notified via onProfileChange.

import { useEffect, useState } from "react";

import type { StudentProfile } from "../../types";
import styles from "./StudentProfileForm.module.css";

const STORAGE_KEY = "campusflow_profile";

// Raw form values are held as strings (year included) so partial/empty input
// can be represented and validated cleanly.
interface FormValues {
  name: string;
  department: string;
  specialization: string;
  year: string;
  section: string;
}

const EMPTY_FORM: FormValues = {
  name: "",
  department: "",
  specialization: "",
  year: "",
  section: "",
};

interface StudentProfileFormProps {
  onProfileChange: (profile: StudentProfile) => void;
}

export function StudentProfileForm({ onProfileChange }: StudentProfileFormProps) {
  const [values, setValues] = useState<FormValues>(EMPTY_FORM);
  const [showErrors, setShowErrors] = useState<boolean>(false);

  // On mount: load a saved profile from localStorage and pre-populate.
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    try {
      const parsed = JSON.parse(saved) as Partial<StudentProfile>;
      setValues({
        name: parsed.name ?? "",
        department: parsed.department ?? "",
        specialization: parsed.specialization ?? "",
        year: parsed.year != null ? String(parsed.year) : "",
        section: parsed.section ?? "",
      });
    } catch {
      // Ignore malformed saved data; start from an empty form.
    }
  }, []);

  function updateField(field: keyof FormValues, value: string) {
    const next = { ...values, [field]: value };
    setValues(next);
    // Persist the current field values on every change.
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }

  // Per-field validation messages (empty string means "no error").
  const yearNumber = Number(values.year);
  const yearValid =
    values.year.trim() !== "" &&
    Number.isInteger(yearNumber) &&
    yearNumber >= 1 &&
    yearNumber <= 4;

  const errors = {
    name: values.name.trim() === "" ? "Name is required." : "",
    department: values.department.trim() === "" ? "Department is required." : "",
    specialization:
      values.specialization.trim() === "" ? "Specialization is required." : "",
    year: !yearValid ? "Year must be a number from 1 to 4." : "",
    section: values.section.trim() === "" ? "Section is required." : "",
  };

  const isValid = Object.values(errors).every((message) => message === "");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isValid) {
      setShowErrors(true);
      return; // Block submission when any field is empty or invalid.
    }
    onProfileChange({
      name: values.name.trim(),
      department: values.department.trim(),
      specialization: values.specialization.trim(),
      year: yearNumber,
      section: values.section.trim(),
    });
  }

  function renderField(
    field: keyof FormValues,
    label: string,
    type: "text" | "number",
  ) {
    const errorId = `${field}-error`;
    const hasError = showErrors && errors[field] !== "";
    return (
      <div className={styles.field}>
        <label htmlFor={field}>{label}</label>
        <input
          id={field}
          name={field}
          type={type}
          value={values[field]}
          min={type === "number" ? 1 : undefined}
          max={type === "number" ? 4 : undefined}
          required
          aria-required="true"
          aria-invalid={hasError}
          aria-describedby={hasError ? errorId : undefined}
          onChange={(e) => updateField(field, e.target.value)}
        />
        {hasError && (
          <span id={errorId} className={styles.error} role="alert">
            {errors[field]}
          </span>
        )}
      </div>
    );
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      {renderField("name", "Name", "text")}
      {renderField("department", "Department", "text")}
      {renderField("specialization", "Specialization", "text")}
      {renderField("year", "Year (1-4)", "number")}
      {renderField("section", "Section", "text")}
      <button type="submit">Save profile</button>
    </form>
  );
}
