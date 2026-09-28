import React from "react";
import { Sparkles, TrendingUp, Plus, User } from "lucide-react";

interface BottomToolbarProps {
  onOpenAI: () => void;
  onOpenAnalytics: () => void;
  onOpenAddWorkout: () => void;
  onOpenSettings: () => void;
}

export const BottomToolbar: React.FC<BottomToolbarProps> = ({
  onOpenAI,
  onOpenAnalytics,
  onOpenAddWorkout,
  onOpenSettings,
}) => {
  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40">
      <nav
        aria-label="Bottom Navigation"
        className="flex items-center gap-1 p-1 rounded-lg bg-[#282a36]/95 border border-[#44475a]/80 shadow-xl backdrop-blur-md"
      >
        {/* AI Assistant */}
        <button
          onClick={onOpenAI}
          className="px-3 py-1.5 rounded-md text-xs font-medium text-[#bd93f9] hover:bg-[#bd93f9]/15 transition-all flex items-center gap-1.5"
          title="AI Coach Chat"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI Coach</span>
        </button>

        {/* Load / Analytics */}
        <button
          onClick={onOpenAnalytics}
          className="px-3 py-1.5 rounded-md text-xs font-medium text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/40 transition-all flex items-center gap-1.5"
          title="Training Load & Readiness"
        >
          <TrendingUp className="w-3.5 h-3.5 text-[#50fa7b]" />
          <span>Load</span>
        </button>

        {/* Add Workout (+) */}
        <button
          onClick={onOpenAddWorkout}
          className="p-1.5 rounded-md bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36] transition-all font-semibold"
          title="Add Workout"
          aria-label="Add Workout"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
        </button>

        {/* Athlete Profile & Preferences */}
        <button
          onClick={onOpenSettings}
          className="px-3 py-1.5 rounded-md text-xs font-medium text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/40 transition-all flex items-center gap-1.5"
          title="Athlete Profile, Goals & Preferences"
        >
          <User className="w-3.5 h-3.5 text-[#8be9fd]" />
          <span>Athlete</span>
        </button>
      </nav>
    </div>
  );
};
