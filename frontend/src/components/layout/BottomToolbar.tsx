import React from "react";
import { Sparkles, Activity, Plus, Settings } from "lucide-react";

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
    <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40">
      <nav aria-label="Bottom Navigation" className="flex items-center gap-1.5 p-1.5 rounded-2xl bg-[#282a36]/90 border border-[#44475a] shadow-2xl backdrop-blur-xl">
        {/* AI Assistant */}
        <button
          onClick={onOpenAI}
          className="px-3.5 py-2 rounded-xl text-xs font-semibold text-[#bd93f9] hover:bg-[#bd93f9]/15 transition-all flex items-center gap-1.5"
        >
          <Sparkles className="w-4 h-4" />
          <span>Ask AI</span>
        </button>

        {/* Load / Analytics */}
        <button
          onClick={onOpenAnalytics}
          className="px-3 py-2 rounded-xl text-xs font-medium text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/40 transition-all flex items-center gap-1.5"
        >
          <Activity className="w-4 h-4 text-[#50fa7b]" />
          <span>Load</span>
        </button>

        {/* Add Workout (+) */}
        <button
          onClick={onOpenAddWorkout}
          className="p-2.5 rounded-xl bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36] shadow-lg shadow-[#bd93f9]/25 transition-all"
          title="Add Workout"
          aria-label="Add Workout"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
        </button>

        {/* Strava & Settings */}
        <button
          onClick={onOpenSettings}
          className="px-3 py-2 rounded-xl text-xs font-medium text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/40 transition-all flex items-center gap-1.5"
        >
          <Settings className="w-4 h-4 text-[#8be9fd]" />
          <span>Settings</span>
        </button>
      </nav>
    </div>
  );
};
