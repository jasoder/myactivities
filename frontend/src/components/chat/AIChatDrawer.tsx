import React, { useState } from "react";
import { useGeneratePlan, useConfirmPlan } from "../../hooks/useQueries";
import {
  X,
  Send,
  Sparkles,
  Bot,
  User,
  CalendarCheck,
  CheckCircle2,
  ArrowRight,
  Loader2
} from "lucide-react";
import { formatISODate, getMonday } from "../../utils/date";

interface AIChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  planPreview?: any;
}

export const AIChatDrawer: React.FC<AIChatDrawerProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial",
      sender: "ai",
      text: "Hello! I am your AI Endurance Coach. Tell me what you'd like to plan (e.g. 'Plan 2 weeks for building aerobic base', 'Create a 4-week block with a deload', or 'Prepare me for a 10k').",
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [confirmedPlanIds, setConfirmedPlanIds] = useState<string[]>([]);

  const generateMutation = useGeneratePlan();
  const confirmMutation = useConfirmPlan();

  if (!isOpen) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: "user",
      text: inputText.trim(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText("");

    // Determine plan duration from input (default 7, check for numbers)
    let duration = 7;
    const lower = userMsg.text.toLowerCase();
    if (lower.includes("month") || lower.includes("4 week") || lower.includes("28 day")) {
      duration = 28;
    } else if (lower.includes("2 week") || lower.includes("14 day")) {
      duration = 14;
    } else if (lower.includes("3 week") || lower.includes("21 day")) {
      duration = 21;
    }

    const startDateStr = formatISODate(getMonday(new Date()));

    try {
      const plan = await generateMutation.mutateAsync({
        startDate: startDateStr,
        durationDays: duration,
      });

      const aiResponse: ChatMessage = {
        id: String(Date.now() + 1),
        sender: "ai",
        text: plan.reasoning || `I have generated a ${duration}-day progressive training block for you. Review the workout preview below and confirm to schedule it into your calendar:`,
        planPreview: plan,
      };
      setMessages((prev) => [...prev, aiResponse]);
    } catch (err: any) {
      const errResponse: ChatMessage = {
        id: String(Date.now() + 1),
        sender: "ai",
        text: `Sorry, I encountered an issue generating your plan: ${err.message}`,
      };
      setMessages((prev) => [...prev, errResponse]);
    }
  };

  const handleConfirmPlan = async (plan: any, msgId: string) => {
    try {
      await confirmMutation.mutateAsync(plan);
      setConfirmedPlanIds((prev) => [...prev, msgId]);
    } catch (err: any) {
      alert(`Failed to commit plan: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-[#282a36] border border-[#44475a] rounded-t-3xl sm:rounded-3xl shadow-2xl flex flex-col h-[85vh] sm:h-[650px] overflow-hidden animate-in slide-in-from-bottom duration-200">
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#44475a]/50 bg-[#282a36]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#bd93f9]/20 text-[#bd93f9]">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#f8f8f2]">AI Coach Chat</h3>
              <p className="text-[11px] text-[#6272a4]">Adaptive Periodization & Adjustments</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a] transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => {
            const isAI = msg.sender === "ai";
            const isConfirmed = confirmedPlanIds.includes(msg.id);

            return (
              <div
                key={msg.id}
                className={`flex gap-3 ${isAI ? "justify-start" : "justify-end"}`}
              >
                {isAI && (
                  <div className="w-7 h-7 rounded-xl bg-[#bd93f9]/20 text-[#bd93f9] flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                    isAI
                      ? "bg-[#44475a]/30 border border-[#44475a]/60 text-[#f8f8f2]"
                      : "bg-[#bd93f9] text-[#282a36] font-medium"
                  }`}
                >
                  <p>{msg.text}</p>

                  {/* Plan Preview Card inside chat */}
                  {msg.planPreview && (
                    <div className="mt-3 p-3 rounded-xl bg-[#282a36] border border-[#bd93f9]/40 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-[#bd93f9] flex items-center gap-1">
                          <CalendarCheck className="w-3.5 h-3.5" /> Proposed Workouts
                        </span>
                        <span className="text-[10px] text-[#6272a4]">
                          {msg.planPreview.workouts?.length || 0} sessions
                        </span>
                      </div>

                      <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                        {msg.planPreview.workouts?.slice(0, 10).map((w: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-2 rounded-lg bg-[#44475a]/30 border border-[#44475a]/50 flex items-center justify-between text-[11px]"
                          >
                            <span className="font-semibold text-[#f8f8f2] truncate">
                              Day {w.day_offset + 1}: {w.name}
                            </span>
                            <span className="text-[#6272a4] shrink-0 ml-2">
                              {w.target_duration_min}m ({w.sport_type})
                            </span>
                          </div>
                        ))}
                        {msg.planPreview.workouts?.length > 10 && (
                          <p className="text-[10px] text-center text-[#6272a4] italic">
                            + {msg.planPreview.workouts.length - 10} more sessions
                          </p>
                        )}
                      </div>

                      {/* Confirm Action Button */}
                      <button
                        onClick={() => handleConfirmPlan(msg.planPreview, msg.id)}
                        disabled={isConfirmed || confirmMutation.isPending}
                        className={`w-full py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-md ${
                          isConfirmed
                            ? "bg-[#50fa7b]/20 text-[#50fa7b] border border-[#50fa7b]/40 cursor-default"
                            : "bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36]"
                        }`}
                      >
                        {isConfirmed ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Plan Scheduled to Calendar</span>
                          </>
                        ) : confirmMutation.isPending ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Scheduling...</span>
                          </>
                        ) : (
                          <>
                            <span>Confirm & Schedule Plan</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>

                {!isAI && (
                  <div className="w-7 h-7 rounded-xl bg-[#44475a] text-[#f8f8f2] flex items-center justify-center shrink-0 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}

          {generateMutation.isPending && (
            <div className="flex gap-3 items-center text-xs text-[#bd93f9] animate-pulse">
              <Bot className="w-4 h-4" />
              <span>Analyzing physiology & designing plan...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} className="p-3 border-t border-[#44475a]/50 bg-[#282a36] flex items-center gap-2">
          <input
            type="text"
            placeholder="Ask AI to plan 4 weeks, change workout, or adjust load..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 px-4 py-2.5 rounded-xl bg-[#44475a]/40 border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9] transition-all"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || generateMutation.isPending}
            className="p-2.5 rounded-xl bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36] transition-all disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
