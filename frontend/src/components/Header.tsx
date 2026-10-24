import React from 'react';
import {
  Shield,
  Activity,
  Cpu,
  Volume2,
  VolumeX,
  Settings as SettingsIcon,
  MessageSquare,
  Wrench,
  Database,
  Monitor,
  LayoutGrid,
  Eye,
  Lock,
  UserCheck
} from 'lucide-react';
import { JarvisState, ScreenView } from '../types';

interface HeaderProps {
  currentView: ScreenView;
  onViewChange: (view: ScreenView) => void;
  state: JarvisState;
  backendOnline: boolean;
  desktopOnline: boolean;
  aiConnected: boolean;
  isSpeaking: boolean;
  onStopSpeaking: () => void;
  onTriggerLock?: () => void;
  userName?: string;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onViewChange,
  state,
  backendOnline,
  desktopOnline,
  aiConnected,
  isSpeaking,
  onStopSpeaking,
  onTriggerLock,
  userName = 'Abdur Rahman'
}) => {
  const [timeStr, setTimeStr] = React.useState('');

  React.useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const navItems: { id: ScreenView; label: string; icon: React.ReactNode }[] = [
    { id: 'command', label: 'Command Center', icon: <LayoutGrid className="w-4 h-4" /> },
    { id: 'chat', label: 'Dialogue', icon: <MessageSquare className="w-4 h-4" /> },
    { id: 'tools', label: 'Capabilities', icon: <Wrench className="w-4 h-4" /> },
    { id: 'memory', label: 'Memory Bank', icon: <Database className="w-4 h-4" /> },
    { id: 'desktop', label: 'Windows Agent', icon: <Monitor className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings', icon: <SettingsIcon className="w-4 h-4" /> }
  ];

  return (
    <header className="w-full bg-[#030712]/90 backdrop-blur-md border-b border-cyan-500/20 px-4 py-3 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Left: Branding & Core Status */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-cyan-950/40 border border-cyan-400/40 shadow-[0_0_15px_rgba(0,240,255,0.2)]">
            <Shield className="w-5 h-5 text-cyan-400" />
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-base tracking-widest text-cyan-300">J.A.R.V.I.S.</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-cyan-500/30 text-cyan-400 bg-cyan-950/30">
                MARK-VIII
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-emerald-500/40 text-emerald-300 bg-emerald-950/30 flex items-center gap-1">
                <UserCheck className="w-2.5 h-2.5" /> {userName.split(' ')[0].toUpperCase()}
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-400 flex items-center gap-2">
              <span>{timeStr}</span>
              <span>•</span>
              <span className="text-cyan-400 uppercase">{state}</span>
            </div>
          </div>
        </div>

        {/* Center: Navigation Bar */}
        <nav className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-cyan-500/20 overflow-x-auto max-w-full">
          {navItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 whitespace-nowrap ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 shadow-[0_0_12px_rgba(0,240,255,0.2)] font-semibold'
                    : 'text-slate-400 hover:text-cyan-200 hover:bg-slate-800/40'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right: Subsystem Telemetry Badges & Biometric Controls */}
        <div className="flex items-center gap-2 text-xs font-mono">
          {isSpeaking && (
            <button
              onClick={onStopSpeaking}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/20 border border-amber-400/40 text-amber-300 hover:bg-amber-500/30 transition animate-pulse"
              title="Stop Speech"
            >
              <VolumeX className="w-3.5 h-3.5" />
              <span>INTERRUPT</span>
            </button>
          )}

          {/* Biometric Lockdown Button */}
          {onTriggerLock && (
            <button
              onClick={onTriggerLock}
              className="flex items-center gap-1 px-2.5 py-1 rounded border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 transition"
              title="Engage Biometric Iris Lockdown"
            >
              <Lock className="w-3 h-3 text-cyan-400" />
              <span className="text-[10px]">LOCK</span>
            </button>
          )}

          {/* Backend Status */}
          <div
            className={`flex items-center gap-1 px-2 py-0.5 rounded border ${
              backendOnline
                ? 'border-emerald-500/30 text-emerald-400 bg-emerald-950/20'
                : 'border-red-500/30 text-red-400 bg-red-950/20'
            }`}
            title={backendOnline ? 'Backend API Core Operational' : 'Backend API Core Offline'}
          >
            <Activity className="w-3 h-3" />
            <span className="text-[10px]">CORE</span>
          </div>

          {/* Desktop Agent Status */}
          <div
            className={`flex items-center gap-1 px-2 py-0.5 rounded border ${
              desktopOnline
                ? 'border-cyan-500/30 text-cyan-400 bg-cyan-950/20'
                : 'border-slate-700 text-slate-500 bg-slate-900/40'
            }`}
            title={desktopOnline ? 'Windows Desktop Agent Paired' : 'Windows Desktop Agent Offline'}
          >
            <Monitor className="w-3 h-3" />
            <span className="text-[10px]">AGENT</span>
          </div>

          {/* AI Intelligence Provider Status */}
          <div
            className={`flex items-center gap-1 px-2 py-0.5 rounded border ${
              aiConnected
                ? 'border-indigo-500/30 text-indigo-400 bg-indigo-950/20'
                : 'border-amber-500/30 text-amber-400 bg-amber-950/20'
            }`}
            title={aiConnected ? 'LLM Intelligence Active' : 'Offline / Smart Persona Active'}
          >
            <Cpu className="w-3 h-3" />
            <span className="text-[10px]">{aiConnected ? 'AI' : 'LOCAL'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
