import React, { useState, useRef, useEffect } from 'react';
import {
  Mic,
  MicOff,
  Send,
  Square,
  Settings,
  LogOut,
  Maximize2,
  Minimize2,
  Terminal,
  Cpu,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  Volume2,
  ExternalLink
} from 'lucide-react';
import { AICore } from '../components/AICore';
import { InteractiveVoiceControl } from '../components/InteractiveVoiceControl';
import { JarvisState, SystemInfo, ActivityLogItem, ChatMessage } from '../types';
import { api } from '../services/api';

interface CommandCenterProps {
  state: JarvisState;
  onStateChange?: (state: JarvisState) => void;
  systemInfo?: SystemInfo;
  activityLogs?: ActivityLogItem[];
  isListening: boolean;
  audioLevel: number;
  onToggleListening: () => void;
  onSubmitCommand: (cmd: string) => void;
  lastResponse?: string;
  isProcessing: boolean;
  reducedMotion?: boolean;
  messages: ChatMessage[];
  interimTranscript?: string;
  isSpeaking?: boolean;
  onStopSpeaking?: () => void;
  onOpenSettings: () => void;
  onLogout: () => void;
  onToggleMiniHUD?: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({
  state,
  systemInfo,
  isListening,
  audioLevel,
  onToggleListening,
  onSubmitCommand,
  isProcessing,
  reducedMotion = false,
  messages,
  interimTranscript = '',
  isSpeaking = false,
  onStopSpeaking,
  onOpenSettings,
  onLogout,
  onToggleMiniHUD
}) => {
  const [inputText, setInputText] = useState('');
  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, isProcessing, interimTranscript]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;
    onSubmitCommand(inputText.trim());
    setInputText('');
  };

  const getStateDescription = () => {
    switch (state) {
      case 'listening':
        return { label: 'LISTENING // AUDIO DETECTED', color: 'border-cyan-400 text-cyan-300 bg-cyan-950/40 animate-pulse' };
      case 'processing':
      case 'thinking':
        return { label: 'EVALUATING // COGNITIVE TREE ACTIVE', color: 'border-blue-400 text-blue-300 bg-blue-950/40 animate-pulse' };
      case 'speaking':
        return { label: 'SYNTHESIZING // AUDIO PLAYBACK ENGAGED', color: 'border-sky-400 text-sky-300 bg-sky-950/40' };
      case 'executing_tool':
        return { label: 'EXECUTING // DESKTOP AGENCY DIRECTIVE', color: 'border-cyan-400 text-cyan-200 bg-cyan-950/60' };
      case 'awaiting_approval':
        return { label: 'SECURITY INTERLOCK // APPROVAL REQUIRED', color: 'border-amber-400 text-amber-300 bg-amber-950/40 animate-pulse' };
      case 'error':
        return { label: 'EXCEPTION // RECOVERY PROTOCOL ACTIVE', color: 'border-red-400 text-red-300 bg-red-950/40' };
      case 'success':
        return { label: 'RESOLVED // ALL SUBSYSTEMS NOMINAL', color: 'border-emerald-400 text-emerald-300 bg-emerald-950/40' };
      case 'idle':
      default:
        return { label: 'ONLINE // READY FOR DIRECTIVE', color: 'border-cyan-500/30 text-cyan-400 bg-slate-900/60' };
    }
  };

  const stateBadge = getStateDescription();

  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#020617] text-slate-100 flex flex-col justify-between font-sans select-none">
      {/* Background Holographic Atmosphere */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-950/20 via-[#020617] to-[#01040f] pointer-events-none" />
      <div 
        className="absolute inset-0 opacity-[0.025] pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(to right, #00f0ff 1px, transparent 1px), linear-gradient(to bottom, #00f0ff 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }}
      />

      {/* Subtle Orbital Background Rings */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[720px] h-[720px] border border-cyan-500/10 rounded-full pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[540px] h-[540px] border border-cyan-400/10 rounded-full border-dashed animate-[spin_80s_linear_infinite] pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] border border-cyan-600/5 rounded-full pointer-events-none" />

      {/* TOP HUD STATUS BAR */}
      <div className="relative z-20 w-full px-6 py-4 flex items-center justify-between border-b border-cyan-500/15 backdrop-blur-md font-mono text-xs">
        {/* Left: System Identifier & State Badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_#00f0ff]" />
            <span className="font-bold tracking-[0.25em] text-white uppercase text-sm">
              J.A.R.V.I.S.
            </span>
            <span className="text-[10px] text-cyan-400/80 px-2 py-0.5 rounded border border-cyan-500/30 bg-cyan-950/40">
              MARK-II
            </span>
          </div>

          <div className={`hidden md:inline-flex items-center px-3 py-1 rounded-full border text-[10px] tracking-wider uppercase font-semibold ${stateBadge.color}`}>
            {stateBadge.label}
          </div>
        </div>

        {/* Right: Telemetry & Controls */}
        <div className="flex items-center gap-3">
          {systemInfo && (
            <div className="hidden lg:flex items-center gap-4 text-[11px] text-slate-400 mr-2 border-r border-cyan-500/20 pr-4">
              <span>CPU: <span className="text-cyan-300 font-bold">{systemInfo.cpu_percent}%</span></span>
              <span>RAM: <span className="text-cyan-300 font-bold">{systemInfo.memory_percent}%</span></span>
            </div>
          )}

          {/* Pop-up Voice Command Option Button */}
          <button
            onClick={() => {
              api.executeDesktopAction('launch_hud', {}).catch(() => {});
            }}
            title="Pop out Always-on-Top Floating Voice Command HUD (Floats over WhatsApp & other apps)"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-cyan-400/50 bg-cyan-950/60 hover:bg-cyan-900/80 hover:border-cyan-300 text-cyan-300 hover:text-white transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)] text-[11px] font-mono font-bold tracking-wider uppercase cursor-pointer"
          >
            <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">POP-UP VOICE HUD</span>
            <span className="sm:hidden">POP-UP</span>
          </button>

          {/* Mini-HUD Popout Toggle */}
          {onToggleMiniHUD && (
            <button
              onClick={() => {
                api.executeDesktopAction('launch_hud', {}).catch(() => {});
                onToggleMiniHUD();
              }}
              title="Toggle Floating Mini HUD (Always on Top over WhatsApp & other apps)"
              className="p-2 rounded-lg border border-cyan-500/20 bg-slate-900/60 hover:bg-cyan-950/40 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 transition-all"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
          )}

          {/* Discreet Settings Overlay Button */}
          <button
            onClick={onOpenSettings}
            title="System Settings & Telemetry"
            className="p-2 rounded-lg border border-cyan-500/20 bg-slate-900/60 hover:bg-cyan-950/40 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 transition-all flex items-center gap-1.5"
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline text-[11px]">CONFIG</span>
          </button>

          {/* Logout Button */}
          <button
            onClick={onLogout}
            title="Lock J.A.R.V.I.S."
            className="p-2 rounded-lg border border-red-500/20 bg-red-950/20 hover:bg-red-900/40 hover:border-red-400 text-red-400 transition-all"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* MAIN IMMERSIVE STAGE: AI CORE & COMPACT CONVERSATION */}
      <div className="relative z-10 flex-1 flex flex-col lg:flex-row items-center justify-between p-4 lg:p-8 gap-6 max-w-7xl mx-auto w-full overflow-hidden">
        {/* HERO: CENTRAL AI CORE (ARC REACTOR) */}
        <div className="flex-1 flex flex-col items-center justify-center relative w-full h-[320px] sm:h-[400px] lg:h-full max-h-[520px]">
          {/* Animated 3D Core */}
          <div className="relative w-full h-full flex items-center justify-center">
            <AICore
              state={state}
              audioLevel={audioLevel}
              reducedMotion={reducedMotion}
              onClick={onToggleListening}
            />

            {/* Interactive Voice Command Control & Minimize Pop-up Button */}
            <div className="absolute -bottom-6 z-20">
              <InteractiveVoiceControl
                state={state}
                isListening={isListening}
                audioLevel={audioLevel}
                onToggleListening={onToggleListening}
                interimTranscript={interimTranscript}
                isProcessing={isProcessing}
                onMinimizeToMiniHUD={onToggleMiniHUD}
              />
            </div>
          </div>
        </div>

        {/* CONVERSATION & TASK EXECUTION FEED (COMPACT HUD) */}
        {messages && messages.length > 0 && (
          <div className="w-full lg:w-[440px] h-[220px] sm:h-[260px] lg:h-[480px] flex flex-col bg-[#050b14]/80 backdrop-blur-xl border border-cyan-500/25 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(0,0,0,0.6)]">
            <div className="px-4 py-2.5 border-b border-cyan-500/20 bg-slate-950/60 flex items-center justify-between font-mono text-[10px] text-cyan-400 tracking-wider">
              <span>TELEMETRY STREAM // LOG</span>
              <span className="text-slate-500">{messages.length} ENTRIES</span>
            </div>

            <div ref={chatScrollRef} className="flex-1 p-4 overflow-y-auto space-y-3 font-mono text-xs">
              {messages.map((msg) => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[90%] p-3 rounded-xl border text-xs leading-relaxed ${
                        isUser
                          ? 'bg-cyan-950/30 border-cyan-500/30 text-cyan-100 rounded-tr-none'
                          : 'bg-slate-900/60 border-slate-700/60 text-slate-200 rounded-tl-none shadow-[0_0_15px_rgba(0,240,255,0.05)]'
                      }`}
                    >
                      <div className="text-[9px] uppercase tracking-wider text-slate-400 mb-1">
                        {isUser ? 'COMMANDER ABDUR RAHMAN' : 'J.A.R.V.I.S.'}
                      </div>
                      <div className="whitespace-pre-wrap">{msg.content}</div>

                      {/* Executed Tools Badge */}
                      {msg.tool_calls && msg.tool_calls.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-cyan-500/20 flex flex-col gap-1">
                          {msg.tool_calls.map((tool, idx) => (
                            <div
                              key={idx}
                              className="text-[10px] px-2 py-1 rounded bg-black/40 border border-cyan-500/20 text-cyan-300 flex items-center gap-1.5"
                            >
                              <Terminal className="w-3 h-3 text-cyan-400" />
                              <span>{tool.name}</span>
                              <span className="text-emerald-400 ml-auto">✓ EXECUTED</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Processing / Executing indicator */}
              {isProcessing && (
                <div className="flex items-center gap-2 p-2.5 rounded-lg border border-cyan-500/30 bg-cyan-950/20 text-cyan-300 text-xs">
                  <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                  <span>Processing directive on Windows host...</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* BOTTOM COMMAND INPUT SECTION */}
      <div className="relative z-20 w-full px-4 pb-6 pt-2 max-w-4xl mx-auto">
        {/* Interim Speech Transcription Banner */}
        {isListening && interimTranscript && (
          <div className="mb-2.5 px-4 py-2 rounded-xl border border-cyan-400/40 bg-cyan-950/60 text-cyan-200 font-mono text-xs flex items-center gap-2.5 shadow-[0_0_20px_rgba(0,240,255,0.2)] animate-pulse">
            <Mic className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="italic">"{interimTranscript}"</span>
          </div>
        )}

        {/* Command Form */}
        <form
          onSubmit={handleSubmit}
          className="relative flex items-center gap-2 p-1.5 rounded-2xl border border-cyan-500/40 bg-[#050b14]/90 backdrop-blur-xl shadow-[0_0_35px_rgba(0,240,255,0.15)] focus-within:border-cyan-400 focus-within:shadow-[0_0_40px_rgba(0,240,255,0.25)] transition-all"
        >
          {/* Microphone Button */}
          <button
            type="button"
            onClick={onToggleListening}
            title={isListening ? 'Stop Listening' : 'Voice Command'}
            className={`p-3 rounded-xl transition-all flex items-center justify-center ${
              isListening
                ? 'bg-red-500/30 border border-red-400 text-red-300 animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.4)]'
                : 'bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-500/30 text-cyan-400'
            }`}
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Floating Pop-up HUD Option Button */}
          <button
            type="button"
            onClick={() => {
              api.executeDesktopAction('launch_hud', {}).catch(() => {});
            }}
            title="Pop out Always-on-Top Floating Voice Command HUD (Floats over WhatsApp & other apps)"
            className="px-3 py-2.5 rounded-xl bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-400/40 hover:border-cyan-300 text-cyan-300 hover:text-cyan-100 transition-all flex items-center gap-1.5 group shadow-[0_0_15px_rgba(0,240,255,0.15)] cursor-pointer"
          >
            <ExternalLink className="w-4 h-4 group-hover:scale-110 transition-transform text-cyan-400" />
            <span className="hidden md:inline text-xs font-mono font-bold uppercase tracking-wider">
              Pop-up HUD
            </span>
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Awaiting command..."
            disabled={isProcessing}
            className="flex-1 bg-transparent px-3 py-2 text-sm text-cyan-100 placeholder-slate-500 focus:outline-none font-mono"
          />

          {/* Speech Stop Button */}
          {isSpeaking && onStopSpeaking && (
            <button
              type="button"
              onClick={onStopSpeaking}
              title="Stop Speech Playback"
              className="p-2.5 rounded-xl border border-sky-400/40 bg-sky-950/40 text-sky-300 hover:bg-sky-900/60 transition-colors"
            >
              <Square className="w-4 h-4 fill-current" />
            </button>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isProcessing || !inputText.trim()}
            className="p-3 rounded-xl bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed text-black font-bold transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)]"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
