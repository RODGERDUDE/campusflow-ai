// Shared TypeScript interfaces for all API request/response shapes.
// These mirror the backend Pydantic models exactly (design §4.4).

export interface StudentProfile {
  name: string;
  department: string;
  specialization: string;
  year: number;
  section: string;
}

export interface DeadlineItem {
  label: string;
  date: string | null;
  original_date_text: string;
  description: string;
}

export interface RequiredActionItem {
  action: string;
  by: string | null;
  original_by_text: string | null;
  details: string | null;
}

export interface AffectedGroups {
  departments: (string | number)[];
  specializations: (string | number)[];
  years: (string | number)[];
  sections: (string | number)[];
}

export type RelevanceStatus = "RELEVANT" | "NOT_RELEVANT" | "UNCERTAIN";
export type Priority = "High" | "Medium" | "Low";

export interface Analysis {
  summary: string;
  what_changed: string;
  affected_groups: AffectedGroups;
  ambiguous_dimensions: string[];
  ambiguous_raw_text: Record<string, string>;
  deadlines: DeadlineItem[];
  required_actions: RequiredActionItem[];
  priority: Priority;
  priority_reason: string;
}

export interface RelevanceResult {
  relevance_status: RelevanceStatus;
  relevance_reason: string;
}

export interface ChecklistItem {
  id: string;
  description: string;
  deadline: string | null;
  deadline_text: string | null;
  completed: boolean;
}

export interface AnalyzeResponse {
  analysis: Analysis;
  relevance: RelevanceResult;
  checklist: ChecklistItem[];
}

export interface ApiError {
  detail: string;
  code: string;
}
