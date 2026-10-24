import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  Key,
  Volume2,
  Mic,
  Monitor,
  CheckCircle2,
  AlertCircle,
  Save,
  RotateCw,
  Eye,
  EyeOff,
  Sparkles,
  ShieldCheck,
  Fingerprint,
  ExternalLink
} from 'lucide-react';
import { SafeSettings } from '../types';

interface SettingsViewProps {
  settings: SafeSettings;
  onUpdateSettings: (newSettings: any) => Promise<void>;
  reducedMotion: boolean;
  onToggleReducedMotion: () => void;
  wakeWordEnabled: boolean;
  onToggleWakeWord: () => void;
  voiceSpeed: number;
  onChangeVoiceSpeed: (speed: number) => void;
  onTestConnection: () => Promise<any>;
  onTriggerIrisScan?: () => void;
  onEnrollVoice?: () => Promise<boolean>;
  isVoiceEnrolling?: boolean;
  voiceEnrollProgress?: number;
  strictVoiceSecurity?: boolean;
  onToggleStrictVoice?: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  settings,
  onUpdateSettings,
  reducedMotion,
  onToggleReducedMotion,
  wakeWordEnabled,
  onToggleWakeWord,
  voiceSpeed,
  onChangeVoiceSpeed,
  onTestConnection,
  onTriggerIrisScan,
  onEnrollVoice,
  isVoiceEnrolling = false,
  voiceEnrollProgress = 0,
  strictVoiceSecurity = true,
  onToggleStrictVoice
}) => {
  const [provider, setProvider] = useState(settings.ai_provider || 'openai');
  const [model, setModel] = useState(settings.ai_model || 'gpt-4o-mini');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [geminiKey, setGeminiKey] = useState('');
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [baseUrl, setBaseUrl] = useState(settings.openai_base_url || '');
  const [agentUrl, setAgentUrl] = useState(settings.desktop_agent_url || 'http://127.0.0.1:8001');
  const [agentToken, setAgentToken] = useState('');
  const [authorizedUser, setAuthorizedUser] = useState(settings.authorized_user || 'Abdur Rahman');
  const [biometricEnforce, setBiometricEnforce] = useState(settings.biometric_enforcement ?? true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveStatus(null);
    try {
      const payload: any = {
        ai_provider: provider,
        ai_model: model,
        openai_base_url: baseUrl,
        desktop_agent_url: agentUrl,
        authorized_user: authorizedUser,
        biometric_enforcement: biometricEnforce
      };
      if (apiKey.trim()) {
        payload.openai_api_key = apiKey.trim();
      }
      if (geminiKey.trim()) {
        payload.gemini_api_key = geminiKey.trim();
      }
      if (agentToken.trim()) {
        payload.desktop_agent_token = agentToken.trim();
      }
      await onUpdateSettings(payload);
      setSaveStatus('Subsystem configurations committed successfully.');
      setApiKey('');
      setGeminiKey('');
      setAgentToken('');
    } catch (err: any) {
      setSaveStatus(`Failed to update settings: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await onTestConnection();
      setTestResult(res);
    } catch (e: any) {
      setTestResult({ error: e.message });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-4 flex flex-col gap-6 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-cyan-500/20">
        <div>
          <h2 className="text-base font-bold text-cyan-300 tracking-wider flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-cyan-400" /> SYSTEM CONFIGURATION & SECURITY PROTOCOLS
          </h2>
          <p className="text-slate-400 text-xs">
            Manage AI cognitive providers (Gemini/Groq/OpenAI), biometric iris/voice profiles, and host security.
          </p>
        </div>
      </div>

      {saveStatus && (
        <div className="jarvis-panel p-3 rounded-xl border border-cyan-400 text-cyan-300 text-xs flex items-center justify-between">
          <span>{saveStatus}</span>
          <button onClick={() => setSaveStatus(null)} className="text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Biometric Identity & Voice Recognition */}
        <div className="jarvis-panel rounded-2xl p-6 flex flex-col gap-4 tech-corner border border-cyan-500/30">
          <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 text-xs font-bold text-cyan-400">
            <span className="flex items-center gap-2">
              <Fingerprint className="w-4 h-4 text-cyan-400" />
              <span>BIOMETRIC IDENTITY & SPEAKER RECOGNITION</span>
            </span>
            <span className="text-[10px] text-emerald-400">LEVEL 10 SECURITY</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Authorized Commander Name:</label>
              <input
                type="text"
                value={authorizedUser}
                onChange={(e) => setAuthorizedUser(e.target.value)}
                placeholder="e.g. Abdur Rahman"
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div className="flex flex-col justify-center gap-2">
              <div className="text-slate-400">Biometric Interlock Status:</div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={onTriggerIrisScan}
                  className="px-3.5 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 text-xs flex items-center gap-1.5 transition"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Test Iris Biometric Scanner</span>
                </button>
              </div>
            </div>
          </div>

          {/* Voiceprint Speaker Verification Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900 border border-cyan-500/20 flex items-center justify-between">
              <div>
                <div className="font-bold text-cyan-200">Strict Voice Biometrics</div>
                <div className="text-[10px] text-slate-400">Only Abdur's voice can issue directives</div>
              </div>
              <input
                type="checkbox"
                checked={strictVoiceSecurity}
                onChange={onToggleStrictVoice}
                className="w-4 h-4 accent-cyan-400 cursor-pointer"
              />
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900 border border-cyan-500/20 flex items-center justify-between">
              <div>
                <div className="font-bold text-cyan-200">Acoustic Voice Calibration</div>
                <div className="text-[10px] text-slate-400">
                  {isVoiceEnrolling ? `Calibrating voice: ${voiceEnrollProgress}%` : 'Calibrate 3s voice sample'}
                </div>
              </div>
              <button
                type="button"
                onClick={onEnrollVoice}
                disabled={isVoiceEnrolling}
                className="px-3 py-1.5 rounded-lg bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 text-xs disabled:opacity-40"
              >
                {isVoiceEnrolling ? 'Listening...' : 'Calibrate'}
              </button>
            </div>
          </div>
        </div>

        {/* Section 2: AI Cognitive Providers (Gemini / Groq / OpenAI) */}
        <div className="jarvis-panel rounded-2xl p-6 flex flex-col gap-4 tech-corner">
          <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 text-xs font-bold text-cyan-400">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              <span>AI COGNITIVE PROVIDERS & API KEYS</span>
            </div>
            <a
              href="https://aistudio.google.com/apikey"
              target="_blank"
              rel="noreferrer"
              className="text-cyan-300 hover:text-white flex items-center gap-1 text-[11px] underline"
            >
              <ExternalLink className="w-3 h-3" /> Get Free Gemini API Key
            </a>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-wrap items-center gap-2 pb-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">Quick Presets:</span>
            {[
              { id: 'gemini', label: 'Google Gemini (Free API)', model: 'gemini-2.0-flash', base: 'https://generativelanguage.googleapis.com/v1beta/openai/' },
              { id: 'groq', label: 'Groq Cloud (Free & Ultra-Fast)', model: 'llama-3.3-70b-versatile', base: 'https://api.groq.com/openai/v1' },
              { id: 'openai', label: 'OpenAI (GPT-4o)', model: 'gpt-4o-mini', base: '' },
              { id: 'openrouter', label: 'OpenRouter', model: 'meta-llama/llama-3.3-70b-instruct', base: 'https://openrouter.ai/api/v1' },
              { id: 'ollama', label: 'Local Ollama', model: 'llama3', base: 'http://localhost:11434/v1' },
              { id: 'mock', label: 'Smart Local J.A.R.V.I.S. Persona', model: 'jarvis-offline', base: '' },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  if (p.id === 'openai') {
                    setProvider('openai');
                  } else if (p.id === 'mock') {
                    setProvider('mock');
                  } else {
                    setProvider('openai-compatible');
                  }
                  setModel(p.model);
                  setBaseUrl(p.base);
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-900 border border-cyan-500/20 text-cyan-300 hover:bg-cyan-500/20 text-[11px] transition"
              >
                {p.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Architecture Provider:</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              >
                <option value="openai">OpenAI Official API</option>
                <option value="openai-compatible">OpenAI-Compatible (Google Gemini / Groq / Ollama)</option>
                <option value="mock">Smart Built-in Offline Fallback</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Target Model Identifier:</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="e.g. gemini-2.0-flash, gpt-4o-mini, llama-3.3-70b-versatile"
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              />
            </div>

            {/* Google Gemini Key */}
            <div>
              <label className="text-slate-400 block mb-1">
                Google Gemini API Key {settings.has_gemini_key && <span className="text-emerald-400">({settings.masked_gemini_key})</span>}:
              </label>
              <div className="relative">
                <input
                  type={showGeminiKey ? 'text' : 'password'}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder={settings.has_gemini_key ? '•••••••••••••••• (Leave blank to retain)' : 'Paste AIzaSy... Gemini API Key'}
                  className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 pr-10 text-cyan-200 focus:outline-none focus:border-cyan-400"
                />
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-cyan-400"
                >
                  {showGeminiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* OpenAI / Groq Key */}
            <div>
              <label className="text-slate-400 block mb-1">
                OpenAI / Groq API Key {settings.has_openai_key && <span className="text-emerald-400">({settings.masked_key})</span>}:
              </label>
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={settings.has_openai_key ? '•••••••••••••••• (Leave blank to retain)' : 'Paste sk-... or gsk_... Key'}
                  className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 pr-10 text-cyan-200 focus:outline-none focus:border-cyan-400"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-cyan-400"
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="md:col-span-2">
              <label className="text-slate-400 block mb-1">Custom Base URL (Optional):</label>
              <input
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="e.g. https://generativelanguage.googleapis.com/v1beta/openai/ for Gemini or https://api.groq.com/openai/v1 for Groq"
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Windows Desktop Agent Security */}
        <div className="jarvis-panel rounded-2xl p-6 flex flex-col gap-4 tech-corner">
          <div className="flex items-center gap-2 pb-2 border-b border-cyan-500/20 text-xs font-bold text-cyan-400">
            <Monitor className="w-4 h-4" />
            <span>LOCAL WINDOWS DESKTOP AGENT SECURITY</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Desktop Service Loopback URL:</label>
              <input
                type="text"
                value={agentUrl}
                onChange={(e) => setAgentUrl(e.target.value)}
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Security Bearer Pairing Token:</label>
              <input
                type="password"
                value={agentToken}
                onChange={(e) => setAgentToken(e.target.value)}
                placeholder="Leave blank to retain configured security token"
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>
        </div>

        {/* Section 4: Voice, Acoustics & Motion */}
        <div className="jarvis-panel rounded-2xl p-6 flex flex-col gap-4 tech-corner">
          <div className="flex items-center gap-2 pb-2 border-b border-cyan-500/20 text-xs font-bold text-cyan-400">
            <Volume2 className="w-4 h-4" />
            <span>ACOUSTICS, WAKE-WORD & VISUALS</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            {/* Wake Word */}
            <div className="p-3.5 rounded-xl bg-slate-900 border border-cyan-500/20 flex items-center justify-between">
              <div>
                <div className="font-bold text-cyan-200">"Hey JARVIS" Wake Word</div>
                <div className="text-[10px] text-slate-400">Listen for hotword in browser</div>
              </div>
              <input
                type="checkbox"
                checked={wakeWordEnabled}
                onChange={onToggleWakeWord}
                className="w-4 h-4 accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Reduced Motion */}
            <div className="p-3.5 rounded-xl bg-slate-900 border border-cyan-500/20 flex items-center justify-between">
              <div>
                <div className="font-bold text-cyan-200">Reduced Motion Mode</div>
                <div className="text-[10px] text-slate-400">Optimize for lower GPU load</div>
              </div>
              <input
                type="checkbox"
                checked={reducedMotion}
                onChange={onToggleReducedMotion}
                className="w-4 h-4 accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Voice Speed */}
            <div className="p-3.5 rounded-xl bg-slate-900 border border-cyan-500/20 flex flex-col gap-1.5 justify-center">
              <div className="flex justify-between font-bold text-cyan-200">
                <span>Speech Pace</span>
                <span>{voiceSpeed}x</span>
              </div>
              <input
                type="range"
                min="0.8"
                max="1.4"
                step="0.1"
                value={voiceSpeed}
                onChange={(e) => onChangeVoiceSpeed(parseFloat(e.target.value))}
                className="accent-cyan-400 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Buttons & Diagnostic Test */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="px-4 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-300 hover:bg-slate-800 text-xs flex items-center gap-2 transition"
          >
            <RotateCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin' : ''}`} />
            <span>Test Core Subsystem Connectivity</span>
          </button>

          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-cyan-500 text-slate-950 font-bold hover:bg-cyan-400 text-xs flex items-center gap-2 transition shadow-[0_0_15px_rgba(0,240,255,0.4)]"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'COMMITTING SETTINGS...' : 'SAVE & APPLY CONFIGURATION'}</span>
          </button>
        </div>
      </form>

      {/* Diagnostics Test Output */}
      {testResult && (
        <div className="jarvis-panel rounded-2xl p-4 border border-cyan-500/30 text-xs space-y-2">
          <div className="font-bold text-cyan-300">DIAGNOSTIC TEST RESULTS:</div>
          <pre className="bg-slate-950 p-3 rounded-lg text-emerald-300 overflow-x-auto text-[11px]">
            {JSON.stringify(testResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
