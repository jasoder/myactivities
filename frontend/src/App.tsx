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
      <header className="w-full border-b border-[#44475a]/60 bg-[#282a36]/90 backdrop-blur-md sticky top-0 z-30 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-md bg-[#bd93f9]/15 text-[#bd93f9] border border-[#bd93f9]/30">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight text-[#f8f8f2] leading-none">
                MyActivities
              </h1>
              <p className="text-[11px] text-[#6272a4] mt-0.5">{athlete.name || athlete.email}</p>
            </div>
          </div>

          <div className="text-xs font-mono text-[#6272a4]">
            {new Date().toLocaleDateString("en-US", {
              weekday: "short",
              month: "short",
              day: "numeric",
            })}
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
