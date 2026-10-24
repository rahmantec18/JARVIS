import React, { useState } from 'react';
import { Mic, MicOff, ExternalLink, Minimize2, Sparkles, Volume2 } from 'lucide-react';
import { JarvisState } from '../types';
import { api } from '../services/api';

interface InteractiveVoiceControlProps {
  state: JarvisState;
  isListening: boolean;
  audioLevel: number;
  onToggleListening: () => void;
  interimTranscript?: string;
  isProcessing?: boolean;
  onMinimizeToMiniHUD?: () => void;
}

export const InteractiveVoiceControl: React.FC<InteractiveVoiceControlProps> = ({
  state,
  isListening,
  audioLevel,
  onToggleListening,
  interimTranscript,
  isProcessing = false,
  onMinimizeToMiniHUD
}) => {
  const [popoutToast, setPopoutToast] = useState<string | null>(null);

  const handlePopout = (e: React.MouseEvent) => {
    e.stopPropagation();
    api.executeDesktopAction('launch_hud', {}).catch(() => {});
    setPopoutToast('Floating Pop-up Activated! Stays on top of WhatsApp.');
    setTimeout(() => setPopoutToast(null), 3500);
  };

  const handleMinimize = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Launch desktop HUD and also switch web to mini HUD
    api.executeDesktopAction('launch_hud', {}).catch(() => {});
    if (onMinimizeToMiniHUD) {
      onMinimizeToMiniHUD();
    }
  };

  // Determine colors based on system state
  const getStateTheme = () => {
    if (isListening) {
      return {
        ring: 'border-emerald-400 text-emerald-300 shadow-[0_0_35px_rgba(16,185,129,0.5)] bg-emerald-950/40',
        core: 'bg-emerald-500/20 border-emerald-400/80 shadow-[0_0_25px_#10b981]',
        text: 'text-emerald-300',
        badge: 'LISTENING // SPEAK DIRECTIVE',
        badgeBg: 'bg-emerald-950/70 border-emerald-400/50 text-emerald-300'
      };
    }
    switch (state) {
      case 'processing':
      case 'thinking':
        return {
          ring: 'border-blue-400 text-blue-300 shadow-[0_0_30px_rgba(56,189,248,0.4)] bg-blue-950/40',
          core: 'bg-blue-500/20 border-blue-400/80 shadow-[0_0_20px_#38bdf8]',
          text: 'text-blue-300',
          badge: 'EVALUATING DIRECTIVE',
          badgeBg: 'bg-blue-950/70 border-blue-400/50 text-blue-300'
        };
      case 'speaking':
        return {
          ring: 'border-sky-400 text-sky-300 shadow-[0_0_30px_rgba(34,211,238,0.4)] bg-sky-950/40',
          core: 'bg-sky-500/20 border-sky-400/80 shadow-[0_0_20px_#22d3ee]',
          text: 'text-sky-300',
          badge: 'SYNTHESIZING RESPONSE',
          badgeBg: 'bg-sky-950/70 border-sky-400/50 text-sky-300'
        };
      case 'error':
        return {
          ring: 'border-red-400 text-red-300 shadow-[0_0_30px_rgba(239,68,68,0.4)] bg-red-950/40',
          core: 'bg-red-500/20 border-red-400/80 shadow-[0_0_20px_#ef4444]',
          text: 'text-red-300',
          badge: 'EXCEPTION DETECTED',
          badgeBg: 'bg-red-950/70 border-red-400/50 text-red-300'
        };
      case 'idle':
      default:
        return {
          ring: 'border-cyan-500/40 text-cyan-400 shadow-[0_0_25px_rgba(0,240,255,0.2)] bg-[#050b14]/90',
          core: 'bg-cyan-950/40 border-cyan-400/50 shadow-[0_0_15px_rgba(0,240,255,0.3)]',
          text: 'text-cyan-400',
          badge: 'VOICE READY // CLICK TO ENGAGE',
          badgeBg: 'bg-slate-900/80 border-cyan-500/30 text-cyan-300'
        };
    }
  };

  const theme = getStateTheme();

  // Equalizer bar heights calculated dynamically from audioLevel
  const barHeights = [
    Math.min(100, Math.max(15, (isListening ? 30 + audioLevel * 70 : 20) + Math.sin(Date.now() / 200) * 10)),
    Math.min(100, Math.max(25, (isListening ? 45 + audioLevel * 85 : 35) + Math.cos(Date.now() / 250) * 15)),
    Math.min(100, Math.max(35, (isListening ? 60 + audioLevel * 100 : 45) + Math.sin(Date.now() / 180) * 20)),
    Math.min(100, Math.max(25, (isListening ? 45 + audioLevel * 85 : 35) + Math.cos(Date.now() / 220) * 15)),
    Math.min(100, Math.max(15, (isListening ? 30 + audioLevel * 70 : 20) + Math.sin(Date.now() / 260) * 10)),
  ];

  return (
    <div className="relative flex flex-col items-center select-none font-sans">
      {/* Toast Notification Banner when Popped Out */}
      {popoutToast && (
        <div className="absolute -top-12 z-30 px-3.5 py-1.5 rounded-full border border-emerald-400/60 bg-emerald-950/90 text-emerald-200 text-xs font-mono shadow-[0_0_25px_rgba(16,185,129,0.4)] backdrop-blur-md flex items-center gap-2 animate-bounce">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>{popoutToast}</span>
        </div>
      )}

      {/* Main Interactive Mic Control Cluster */}
      <div className="relative flex items-center gap-3">
        {/* Pulsing Sonar Ring Waves (when listening) */}
        {isListening && (
          <>
            <div 
              className="absolute -inset-3 rounded-full border border-emerald-400/30 animate-ping pointer-events-none" 
              style={{ animationDuration: '2s' }}
            />
            <div 
              className="absolute -inset-6 rounded-full border border-emerald-400/20 animate-pulse pointer-events-none" 
              style={{ animationDuration: '1.4s' }}
            />
          </>
        )}

        {/* Outer Rotating Cyberpunk Ring */}
        <div 
          onClick={onToggleListening}
          className={`relative w-16 h-16 sm:w-20 sm:h-20 rounded-full border-2 p-1.5 flex items-center justify-center cursor-pointer transition-all duration-300 hover:scale-105 group ${theme.ring}`}
          title={isListening ? "Listening... Click to Pause" : "Click to Speak Directive"}
        >
          {/* Animated Dashed Tech Ring */}
          <div className="absolute inset-1 rounded-full border border-dashed border-cyan-400/30 animate-[spin_30s_linear_infinite] group-hover:border-cyan-300/60 pointer-events-none" />

          {/* Inner Audio-Reactive Core */}
          <div 
            className={`w-full h-full rounded-full border flex flex-col items-center justify-center transition-all duration-150 relative overflow-hidden ${theme.core}`}
            style={{
              transform: `scale(${1 + (isListening ? Math.min(0.2, audioLevel * 0.25) : 0)})`
            }}
          >
            {/* Animated Equalizer Sound Bars (Visible when listening or speaking) */}
            {isListening ? (
              <div className="flex items-center gap-1 h-6">
                {barHeights.map((h, i) => (
                  <div
                    key={i}
                    className="w-1 rounded-full bg-emerald-400 transition-all duration-75 shadow-[0_0_8px_#10b981]"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            ) : (
              <Mic className={`w-7 h-7 sm:w-8 sm:h-8 transition-transform group-hover:scale-110 ${theme.text}`} />
            )}
          </div>
        </div>

        {/* Pop-up Voice HUD Launch Button Cluster */}
        <div className="flex flex-col gap-1.5">
          <button
            type="button"
            onClick={handlePopout}
            title="Pop out Always-on-Top Floating Voice Command HUD (Floats over WhatsApp & other applications)"
            className="px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-xl border border-cyan-400/50 bg-cyan-950/70 hover:bg-cyan-900/90 hover:border-cyan-300 text-cyan-200 hover:text-white transition-all shadow-[0_0_20px_rgba(0,240,255,0.25)] flex items-center gap-1.5 group cursor-pointer"
          >
            <ExternalLink className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] sm:text-[11px] font-mono font-bold tracking-wider uppercase">
              POP-UP HUD
            </span>
          </button>

          {onMinimizeToMiniHUD && (
            <button
              type="button"
              onClick={handleMinimize}
              title="Minimize website to compact corner pill"
              className="px-2 py-1 rounded-lg border border-cyan-500/20 bg-slate-900/60 hover:bg-cyan-950/40 hover:border-cyan-400 text-slate-400 hover:text-cyan-300 transition-all flex items-center justify-center gap-1 group cursor-pointer"
            >
              <Minimize2 className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
              <span className="text-[9px] font-mono tracking-wider uppercase">
                MINI
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Holographic Interactive Status Badge */}
      <div 
        onClick={onToggleListening}
        className={`mt-2.5 px-3.5 py-1 rounded-full border text-[10px] font-mono tracking-widest uppercase cursor-pointer hover:scale-105 transition-all backdrop-blur-md shadow-[0_0_15px_rgba(0,240,255,0.1)] flex items-center gap-2 ${theme.badgeBg}`}
      >
        <div className={`w-1.5 h-1.5 rounded-full ${isListening ? 'bg-emerald-400 animate-ping' : 'bg-cyan-400'}`} />
        <span>
          {isListening ? (interimTranscript ? `"${interimTranscript.slice(0, 30)}..."` : theme.badge) : theme.badge}
        </span>
      </div>
    </div>
  );
};
