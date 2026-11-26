import React, { useState } from "react";
import { useGeneratePlan, useConfirmPlan } from "../../hooks/useQueries";
import {
  Send,
  Sparkles,
  Bot,
  User,
  CalendarCheck,
  CheckCircle2,
  ArrowRight,
  Loader2,
  Trash2,
} from "lucide-react";
import { formatISODate, getMonday } from "../../utils/date";
import { ModalDrawer } from "../layout/ModalDrawer";

interface AIChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  planPreview?: Record<string, any>;
}

const WorkoutPreviewList: React.FC<{
  items: any[];
  variant: "remove" | "add";
}> = ({ items, variant }) => {
  const isRemove = variant === "remove";
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span
          className={`text-[10px] font-mono font-bold uppercase tracking-wider flex items-center gap-1 ${
            isRemove ? "text-[#ff5555]" : "text-[#bd93f9]"
          }`}
        >
          {isRemove ? <Trash2 className="w-3 h-3" /> : <CalendarCheck className="w-3 h-3" />}
          {isRemove ? "Workouts to Remove" : "Proposed Workouts"}
        </span>
        <span className="text-[10px] font-mono text-[#6272a4]">
          {items.length} session{items.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className={`${isRemove ? "max-h-32" : "max-h-44"} overflow-y-auto space-y-1 pr-1`}>
        {items.slice(0, 10).map((w, idx) => (
          <div
            key={w.id || idx}
            className={`p-1.5 rounded bg-[#1e1f29] border flex items-center justify-between text-[11px] ${
              isRemove ? "border-[#ff5555]/30" : "border-[#44475a]/50"
            }`}
          >
            <span
              className={`font-medium text-[#f8f8f2] truncate ${
                isRemove ? "line-through opacity-80" : ""
              }`}
            >
              {isRemove
                ? `${w.planned_date ? `${w.planned_date.slice(0, 10)}: ` : ""}${w.name}`
                : `Day ${w.day_offset + 1}: ${w.name}`}
            </span>
            <span
              className={`font-mono shrink-0 ml-2 ${
                isRemove ? "text-[#ff5555]/80" : "text-[#6272a4]"
              }`}
            >
              {w.duration_min ?? w.target_duration_min ?? 0}m ({w.sport_type})
            </span>
          </div>
        ))}
        {items.length > 10 && (
          <p className="text-[10px] text-center text-[#6272a4] italic">
            + {items.length - 10} more {isRemove ? "to remove" : "sessions"}
          </p>
        )}
      </div>
    </div>
  );
};

