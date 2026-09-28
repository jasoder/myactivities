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
        return <span className="text-[10px] text-[#50fa7b] font-medium flex items-center gap-0.5"><CheckCircle2 className="w-2.5 h-2.5" /> Done</span>;
      case "missed":
        return <span className="text-[10px] text-[#ff5555] font-medium flex items-center gap-0.5"><AlertCircle className="w-2.5 h-2.5" /> Missed</span>;
      case "modified":
        return <span className="text-[10px] text-[#ffb86c] font-medium">Modified</span>;
      default:
        return <span className="text-[10px] text-[#8be9fd] font-medium">Planned</span>;
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
          <CalendarDays className="w-5 h-5 text-[#bd93f9]" />
          <h2 className="text-base sm:text-lg font-bold text-[#f8f8f2]">
            {formatDateLabel(currentMonday)} – {formatDateLabel(sunday)}
          </h2>
          {!isCurrentWeek && (
            <button
              onClick={handleResetToday}
              className="ml-2 px-2.5 py-1 rounded-lg bg-[#44475a]/60 hover:bg-[#44475a] text-[11px] font-medium text-[#8be9fd] flex items-center gap-1 transition-all"
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
            className="p-2 rounded-xl bg-[#44475a]/40 hover:bg-[#44475a] text-[#f8f8f2] transition-all"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleNextWeek}
            aria-label="Next week"
            className="p-2 rounded-xl bg-[#44475a]/40 hover:bg-[#44475a] text-[#f8f8f2] transition-all"
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
              className={`rounded-2xl border transition-all ${
                isToday
                  ? "bg-[#44475a]/40 border-[#bd93f9]/60 shadow-lg shadow-[#bd93f9]/5"
                  : "bg-[#44475a]/20 border-[#44475a]/40 hover:border-[#6272a4]/60"
              } p-3.5`}
            >
              <div className="flex items-center justify-between">
                {/* Day Header Info */}
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-9 h-9 rounded-xl flex flex-col items-center justify-center font-bold transition-all ${
                      isToday
                        ? "bg-[#bd93f9] text-[#282a36]"
                        : "bg-[#282a36] text-[#6272a4]"
                    }`}
                  >
                    <span className="text-[10px] uppercase leading-none font-semibold">
                      {DAY_NAMES[dayIdx]}
                    </span>
                    <span className="text-xs leading-none mt-0.5">{dayDate.getDate()}</span>
                  </div>

                  <span className="text-xs font-medium text-[#6272a4]">
                    {dayDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </span>
                </div>

                {/* Day Add Workout Trigger */}
                <button
                  onClick={() => onOpenAddWorkout(dayDate)}
                  className="p-1 rounded-lg text-[#6272a4] hover:text-[#bd93f9] hover:bg-[#44475a]/60 transition-all text-xs flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline text-[11px]">Add</span>
                </button>
              </div>

              {/* Day Workouts Cards */}
              <div className="mt-2.5 space-y-2">
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
                          className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                            isExpanded
                              ? "bg-[#282a36] border-[#bd93f9] shadow-md"
                              : "bg-[#282a36]/60 border-[#44475a]/60 hover:bg-[#282a36] hover:border-[#6272a4]"
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="p-1.5 rounded-lg bg-[#44475a]/50 shrink-0">
                              {getSportIcon(event.type)}
                            </div>
                            <div className="truncate">
                              <p className="text-xs font-semibold text-[#f8f8f2] truncate">
                                {event.title || "Untitled Activity"}
                              </p>
                              <div className="flex items-center gap-2 text-[11px] text-[#6272a4] mt-0.5">
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
                  <div className="py-2 text-center text-xs text-[#6272a4]/70 italic">
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
        <div className="mt-6 p-6 rounded-3xl bg-[#44475a]/20 border border-[#bd93f9]/20 text-center space-y-3">
          <div className="w-10 h-10 mx-auto rounded-2xl bg-[#bd93f9]/20 flex items-center justify-center text-[#bd93f9]">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#f8f8f2]">No workouts scheduled this week</h3>
            <p className="text-xs text-[#6272a4] mt-1 max-w-sm mx-auto">
              Tap "Ask AI" in the bottom dock to generate a periodized training block, or log an activity manually.
            </p>
          </div>
          <button
            onClick={onOpenAI}
            className="px-4 py-2 rounded-xl bg-[#bd93f9] text-[#282a36] font-semibold text-xs transition-all shadow-lg shadow-[#bd93f9]/20 hover:bg-[#caa5fb]"
          >
            Plan with AI Coach
          </button>
        </div>
      )}
    </div>
  );
};
