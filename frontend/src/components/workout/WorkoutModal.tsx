import React, { useState } from "react";
import { useCreateActivity } from "../../hooks/useQueries";
import { X, Plus } from "lucide-react";
import { formatISODate } from "../../utils/date";

interface WorkoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultDate?: Date;
}

export const WorkoutModal: React.FC<WorkoutModalProps> = ({ isOpen, onClose, defaultDate }) => {
  const createMutation = useCreateActivity();
  const [name, setName] = useState("");
  const [sportType, setSportType] = useState("Run");
  const [plannedDate, setPlannedDate] = useState(
    defaultDate ? formatISODate(defaultDate) : formatISODate(new Date())
  );
  const [durationMin, setDurationMin] = useState(45);
  const [distanceKm, setDistanceKm] = useState<number | "">("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<"planned" | "completed">("planned");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(
      {
        name: name.trim() || `${sportType} Workout`,
        sport_type: sportType,
        status: status as any,
        planned_date: `${plannedDate}T09:00:00Z`,
        actual_date: status === "completed" ? `${plannedDate}T09:00:00Z` : undefined,
        duration_min: Number(durationMin),
        distance_m: distanceKm ? Number(distanceKm) * 1000 : undefined,
        description: description.trim() || undefined,
        source: "manual" as any,
      },
      {
        onSuccess: () => {
          onClose();
          setName("");
          setDescription("");
        },
      }
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[#282a36] border border-[#44475a] rounded-3xl p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#50fa7b]/20 text-[#50fa7b]">
              <Plus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#f8f8f2]">Add Workout</h3>
              <p className="text-xs text-[#6272a4]">Schedule or log an activity</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a] transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Workout Title</label>
            <input
              type="text"
              placeholder="e.g. Morning Easy Run, Sweet Spot Intervals"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#44475a]/50 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Sport</label>
              <select
                value={sportType}
                onChange={(e) => setSportType(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#44475a]/50 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9]"
              >
                <option value="Run">Run</option>
                <option value="Ride">Ride</option>
                <option value="Swim">Swim</option>
                <option value="Other">Cross-Training / Strength</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#44475a]/50 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9]"
              >
                <option value="planned">Planned</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Date</label>
              <input
                type="date"
                required
                value={plannedDate}
                onChange={(e) => setPlannedDate(e.target.value)}
                className="w-full px-2.5 py-2.5 rounded-xl bg-[#44475a]/50 border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Duration (min)</label>
              <input
                type="number"
                min={5}
                max={600}
                required
                value={durationMin}
                onChange={(e) => setDurationMin(Number(e.target.value))}
                className="w-full px-3 py-2.5 rounded-xl bg-[#44475a]/50 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9]"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Distance (km)</label>
              <input
                type="number"
                step="0.1"
                placeholder="Optional"
                value={distanceKm}
                onChange={(e) => setDistanceKm(e.target.value === "" ? "" : Number(e.target.value))}
                className="w-full px-3 py-2.5 rounded-xl bg-[#44475a]/50 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Notes or Goals</label>
            <textarea
              rows={2}
              placeholder="e.g. Keep HR under 145 bpm, practice fueling"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-[#44475a]/50 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9]"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-[#6272a4] hover:text-[#f8f8f2]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-5 py-2.5 rounded-xl bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36] font-semibold text-xs shadow-lg shadow-[#bd93f9]/20 transition-all disabled:opacity-50"
            >
              {createMutation.isPending ? "Adding..." : "Save Workout"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
