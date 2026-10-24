import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Maximize2, Cpu, Square, ExternalLink } from 'lucide-react';
import { JarvisState } from '../types';
import { api } from '../services/api';

interface FloatingMiniHUDProps {
  state: JarvisState;
  isListening: boolean;
  audioLevel: number;
  onToggleListening: () => void;
  lastTranscript?: string;
  onExpand: () => void;
  onStopSpeaking?: () => void;
  isSpeaking?: boolean;
}

export const FloatingMiniHUD: React.FC<FloatingMiniHUDProps> = ({
  state,
  isListening,
  audioLevel,
  onToggleListening,
  lastTranscript,
  onExpand,
  onStopSpeaking,
  isSpeaking
}) => {
  // Position state (persisted or centered-right by default)
  const [position, setPosition] = useState<{ x: number; y: number }>(() => {
    try {
      const saved = localStorage.getItem('jarvis_mini_pos');
      if (saved) return JSON.parse(saved);
    } catch {}
    return { x: window.innerWidth - 220, y: window.innerHeight - 180 };
  });

  const isDraggingRef = useRef(false);
  const dragOffsetRef = useRef({ x: 0, y: 0 });

  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    dragOffsetRef.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y
    };
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const newX = Math.max(10, Math.min(window.innerWidth - 180, e.clientX - dragOffsetRef.current.x));
      const newY = Math.max(10, Math.min(window.innerHeight - 100, e.clientY - dragOffsetRef.current.y));
      const newPos = { x: newX, y: newY };
      setPosition(newPos);
      try {
        localStorage.setItem('jarvis_mini_pos', JSON.stringify(newPos));
      } catch {}
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const getStateColor = () => {
    switch (state) {
      case 'listening':
        return 'border-cyan-400 bg-cyan-950/70 text-cyan-300 shadow-[0_0_25px_rgba(0,240,255,0.4)] animate-pulse';
      case 'thinking':
      case 'processing':
        return 'border-blue-400 bg-blue-950/70 text-blue-300 shadow-[0_0_20px_rgba(56,189,248,0.3)]';
      case 'speaking':
        return 'border-sky-400 bg-sky-950/70 text-sky-300 shadow-[0_0_20px_rgba(34,211,238,0.3)]';
      case 'executing_tool':
        return 'border-cyan-400 bg-cyan-950/80 text-cyan-200 shadow-[0_0_25px_rgba(6,182,212,0.4)]';
      case 'error':
        return 'border-red-400 bg-red-950/70 text-red-300 shadow-[0_0_20px_rgba(239,68,68,0.3)]';
      case 'idle':
      default:
        return 'border-cyan-500/30 bg-[#050b14]/90 text-cyan-400 shadow-[0_0_20px_rgba(0,240,255,0.15)]';
    }
  };

  return (
    <div
      style={{ left: `${position.x}px`, top: `${position.y}px` }}
      className={`fixed z-50 flex items-center gap-3 p-2 rounded-full border backdrop-blur-xl transition-colors select-none font-sans cursor-move ${getStateColor()}`}
      onMouseDown={handleMouseDown}
    >
      {/* Mini Arc Reactor Icon */}
      <div 
        onClick={(e) => {
          e.stopPropagation();
          onToggleListening();
        }}
        className="w-12 h-12 rounded-full border border-cyan-400/50 bg-black/60 flex items-center justify-center relative cursor-pointer group"
      >
        <div 
          className="absolute inset-0 rounded-full border border-cyan-400/40 transition-transform duration-75"
          style={{ transform: `scale(${1 + (isListening ? audioLevel * 0.4 : 0)})` }}
        />
        {isListening ? (
          <Mic className="w-5 h-5 text-cyan-400 animate-pulse" />
        ) : (
          <Cpu className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
        )}
      </div>

      {/* Mini Info Pill */}
      <div className="flex flex-col pr-1 pointer-events-none max-w-[100px]">
        <div className="text-[9px] font-mono tracking-widest uppercase text-cyan-300 font-bold truncate">
          J.A.R.V.I.S.
        </div>
        <div className="text-[10px] text-slate-300 font-mono truncate">
          {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Ready'}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-1 pl-1 border-l border-cyan-500/20">
        {isSpeaking && onStopSpeaking && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onStopSpeaking();
            }}
            title="Stop Speech"
            className="p-1.5 rounded-full hover:bg-cyan-950 text-cyan-300 transition-colors"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
          </button>
        )}

        <button
          onClick={(e) => {
            e.stopPropagation();
            api.executeDesktopAction('launch_hud', {}).catch(() => {});
          }}
          title="Launch Always-on-Top Floating Desktop Icon (Over WhatsApp & other apps)"
          className="p-1.5 rounded-full hover:bg-cyan-950 text-cyan-300 transition-colors"
        >
          <ExternalLink className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onExpand();
          }}
          title="Expand to Fullscreen"
          className="p-1.5 rounded-full hover:bg-cyan-950 text-cyan-300 transition-colors"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
