import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AuthScreen } from "./components/auth/AuthScreen";
import { CalendarStrip } from "./components/calendar/CalendarStrip";
import { BottomToolbar } from "./components/layout/BottomToolbar";
import { AIChatDrawer } from "./components/chat/AIChatDrawer";
import { TrainingLoadDrawer } from "./components/analytics/TrainingLoadDrawer";
import { SettingsDrawer } from "./components/settings/SettingsDrawer";
import { WorkoutModal } from "./components/workout/WorkoutModal";
import { Activity, Loader2 } from "lucide-react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 1,
    },
  },
});

const Dashboard: React.FC = () => {
  const { athlete, isLoading } = useAuth();
  const [isAIOpen, setIsAIOpen] = useState(false);
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAddWorkoutOpen, setIsAddWorkoutOpen] = useState(false);
  const [selectedAddDate, setSelectedAddDate] = useState<Date | undefined>(undefined);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#282a36] flex items-center justify-center text-[#bd93f9]">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (!athlete) {
    return <AuthScreen />;
  }

  const handleOpenAddWorkout = (date?: Date) => {
    setSelectedAddDate(date);
    setIsAddWorkoutOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#282a36] text-[#f8f8f2] flex flex-col pb-24">
      {/* Top Bar */}
      <header className="w-full border-b border-[#44475a]/40 bg-[#282a36]/80 backdrop-blur-md sticky top-0 z-30 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-xl bg-[#bd93f9]/20 text-[#bd93f9]">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-[#f8f8f2] leading-none">MyActivities</h1>
              <p className="text-[10px] text-[#6272a4] mt-0.5">{athlete.name || athlete.email}</p>
            </div>
          </div>

          {/* Strava status indicator */}
          <div className="flex items-center gap-2">
            {athlete.strava_connected ? (
              <span className="px-2.5 py-1 rounded-full bg-[#50fa7b]/15 text-[#50fa7b] text-[10px] font-semibold flex items-center gap-1 border border-[#50fa7b]/30">
                <span className="w-1.5 h-1.5 rounded-full bg-[#50fa7b]" /> Strava Synced
              </span>
            ) : (
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="px-2.5 py-1 rounded-full bg-[#44475a]/50 hover:bg-[#44475a] text-[#6272a4] hover:text-[#f8f8f2] text-[10px] font-medium transition-all"
              >
                + Connect Strava
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Calendar View */}
      <main className="flex-1">
        <CalendarStrip
          onOpenAI={() => setIsAIOpen(true)}
          onOpenAddWorkout={handleOpenAddWorkout}
        />
      </main>

      {/* Fixed Bottom Toolbar */}
      <BottomToolbar
        onOpenAI={() => setIsAIOpen(true)}
        onOpenAnalytics={() => setIsAnalyticsOpen(true)}
        onOpenAddWorkout={() => handleOpenAddWorkout()}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Modals & Drawers */}
      <AIChatDrawer isOpen={isAIOpen} onClose={() => setIsAIOpen(false)} />
      <TrainingLoadDrawer isOpen={isAnalyticsOpen} onClose={() => setIsAnalyticsOpen(false)} />
      <SettingsDrawer isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <WorkoutModal
        isOpen={isAddWorkoutOpen}
        onClose={() => setIsAddWorkoutOpen(false)}
        defaultDate={selectedAddDate}
      />
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Dashboard />
      </AuthProvider>
    </QueryClientProvider>
  );
}
