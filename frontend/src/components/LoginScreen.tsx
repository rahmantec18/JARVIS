import React, { useState } from 'react';
import { Lock, Eye, EyeOff, ShieldAlert, Cpu, ArrowRight } from 'lucide-react';
import { api } from '../services/api';

interface LoginScreenProps {
  onLoginSuccess: (token: string) => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess }) => {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const resp = await api.login(password);
      if (resp.success && resp.token) {
        sessionStorage.setItem('jarvis_session_token', resp.token);
        onLoginSuccess(resp.token);
      } else {
        setError(resp.message || 'Access Denied: Invalid security clearance key.');
      }
    } catch (err: any) {
      setError(err.message || 'Access Denied: Invalid security clearance key.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#020617] flex items-center justify-center p-4 overflow-hidden select-none font-sans">
      {/* Background Holographic Grid & Radial Aura */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-950/20 via-[#020617] to-[#01040f] pointer-events-none" />
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(to right, #00f0ff 1px, transparent 1px), linear-gradient(to bottom, #00f0ff 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }}
      />

      {/* Ambient Rotating Concentric Rings */}
      <div className="absolute w-[500px] h-[500px] border border-cyan-500/10 rounded-full animate-[spin_60s_linear_infinite] pointer-events-none" />
      <div className="absolute w-[360px] h-[360px] border border-cyan-400/15 rounded-full border-dashed animate-[spin_40s_linear_infinite_reverse] pointer-events-none" />

      {/* Main Login Vault Box */}
      <div className="relative z-10 w-full max-w-md bg-[#050b14]/90 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-8 shadow-[0_0_50px_rgba(0,240,255,0.12)] flex flex-col items-center gap-6">
        {/* Subtle Tech Corner Accents */}
        <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-cyan-400/80" />
        <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-cyan-400/80" />
        <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-cyan-400/80" />
        <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-cyan-400/80" />

        {/* Central Glowing Security Emblem */}
        <div className="relative flex items-center justify-center w-20 h-20">
          <div className="absolute inset-0 rounded-full bg-cyan-500/10 animate-ping opacity-30" />
          <div className="w-16 h-16 rounded-full border border-cyan-400/40 bg-cyan-950/30 flex items-center justify-center shadow-[0_0_20px_rgba(0,240,255,0.25)]">
            <Cpu className="w-8 h-8 text-cyan-400 animate-pulse" />
          </div>
        </div>

        {/* System Title */}
        <div className="text-center">
          <div className="font-mono text-[10px] tracking-[0.3em] text-cyan-400 uppercase font-semibold">
            Security Interlock // Clearance Required
          </div>
          <h1 className="text-2xl font-bold tracking-widest text-white mt-1">
            J.A.R.V.I.S.
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Stark Industries Mark-II Neural Ecosystem
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="w-full bg-red-950/40 border border-red-500/50 rounded-lg p-3 text-red-300 text-xs flex items-center gap-2.5 font-mono animate-shake">
            <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Password Form */}
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-cyan-400/70">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter authorization key..."
              autoFocus
              className="w-full bg-slate-950/80 border border-cyan-500/30 rounded-xl pl-10 pr-11 py-3 text-sm text-cyan-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/50 transition-all font-mono"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-cyan-300 transition-colors"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          <button
            type="submit"
            disabled={isLoading || !password.trim()}
            className="w-full bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-black font-semibold text-xs tracking-wider uppercase py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(0,240,255,0.2)] flex items-center justify-center gap-2 font-mono"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-black border-t-transparent rounded-full animate-spin" />
                AUTHENTICATING...
              </span>
            ) : (
              <>
                <span>INITIALIZE JARVIS</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Technical Metadata */}
        <div className="w-full pt-2 border-t border-cyan-500/10 flex items-center justify-between text-[10px] text-slate-500 font-mono">
          <span>HOST: SECURE LOCALHOST</span>
          <span>SYSTEM READY</span>
        </div>
      </div>
    </div>
  );
};
