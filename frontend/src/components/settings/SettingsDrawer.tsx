import React from "react";
import { useAuth } from "../../context/AuthContext";
import { useSyncStrava } from "../../hooks/useQueries";
import { X, RefreshCw, Unlink, LogOut, CheckCircle, ExternalLink, Settings, User } from "lucide-react";
import { api } from "../../api/client";

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({ isOpen, onClose }) => {
  const { athlete, logout, refreshProfile } = useAuth();
  const syncMutation = useSyncStrava();

  if (!isOpen) return null;

  const isStravaConnected = Boolean(athlete?.strava_connected);

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
        alert("Failed to get Strava authorization URL");
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
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[#282a36] border border-[#44475a] rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl space-y-6 max-h-[85vh] overflow-y-auto animate-in slide-in-from-bottom duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#44475a]/50 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#bd93f9]/20 text-[#bd93f9]">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#f8f8f2]">Settings & Integrations</h3>
              <p className="text-xs text-[#6272a4]">Manage Strava & Profile</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a] transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Profile Card */}
        <div className="bg-[#44475a]/20 border border-[#44475a]/50 p-4 rounded-2xl flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#bd93f9]/20 text-[#bd93f9] flex items-center justify-center font-bold">
            <User className="w-5 h-5" />
          </div>
          <div className="truncate">
            <h4 className="text-sm font-bold text-[#f8f8f2] truncate">
              {athlete?.name || "Athlete Profile"}
            </h4>
            <p className="text-xs text-[#6272a4] truncate">{athlete?.email}</p>
          </div>
        </div>

        {/* Strava Integration Section */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-[#6272a4]">
            External Integrations
          </h4>

          <div className="p-4 rounded-2xl bg-[#44475a]/30 border border-[#44475a]/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-[#ff5555]/20 text-[#ff5555] font-black text-xs flex items-center justify-center">
                  S
                </div>
                <div>
                  <p className="text-xs font-bold text-[#f8f8f2]">Strava</p>
                  <p className="text-[11px] text-[#6272a4]">
                    {isStravaConnected ? "Connected & Synchronized" : "Not connected"}
                  </p>
                </div>
              </div>

              {isStravaConnected ? (
                <span className="px-2 py-0.5 rounded-full bg-[#50fa7b]/20 text-[#50fa7b] text-[10px] font-semibold flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Active
                </span>
              ) : (
                <button
                  onClick={handleConnectStrava}
                  className="px-3 py-1.5 rounded-xl bg-[#ff5555] hover:bg-[#ff6e6e] text-white font-semibold text-xs flex items-center gap-1 shadow-md transition-all"
                >
                  <span>Connect</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              )}
            </div>

            {isStravaConnected && (
              <div className="pt-2 border-t border-[#44475a]/40 flex items-center justify-between gap-2">
                <button
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                  className="px-3 py-1.5 rounded-xl bg-[#44475a] hover:bg-[#6272a4]/40 text-xs font-medium text-[#f8f8f2] flex items-center gap-1.5 transition-all disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                  {syncMutation.isPending ? "Syncing..." : "Sync Now"}
                </button>

                <button
                  onClick={handleDisconnectStrava}
                  className="text-xs text-[#ff5555]/80 hover:text-[#ff5555] flex items-center gap-1 transition-all"
                >
                  <Unlink className="w-3.5 h-3.5" />
                  Disconnect
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Logout */}
        <div className="pt-4 border-t border-[#44475a]/50">
          <button
            onClick={() => {
              logout();
              onClose();
            }}
            className="w-full py-2.5 px-4 rounded-xl bg-[#44475a]/30 hover:bg-[#ff5555]/20 text-[#ff5555] font-semibold text-xs transition-all flex items-center justify-center gap-2 border border-transparent hover:border-[#ff5555]/40"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
};
