import React, { useState } from 'react';
import { X, Cpu, Key, Volume2, Shield, LogOut, Check, AlertCircle, RefreshCw, ExternalLink } from 'lucide-react';
import { SafeSettings } from '../types';
import { api } from '../services/api';

interface SettingsOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  settings: SafeSettings;
  onUpdateSettings: (newSettings: Partial<SafeSettings>) => Promise<void>;
  onReEnrollVoice: () => void;
  onLogout: () => void;
  backendOnline: boolean;
  desktopOnline: boolean;
  aiConnected: boolean;
}

export const SettingsOverlay: React.FC<SettingsOverlayProps> = ({
  isOpen,
  onClose,
  settings,
  onUpdateSettings,
  onReEnrollVoice,
  onLogout,
  backendOnline,
  desktopOnline,
  aiConnected
}) => {
  const [geminiKeyInput, setGeminiKeyInput] = useState('');
  const [voiceSpeed, setVoiceSpeed] = useState(1.0);
  const [testingGemini, setTestingGemini] = useState(false);
  const [geminiStatus, setGeminiStatus] = useState<{ status: string; message: string; online: boolean } | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  if (!isOpen) return null;

  const handleTestGemini = async () => {
    setTestingGemini(true);
    setGeminiStatus(null);
    try {
      const res = await api.testGemini(geminiKeyInput.trim() || undefined);
      setGeminiStatus(res);
    } catch (err: any) {
      setGeminiStatus({ online: false, status: 'error', message: err.message || 'Connection test failed.' });
    } finally {
      setTestingGemini(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const updates: any = {};
      if (geminiKeyInput.trim()) {
        updates.gemini_api_key = geminiKeyInput.trim();
        updates.ai_provider = 'gemini';
        updates.ai_model = 'gemini-2.0-flash';
      }
      await onUpdateSettings(updates);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex justify-end font-sans select-none animate-fadeIn">
      {/* Click outside to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Slide-in Drawer */}
      <div className="w-full max-w-md bg-[#050b14] border-l border-cyan-500/30 h-full p-6 flex flex-col justify-between overflow-y-auto shadow-[-10px_0_40px_rgba(0,0,0,0.8)]">
        <div>
          {/* Top Bar */}
          <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20">
            <div>
              <div className="text-[10px] text-cyan-400 font-mono tracking-widest uppercase">System Configuration</div>
              <h3 className="text-lg font-bold text-white tracking-wider">J.A.R.V.I.S. OVERLAY</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-cyan-950/40 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Subsystems Telemetry Grid */}
          <div className="my-5 flex flex-col gap-2 font-mono text-xs">
            <div className="text-[10px] text-slate-400 uppercase tracking-widest mb-1">Subsystem Matrix</div>
            <div className="grid grid-cols-3 gap-2">
              <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col items-center gap-1 text-center">
                <span className="text-[10px] text-slate-400">CORE (8000)</span>
                <span className={`text-[11px] font-bold ${backendOnline ? 'text-emerald-400' : 'text-red-400'}`}>
                  {backendOnline ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col items-center gap-1 text-center">
                <span className="text-[10px] text-slate-400">AGENT (8001)</span>
                <span className={`text-[11px] font-bold ${desktopOnline ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {desktopOnline ? 'PAIRED' : 'STANDBY'}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col items-center gap-1 text-center">
                <span className="text-[10px] text-slate-400">AI NEURAL</span>
                <span className={`text-[11px] font-bold ${aiConnected ? 'text-cyan-400' : 'text-sky-300'}`}>
                  {aiConnected ? 'CONNECTED' : 'LOCAL ENGINE'}
                </span>
              </div>
            </div>
          </div>

          {/* Gemini AI Integration */}
          <div className="my-5 p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex flex-col gap-3 font-mono">
            <div className="flex items-center justify-between">
              <span className="text-xs text-cyan-300 font-semibold flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-cyan-400" />
                GOOGLE GEMINI AI
              </span>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-[10px] text-cyan-400/80 hover:text-cyan-300 flex items-center gap-1 underline"
              >
                Get Key <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>

            <div className="text-[11px] text-slate-400">
              {settings.has_gemini_key ? (
                <span className="text-emerald-400">Active Key: {settings.masked_gemini_key}</span>
              ) : (
                'No Gemini key configured in backend. Running on smart local engine.'
              )}
            </div>

            <input
              type="password"
              value={geminiKeyInput}
              onChange={(e) => setGeminiKeyInput(e.target.value)}
              placeholder="Paste new Gemini API key..."
              className="w-full bg-slate-950/80 border border-cyan-500/30 rounded-lg px-3 py-2 text-xs text-cyan-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400"
            />

            <div className="flex items-center gap-2">
              <button
                onClick={handleTestGemini}
                disabled={testingGemini}
                className="flex-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 py-1.5 rounded-lg text-xs tracking-wider uppercase transition-colors flex items-center justify-center gap-1.5"
              >
                {testingGemini ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Cpu className="w-3 h-3" />}
                {testingGemini ? 'Testing...' : 'Test Connection'}
              </button>

              <button
                onClick={handleSave}
                disabled={isSaving || !geminiKeyInput.trim()}
                className="bg-cyan-600 hover:bg-cyan-500 text-black font-semibold px-4 py-1.5 rounded-lg text-xs tracking-wider uppercase transition-colors flex items-center justify-center gap-1 disabled:opacity-40"
              >
                {saveSuccess ? <Check className="w-3 h-3" /> : null}
                {saveSuccess ? 'Saved' : 'Save'}
              </button>
            </div>

            {geminiStatus && (
              <div className={`p-2.5 rounded-lg text-[11px] flex items-start gap-2 ${
                geminiStatus.online ? 'bg-emerald-950/40 border border-emerald-500/40 text-emerald-300' : 'bg-red-950/40 border border-red-500/40 text-red-300'
              }`}>
                {geminiStatus.online ? <Check className="w-3.5 h-3.5 shrink-0 mt-0.5" /> : <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />}
                <span>{geminiStatus.message}</span>
              </div>
            )}
          </div>

          {/* Voice Configuration */}
          <div className="my-5 p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex flex-col gap-3 font-mono">
            <div className="text-xs text-slate-300 font-semibold flex items-center gap-1.5">
              <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
              VOICE & ACOUSTICS
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Speech Rate</span>
              <span className="text-cyan-400">{voiceSpeed.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="1.5"
              step="0.1"
              value={voiceSpeed}
              onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
              className="w-full accent-cyan-400"
            />

            <button
              onClick={() => {
                onClose();
                onReEnrollVoice();
              }}
              className="w-full mt-2 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded-lg text-xs tracking-wider uppercase transition-colors flex items-center justify-center gap-1.5"
            >
              <RefreshCw className="w-3 h-3" />
              Re-enroll Voice Profile
            </button>
          </div>
        </div>

        {/* Bottom Actions: Lock & Logout */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[10px] text-slate-500 font-mono">
            USER: {settings.authorized_user || 'Abdur Rahman'}
          </div>

          <button
            onClick={onLogout}
            className="bg-red-950/40 hover:bg-red-900/60 border border-red-500/40 text-red-300 px-3.5 py-1.5 rounded-lg text-xs font-mono tracking-wider uppercase transition-colors flex items-center gap-1.5"
          >
            <LogOut className="w-3.5 h-3.5" />
            Lock & Exit
          </button>
        </div>
      </div>
    </div>
  );
};