export const AIChatDrawer: React.FC<AIChatDrawerProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial",
      sender: "ai",
      text: "Hello! I am your AI Endurance Coach. Tell me what you would like to plan, change, or remove (e.g. 'Plan 2 weeks for building aerobic base', 'Change this week to focus on running', or 'Remove Wednesday's workout').",
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [confirmedPlanIds, setConfirmedPlanIds] = useState<string[]>([]);

  const generateMutation = useGeneratePlan();
  const confirmMutation = useConfirmPlan();

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      sender: "user",
      text: inputText.trim(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText("");

    const lower = userMsg.text.toLowerCase();
    const duration =
      lower.includes("month") || lower.includes("4 week") || lower.includes("28 day")
        ? 28
        : lower.includes("3 week") || lower.includes("21 day")
        ? 21
        : lower.includes("2 week") || lower.includes("14 day")
        ? 14
        : 7;

    try {
      const plan = await generateMutation.mutateAsync({
        startDate: formatISODate(getMonday(new Date())),
        durationDays: duration,
        prompt: userMsg.text,
      });

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          sender: "ai",
          text:
            plan.reasoning ||
            `I have generated a ${duration}-day progressive training block for you. Review the workout preview below and confirm to schedule it into your calendar:`,
          planPreview: plan,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          sender: "ai",
          text: `Sorry, I encountered an issue generating your plan: ${err.message}`,
        },
      ]);
    }
  };

  const handleConfirmPlan = async (plan: Record<string, any>, msgId: string) => {
    try {
      await confirmMutation.mutateAsync(plan as any);
      setConfirmedPlanIds((prev) => [...prev, msgId]);
    } catch (err: any) {
      alert(`Failed to commit plan: ${err.message}`);
    }
  };

  return (
    <ModalDrawer
      isOpen={isOpen}
      onClose={onClose}
      title="AI Coach Chat"
      subtitle="Adaptive Periodization & Adjustments"
      icon={<Sparkles className="w-4 h-4" />}
      headerClassName="px-4 py-3.5"
      panelClassName="max-w-lg rounded-t-lg sm:rounded-lg flex flex-col h-[85vh] sm:h-[650px]"
    >
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {messages.map((msg) => {
          const isAI = msg.sender === "ai";
          const isConfirmed = confirmedPlanIds.includes(msg.id);
          const proposedWorkouts = msg.planPreview?.workouts || [];
          const removedWorkouts = msg.planPreview?.removed_workouts || [];
          const hasProposed = proposedWorkouts.length > 0;
          const hasRemoved = removedWorkouts.length > 0;

          const confirmLabel =
            hasRemoved && !hasProposed
              ? "Confirm & Remove Workouts"
              : hasRemoved && hasProposed
              ? "Confirm & Replace Workouts"
              : "Confirm & Schedule Plan";

          const confirmedLabel =
            hasRemoved && !hasProposed
              ? "Workouts Removed from Calendar"
              : hasRemoved && hasProposed
              ? "Plan Updated on Calendar"
              : "Plan Scheduled to Calendar";

          return (
            <div key={msg.id} className={`flex gap-2.5 ${isAI ? "justify-start" : "justify-end"}`}>
              {isAI && (
                <div className="w-6 h-6 rounded-md bg-[#bd93f9]/15 text-[#bd93f9] border border-[#bd93f9]/30 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-md p-3 text-xs leading-relaxed ${
                  isAI
                    ? "bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2]"
                    : "bg-[#bd93f9] text-[#282a36] font-medium"
                }`}
              >
                <p>{msg.text}</p>

                {msg.planPreview && (hasProposed || hasRemoved) && (
                  <div className="mt-2.5 p-2.5 rounded-md bg-[#282a36] border border-[#bd93f9]/40 space-y-2.5">
                    {hasRemoved && <WorkoutPreviewList items={removedWorkouts} variant="remove" />}
                    {hasProposed && <WorkoutPreviewList items={proposedWorkouts} variant="add" />}

                    <button
                      onClick={() => handleConfirmPlan(msg.planPreview!, msg.id)}
                      disabled={isConfirmed || confirmMutation.isPending}
                      className={`w-full py-1.5 px-3 rounded-md text-xs font-semibold transition-all flex items-center justify-center gap-1.5 ${
                        isConfirmed
                          ? "bg-[#50fa7b]/20 text-[#50fa7b] border border-[#50fa7b]/40 cursor-default"
                          : hasRemoved && !hasProposed
                          ? "bg-[#ff5555] hover:bg-[#ff6e6e] text-[#282a36]"
                          : "bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36]"
                      }`}
                    >
                      {isConfirmed ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{confirmedLabel}</span>
                        </>
                      ) : confirmMutation.isPending ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Applying...</span>
                        </>
                      ) : (
                        <>
                          <span>{confirmLabel}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {!isAI && (
                <div className="w-6 h-6 rounded-md bg-[#44475a] text-[#f8f8f2] flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          );
        })}

        {generateMutation.isPending && (
          <div className="flex gap-2 items-center text-xs text-[#bd93f9] animate-pulse">
            <Bot className="w-4 h-4" />
            <span>Analyzing physiology & designing plan...</span>
          </div>
        )}
      </div>

      <form
        onSubmit={handleSend}
        className="p-3 border-t border-[#44475a]/60 bg-[#282a36] flex items-center gap-2"
      >
        <input
          type="text"
          placeholder="Ask AI to plan, change, or remove workouts..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          className="flex-1 px-3 py-2 rounded-md bg-[#1e1f29] border border-[#44475a] text-[#f8f8f2] text-xs focus:outline-none focus:border-[#bd93f9] transition-all"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || generateMutation.isPending}
          className="p-2 rounded-md bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36] transition-all disabled:opacity-50"
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </ModalDrawer>
  );
};
