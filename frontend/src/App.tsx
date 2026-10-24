import React, { useState, useEffect, useCallback, useRef } from 'react';
import { CommandCenter } from './pages/CommandCenter';
import { LoginScreen } from './components/LoginScreen';
import { VoiceEnrollmentScreen } from './components/VoiceEnrollmentScreen';
import { SettingsOverlay } from './components/SettingsOverlay';
import { FloatingMiniHUD } from './components/FloatingMiniHUD';
import { useVoiceInput } from './hooks/useVoiceInput';
import { useVoiceOutput } from './hooks/useVoiceOutput';
import { api } from './services/api';
import {
  JarvisState,
  ChatMessage,
  ConversationSummary,
  ToolDefinition,
  MemoryItem,
  DesktopStatus,
  SafeSettings,
  ActivityLogItem
} from './types';
import { AlertTriangle, Check, X } from 'lucide-react';

export const App: React.FC = () => {
  // Authentication State
  const [sessionToken, setSessionToken] = useState<string | null>(() => {
    return sessionStorage.getItem('jarvis_session_token');
  });
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(sessionStorage.getItem('jarvis_session_token'));
  });

  // Voice Enrollment State (Only shown once on first login)
  const [isVoiceEnrolled, setIsVoiceEnrolled] = useState<boolean>(() => {
    const status = localStorage.getItem('jarvis_voice_enrolled');
    return status === 'true' || status === 'skipped';
  });

  // Floating Mini-HUD Mode State
  const [isMiniMode, setIsMiniMode] = useState<boolean>(false);

  // Discreet Settings Overlay State
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Core System States
  const [jarvisState, setJarvisState] = useState<JarvisState>('idle');
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [desktopOnline, setDesktopOnline] = useState<boolean>(false);
  const [aiConnected, setAiConnected] = useState<boolean>(false);

  // Data Store
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLogItem[]>([]);
  const [lastResponse, setLastResponse] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Desktop Status
  const [desktopStatus, setDesktopStatus] = useState<DesktopStatus>({
    connected: false,
    service_url: 'http://127.0.0.1:8001',
    approved_apps: [],
    allowed_directories: [],
    pending_approvals: 0
  });

  // Pending Approval Modal State
  const [pendingApproval, setPendingApproval] = useState<{ id: string; message: string } | null>(null);

  // User Settings
  const [safeSettings, setSafeSettings] = useState<SafeSettings>({
    assistant_name: 'J.A.R.V.I.S.',
    assistant_voice: 'onyx',
    ai_provider: 'gemini',
    ai_model: 'gemini-2.0-flash',
    has_openai_key: false,
    masked_key: '',
    has_gemini_key: true,
    masked_gemini_key: 'AQ.A...vmBQ',
    desktop_agent_enabled: true,
    desktop_agent_url: 'http://127.0.0.1:8001',
    has_desktop_token: true,
    search_provider: 'duckduckgo',
    authorized_user: 'Abdur Rahman',
    biometric_enforcement: false
  });

  const [voiceSpeed, setVoiceSpeed] = useState(1.0);

  // Verify existing session on page load
  useEffect(() => {
    if (sessionToken) {
      api.verifySession(sessionToken).then((res) => {
        if (!res.authenticated) {
          sessionStorage.removeItem('jarvis_session_token');
          setSessionToken(null);
          setIsAuthenticated(false);
        }
      }).catch(() => {
        sessionStorage.removeItem('jarvis_session_token');
        setSessionToken(null);
        setIsAuthenticated(false);
      });
    }
  }, [sessionToken]);

  // Voice Output Hook
  const { isSpeaking, speak, stop: stopSpeaking } = useVoiceOutput({
    rate: voiceSpeed,
    onStart: () => setJarvisState('speaking'),
    onEnd: () => {
      if (jarvisState === 'speaking') {
        setJarvisState('idle');
      }
    }
  });

  // Voice Input Hook with fast debounce
  const handleFinalVoiceTranscript = (text: string) => {
    if (text.trim()) {
      handleDispatchCommand(text.trim());
    }
  };

  const {
    isListening,
    interimTranscript,
    audioLevel,
    startListening,
    stopListening
  } = useVoiceInput({
    onFinalTranscript: handleFinalVoiceTranscript
  });

  const toggleListening = () => {
    if (isListening) {
      stopListening();
      setJarvisState('idle');
    } else {
      if (isSpeaking) stopSpeaking();
      startListening();
      setJarvisState('listening');
    }
  };

  // Poll Initial Subsystems & Telemetry
  const refreshAllSubsystems = useCallback(async () => {
    try {
      const health = await api.getHealth();
      setBackendOnline(health.status === 'healthy' || health.status === 'degraded');
      setAiConnected(health.ai_connected);
      setDesktopOnline(health.desktop_agent_connected);
    } catch {
      setBackendOnline(false);
    }

    try {
      const dStatus = await api.getDesktopStatus();
      setDesktopStatus(dStatus);
      setDesktopOnline(dStatus.connected);
    } catch {}

    try {
      const s = await api.getSettings();
      setSafeSettings(s);
    } catch {}
  }, []);

  useEffect(() => {
    refreshAllSubsystems();
    const interval = setInterval(refreshAllSubsystems, 8000);
    return () => clearInterval(interval);
  }, [refreshAllSubsystems]);

  // Deduplication ref for fast speech dispatch
  const lastDispatchedRef = useRef<{ text: string; time: number }>({ text: '', time: 0 });

  // Handle Command Submission
  const handleDispatchCommand = async (cmdText: string) => {
    const cleanCmd = cmdText.trim();
    if (!cleanCmd) return;

    // Deduplicate rapid triggers within 1.4s
    const now = Date.now();
    if (cleanCmd.toLowerCase() === lastDispatchedRef.current.text.toLowerCase() && (now - lastDispatchedRef.current.time) < 1400) {
      return;
    }
    lastDispatchedRef.current = { text: cleanCmd, time: now };

    if (isListening) stopListening();
    if (isSpeaking) stopSpeaking();

    setIsProcessing(true);
    setJarvisState('thinking');

    // Add user message to UI immediately
    const tempUserMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: cleanCmd,
      created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      setJarvisState('executing_tool');
      const response = await api.sendChat(cleanCmd, activeConversationId || undefined);

      if (!activeConversationId && response.conversation_id) {
        setActiveConversationId(response.conversation_id);
      }

      setLastResponse(response.message);

      // Append assistant message
      const asstMsg: ChatMessage = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: response.message,
        created_at: new Date().toISOString(),
        tool_calls: response.tool_calls,
        status: 'complete'
      };
      setMessages((prev) => [...prev, asstMsg]);

      // Handle Awaiting Approval state
      if (response.status === 'awaiting_approval') {
        setJarvisState('awaiting_approval');
        setPendingApproval({
          id: response.tool_calls?.[0]?.id || 'approval_req',
          message: response.message
        });
      } else {
        setJarvisState('speaking');
        speak(response.message);
      }

      refreshAllSubsystems();
    } catch (err: any) {
      setJarvisState('error');
      const errorMsg = `Directive disruption: ${err.message}`;
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: errorMsg,
          created_at: new Date().toISOString(),
          status: 'error'
        }
      ]);
      speak("Encountered a complication processing the directive, sir.");
      setTimeout(() => setJarvisState('idle'), 3500);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Approvals
  const handleResolveApproval = async (approvalId: string, approved: boolean) => {
    try {
      await api.approveDesktopAction(approvalId, approved);
      setPendingApproval(null);
      setJarvisState(approved ? 'success' : 'idle');
      speak(approved ? 'Directive authorized and dispatched, sir.' : 'Directive cancelled, sir.');
      setTimeout(() => setJarvisState('idle'), 2000);
      refreshAllSubsystems();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  // Login Success
  const handleLoginSuccess = (token: string) => {
    setSessionToken(token);
    setIsAuthenticated(true);
  };

  // Voice Enrollment Complete
  const handleVoiceEnrollmentComplete = () => {
    setIsVoiceEnrolled(true);
  };

  // Re-enroll Voice from Settings
  const handleReEnrollVoice = () => {
    localStorage.removeItem('jarvis_voice_enrolled');
    setIsVoiceEnrolled(false);
  };

  // Logout / Lock
  const handleLogout = async () => {
    try {
      if (sessionToken) await api.logout(sessionToken);
    } catch {}
    sessionStorage.removeItem('jarvis_session_token');
    setSessionToken(null);
    setIsAuthenticated(false);
    setIsSettingsOpen(false);
    setIsMiniMode(false);
    if (isSpeaking) stopSpeaking();
    if (isListening) stopListening();
  };

  // 1. Unauthenticated -> Show Login Screen
  if (!isAuthenticated) {
    return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
  }

  // 2. Authenticated but first-time voice enrollment pending -> Show Voice Enrollment Screen
  if (!isVoiceEnrolled) {
    return <VoiceEnrollmentScreen onComplete={handleVoiceEnrollmentComplete} />;
  }

  // 3. Authenticated & Enrolled -> Main J.A.R.V.I.S. Command Center
  return (
    <div className="w-full h-screen overflow-hidden bg-[#020617] text-slate-100 flex flex-col font-sans">
      {/* Floating Mini HUD Mode */}
      {isMiniMode ? (
        <FloatingMiniHUD
          state={jarvisState}
          isListening={isListening}
          audioLevel={audioLevel}
          onToggleListening={toggleListening}
          lastTranscript={interimTranscript}
          onExpand={() => setIsMiniMode(false)}
          onStopSpeaking={stopSpeaking}
          isSpeaking={isSpeaking}
        />
      ) : (
        /* Full-Screen Immersive Command Center */
        <CommandCenter
          state={jarvisState}
          systemInfo={desktopStatus.system_info}
          activityLogs={activityLogs}
          isListening={isListening}
          audioLevel={audioLevel}
          onToggleListening={toggleListening}
          onSubmitCommand={handleDispatchCommand}
          lastResponse={lastResponse}
          isProcessing={isProcessing}
          messages={messages}
          interimTranscript={interimTranscript}
          isSpeaking={isSpeaking}
          onStopSpeaking={stopSpeaking}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onLogout={handleLogout}
          onToggleMiniHUD={() => setIsMiniMode(true)}
        />
      )}

      {/* Security Interlock / Pending Approval Banner */}
      {pendingApproval && (
        <div className="fixed top-14 left-1/2 -translate-x-1/2 z-50 w-full max-w-xl bg-amber-950/90 border border-amber-500/60 p-4 rounded-2xl shadow-[0_0_40px_rgba(245,158,11,0.3)] backdrop-blur-xl font-mono text-xs">
          <div className="flex items-center gap-2.5 text-amber-300 mb-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 animate-pulse" />
            <span>
              <strong>SECURITY INTERLOCK:</strong> {pendingApproval.message}
            </span>
          </div>
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={() => handleResolveApproval(pendingApproval.id, true)}
              className="px-4 py-1.5 rounded-lg bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition flex items-center gap-1 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
            >
              <Check className="w-4 h-4" /> AUTHORIZE
            </button>
            <button
              onClick={() => handleResolveApproval(pendingApproval.id, false)}
              className="px-4 py-1.5 rounded-lg bg-red-600 text-white font-bold hover:bg-red-500 transition flex items-center gap-1"
            >
              <X className="w-4 h-4" /> REJECT
            </button>
          </div>
        </div>
      )}

      {/* Discreet Settings Overlay */}
      <SettingsOverlay
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={safeSettings}
        onUpdateSettings={async (data) => {
          await api.updateSettings(data);
          await refreshAllSubsystems();
        }}
        onReEnrollVoice={handleReEnrollVoice}
        onLogout={handleLogout}
        backendOnline={backendOnline}
        desktopOnline={desktopOnline}
        aiConnected={aiConnected}
      />
    </div>
  );
};

export default App;
