import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type ActivityCreate, type ActivityUpdate, type ConfirmPlanRequest } from "../api/client";

export function useActivities(startDate: string, endDate: string, enabled = true) {
  return useQuery({
    queryKey: ["activities", startDate, endDate],
    queryFn: async () => {
      const { data, error } = await api.GET("/myactivities/user/activities", {
        params: {
          query: {
            start_date: `${startDate}T00:00:00Z`,
            end_date: `${endDate}T23:59:59Z`,
          },
        },
      });
      if (error) throw new Error((error as any)?.detail || "Failed to fetch activities");
      return data?.events || [];
    },
    enabled: enabled && Boolean(startDate && endDate),
  });
}

export function useActivityDetail(activityId: string | null) {
  return useQuery({
    queryKey: ["activity-detail", activityId],
    queryFn: async () => {
      if (!activityId) return null;
      const { data, error } = await api.GET("/myactivities/activities/detail/{activity_id}", {
        params: { path: { activity_id: activityId } },
      });
      if (error) throw new Error((error as any)?.detail || "Failed to fetch activity");
      return data;
    },
    enabled: Boolean(activityId),
  });
}

export function useTrainingLoad(enabled = true) {
  return useQuery({
    queryKey: ["training-load"],
    queryFn: async () => {
      const { data, error } = await api.GET("/myactivities/ai/training-load");
      if (error) throw new Error((error as any)?.detail || "Failed to fetch training load");
      return data;
    },
    enabled,
  });
}

export function useWeeklyRecap(weekStart: string, enabled = true) {
  return useQuery({
    queryKey: ["weekly-recap", weekStart],
    queryFn: async () => {
      const { data, error } = await api.GET("/myactivities/ai/weekly-recap", {
        params: {
          query: { week_start: `${weekStart}T00:00:00Z`, duration_days: 7 },
        },
      });
      if (error) throw new Error((error as any)?.detail || "Failed to fetch weekly recap");
      return data;
    },
    enabled: enabled && Boolean(weekStart),
  });
}

export function useCreateActivity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newActivity: ActivityCreate) => {
      const { data, error } = await api.POST("/myactivities/activities/", {
        body: newActivity,
      });
      if (error) throw new Error((error as any)?.detail || "Failed to create activity");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["training-load"] });
    },
  });
}

export function useUpdateActivity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ activityId, update }: { activityId: string; update: ActivityUpdate }) => {
      const { data, error } = await api.PUT("/myactivities/activities/{activity_id}", {
        params: { path: { activity_id: activityId } },
        body: update,
      });
      if (error) throw new Error((error as any)?.detail || "Failed to update activity");
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["activity-detail", variables.activityId] });
      queryClient.invalidateQueries({ queryKey: ["training-load"] });
    },
  });
}

export function useDeleteActivity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (activityId: string) => {
      const { error } = await api.DELETE("/myactivities/activities/{activity_id}", {
        params: { path: { activity_id: activityId } },
      });
      if (error) throw new Error((error as any)?.detail || "Failed to delete activity");
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["training-load"] });
    },
  });
}

export function useGeneratePlan() {
  return useMutation({
    mutationFn: async ({ startDate, durationDays }: { startDate: string; durationDays: number }) => {
      const { data, error } = await api.POST("/myactivities/ai/generate-plan", {
        params: {
          query: {
            start_date: `${startDate}T00:00:00Z`,
            duration_days: durationDays,
          },
        },
      });
      if (error) throw new Error((error as any)?.detail || "Plan generation failed");
      return data as any;
    },
  });
}

export function useConfirmPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planPayload: ConfirmPlanRequest) => {
      const { data, error } = await api.POST("/myactivities/ai/confirm-plan", {
        body: planPayload,
      });
      if (error) throw new Error((error as any)?.detail || "Failed to confirm plan");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["training-load"] });
      queryClient.invalidateQueries({ queryKey: ["weekly-recap"] });
    },
  });
}

export function useSyncStrava() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/myactivities/strava/sync", {
        params: { query: { force: true, limit: 50 } },
      });
      if (error) throw new Error((error as any)?.detail || "Strava sync failed");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activities"] });
      queryClient.invalidateQueries({ queryKey: ["training-load"] });
    },
  });
}
