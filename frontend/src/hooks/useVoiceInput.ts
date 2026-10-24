import { useState, useEffect, useRef, useCallback } from 'react';

// Declare types for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface UseVoiceInputOptions {
  onFinalTranscript?: (text: string) => void;
  onWakeWordDetected?: () => void;
  wakeWordEnabled?: boolean;
}

export const useVoiceInput = ({
  onFinalTranscript,
  onWakeWordDetected,
  wakeWordEnabled = false
}: UseVoiceInputOptions = {}) => {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [isSupported, setIsSupported] = useState<boolean>(true);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [audioLevel, setAudioLevel] = useState<number>(0);

  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Fast End-of-Utterance Silence Detector refs
  const pauseTimerRef = useRef<any>(null);
  const lastDispatchedRef = useRef<string>('');
  const lastDispatchTimeRef = useRef<number>(0);

  // Initialize SpeechRecognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let currentInterim = '';
      let currentFinal = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const item = event.results[i];
        if (item.isFinal) {
          currentFinal += item[0].transcript;
        } else {
          currentInterim += item[0].transcript;
        }
      }

      const combinedText = (currentFinal || currentInterim).toLowerCase().trim();

      // Check wake word if enabled
      if (wakeWordEnabled && onWakeWordDetected) {
        if (combinedText.includes('jarvis') || combinedText.includes('hey jarvis')) {
          onWakeWordDetected();
        }
      }

      // Clear any pending pause timer
      if (pauseTimerRef.current) {
        clearTimeout(pauseTimerRef.current);
        pauseTimerRef.current = null;
      }

      if (currentFinal) {
        const trimmedFinal = currentFinal.trim();
        const now = Date.now();
        // Prevent duplicate dispatch if our fast-detector already dispatched it within 1.5s
        if (trimmedFinal && (trimmedFinal.toLowerCase() !== lastDispatchedRef.current.toLowerCase() || (now - lastDispatchTimeRef.current) > 1500)) {
          lastDispatchedRef.current = trimmedFinal;
          lastDispatchTimeRef.current = now;
          setTranscript(trimmedFinal);
          setInterimTranscript('');
          if (onFinalTranscript) {
            onFinalTranscript(trimmedFinal);
          }
        } else {
          setInterimTranscript('');
        }
      } else if (currentInterim.trim()) {
        const trimmedInterim = currentInterim.trim();
        setInterimTranscript(trimmedInterim);

        // Instant Fast-Dispatch Debounce for Direct Commands
        // When user pauses speaking for 400ms on actionable directives, or 700ms on general speech, dispatch immediately!
        const lower = trimmedInterim.toLowerCase();
        const isActionDirective = /^(open|launch|start|run|close|kill|mute|unmute|volume|screenshot|lock|what time|who|how|ipconfig|whatsapp|chrome|spotify|calculator|notepad|explorer)/i.test(lower);
        const debounceDelay = isActionDirective ? 400 : 700;

        pauseTimerRef.current = setTimeout(() => {
          const now = Date.now();
          if (trimmedInterim && (trimmedInterim.toLowerCase() !== lastDispatchedRef.current.toLowerCase() || (now - lastDispatchTimeRef.current) > 1500)) {
            lastDispatchedRef.current = trimmedInterim;
            lastDispatchTimeRef.current = now;
            setTranscript(trimmedInterim);
            setInterimTranscript('');
            if (onFinalTranscript) {
              onFinalTranscript(trimmedInterim);
            }
          }
        }, debounceDelay);
      }
    };

    recognition.onerror = (event: any) => {
      console.warn('Speech recognition error:', event.error);
      if (event.error === 'not-allowed') {
        setHasPermission(false);
        setIsListening(false);
      }
    };

    recognition.onend = () => {
      if (pauseTimerRef.current) {
        clearTimeout(pauseTimerRef.current);
        pauseTimerRef.current = null;
      }
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (pauseTimerRef.current) {
        clearTimeout(pauseTimerRef.current);
        pauseTimerRef.current = null;
      }
      try {
        recognition.stop();
      } catch (e) {}
    };
  }, [wakeWordEnabled, onWakeWordDetected, onFinalTranscript]);

  // Audio meter for visual reactivity
  const startAudioMeter = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setHasPermission(true);

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioContextClass();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      const microphone = audioCtx.createMediaStreamSource(stream);
      microphone.connect(analyser);

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;
      microphoneRef.current = microphone;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateMeter = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        setAudioLevel(Math.min(avg / 128, 1));
        animFrameRef.current = requestAnimationFrame(updateMeter);
      };
      updateMeter();
    } catch (err) {
      console.warn('Microphone permission denied or not available:', err);
      setHasPermission(false);
    }
  };

  const stopAudioMeter = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (microphoneRef.current) microphoneRef.current.disconnect();
    if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    setAudioLevel(0);
  };

  const startListening = useCallback(async () => {
    if (!recognitionRef.current) return;
    try {
      setTranscript('');
      setInterimTranscript('');
      recognitionRef.current.start();
      setIsListening(true);
      await startAudioMeter();
    } catch (err) {
      console.warn('Error starting speech recognition:', err);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
      setIsListening(false);
      stopAudioMeter();
    } catch (err) {
      console.warn('Error stopping speech recognition:', err);
    }
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    isSupported,
    hasPermission,
    audioLevel,
    startListening,
    stopListening,
    getAnalyser: () => analyserRef.current
  };
};
