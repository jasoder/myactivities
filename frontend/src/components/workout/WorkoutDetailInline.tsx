import React, { useState } from "react";
import { useActivityDetail, useDeleteActivity, useUpdateActivity } from "../../hooks/useQueries";
import {
  Clock,
  Gauge,
  Heart,
  Zap,
  Trash2,
  Calendar,
  Sparkles,
  ChevronUp,
  CheckCircle2,
  Circle,
  AlertCircle
} from "lucide-react";
import { formatISODate } from "../../utils/date";

interface WorkoutDetailInlineProps {
  activityId: string;
  onClose: () => void;
}

export const WorkoutDetailInline: React.FC<WorkoutDetailInlineProps> = ({ activityId, onClose }) => {
  const { data: activity, isLoading } = useActivityDetail(activityId);
  const deleteMutation = useDeleteActivity();
  const updateMutation = useUpdateActivity();
  const [isEditingDate, setIsEditingDate] = useState(false);
  const [newDate, setNewDate] = useState("");

  if (isLoading) {
    return (
      <div className="p-3 bg-[#1e1f29] rounded-md border border-[#44475a] text-center text-xs text-[#6272a4] animate-pulse">
        Loading workout details...
      </div>
    );
  }

  if (!activity) return null;

  const metrics = activity.metrics;
  const structure = (activity.plan_metadata as any)?.structure;
  const reasoning = (activity.plan_metadata as any)?.reasoning as string | undefined;

  const handleStatusToggle = (newStatus: "planned" | "completed" | "missed") => {
    updateMutation.mutate({
      activityId,
      update: {
        status: newStatus as any,
        actual_date: newStatus === "completed" ? new Date().toISOString() : undefined,
      },
    });
  };

  const handleDateReschedule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDate) return;
    updateMutation.mutate({
      activityId,
      update: {
        planned_date: `${newDate}T09:00:00Z`,
      },
    });
    setIsEditingDate(false);
  };

  return (
    <div className="mt-2 p-3 bg-[#1e1f29] rounded-md border border-[#44475a] text-left shadow-md space-y-3">
      {/* Header bar */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#44475a]/70 text-[#8be9fd]">
            {activity.sport_type || "Workout"}
          </span>
          <h4 className="text-xs font-semibold text-[#f8f8f2] mt-1">{activity.name || "Untitled"}</h4>
          {activity.description && (
            <p className="text-[11px] text-[#6272a4] mt-0.5">{activity.description}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/60 transition-all"
          aria-label="Collapse details"
        >
          <ChevronUp className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Quick Status Bar */}
      <div className="flex items-center gap-1.5 pt-1">
        <button
          onClick={() => handleStatusToggle("completed")}
          className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
            activity.status === "completed"
              ? "bg-[#50fa7b]/20 text-[#50fa7b] border border-[#50fa7b]/40"
              : "bg-[#282a36] text-[#6272a4] hover:text-[#f8f8f2] border border-[#44475a]/60"
          }`}
        >
          <CheckCircle2 className="w-3 h-3" />
          <span>Completed</span>
        </button>
        <button
          onClick={() => handleStatusToggle("planned")}
          className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
            activity.status === "planned"
              ? "bg-[#8be9fd]/20 text-[#8be9fd] border border-[#8be9fd]/40"
              : "bg-[#282a36] text-[#6272a4] hover:text-[#f8f8f2] border border-[#44475a]/60"
          }`}
        >
          <Circle className="w-3 h-3" />
          <span>Planned</span>
        </button>
        <button
          onClick={() => handleStatusToggle("missed")}
          className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
            activity.status === "missed"
              ? "bg-[#ff5555]/20 text-[#ff5555] border border-[#ff5555]/40"
              : "bg-[#282a36] text-[#6272a4] hover:text-[#f8f8f2] border border-[#44475a]/60"
          }`}
        >
          <AlertCircle className="w-3 h-3" />
          <span>Missed</span>
        </button>
      </div>

      {/* Target/Completed Telemetry Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[#44475a]/40">
        <div className="bg-[#282a36] p-2 rounded border border-[#44475a]/50">
          <div className="flex items-center gap-1 text-[10px] text-[#6272a4]">
            <Clock className="w-3 h-3 text-[#bd93f9]" /> Duration
          </div>
          <p className="text-xs font-mono font-semibold text-[#f8f8f2] mt-0.5">
            {metrics?.duration_min || activity.duration_min || 0} min
          </p>
        </div>

        <div className="bg-[#282a36] p-2 rounded border border-[#44475a]/50">
          <div className="flex items-center gap-1 text-[10px] text-[#6272a4]">
            <Gauge className="w-3 h-3 text-[#50fa7b]" /> Distance
          </div>
          <p className="text-xs font-mono font-semibold text-[#f8f8f2] mt-0.5">
            {metrics?.distance_m
              ? `${(metrics.distance_m / 1000).toFixed(1)} km`
              : activity.distance_m
              ? `${(activity.distance_m / 1000).toFixed(1)} km`
              : "—"}
          </p>
        </div>

        <div className="bg-[#282a36] p-2 rounded border border-[#44475a]/50">
          <div className="flex items-center gap-1 text-[10px] text-[#6272a4]">
            <Heart className="w-3 h-3 text-[#ff79c6]" /> Heart Rate
          </div>
          <p className="text-xs font-mono font-semibold text-[#f8f8f2] mt-0.5">
            {metrics?.average_hr_bpm ? `${Math.round(metrics.average_hr_bpm)} bpm` : "—"}
          </p>
        </div>

        <div className="bg-[#282a36] p-2 rounded border border-[#44475a]/50">
          <div className="flex items-center gap-1 text-[10px] text-[#6272a4]">
            <Zap className="w-3 h-3 text-[#ffb86c]" /> Power / Load
          </div>
          <p className="text-xs font-mono font-semibold text-[#f8f8f2] mt-0.5">
            {metrics?.average_power_w
              ? `${Math.round(metrics.average_power_w)} W`
              : activity.intensity
              ? `${activity.intensity}%`
              : "—"}
          </p>
        </div>
      </div>

      {/* Structured Interval Breakdown (if planned by AI or template) */}
      {structure && (
        <div className="space-y-1.5 pt-2 border-t border-[#44475a]/40">
          <h5 className="text-[10px] font-mono uppercase tracking-wider text-[#bd93f9]">
            Structured Workout Steps
          </h5>
          <div className="space-y-1 text-xs">
            {structure.warmup && (
              <div className="p-1.5 rounded bg-[#282a36] border border-[#44475a]/40 flex justify-between">
                <span className="text-[#6272a4]">Warmup</span>
                <span className="text-[#f8f8f2]">
                  {structure.warmup.duration_min}m ({structure.warmup.description})
                </span>
              </div>
            )}
            {structure.main_set?.map((step: any, idx: number) => (
              <div
                key={idx}
                className="p-1.5 rounded bg-[#bd93f9]/10 border border-[#bd93f9]/20 flex justify-between"
              >
                <span className="text-[#bd93f9] font-medium">
                  Set {idx + 1}: {step.intervals}x {step.duration_min}m
                </span>
                <span className="text-[#f8f8f2]">{step.intensity}</span>
              </div>
            ))}
            {structure.cooldown && (
              <div className="p-1.5 rounded bg-[#282a36] border border-[#44475a]/40 flex justify-between">
                <span className="text-[#6272a4]">Cooldown</span>
                <span className="text-[#f8f8f2]">
                  {structure.cooldown.duration_min}m ({structure.cooldown.description})
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Coach Reasoning */}
      {reasoning && (
        <div className="p-2 rounded bg-[#bd93f9]/10 border border-[#bd93f9]/30 text-xs text-[#bd93f9] flex items-start gap-2">
          <Sparkles className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <span className="font-semibold text-[#f8f8f2]">Coach notes:</span> {reasoning}
          </p>
        </div>
      )}

      {/* Reschedule & Delete Actions */}
      <div className="pt-2 border-t border-[#44475a]/40 flex items-center justify-between gap-2">
        {isEditingDate ? (
          <form onSubmit={handleDateReschedule} className="flex items-center gap-2">
            <input
              type="date"
              required
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
              className="px-2 py-1 text-xs rounded bg-[#282a36] text-[#f8f8f2] border border-[#6272a4] focus:outline-none"
            />
            <button
              type="submit"
              className="px-2 py-1 text-xs font-semibold bg-[#bd93f9] text-[#282a36] rounded"
            >
              Move
            </button>
            <button
              type="button"
              onClick={() => setIsEditingDate(false)}
              className="text-xs text-[#6272a4] hover:text-[#f8f8f2]"
            >
              Cancel
            </button>
          </form>
        ) : (
          <button
            onClick={() => {
              setNewDate(
                activity.planned_date
                  ? formatISODate(new Date(activity.planned_date))
                  : formatISODate(new Date())
              );
              setIsEditingDate(true);
            }}
            className="text-xs text-[#6272a4] hover:text-[#bd93f9] flex items-center gap-1.5 transition-all"
          >
            <Calendar className="w-3.5 h-3.5" />
            Reschedule
          </button>
        )}

        <button
          onClick={() => {
            if (confirm("Delete this workout?")) {
              deleteMutation.mutate(activityId);
              onClose();
            }
          }}
          className="text-xs text-[#ff5555]/80 hover:text-[#ff5555] flex items-center gap-1 transition-all"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Delete
        </button>
      </div>
    </div>
  );
};
