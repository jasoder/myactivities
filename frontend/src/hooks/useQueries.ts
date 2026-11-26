import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  throwIfError,
  unwrap,
  type ActivityCreate,
  type ActivityUpdate,
  type ConfirmPlanRequest,
  type AthleteUpdate,
  type TrainingPreferenceUpdate,
} from "../api/client";

function useInvalidateCalendar() {
  const queryClient = useQueryClient();
  return (extraKeys: unknown[][] = []) => {
    queryClient.invalidateQueries({ queryKey: ["activities"] });
    queryClient.invalidateQueries({ queryKey: ["training-load"] });
    for (const key of extraKeys) {
      queryClient.invalidateQueries({ queryKey: key });
    }
  };
}

export function useActivities(startDate: string, endDate: string, enabled = true) {
  return useQuery({
    queryKey: ["activities", startDate, endDate],
    queryFn: async () => {
      const res = await api.GET("/myactivities/user/activities", {
        params: {
          query: {
            start_date: `${startDate}T00:00:00Z`,
            end_date: `${endDate}T23:59:59Z`,
          },
        },
      });
      return unwrap(res, "Failed to fetch activities").events || [];
    },
    enabled: enabled && Boolean(startDate && endDate),
  });
}

export function useActivityDetail(activityId: string | null) {
  return useQuery({
    queryKey: ["activity-detail", activityId],
    queryFn: async () => {
      if (!activityId) return null;
      const res = await api.GET("/myactivities/activities/detail/{activity_id}", {
        params: { path: { activity_id: activityId } },
      });
      return unwrap(res, "Failed to fetch activity");
    },
    enabled: Boolean(activityId),
  });
}

export function useTrainingLoad(enabled = true) {
  return useQuery({
    queryKey: ["training-load"],
    queryFn: async () => {
      const res = await api.GET("/myactivities/ai/training-load");
      return unwrap(res, "Failed to fetch training load");
    },
    enabled,
  });
}

export function useWeeklyRecap(weekStart: string, enabled = true) {
  return useQuery({
    queryKey: ["weekly-recap", weekStart],
    queryFn: async () => {
      const res = await api.GET("/myactivities/ai/weekly-recap", {
        params: {
          query: { week_start: `${weekStart}T00:00:00Z`, duration_days: 7 },
        },
      });
      return unwrap(res, "Failed to fetch weekly recap");
    },
    enabled: enabled && Boolean(weekStart),
  });
}

export function useCreateActivity() {
  const invalidate = useInvalidateCalendar();
  return useMutation({
    mutationFn: async (newActivity: ActivityCreate) =>
      unwrap(
        await api.POST("/myactivities/activities/", { body: newActivity }),
        "Failed to create activity"
      ),
    onSuccess: () => invalidate(),
  });
}

export function useUpdateActivity() {
  const invalidate = useInvalidateCalendar();
  return useMutation({
    mutationFn: async ({ activityId, update }: { activityId: string; update: ActivityUpdate }) =>
      unwrap(
        await api.PUT("/myactivities/activities/{activity_id}", {
          params: { path: { activity_id: activityId } },
          body: update,
        }),
        "Failed to update activity"
      ),
    onSuccess: (_, variables) => invalidate([["activity-detail", variables.activityId]]),
  });
}

export function useDeleteActivity() {
  const invalidate = useInvalidateCalendar();
  return useMutation({
    mutationFn: async (activityId: string) => {
      const { error } = await api.DELETE("/myactivities/activities/{activity_id}", {
        params: { path: { activity_id: activityId } },
      });
      throwIfError(error, "Failed to delete activity");
      return true;
    },
    onSuccess: () => invalidate(),
  });
}

export function useGeneratePlan() {
  return useMutation({
    mutationFn: async ({
      startDate,
      durationDays,
      prompt,
    }: {
      startDate: string;
      durationDays: number;
      prompt?: string;
    }) => {
      const res = await api.POST("/myactivities/ai/generate-plan", {
        params: {
          query: {
            start_date: `${startDate}T00:00:00Z`,
            duration_days: durationDays,
            user_prompt: prompt || undefined,
          },
        },
      });
      return unwrap(res, "Plan generation failed") as Record<string, any>;
    },
  });
}

export function useConfirmPlan() {
  const invalidate = useInvalidateCalendar();
  return useMutation({
    mutationFn: async (planPayload: ConfirmPlanRequest) =>
      unwrap(
        await api.POST("/myactivities/ai/confirm-plan", { body: planPayload }),
        "Failed to confirm plan"
      ),
    onSuccess: () => invalidate([["weekly-recap"]]),
  });
}

export function useSyncStrava() {
  const invalidate = useInvalidateCalendar();
  return useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/myactivities/strava/sync", {
          params: { query: { force: true, limit: 50 } },
        }),
        "Strava sync failed"
      ),
    onSuccess: () => invalidate(),
  });
}

export function useTrainingPreferences(enabled = true) {
  return useQuery({
    queryKey: ["user-preferences"],
    queryFn: async () =>
      unwrap(
        await api.GET("/myactivities/user/preferences"),
        "Failed to fetch preferences"
      ),
    enabled,
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (prefs: TrainingPreferenceUpdate) =>
      unwrap(
        await api.PUT("/myactivities/user/preferences", { body: prefs }),
        "Failed to update preferences"
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-preferences"] });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (profile: AthleteUpdate) =>
      unwrap(
        await api.PUT("/myactivities/user", { body: profile }),
        "Failed to update profile"
      ),
    onSuccess: (updatedAthlete) => {
      queryClient.setQueryData(["user-profile"], updatedAthlete);
      queryClient.invalidateQueries({ queryKey: ["user-profile"] });
    },
  });
}
