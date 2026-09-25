// CampusFlow AI — Backend API service.
//
// All HTTP access to the backend is isolated here (design §2.1, §14).
// Components never call axios/fetch directly, and the frontend only ever talks
// to our backend — never to Gemini. The Gemini API key lives only on the
// backend and is never referenced here.

import axios from "axios";

import type { AnalyzeResponse, ApiError, StudentProfile } from "../types";

// A request that has not completed within 30 seconds is treated as timed out
// by the frontend (FR-03).
const REQUEST_TIMEOUT_MS = 30000;

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: { "Content-Type": "application/json" },
});

/**
 * Send an announcement and student profile to the backend for analysis.
 *
 * @throws Error with a user-friendly message on timeout, HTTP error, or
 *         network failure.
 */
export async function analyzeAnnouncement(
  announcementText: string,
  profile: StudentProfile,
): Promise<AnalyzeResponse> {
  try {
    const response = await apiClient.post<AnalyzeResponse>("/api/v1/analyze", {
      announcement_text: announcementText,
      student_profile: profile,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // Frontend timeout (request aborted after REQUEST_TIMEOUT_MS).
      if (error.code === "ECONNABORTED") {
        throw new Error(
          "The request took too long and timed out. Please try again.",
        );
      }

      // The backend responded with an error status: surface its message/code.
      if (error.response) {
        const data = error.response.data as Partial<ApiError> | undefined;
        const detail = data?.detail ?? "The analysis failed. Please try again.";
        const code = data?.code ?? "UNKNOWN_ERROR";
        throw new Error(`${detail} (${code})`);
      }

      // No response received — a network/connectivity problem.
      throw new Error(
        "Could not reach the server. Please check your connection and try again.",
      );
    }

    // Non-Axios error — rethrow a generic message.
    throw new Error("An unexpected error occurred. Please try again.");
  }
}
