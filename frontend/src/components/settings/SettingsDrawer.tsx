import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import {
  useSyncStrava,
  useTrainingPreferences,
  useUpdatePreferences,
  useUpdateProfile
} from "../../hooks/useQueries";
import {
  X,
  RefreshCw,
  Unlink,
  LogOut,
  CheckCircle2,
  ExternalLink,
  User,
  Target,
  Gauge,
  Sliders,
  Save,
  Check
} from "lucide-react";
import { api } from "../../api/client";

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const AVAILABLE_SPORTS = ["Run", "Ride", "Swim", "WeightTraining", "Walk", "Rowing"];
const WEEKDAYS = [
  { key: "Monday", label: "Mon" },
  { key: "Tuesday", label: "Tue" },
  { key: "Wednesday", label: "Wed" },
  { key: "Thursday", label: "Thu" },
  { key: "Friday", label: "Fri" },
  { key: "Saturday", label: "Sat" },
  { key: "Sunday", label: "Sun" },
];

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({ isOpen, onClose }) => {
  const { athlete, logout, refreshProfile } = useAuth();
  const syncMutation = useSyncStrava();
  const { data: preferences } = useTrainingPreferences(isOpen);
  const updatePreferencesMutation = useUpdatePreferences();
  const updateProfileMutation = useUpdateProfile();

  const [activeTab, setActiveTab] = useState<"goals" | "metrics" | "integrations">("goals");

  // Goals & Training Preferences State
  const [weeklyHours, setWeeklyHours] = useState<number | "">("");
  const [maxDaysPerWeek, setMaxDaysPerWeek] = useState<number>(6);
  const [restDays, setRestDays] = useState<string[]>([]);
  const [selectedSports, setSelectedSports] = useState<string[]>([]);
  const [splitNotes, setSplitNotes] = useState<string>("");

  // Performance Metrics State
  const [athleteName, setAthleteName] = useState<string>("");
  const [weightKg, setWeightKg] = useState<number | "">("");
  const [ftpWatts, setFtpWatts] = useState<number | "">("");
  const [maxHrBpm, setMaxHrBpm] = useState<number | "">("");
  const [lthrBpm, setLthrBpm] = useState<number | "">("");
  const [thresholdPaceMinKm, setThresholdPaceMinKm] = useState<number | "">("");

  // Save feedback
  const [isSaved, setIsSaved] = useState(false);

  // Sync state from athlete & preferences
  useEffect(() => {
    if (athlete) {
      setAthleteName(athlete.name || "");
      setWeeklyHours(athlete.weekly_training_hours ?? "");
      setWeightKg(athlete.weight ?? "");
      setFtpWatts(athlete.ftp ?? "");
      setMaxHrBpm(athlete.max_hr ?? "");
      setLthrBpm(athlete.lthr ?? "");
      setThresholdPaceMinKm(athlete.threshold_pace ?? "");
      setSelectedSports(athlete.preferred_sports || ["Run", "Ride"]);
    }
  }, [athlete]);

  useEffect(() => {
    if (preferences) {
      setMaxDaysPerWeek(preferences.max_days_per_week ?? 6);
      setRestDays(preferences.rest_day_preference || ["Monday"]);
      setSplitNotes(preferences.split_notes || "");
    }
  }, [preferences]);

  if (!isOpen) return null;

  const isStravaConnected = Boolean(athlete?.strava_connected);

  const toggleRestDay = (day: string) => {
    setRestDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const toggleSport = (sport: string) => {
    setSelectedSports((prev) =>
      prev.includes(sport) ? prev.filter((s) => s !== sport) : [...prev, sport]
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // 1. Update Athlete Profile & Performance metrics
      await updateProfileMutation.mutateAsync({
        name: athleteName.trim() || undefined,
        weekly_training_hours: weeklyHours === "" ? undefined : Number(weeklyHours),
        weight: weightKg === "" ? undefined : Number(weightKg),
        ftp: ftpWatts === "" ? undefined : Number(ftpWatts),
        max_hr: maxHrBpm === "" ? undefined : Number(maxHrBpm),
        lthr: lthrBpm === "" ? undefined : Number(lthrBpm),
        threshold_pace: thresholdPaceMinKm === "" ? undefined : Number(thresholdPaceMinKm),
        preferred_sports: selectedSports,
      });

      // 2. Update Training Preferences & Goals
      await updatePreferencesMutation.mutateAsync({
        max_days_per_week: Number(maxDaysPerWeek),
        rest_day_preference: restDays,
        split_notes: splitNotes.trim() || undefined,
      });

      await refreshProfile();
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2500);
    } catch {
      alert("Failed to save changes. Please check input values.");
    }
  };

  const handleConnectStrava = async () => {
    try {
      const redirectUri = `${window.location.origin}/strava-callback`;
      const { data } = await api.GET("/myactivities/strava/auth-url", {
        params: { query: { redirect_uri: redirectUri } },
      });
      const authUrl = (data as any)?.auth_url;
      if (authUrl) {
        window.location.href = authUrl;
      } else {
        alert("Failed to obtain Strava authorization link");
      }
    } catch {
      alert("Error initiating Strava connection");
    }
  };

  const handleDisconnectStrava = async () => {
    if (!confirm("Are you sure you want to disconnect Strava?")) return;
    try {
      await api.DELETE("/myactivities/user/strava");
      await refreshProfile();
    } catch {
      alert("Failed to disconnect Strava");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-[#282a36] border border-[#44475a] rounded-t-lg sm:rounded-lg shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#44475a]/60 bg-[#282a36]">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-md bg-[#bd93f9]/15 text-[#bd93f9] border border-[#bd93f9]/30">
              <User className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#f8f8f2]">Athlete Profile & Settings</h3>
              <p className="text-[11px] text-[#6272a4]">{athlete?.email}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/50 transition-all"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-[#44475a]/60 px-5 pt-2 bg-[#282a36] gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("goals")}
            className={`pb-2.5 px-2 text-xs font-medium border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === "goals"
                ? "border-[#bd93f9] text-[#bd93f9]"
                : "border-transparent text-[#6272a4] hover:text-[#f8f8f2]"
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            <span>Goals & Preferences</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("metrics")}
            className={`pb-2.5 px-2 text-xs font-medium border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === "metrics"
                ? "border-[#8be9fd] text-[#8be9fd]"
                : "border-transparent text-[#6272a4] hover:text-[#f8f8f2]"
            }`}
          >
            <Gauge className="w-3.5 h-3.5" />
            <span>Metrics</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("integrations")}
            className={`pb-2.5 px-2 text-xs font-medium border-b-2 flex items-center gap-1.5 transition-all ${
              activeTab === "integrations"
                ? "border-[#ff5555] text-[#ff5555]"
                : "border-transparent text-[#6272a4] hover:text-[#f8f8f2]"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Integrations</span>
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* TAB 1: Goals & Preferences */}
          {activeTab === "goals" && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#6272a4] mb-1">
                  Athlete Display Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Alex"
                  value={athleteName}
                  onChange={(e) => setAthleteName(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#6272a4] mb-1">
                    Weekly Hours Target
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    max="40"
                    placeholder="e.g. 8.0"
                    value={weeklyHours}
                    onChange={(e) =>
                      setWeeklyHours(e.target.value === "" ? "" : Number(e.target.value))
                    }
                    className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#6272a4] mb-1">
                    Max Training Days / Week
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="7"
                    value={maxDaysPerWeek}
                    onChange={(e) => setMaxDaysPerWeek(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
                  />
                </div>
              </div>

              {/* Preferred Rest Days Selector */}
              <div>
                <label className="block text-xs font-medium text-[#6272a4] mb-1.5">
                  Preferred Rest Days
                </label>
                <div className="grid grid-cols-7 gap-1">
                  {WEEKDAYS.map((day) => {
                    const isRest = restDays.includes(day.key);
                    return (
                      <button
                        key={day.key}
                        type="button"
                        onClick={() => toggleRestDay(day.key)}
                        className={`py-1.5 text-center text-xs font-medium rounded-md border transition-all ${
                          isRest
                            ? "bg-[#ff79c6]/20 border-[#ff79c6]/60 text-[#ff79c6]"
                            : "bg-[#1e1f29] border-[#44475a] text-[#6272a4] hover:text-[#f8f8f2]"
                        }`}
                      >
                        {day.label}
                      </button>
                    );
                  })}
                </div>
                <p className="text-[10px] text-[#6272a4] mt-1">
                  AI coach avoids scheduling hard sessions on selected rest days.
                </p>
              </div>

              {/* Preferred Sports */}
              <div>
                <label className="block text-xs font-medium text-[#6272a4] mb-1.5">
                  Active Sports
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {AVAILABLE_SPORTS.map((sport) => {
                    const isSelected = selectedSports.includes(sport);
                    return (
                      <button
                        key={sport}
                        type="button"
                        onClick={() => toggleSport(sport)}
                        className={`px-2.5 py-1 text-xs rounded-md border transition-all ${
                          isSelected
                            ? "bg-[#bd93f9]/20 border-[#bd93f9]/60 text-[#bd93f9] font-medium"
                            : "bg-[#1e1f29] border-[#44475a] text-[#6272a4] hover:text-[#f8f8f2]"
                        }`}
                      >
                        {sport}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Split Notes / Focus */}
              <div>
                <label className="block text-xs font-medium text-[#6272a4] mb-1">
                  Training Focus & Instructions
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Preparing for autumn marathon. Long run on Sunday, recovery ride on Tuesday."
                  value={splitNotes}
                  onChange={(e) => setSplitNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9]"
                />
              </div>
            </div>
          )}

          {/* TAB 2: Performance Metrics */}
          {activeTab === "metrics" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#6272a4] mb-1">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="30"
                    max="250"
                    placeholder="72.0"
                    value={weightKg}
                    onChange={(e) =>
                      setWeightKg(e.target.value === "" ? "" : Number(e.target.value))
                    }
                    className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#8be9fd]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#6272a4] mb-1">
                    FTP (Watts)
                  </label>
                  <input
                    type="number"
                    min="50"
                    max="600"
                    placeholder="250"
                    value={ftpWatts}
                    onChange={(e) =>
                      setFtpWatts(e.target.value === "" ? "" : Number(e.target.value))
                    }
                    className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#8be9fd]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-[#6272a4] mb-1">
                    Max Heart Rate (bpm)
                  </label>
                  <input
                    type="number"
                    min="100"
                    max="240"
                    placeholder="190"
                    value={maxHrBpm}
                    onChange={(e) =>
                      setMaxHrBpm(e.target.value === "" ? "" : Number(e.target.value))
                    }
                    className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#8be9fd]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#6272a4] mb-1">
                    LTHR (Lactate Threshold HR)
                  </label>
                  <input
                    type="number"
                    min="80"
                    max="220"
                    placeholder="172"
                    value={lthrBpm}
                    onChange={(e) =>
                      setLthrBpm(e.target.value === "" ? "" : Number(e.target.value))
                    }
                    className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#8be9fd]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#6272a4] mb-1">
                  Threshold Pace (min/km)
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="2.5"
                  max="12.0"
                  placeholder="4.50"
                  value={thresholdPaceMinKm}
                  onChange={(e) =>
                    setThresholdPaceMinKm(e.target.value === "" ? "" : Number(e.target.value))
                  }
                  className="w-full px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#8be9fd]"
                />
                <p className="text-[10px] text-[#6272a4] mt-1">
                  Used for calculating running training stress score (rTSS) and workout intervals.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: Integrations & Strava */}
          {activeTab === "integrations" && (
            <div className="space-y-4">
              <div className="p-4 rounded-md bg-[#1e1f29] border border-[#44475a] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-[#ff5555]/15 text-[#ff5555] font-bold text-xs flex items-center justify-center border border-[#ff5555]/30">
                      S
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-[#f8f8f2]">Strava Integration</p>
                      <p className="text-[11px] text-[#6272a4]">
                        {isStravaConnected
                          ? "Connected & Synchronized"
                          : "Connect to sync completed workouts"}
                      </p>
                    </div>
                  </div>

                  {isStravaConnected ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono text-[#50fa7b] bg-[#50fa7b]/15 border border-[#50fa7b]/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Synced
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={handleConnectStrava}
                      className="px-3 py-1.5 rounded-md bg-[#ff5555] hover:bg-[#ff6e6e] text-white text-xs font-medium flex items-center gap-1 transition-all"
                    >
                      <span>Connect</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  )}
                </div>

                {isStravaConnected && (
                  <div className="pt-3 border-t border-[#44475a]/40 flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => syncMutation.mutate()}
                      disabled={syncMutation.isPending}
                      className="px-3 py-1.5 rounded-md bg-[#44475a]/60 hover:bg-[#44475a] text-xs font-medium text-[#f8f8f2] flex items-center gap-1.5 transition-all disabled:opacity-50"
                    >
                      <RefreshCw
                        className={`w-3.5 h-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`}
                      />
                      <span>{syncMutation.isPending ? "Syncing..." : "Sync Now"}</span>
                    </button>

                    <button
                      type="button"
                      onClick={handleDisconnectStrava}
                      className="text-xs text-[#ff5555]/80 hover:text-[#ff5555] flex items-center gap-1 transition-all"
                    >
                      <Unlink className="w-3.5 h-3.5" />
                      <span>Disconnect</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="pt-3 border-t border-[#44475a]/60 flex items-center justify-between gap-3">
            <button
              type="submit"
              disabled={updateProfileMutation.isPending || updatePreferencesMutation.isPending}
              className={`px-4 py-2 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${
                isSaved
                  ? "bg-[#50fa7b] text-[#282a36]"
                  : "bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36]"
              }`}
            >
              {isSaved ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Saved</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Changes</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                logout();
                onClose();
              }}
              className="px-3 py-2 rounded-md text-xs text-[#ff5555] hover:bg-[#ff5555]/15 transition-all flex items-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
