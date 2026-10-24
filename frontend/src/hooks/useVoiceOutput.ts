import { useState, useEffect, useRef, useCallback } from 'react';

interface UseVoiceOutputOptions {
  rate?: number;
  pitch?: number;
  volume?: number;
  preferredVoice?: string;
  onStart?: () => void;
  onEnd?: () => void;
}

export const useVoiceOutput = ({
  rate = 1.0,
  pitch = 1.0,
  volume = 1.0,
  preferredVoice = 'en-GB',
  onStart,
  onEnd
}: UseVoiceOutputOptions = {}) => {
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const selectedVoiceRef = useRef<SpeechSynthesisVoice | null>(null);

  // Load available system voices
  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    const updateVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      setAvailableVoices(voices);

      // Try selecting British or calm articulate male/female voice
      const british = voices.find(
        (v) =>
          v.lang.includes('en-GB') ||
          v.name.includes('George') ||
          v.name.includes('UK') ||
          v.name.includes('Natural')
      );
      const englishFallback = voices.find((v) => v.lang.startsWith('en'));
      selectedVoiceRef.current = british || englishFallback || voices[0] || null;
    };

    updateVoices();
    window.speechSynthesis.onvoiceschanged = updateVoices;
  }, [preferredVoice]);

  const speak = useCallback(
    (text: string) => {
      if (typeof window === 'undefined' || !window.speechSynthesis) return;

      // Stop any ongoing speech
      window.speechSynthesis.cancel();

      // Clean text of markdown asterisks, backticks, code blocks
      const cleanText = text
        .replace(/```[\s\S]*?```/g, 'Code block omitted.')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')
        .replace(/#+\s/g, '')
        .trim();

      if (!cleanText) return;

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = rate;
      utterance.pitch = pitch;
      utterance.volume = volume;
      if (selectedVoiceRef.current) {
        utterance.voice = selectedVoiceRef.current;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
        if (onStart) onStart();
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        if (onEnd) onEnd();
      };

      utterance.onerror = () => {
        setIsSpeaking(false);
        if (onEnd) onEnd();
      };

      window.speechSynthesis.speak(utterance);
    },
    [rate, pitch, volume, onStart, onEnd]
  );

  const stop = useCallback(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    if (onEnd) onEnd();
  }, [onEnd]);

  return {
    isSpeaking,
    availableVoices,
    speak,
    stop
  };
};
