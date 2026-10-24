import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, Check, ChevronRight, Volume2, Shield } from 'lucide-react';
import { api } from '../services/api';

interface VoiceEnrollmentScreenProps {
  onComplete: () => void;
}

export const VoiceEnrollmentScreen: React.FC<VoiceEnrollmentScreenProps> = ({ onComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [hasRecorded, setHasRecorded] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  const samplePhrase = "I am Commander Abdur Rahman, and I command J.A.R.V.I.S.";

  const startAudioMeter = (stream: MediaStream) => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioCtx();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      const src = ctx.createMediaStreamSource(stream);
      src.connect(analyser);

      audioContextRef.current = ctx;
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const update = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        setAudioLevel(Math.min((sum / dataArray.length) / 128, 1));
        animFrameRef.current = requestAnimationFrame(update);
      };
      update();
    } catch (e) {
      console.warn("Audio meter init error:", e);
    }
  };

  const stopAudioMeter = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    setAudioLevel(0);
  };

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      startAudioMeter(stream);

      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        setHasRecorded(true);
        stream.getTracks().forEach((t) => t.stop());
        stopAudioMeter();
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      alert("Microphone permission required to calibrate your voice profile. You may skip for now.");
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handlePlayRecording = () => {
    if (!audioUrl) return;
    if (audioElementRef.current) {
      audioElementRef.current.pause();
    }
    const audio = new Audio(audioUrl);
    audioElementRef.current = audio;
    setIsPlaying(true);
    audio.play();
    audio.onended = () => setIsPlaying(false);
  };

  const handleConfirm = async () => {
    setIsSaving(true);
    try {
      localStorage.setItem('jarvis_voice_enrolled', 'true');
      await api.saveVoiceProfile({ enrolled: true, phrase: samplePhrase });
    } catch (e) {}
    setIsSaving(false);
    onComplete();
  };

  const handleSkip = () => {
    localStorage.setItem('jarvis_voice_enrolled', 'skipped');
    onComplete();
  };

  useEffect(() => {
    return () => {
      stopAudioMeter();
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  return (
    <div className="fixed inset-0 z-50 bg-[#020617] flex items-center justify-center p-4 font-sans select-none">
      {/* Background Holographic Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-950/20 via-[#020617] to-[#01040f] pointer-events-none" />

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-lg bg-[#050b14]/90 backdrop-blur-xl border border-cyan-500/30 rounded-2xl p-8 shadow-[0_0_50px_rgba(0,240,255,0.15)] flex flex-col items-center gap-6">
        {/* Tech Corner Accents */}
        <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-cyan-400" />
        <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-cyan-400" />
        <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-cyan-400" />
        <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-cyan-400" />

        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-[10px] text-cyan-300 font-mono tracking-widest uppercase mb-2">
            <Shield className="w-3 h-3 text-cyan-400" />
            First-Time Setup
          </div>
          <h2 className="text-xl font-bold tracking-widest text-white uppercase">
            Voice Profile Initialization
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-sm font-mono">
            Record your voice to configure your JARVIS voice interaction profile.
          </p>
        </div>

        {/* Prompt Phrase Card */}
        <div className="w-full bg-cyan-950/20 border border-cyan-500/30 rounded-xl p-4 text-center font-mono">
          <div className="text-[10px] text-cyan-400 uppercase tracking-widest mb-1.5">
            Read the following phrase aloud:
          </div>
          <div className="text-sm text-cyan-100 font-semibold italic">
            "{samplePhrase}"
          </div>
        </div>

        {/* Visualizer & Mic State */}
        <div className="flex flex-col items-center gap-4 my-2">
          {/* Animated Central Pulse Ring */}
          <div className="relative flex items-center justify-center w-28 h-28">
            {isRecording && (
              <div 
                className="absolute inset-0 rounded-full border border-cyan-400/60 transition-all duration-75"
                style={{ transform: `scale(${1 + audioLevel * 0.5})`, opacity: 0.4 + audioLevel * 0.6 }}
              />
            )}
            <div className={`w-20 h-20 rounded-full border flex items-center justify-center transition-all ${
              isRecording 
                ? 'border-red-400 bg-red-950/30 shadow-[0_0_30px_rgba(239,68,68,0.4)]' 
                : hasRecorded 
                ? 'border-emerald-400 bg-emerald-950/30 shadow-[0_0_20px_rgba(16,185,129,0.3)]'
                : 'border-cyan-400/40 bg-cyan-950/30 shadow-[0_0_20px_rgba(0,240,255,0.2)]'
            }`}>
              <Mic className={`w-8 h-8 transition-colors ${
                isRecording ? 'text-red-400 animate-pulse' : hasRecorded ? 'text-emerald-400' : 'text-cyan-400'
              }`} />
            </div>
          </div>

          {/* Status Label */}
          <div className="font-mono text-xs text-cyan-300 tracking-wider">
            {isRecording ? (
              <span className="text-red-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                RECORDING AUDIO...
              </span>
            ) : hasRecorded ? (
              <span className="text-emerald-400 flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5" /> SAMPLE CAPTURED
              </span>
            ) : (
              'MICROPHONE READY'
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="w-full flex flex-col gap-3">
          {!isRecording ? (
            <button
              onClick={handleStartRecording}
              className="w-full bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/50 text-cyan-300 py-2.5 rounded-xl text-xs font-mono tracking-wider uppercase transition-all flex items-center justify-center gap-2"
            >
              <Mic className="w-4 h-4" />
              {hasRecorded ? 'Re-record Sample' : 'Start Recording'}
            </button>
          ) : (
            <button
              onClick={handleStopRecording}
              className="w-full bg-red-500/20 hover:bg-red-500/30 border border-red-400/50 text-red-300 py-2.5 rounded-xl text-xs font-mono tracking-wider uppercase transition-all flex items-center justify-center gap-2"
            >
              <Square className="w-4 h-4 fill-current" />
              Stop Recording
            </button>
          )}

          {hasRecorded && !isRecording && (
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handlePlayRecording}
                disabled={isPlaying}
                className="bg-slate-900/80 hover:bg-slate-800 border border-slate-700 text-slate-200 py-2.5 rounded-xl text-xs font-mono tracking-wider uppercase transition-all flex items-center justify-center gap-2"
              >
                {isPlaying ? <Volume2 className="w-4 h-4 animate-bounce" /> : <Play className="w-4 h-4" />}
                {isPlaying ? 'Playing...' : 'Replay'}
              </button>

              <button
                onClick={handleConfirm}
                disabled={isSaving}
                className="bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-black font-semibold py-2.5 rounded-xl text-xs font-mono tracking-wider uppercase transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
              >
                <Check className="w-4 h-4" />
                {isSaving ? 'Saving...' : 'Confirm Profile'}
              </button>
            </div>
          )}

          {/* Skip for now option */}
          <button
            onClick={handleSkip}
            className="w-full text-center text-slate-500 hover:text-slate-400 text-xs font-mono mt-1 transition-colors flex items-center justify-center gap-1"
          >
            Skip for now <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Disclaimer Note */}
        <div className="text-[10px] text-slate-500 text-center font-mono border-t border-cyan-500/10 pt-3 w-full">
          Note: This profile configures your microphone and voice experience. It does not replace your master password.
        </div>
      </div>
    </div>
  );
};
