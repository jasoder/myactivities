import React, { useState } from "react";
import { useCreateActivity } from "../../hooks/useQueries";
import { Plus } from "lucide-react";
import { formatISODate } from "../../utils/date";
import { ModalDrawer } from "../layout/ModalDrawer";

interface WorkoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultDate?: Date;
}

export const WorkoutModal: React.FC<WorkoutModalProps> = ({ isOpen, onClose, defaultDate }) => {
  const createMutation = useCreateActivity();
  const [name, setName] = useState("");
  const [sportType, setSportType] = useState("Run");
  const [plannedDate, setPlannedDate] = useState(() => formatISODate(defaultDate || new Date()));
  const [durationMin, setDurationMin] = useState(45);
  const [distanceKm, setDistanceKm] = useState<number | "">("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<"planned" | "completed">("planned");

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
    <ModalDrawer
      isOpen={isOpen}
      onClose={onClose}
      title="Add Workout"
      subtitle="Schedule or record an activity"
      icon={<Plus className="w-4 h-4" />}
      iconClassName="bg-[#50fa7b]/15 text-[#50fa7b] border-[#50fa7b]/30"
      panelClassName="max-w-md rounded-lg"
      alignBottomOnMobile={false}
    >
      <form onSubmit={handleSubmit} className="p-5 space-y-3.5">
        <div>
          <label className="block text-xs font-medium text-[#6272a4] mb-1">Workout Title</label>
          <input
            type="text"
            placeholder="e.g. Morning Easy Run, Sweet Spot Intervals"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1">Sport</label>
            <select
              value={sportType}
              onChange={(e) => setSportType(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
            >
              <option value="Run">Run</option>
              <option value="Ride">Ride</option>
              <option value="Swim">Swim</option>
              <option value="WeightTraining">Strength</option>
              <option value="Walk">Walk</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as "planned" | "completed")}
              className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
            >
              <option value="planned">Planned</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1">Date</label>
            <input
              type="date"
              required
              value={plannedDate}
              onChange={(e) => setPlannedDate(e.target.value)}
              className="w-full px-2 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1">Duration (min)</label>
            <input
              type="number"
              min={5}
              max={600}
              required
              value={durationMin}
              onChange={(e) => setDurationMin(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1">Distance (km)</label>
            <input
              type="number"
              step="0.1"
              placeholder="Optional"
              value={distanceKm}
              onChange={(e) => setDistanceKm(e.target.value === "" ? "" : Number(e.target.value))}
              className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-[#6272a4] mb-1">Notes or Goals</label>
          <textarea
            rows={2}
            placeholder="Target heart rate zone, intervals, notes..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
          />
        </div>

        <div className="pt-2 flex items-center justify-end gap-2 border-t border-[#44475a]/60">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-md text-xs text-[#6272a4] hover:text-[#f8f8f2] transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-1.5 rounded-md bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36] font-medium text-xs transition-all disabled:opacity-50"
          >
            {createMutation.isPending ? "Adding..." : "Add Activity"}
          </button>
        </div>
      </form>
    </ModalDrawer>
  );
};
