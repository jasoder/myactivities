import React from "react";
import { useTrainingLoad, useWeeklyRecap } from "../../hooks/useQueries";
import { X, TrendingUp, HeartPulse, BatteryCharging, Zap, Award } from "lucide-react";
import { formatISODate, getMonday } from "../../utils/date";

interface TrainingLoadDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const TrainingLoadDrawer: React.FC<TrainingLoadDrawerProps> = ({ isOpen, onClose }) => {
  const currentMondayStr = formatISODate(getMonday(new Date()));
  const { data: loadDataRaw, isLoading: isLoadLoading } = useTrainingLoad(isOpen);
  const { data: recapDataRaw, isLoading: isRecapLoading } = useWeeklyRecap(currentMondayStr, isOpen);

  if (!isOpen) return null;

  const loadData = loadDataRaw as any;
  const recapData = recapDataRaw as any;

  const ctl = Math.round(loadData?.ctl ?? 0);
  const atl = Math.round(loadData?.atl ?? 0);
  const tsb = Math.round(loadData?.tsb ?? 0);
  const formStatus = loadData?.form_status || (tsb > 5 ? "Fresh" : tsb < -10 ? "Fatigued" : "Optimal");

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-[#282a36] border border-[#44475a] rounded-t-lg sm:rounded-lg p-5 shadow-2xl space-y-5 max-h-[85vh] overflow-y-auto animate-in fade-in duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#44475a]/60 pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-md bg-[#8be9fd]/15 text-[#8be9fd] border border-[#8be9fd]/30">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#f8f8f2]">Training Load & Physiology</h3>
              <p className="text-[11px] text-[#6272a4]">Chronic & Acute Workload Analytics</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/50 transition-all"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* CTL / ATL / TSB Gauges */}
        {isLoadLoading ? (
          <div className="p-8 text-center text-xs text-[#6272a4] animate-pulse">
            Calculating physiological load...
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-2.5">
            <div className="bg-[#1e1f29] border border-[#44475a] p-3 rounded-md text-center">
              <div className="flex items-center justify-center gap-1 text-[10px] font-mono text-[#6272a4]">
                <HeartPulse className="w-3 h-3 text-[#50fa7b]" /> CTL
              </div>
              <p className="text-xl font-mono font-bold text-[#50fa7b] mt-1">{ctl}</p>
              <span className="text-[10px] text-[#6272a4]">Fitness (42d)</span>
            </div>

            <div className="bg-[#1e1f29] border border-[#44475a] p-3 rounded-md text-center">
              <div className="flex items-center justify-center gap-1 text-[10px] font-mono text-[#6272a4]">
                <BatteryCharging className="w-3 h-3 text-[#ff5555]" /> ATL
              </div>
              <p className="text-xl font-mono font-bold text-[#ff5555] mt-1">{atl}</p>
              <span className="text-[10px] text-[#6272a4]">Fatigue (7d)</span>
            </div>

            <div className="bg-[#1e1f29] border border-[#44475a] p-3 rounded-md text-center">
              <div className="flex items-center justify-center gap-1 text-[10px] font-mono text-[#6272a4]">
                <Zap className="w-3 h-3 text-[#bd93f9]" /> TSB
              </div>
              <p
                className={`text-xl font-mono font-bold mt-1 ${
                  tsb >= 0 ? "text-[#8be9fd]" : "text-[#ffb86c]"
                }`}
              >
                {tsb > 0 ? `+${tsb}` : tsb}
              </p>
              <span className="text-[10px] font-medium text-[#f8f8f2]">{formStatus}</span>
            </div>
          </div>
        )}

        {/* Weekly Recap / Morning Report */}
        <div className="space-y-2.5 pt-2 border-t border-[#44475a]/60">
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-[#bd93f9]" />
            <h4 className="text-xs font-semibold text-[#f8f8f2]">Current Week Recap</h4>
          </div>

          {isRecapLoading ? (
            <div className="p-4 text-center text-xs text-[#6272a4] animate-pulse">
              Compiling weekly performance summary...
            </div>
          ) : recapData ? (
            <div className="bg-[#1e1f29] border border-[#bd93f9]/30 p-3.5 rounded-md space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#6272a4]">Compliance Rate:</span>
                <span className="font-mono font-semibold text-[#50fa7b]">
                  {recapData.compliance_rate ? `${Math.round(recapData.compliance_rate)}%` : "N/A"}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#6272a4]">Sessions Completed / Planned:</span>
                <span className="font-mono font-semibold text-[#f8f8f2]">
                  {recapData.completed_sessions ?? 0} / {recapData.planned_sessions ?? 0}
                </span>
              </div>
              {recapData.coach_feedback && (
                <div className="pt-2 border-t border-[#44475a]/40 text-xs text-[#bd93f9] leading-relaxed">
                  <span className="font-semibold text-[#f8f8f2]">Coach Review: </span>
                  {recapData.coach_feedback}
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-[#6272a4] italic">No recap available for this microcycle yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};
