import createClient from "openapi-fetch";
import type { paths, components } from "./schema";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

// Create typed OpenAPI client
export const api = createClient<paths>({
  baseUrl: API_BASE_URL,
});

// Helper for managing auth tokens in headers
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

// Intercept requests to attach Bearer token automatically
api.use({
  async onRequest({ request }) {
    if (authToken) {
      request.headers.set("Authorization", `Bearer ${authToken}`);
    }
    return request;
  },
  async onResponse({ response }) {
    if (response.status === 401) {
      // Clear token on 401 unauthorized
      setAuthToken(null);
    }
    return response;
  },
});

// Convenient shortcut types
export type Schema<T extends keyof components["schemas"]> = components["schemas"][T];

export type Athlete = Schema<"AthleteRead">;
export type Activity = Schema<"ActivityRead">;
export type ActivitiesResponse = Schema<"ActivitiesResponse">;
export type ActivitiesEntry = Schema<"ActivitiesEntry">;
export type ActivityCreate = Schema<"ActivityCreate">;
export type ActivityUpdate = Schema<"ActivityUpdate">;
export type TrainingPreference = Schema<"TrainingPreferenceRead">;
export type TrainingPreferenceUpdate = Schema<"TrainingPreferenceUpdate">;
export type ConfirmPlanRequest = Schema<"ConfirmPlanRequest">;
