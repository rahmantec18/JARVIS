import React, { useState } from 'react';
import {
  Monitor,
  Cpu,
  Layers,
  HardDrive,
  Battery,
  Play,
  Folder,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Bell,
  RefreshCw,
  Terminal,
  Camera,
  Volume2,
  VolumeX,
  Lock,
  Settings,
  Search,
  Trash2,
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';
import { DesktopStatus } from '../types';

interface DesktopCenterProps {
  desktopStatus: DesktopStatus;
  onRefresh: () => void;
  onLaunchApp: (appId: string) => Promise<any>;
  onTriggerNotify: (title: string, message: string) => Promise<any>;
  onApproveAction: (approvalId: string, approved: boolean) => Promise<any>;
  onExecuteAction?: (action: string, parameters?: Record<string, any>, confirmed?: boolean) => Promise<any>;
}

export const DesktopCenter: React.FC<DesktopCenterProps> = ({
  desktopStatus,
  onRefresh,
  onLaunchApp,
  onTriggerNotify,
  onApproveAction,
  onExecuteAction
}) => {
  const [launchingApp, setLaunchingApp] = useState<string | null>(null);
  const [customApp, setCustomApp] = useState('');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Terminal state
  const [terminalCmd, setTerminalCmd] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<string | null>(null);
  const [executingCmd, setExecutingCmd] = useState(false);
  const [copiedOutput, setCopiedOutput] = useState(false);

  // Screenshot state
  const [takingScreenshot, setTakingScreenshot] = useState(false);
  const [screenshotPreview, setScreenshotPreview] = useState<{ path: string; name: string; b64?: string } | null>(null);

  // Process Kill state
  const [processTarget, setProcessTarget] = useState('');
  const [killingProc, setKillingProc] = useState(false);

  // File Search state
  const [fileQuery, setFileQuery] = useState('');
  const [fileResults, setFileResults] = useState<any[]>([]);
  const [searchingFiles, setSearchingFiles] = useState(false);

  // Notification state
  const [notifyTitle, setNotifyTitle] = useState('J.A.R.V.I.S. Alert');
  const [notifyMsg, setNotifyMsg] = useState('System telemetry nominal.');

  // Generic action dispatcher helper
  const dispatchAction = async (action: string, params: Record<string, any> = {}, confirmed = false) => {
    if (onExecuteAction) {
      return await onExecuteAction(action, params, confirmed);
    }
    return { success: false, error: 'Action dispatcher unavailable' };
  };

  const handleLaunch = async (appId: string) => {
    setLaunchingApp(appId);
    setActionFeedback(null);
    try {
      const res = await onLaunchApp(appId);
      if (res.requires_confirmation) {
        setActionFeedback(`Action flagged: '${appId}' requires user confirmation.`);
      } else if (res.success) {
        setActionFeedback(`Dispatched launch directive for '${appId}'.`);
      } else {
        setActionFeedback(`Launch failed: ${res.error}`);
      }
    } catch (e: any) {
      setActionFeedback(`Error: ${e.message}`);
    } finally {
      setLaunchingApp(null);
    }
  };

  const handleCustomLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customApp.trim()) return;
    setLaunchingApp('custom');
    try {
      const res = await dispatchAction('launch_custom_app', { target: customApp.trim() });
      if (res.success) {
        setActionFeedback(`Dispatched launch for '${customApp}'.`);
        setCustomApp('');
      } else {
        setActionFeedback(`Launch error: ${res.error || 'Failed'}`);
      }
    } catch (e: any) {
      setActionFeedback(`Error: ${e.message}`);
    } finally {
      setLaunchingApp(null);
    }
  };

  const handleRunCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!terminalCmd.trim()) return;
    setExecutingCmd(true);
    setTerminalOutput(null);
    try {
      const res = await dispatchAction('run_command', { command: terminalCmd.trim() });
      const out = res.result?.output || res.output || res.stdout || res.error || (res.success ? 'Command executed with no console output.' : 'Execution failed.');
      setTerminalOutput(out);
      setActionFeedback(`PowerShell executed in ${res.duration_sec || 0.1}s.`);
    } catch (e: any) {
      setTerminalOutput(`Error: ${e.message}`);
    } finally {
      setExecutingCmd(false);
    }
  };

  const handleVolume = async (act: string) => {
    try {
      const res = await dispatchAction('control_volume', { action: act });
      setActionFeedback(res.message || `Volume ${act} executed.`);
    } catch (e: any) {
      setActionFeedback(`Volume error: ${e.message}`);
    }
  };

  const handleScreenshot = async () => {
    setTakingScreenshot(true);
    try {
      const res = await dispatchAction('take_screenshot', { include_base64: true });
      if (res.success || res.result?.success) {
        const data = res.result || res;
        setScreenshotPreview({
          path: data.file_path,
          name: data.file_name,
          b64: data.base64
        });
        setActionFeedback(`Screenshot captured and saved to ${data.file_name}`);
      } else {
        setActionFeedback(`Screenshot failed: ${res.error || 'Desktop display unavailable'}`);
      }
    } catch (e: any) {
      setActionFeedback(`Screenshot error: ${e.message}`);
    } finally {
      setTakingScreenshot(false);
    }
  };

  const handleLockPC = async () => {
    try {
      await dispatchAction('lock_workstation', {});
      setActionFeedback('Lock workstation directive dispatched.');
    } catch (e: any) {
      setActionFeedback(`Lock error: ${e.message}`);
    }
  };

  const handleOpenSettings = async () => {
    try {
      await dispatchAction('open_settings', {});
      setActionFeedback('Opened Windows Settings.');
    } catch (e: any) {
      setActionFeedback(`Settings error: ${e.message}`);
    }
  };

  const handleKillProcess = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!processTarget.trim()) return;
    setKillingProc(true);
    try {
      const res = await dispatchAction('kill_process', { target: processTarget.trim() });
      setActionFeedback(res.message || res.error || 'Process kill sent.');
      if (res.success) setProcessTarget('');
      onRefresh();
    } catch (e: any) {
      setActionFeedback(`Kill error: ${e.message}`);
    } finally {
      setKillingProc(false);
    }
  };

  const handleSearchFiles = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileQuery.trim()) return;
    setSearchingFiles(true);
    try {
      const res = await dispatchAction('search_files', { query: fileQuery.trim(), base_dir: 'C:\\Users\\abdur' });
      setFileResults(res.files || res.result?.files || []);
      setActionFeedback(`Search returned ${res.count || 0} match(es).`);
    } catch (e: any) {
      setActionFeedback(`Search error: ${e.message}`);
    } finally {
      setSearchingFiles(false);
    }
  };

  const handleRevealFile = async (path: string) => {
    try {
      await dispatchAction('reveal_file', { path });
      setActionFeedback('Opened in Windows Explorer.');
    } catch (e: any) {
      setActionFeedback(`Explorer error: ${e.message}`);
    }
  };

  const handleSendNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await onTriggerNotify(notifyTitle, notifyMsg);
      setActionFeedback('Native Windows notification dispatched.');
    } catch (e: any) {
      setActionFeedback(`Notification error: ${e.message}`);
    }
  };

  const copyTerminalOutput = () => {
    if (terminalOutput) {
      navigator.clipboard.writeText(terminalOutput);
      setCopiedOutput(true);
      setTimeout(() => setCopiedOutput(false), 2000);
    }
  };

  const sys = desktopStatus.system_info;

  return (
    <div className="w-full max-w-7xl mx-auto p-4 flex flex-col gap-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-cyan-500/20 font-mono">
        <div>
          <h2 className="text-base font-bold text-cyan-300 tracking-wider flex items-center gap-2">
            <Monitor className="w-5 h-5 text-cyan-400" /> WINDOWS FULL SYSTEM CONTROLLER
          </h2>
          <p className="text-slate-400 text-xs">
            Direct host agency: applications, PowerShell, volume, telemetry, and file system.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-mono ${
              desktopStatus.connected
                ? 'border-emerald-500/40 text-emerald-400 bg-emerald-950/30'
                : 'border-red-500/40 text-red-400 bg-red-950/30'
            }`}
          >
            {desktopStatus.connected ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
            <span>{desktopStatus.connected ? 'DESKTOP AGENT ACTIVE' : 'DESKTOP SERVICE OFFLINE'}</span>
          </div>

          <button
            onClick={onRefresh}
            className="p-2 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10 transition"
            title="Refresh status"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className="jarvis-panel p-3 rounded-xl border border-cyan-400/40 font-mono text-xs text-cyan-300 flex items-center justify-between">
          <span>{actionFeedback}</span>
          <button onClick={() => setActionFeedback(null)} className="text-slate-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Real Hardware Telemetry Gauges */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        {/* CPU */}
        <div className="jarvis-panel rounded-2xl p-4 flex flex-col gap-2 tech-corner">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-cyan-400" /> PROCESSOR
            </span>
            <span className="text-cyan-300 font-bold">{sys?.cpu_percent || 0}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-cyan-500/20">
            <div
              className="h-full bg-cyan-400 transition-all duration-300"
              style={{ width: `${sys?.cpu_percent || 0}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-500">
            {sys?.cpu_cores ? `${sys.cpu_cores} Logical Cores` : 'Windows Cores'}
          </div>
        </div>

        {/* Memory */}
        <div className="jarvis-panel rounded-2xl p-4 flex flex-col gap-2 tech-corner">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-cyan-400" /> SYSTEM RAM
            </span>
            <span className="text-cyan-300 font-bold">{sys?.memory_percent || 0}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-cyan-500/20">
            <div
              className="h-full bg-cyan-400 transition-all duration-300"
              style={{ width: `${sys?.memory_percent || 0}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-500">
            {sys?.memory_used_gb} GB / {sys?.memory_total_gb} GB Commited
          </div>
        </div>

        {/* Disk */}
        <div className="jarvis-panel rounded-2xl p-4 flex flex-col gap-2 tech-corner">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <HardDrive className="w-4 h-4 text-cyan-400" /> STORAGE (C:)
            </span>
            <span className="text-cyan-300 font-bold">{sys?.disk_percent || 0}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-cyan-500/20">
            <div
              className="h-full bg-cyan-400 transition-all duration-300"
              style={{ width: `${sys?.disk_percent || 0}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-500">
            {sys?.disk_free_gb ? `${sys.disk_free_gb} GB Free Space` : 'Local Disk'}
          </div>
        </div>

        {/* Battery */}
        <div className="jarvis-panel rounded-2xl p-4 flex flex-col gap-2 tech-corner">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Battery className="w-4 h-4 text-cyan-400" /> POWER CELL
            </span>
            <span className="text-cyan-300 font-bold">
              {sys?.battery?.percent !== undefined ? `${sys.battery.percent}%` : 'AC Main'}
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-cyan-500/20">
            <div
              className="h-full bg-emerald-400 transition-all duration-300"
              style={{ width: `${sys?.battery?.percent || 100}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-500">
            {sys?.battery?.charging ? 'Charging (Plugged In)' : 'Operating on Battery / AC'}
          </div>
        </div>
      </div>

      {/* QUICK SYSTEM HARDWARE DIRECTIVES */}
      <div className="jarvis-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 font-mono text-xs tech-corner">
        <div className="flex items-center gap-2 text-cyan-400 font-bold">
          <Cpu className="w-4 h-4" />
          <span>QUICK HARDWARE DIRECTIVES:</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {/* Audio controls */}
          <button
            onClick={() => handleVolume('mute')}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 transition flex items-center gap-1.5"
            title="Toggle Audio Mute"
          >
            <VolumeX className="w-3.5 h-3.5" />
            <span>Mute / Unmute</span>
          </button>
          <button
            onClick={() => handleVolume('up')}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 transition flex items-center gap-1.5"
            title="Volume Up"
          >
            <Volume2 className="w-3.5 h-3.5" />
            <span>Vol +</span>
          </button>
          <button
            onClick={() => handleVolume('down')}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 transition flex items-center gap-1.5"
            title="Volume Down"
          >
            <Volume2 className="w-3.5 h-3.5" />
            <span>Vol -</span>
          </button>

          {/* Screenshot */}
          <button
            onClick={handleScreenshot}
            disabled={takingScreenshot}
            className="px-3 py-1.5 rounded-xl bg-cyan-500/20 border border-cyan-400/50 text-cyan-200 hover:bg-cyan-500/30 transition flex items-center gap-1.5 shadow-[0_0_10px_rgba(0,240,255,0.2)]"
            title="Capture Screenshot"
          >
            <Camera className="w-3.5 h-3.5 text-cyan-400" />
            <span>{takingScreenshot ? 'Capturing...' : 'Capture Screen'}</span>
          </button>

          {/* Settings */}
          <button
            onClick={handleOpenSettings}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 transition flex items-center gap-1.5"
            title="Open Windows Settings"
          >
            <Settings className="w-3.5 h-3.5" />
            <span>Windows Settings</span>
          </button>

          {/* Lock */}
          <button
            onClick={handleLockPC}
            className="px-3 py-1.5 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-300 hover:bg-amber-900/40 transition flex items-center gap-1.5"
            title="Lock PC"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Lock Workstation</span>
          </button>
        </div>
      </div>

      {/* SCREENSHOT PREVIEW MODAL */}
      {screenshotPreview && (
        <div className="jarvis-panel rounded-2xl p-4 border border-cyan-400 font-mono text-xs flex flex-col gap-3">
          <div className="flex items-center justify-between text-cyan-300 font-bold">
            <span className="flex items-center gap-2">
              <Camera className="w-4 h-4" /> SCREENSHOT CAPTURED: {screenshotPreview.name}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleRevealFile(screenshotPreview.path)}
                className="px-2.5 py-1 rounded bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 border border-cyan-400/40 text-[11px] flex items-center gap-1"
              >
                <ExternalLink className="w-3 h-3" /> Reveal in Explorer
              </button>
              <button
                onClick={() => setScreenshotPreview(null)}
                className="text-slate-400 hover:text-white px-2 py-1"
              >
                Close
              </button>
            </div>
          </div>
          {screenshotPreview.b64 && (
            <div className="rounded-xl overflow-hidden border border-cyan-500/30 max-h-[300px] flex items-center justify-center bg-black">
              <img
                src={`data:image/png;base64,${screenshotPreview.b64}`}
                alt="Desktop Screenshot"
                className="max-h-[300px] w-auto object-contain"
              />
            </div>
          )}
          <div className="text-[11px] text-slate-400 truncate">Saved to: {screenshotPreview.path}</div>
        </div>
      )}

      {/* INTERACTIVE POWERSHELL TERMINAL */}
      <div className="jarvis-panel rounded-2xl p-5 flex flex-col gap-3 tech-corner font-mono">
        <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 text-xs text-cyan-400 font-bold">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span>DIRECT POWERSHELL HOST CONSOLE</span>
          </div>
          <span className="text-[10px] text-slate-500">LIVE SHELL BRIDGE</span>
        </div>

        <form onSubmit={handleRunCommand} className="flex gap-2">
          <div className="relative flex-1">
            <span className="absolute left-3 top-2.5 text-cyan-400 font-bold text-xs">PS &gt;</span>
            <input
              type="text"
              value={terminalCmd}
              onChange={(e) => setTerminalCmd(e.target.value)}
              placeholder="e.g. Get-Process, ipconfig, dir, git status, ping 8.8.8.8"
              className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl py-2 pl-12 pr-3 text-cyan-200 text-xs focus:outline-none focus:border-cyan-400"
            />
          </div>
          <button
            type="submit"
            disabled={executingCmd || !terminalCmd.trim()}
            className="px-5 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 transition text-xs font-bold disabled:opacity-40"
          >
            {executingCmd ? 'Executing...' : 'Run Command'}
          </button>
        </form>

        {terminalOutput && (
          <div className="relative mt-2">
            <div className="flex items-center justify-between px-3 py-1 bg-slate-950 rounded-t-lg border-t border-x border-cyan-500/30 text-[10px] text-slate-400">
              <span>Standard Output / Return</span>
              <button
                onClick={copyTerminalOutput}
                className="hover:text-cyan-300 flex items-center gap-1"
                title="Copy output"
              >
                {copiedOutput ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copiedOutput ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
            <pre className="bg-slate-950 p-3 rounded-b-lg border-b border-x border-cyan-500/30 text-emerald-300 overflow-x-auto text-xs max-h-60 leading-relaxed font-mono whitespace-pre-wrap">
              {terminalOutput}
            </pre>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Approved Application Launcher Grid (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <div className="jarvis-panel rounded-2xl p-5 flex flex-col gap-4 tech-corner">
            <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 font-mono text-xs">
              <span className="text-cyan-400 font-bold tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400" /> UNIVERSAL APPLICATION LAUNCHER
              </span>
              <span className="text-[10px] text-slate-500">FULL ACCESS ACTIVE</span>
            </div>

            {/* Custom App Launcher Box */}
            <form onSubmit={handleCustomLaunch} className="flex gap-2 font-mono text-xs">
              <input
                type="text"
                value={customApp}
                onChange={(e) => setCustomApp(e.target.value)}
                placeholder="Launch any app by name or path (e.g. steam, vlc, code, word)..."
                className="flex-1 bg-slate-900 border border-cyan-500/30 rounded-xl p-2 text-cyan-200 focus:outline-none focus:border-cyan-400"
              />
              <button
                type="submit"
                disabled={!customApp.trim() || launchingApp === 'custom'}
                className="px-4 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 transition text-xs font-bold disabled:opacity-40"
              >
                {launchingApp === 'custom' ? 'Opening...' : 'Launch App'}
              </button>
            </form>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono">
              {desktopStatus.approved_apps.map((app) => (
                <div
                  key={app.id}
                  className="p-3.5 rounded-xl border border-cyan-500/20 bg-slate-900/60 flex items-center justify-between hover:border-cyan-500/40 transition jarvis-panel-interactive"
                >
                  <div className="truncate pr-2">
                    <div className="text-xs font-bold text-cyan-200 truncate">{app.name}</div>
                    <div className="text-[10px] text-slate-400 truncate">{app.description}</div>
                    {app.requires_approval && (
                      <span className="text-[9px] text-amber-400 flex items-center gap-1 mt-1">
                        <AlertTriangle className="w-2.5 h-2.5" /> Requires Confirm
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => handleLaunch(app.id)}
                    disabled={launchingApp === app.id}
                    className="p-2 rounded-lg bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 transition text-xs flex items-center gap-1 shrink-0"
                    title={`Launch ${app.name}`}
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span className="text-[10px]">OPEN</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Windows Notification Trigger */}
          <div className="jarvis-panel rounded-2xl p-5 flex flex-col gap-3 tech-corner font-mono">
            <div className="flex items-center gap-2 pb-2 border-b border-cyan-500/20 text-xs text-cyan-400 font-bold">
              <Bell className="w-4 h-4" />
              <span>DISPATCH WINDOWS TOAST NOTIFICATION</span>
            </div>
            <form onSubmit={handleSendNotification} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Title:</label>
                <input
                  type="text"
                  value={notifyTitle}
                  onChange={(e) => setNotifyTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2 text-cyan-200 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Message Body:</label>
                <input
                  type="text"
                  value={notifyMsg}
                  onChange={(e) => setNotifyMsg(e.target.value)}
                  className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2 text-cyan-200 focus:outline-none"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 transition text-xs font-bold"
              >
                Trigger Desktop Toast
              </button>
            </form>
          </div>
        </div>

        {/* File Search & Process Management (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4 font-mono">
          {/* File Search Box */}
          <div className="jarvis-panel rounded-2xl p-5 flex flex-col gap-3 tech-corner">
            <div className="pb-2 border-b border-cyan-500/20 text-xs text-cyan-400 font-bold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Search className="w-4 h-4" />
                <span>HOST FILE SEARCH</span>
              </span>
              <span className="text-[10px] text-slate-500">SYSTEM DRIVES</span>
            </div>
            <form onSubmit={handleSearchFiles} className="flex gap-2 text-xs">
              <input
                type="text"
                value={fileQuery}
                onChange={(e) => setFileQuery(e.target.value)}
                placeholder="Search file name (e.g. *.py, resume, notes)..."
                className="flex-1 bg-slate-900 border border-cyan-500/30 rounded-xl p-2 text-cyan-200 focus:outline-none focus:border-cyan-400"
              />
              <button
                type="submit"
                disabled={searchingFiles || !fileQuery.trim()}
                className="px-3 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 transition text-xs disabled:opacity-40"
              >
                {searchingFiles ? 'Searching...' : 'Search'}
              </button>
            </form>

            {fileResults.length > 0 && (
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {fileResults.map((f, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-slate-900/80 border border-cyan-500/20 flex items-center justify-between text-xs"
                  >
                    <div className="truncate pr-2">
                      <div className="text-cyan-200 font-bold truncate">{f.name}</div>
                      <div className="text-[10px] text-slate-400 truncate">{f.path}</div>
                    </div>
                    <button
                      onClick={() => handleRevealFile(f.path)}
                      className="p-1 rounded bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/40 shrink-0"
                      title="Reveal in Explorer"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top Running Processes & Process Termination */}
          <div className="jarvis-panel rounded-2xl p-5 flex flex-col gap-3">
            <div className="pb-2 border-b border-cyan-500/20 text-xs text-cyan-400 font-bold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                <span>PROCESS MANAGER</span>
              </span>
              <span className="text-[10px] text-slate-500">TASK CONTROL</span>
            </div>

            {/* Kill process form */}
            <form onSubmit={handleKillProcess} className="flex gap-2 text-xs">
              <input
                type="text"
                value={processTarget}
                onChange={(e) => setProcessTarget(e.target.value)}
                placeholder="Terminate PID or name (e.g. notepad.exe)..."
                className="flex-1 bg-slate-900 border border-cyan-500/30 rounded-xl p-2 text-cyan-200 focus:outline-none focus:border-red-400"
              />
              <button
                type="submit"
                disabled={killingProc || !processTarget.trim()}
                className="px-3 py-2 rounded-xl bg-red-500/20 border border-red-500/40 text-red-300 hover:bg-red-500/30 transition text-xs font-bold disabled:opacity-40 flex items-center gap-1"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>End Task</span>
              </button>
            </form>

            {sys?.top_processes && sys.top_processes.length > 0 && (
              <div className="space-y-2 pt-1">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">Top Memory Consumers:</div>
                {sys.top_processes.map((proc, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs text-slate-300">
                    <span className="truncate max-w-[160px] text-slate-200">{proc.name}</span>
                    <span className="text-cyan-400 text-[11px] font-bold">{proc.memory}% RAM</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
