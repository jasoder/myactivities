import React, { useState, useRef } from "react";
import {
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Sparkles,
  Plus,
  Bike,
  Footprints,
  Waves,
  Dumbbell,
  CheckCircle2,
  AlertCircle,
  CalendarDays
} from "lucide-react";
import { useActivities } from "../../hooks/useQueries";
import { WorkoutDetailInline } from "../workout/WorkoutDetailInline";
import {
  getMonday,
  addDays,
  formatISODate,
  formatDateLabel,
  isSameDay,
  DAY_NAMES
} from "../../utils/date";

interface CalendarStripProps {
  onOpenAI: () => void;
  onOpenAddWorkout: (date: Date) => void;
}

export const CalendarStrip: React.FC<CalendarStripProps> = ({ onOpenAI, onOpenAddWorkout }) => {
  const [currentMonday, setCurrentMonday] = useState<Date>(() => getMonday(new Date()));
  const [expandedActivityId, setExpandedActivityId] = useState<string | null>(null);

  // Swipe gesture tracking
  const touchStartX = useRef<number | null>(null);
  const touchEndX = useRef<number | null>(null);

  const sunday = addDays(currentMonday, 6);
  const startDateStr = formatISODate(currentMonday);
  const endDateStr = formatISODate(sunday);

  const { data: events = [], isLoading } = useActivities(startDateStr, endDateStr);

  const isCurrentWeek = isSameDay(currentMonday, getMonday(new Date()));

  const handlePrevWeek = () => {
    setCurrentMonday((prev) => addDays(prev, -7));
    setExpandedActivityId(null);
  };

  const handleNextWeek = () => {
    setCurrentMonday((prev) => addDays(prev, 7));
    setExpandedActivityId(null);
  };

  const handleResetToday = () => {
    setCurrentMonday(getMonday(new Date()));
    setExpandedActivityId(null);
  };

  // Touch Swipe handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.targetTouches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.targetTouches[0].clientX;
  };

  const handleTouchEnd = () => {
    if (!touchStartX.current || !touchEndX.current) return;
    const diff = touchStartX.current - touchEndX.current;
    if (diff > 50) {
      handleNextWeek(); // swiped left
    } else if (diff < -50) {
      handlePrevWeek(); // swiped right
    }
    touchStartX.current = null;
    touchEndX.current = null;
  };

  const days = Array.from({ length: 7 }).map((_, idx) => addDays(currentMonday, idx));

  const getSportIcon = (type?: string | null) => {
    const t = (type || "").toLowerCase();
    if (t.includes("run")) return <Footprints className="w-3.5 h-3.5 text-[#50fa7b]" />;
    if (t.includes("ride") || t.includes("bike") || t.includes("cycle"))
      return <Bike className="w-3.5 h-3.5 text-[#8be9fd]" />;
    if (t.includes("swim")) return <Waves className="w-3.5 h-3.5 text-[#bd93f9]" />;
    return <Dumbbell className="w-3.5 h-3.5 text-[#ffb86c]" />;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="text-[10px] text-[#50fa7b] bg-[#50fa7b]/10 border border-[#50fa7b]/30 px-1.5 py-0.5 rounded font-mono flex items-center gap-1">
            <CheckCircle2 className="w-2.5 h-2.5" /> Done
          </span>
        );
      case "missed":
        return (
          <span className="text-[10px] text-[#ff5555] bg-[#ff5555]/10 border border-[#ff5555]/30 px-1.5 py-0.5 rounded font-mono flex items-center gap-1">
            <AlertCircle className="w-2.5 h-2.5" /> Missed
          </span>
        );
      case "modified":
        return (
          <span className="text-[10px] text-[#ffb86c] bg-[#ffb86c]/10 border border-[#ffb86c]/30 px-1.5 py-0.5 rounded font-mono">
            Modified
          </span>
        );
      default:
        return (
          <span className="text-[10px] text-[#8be9fd] bg-[#8be9fd]/10 border border-[#8be9fd]/30 px-1.5 py-0.5 rounded font-mono">
            Planned
          </span>
        );
    }
  };

  return (
    <div
      className="w-full max-w-4xl mx-auto px-4 py-6"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Calendar Header Navigation */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <CalendarDays className="w-4 h-4 text-[#bd93f9]" />
          <h2 className="text-sm sm:text-base font-semibold text-[#f8f8f2]">
            {formatDateLabel(currentMonday)} – {formatDateLabel(sunday)}
          </h2>
          {!isCurrentWeek && (
            <button
              onClick={handleResetToday}
              className="ml-2 px-2 py-0.5 rounded-md bg-[#44475a]/60 hover:bg-[#44475a] text-[11px] font-mono text-[#8be9fd] flex items-center gap-1 transition-all border border-[#44475a]"
            >
              <RotateCcw className="w-3 h-3" />
              Today
            </button>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handlePrevWeek}
            aria-label="Previous week"
            className="p-1.5 rounded-md bg-[#44475a]/40 hover:bg-[#44475a] text-[#f8f8f2] transition-all border border-[#44475a]/60"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleNextWeek}
            aria-label="Next week"
            className="p-1.5 rounded-md bg-[#44475a]/40 hover:bg-[#44475a] text-[#f8f8f2] transition-all border border-[#44475a]/60"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 7-Day Microcycle Strip */}
      <div className="space-y-2.5">
        {days.map((dayDate, dayIdx) => {
          const isToday = isSameDay(dayDate, new Date());
          const dateISO = formatISODate(dayDate);

          // Find activities matching this day
          const dayEvents = events.filter((ev) => {
            const evDate = new Date(ev.date);
            return isSameDay(evDate, dayDate);
          });

          return (
            <div
              key={dateISO}
              className={`rounded-lg border transition-all ${
                isToday
                  ? "bg-[#44475a]/30 border-[#bd93f9]/50 shadow-sm"
                  : "bg-[#44475a]/15 border-[#44475a]/50 hover:border-[#6272a4]/50"
              } p-3`}
            >
              <div className="flex items-center justify-between">
                {/* Day Header Info */}
                <div className="flex items-center gap-2">
                  <div
                    className={`w-8 h-8 rounded-md flex flex-col items-center justify-center font-mono font-bold transition-all ${
                      isToday
                        ? "bg-[#bd93f9] text-[#282a36]"
                        : "bg-[#1e1f29] text-[#6272a4] border border-[#44475a]/60"
                    }`}
                  >
                    <span className="text-[9px] uppercase leading-none font-semibold">
                      {DAY_NAMES[dayIdx]}
                    </span>
                    <span className="text-xs leading-none mt-0.5">{dayDate.getDate()}</span>
                  </div>

                  <span className="text-xs font-mono text-[#6272a4]">
                    {dayDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </span>
                </div>

                {/* Day Add Workout Trigger */}
                <button
                  onClick={() => onOpenAddWorkout(dayDate)}
                  className="px-1.5 py-1 rounded text-[#6272a4] hover:text-[#bd93f9] hover:bg-[#44475a]/50 transition-all text-xs flex items-center gap-1 border border-transparent hover:border-[#44475a]"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline text-[11px]">Add</span>
                </button>
              </div>

              {/* Day Workouts Cards */}
              <div className="mt-2 space-y-1.5">
                {dayEvents.length > 0 ? (
                  dayEvents.map((event) => {
                    const isExpanded = expandedActivityId === event.id;
                    const durationMin = event.data?.duration_s
                      ? Math.round(event.data.duration_s / 60)
                      : null;
                    const distanceKm = event.data?.distance_m
                      ? (event.data.distance_m / 1000).toFixed(1)
                      : null;

                    return (
                      <div key={event.id} className="w-full">
                        <button
                          type="button"
                          onClick={() => setExpandedActivityId(isExpanded ? null : event.id)}
                          className={`w-full text-left p-2.5 rounded-md border transition-all flex items-center justify-between gap-3 ${
                            isExpanded
                              ? "bg-[#1e1f29] border-[#bd93f9]/70 shadow-sm"
                              : "bg-[#1e1f29]/70 border-[#44475a]/60 hover:bg-[#1e1f29] hover:border-[#6272a4]/70"
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="p-1 rounded bg-[#44475a]/40 shrink-0">
                              {getSportIcon(event.type)}
                            </div>
                            <div className="truncate">
                              <p className="text-xs font-medium text-[#f8f8f2] truncate">
                                {event.title || "Untitled Activity"}
                              </p>
                              <div className="flex items-center gap-2 text-[10px] font-mono text-[#6272a4] mt-0.5">
                                {durationMin && <span>{durationMin} min</span>}
                                {distanceKm && <span>{distanceKm} km</span>}
                              </div>
                            </div>
                          </div>

                          <div className="shrink-0">{getStatusBadge(event.status)}</div>
                        </button>

                        {/* Inline Detail Expansion */}
                        {isExpanded && (
                          <WorkoutDetailInline
                            activityId={event.id}
                            onClose={() => setExpandedActivityId(null)}
                          />
                        )}
                      </div>
                    );
                  })
                ) : (
                  <div className="py-1.5 text-center text-[11px] text-[#6272a4]/70 italic">
                    Rest or unstructured day
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State Banner (if entire week has 0 events) */}
      {!isLoading && events.length === 0 && (
        <div className="mt-6 p-5 rounded-lg bg-[#44475a]/15 border border-[#bd93f9]/20 text-center space-y-3">
          <div className="w-9 h-9 mx-auto rounded-md bg-[#bd93f9]/15 flex items-center justify-center text-[#bd93f9] border border-[#bd93f9]/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-[#f8f8f2]">No workouts scheduled this week</h3>
            <p className="text-[11px] text-[#6272a4] mt-1 max-w-sm mx-auto">
              Tap "AI Coach" in the bottom dock to generate a periodized training block, or log an activity manually.
            </p>
          </div>
          <button
            onClick={onOpenAI}
            className="px-3.5 py-1.5 rounded-md bg-[#bd93f9] text-[#282a36] font-medium text-xs transition-all hover:bg-[#caa5fb]"
          >
            Plan with AI Coach
          </button>
        </div>
      )}
    </div>
  );
};
