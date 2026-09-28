import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { Activity, Dumbbell, ShieldCheck, Sparkles, ArrowRight, Loader2 } from "lucide-react";

export const AuthScreen: React.FC = () => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(email, password, name.trim() || undefined);
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#282a36] text-[#f8f8f2] flex flex-col justify-center items-center p-4">
      {/* Brand Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-[#bd93f9]/20 border border-[#bd93f9]/40 rounded-2xl text-[#bd93f9] shadow-lg shadow-[#bd93f9]/10">
          <Activity className="w-8 h-8" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#f8f8f2]">MyActivities</h1>
          <p className="text-xs text-[#6272a4] font-medium">Adaptive AI Endurance Coaching</p>
        </div>
      </div>

      {/* Auth Card */}
      <div className="w-full max-w-md bg-[#44475a]/40 border border-[#44475a] rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
        <div className="flex rounded-xl bg-[#282a36] p-1 mb-6 border border-[#44475a]/50">
          <button
            type="button"
            onClick={() => { setIsLogin(true); setError(null); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              isLogin ? "bg-[#bd93f9] text-[#282a36] shadow" : "text-[#6272a4] hover:text-[#f8f8f2]"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsLogin(false); setError(null); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
              !isLogin ? "bg-[#bd93f9] text-[#282a36] shadow" : "text-[#6272a4] hover:text-[#f8f8f2]"
            }`}
          >
            Register
          </button>
        </div>

        {error && (
          <div className="mb-5 p-3 rounded-xl bg-[#ff5555]/15 border border-[#ff5555]/40 text-[#ff5555] text-xs font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Athlete Name</label>
              <input
                type="text"
                placeholder="Alex Morgan"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl bg-[#282a36]/80 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9] transition-all"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Email Address</label>
            <input
              type="email"
              required
              placeholder="athlete@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-[#282a36]/80 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9] transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#6272a4] mb-1.5">Password</label>
            <input
              type="password"
              required
              minLength={8}
              placeholder="Minimum 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-[#282a36]/80 border border-[#44475a] text-[#f8f8f2] text-sm focus:outline-none focus:border-[#bd93f9] transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 px-4 rounded-xl bg-[#bd93f9] hover:bg-[#caa5fb] text-[#282a36] font-semibold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-[#bd93f9]/20 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>{isLogin ? "Sign In" : "Create Account"}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Feature Highlights */}
        <div className="mt-8 pt-6 border-t border-[#44475a]/50 grid grid-cols-3 gap-2 text-center text-[10px] text-[#6272a4]">
          <div className="flex flex-col items-center gap-1">
            <Sparkles className="w-4 h-4 text-[#bd93f9]" />
            <span>AI Periodization</span>
          </div>
          <div className="flex flex-col items-center gap-1">
            <Dumbbell className="w-4 h-4 text-[#50fa7b]" />
            <span>Strava Sync</span>
          </div>
          <div className="flex flex-col items-center gap-1">
            <ShieldCheck className="w-4 h-4 text-[#8be9fd]" />
            <span>Load Analytics</span>
          </div>
        </div>
      </div>
    </div>
  );
};
