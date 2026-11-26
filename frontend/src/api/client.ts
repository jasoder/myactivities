import createClient from "openapi-fetch";
import type { paths, components } from "./schema";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const api = createClient<paths>({
  baseUrl: API_BASE_URL,
});

let authToken: string | null = localStorage.getItem("auth_token");

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem("auth_token", token);
  } else {
    localStorage.removeItem("auth_token");
  }
};

export const getAuthToken = () => authToken;

api.use({
  async onRequest({ request }) {
    if (authToken) {
      request.headers.set("Authorization", `Bearer ${authToken}`);
    }
    return request;
  },
  async onResponse({ response }) {
    if (response.status === 401) {
      setAuthToken(null);
    }
    return response;
  },
});

export function throwIfError(error: unknown, fallbackMessage: string): void {
  if (!error) return;
  const detail = (error as { detail?: string | Array<{ msg?: string }> })?.detail;
  const message = Array.isArray(detail) ? detail[0]?.msg : detail;
  throw new Error(message || fallbackMessage);
}

export function unwrap<T>(
  result: { data?: T; error?: unknown },
  fallbackMessage: string
): T {
  throwIfError(result.error, fallbackMessage);
  if (result.data === undefined) {
    throw new Error(fallbackMessage);
  }
  return result.data;
}

type Schema<T extends keyof components["schemas"]> = components["schemas"][T];

export type Athlete = Schema<"AthleteRead">;
export type AthleteUpdate = Schema<"AthleteUpdate">;
export type ActivityCreate = Schema<"ActivityCreate">;
export type ActivityUpdate = Schema<"ActivityUpdate">;
export type TrainingPreferenceUpdate = Schema<"TrainingPreferenceUpdate">;
export type ConfirmPlanRequest = Schema<"ConfirmPlanRequest">;
