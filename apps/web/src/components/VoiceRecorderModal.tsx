"use client";

import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, RefreshCw, Check, Sparkles, AlertCircle, Play, Square } from "lucide-react";
import { api } from "@/lib/api";

interface VoiceRecorderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTranscriptComplete: (transcript: string, title?: string) => void;
}

export function VoiceRecorderModal({ isOpen, onClose, onTranscriptComplete }: VoiceRecorderModalProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (!isOpen) {
      setIsRecording(false);
      setSeconds(0);
      return;
    }

    // Initialize Web Speech API if supported
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "vi-VN";

      recognition.onresult = (event: any) => {
        let current = "";
        for (let i = 0; i < event.results.length; i++) {
          current += event.results[i][0].transcript + " ";
        }
        setTranscript(current.trim());
      };

      recognition.onerror = (e: any) => {
        console.warn("Speech recognition error:", e);
      };

      recognitionRef.current = recognition;
    }
  }, [isOpen]);

  useEffect(() => {
    let interval: any = null;
    if (isRecording) {
      interval = setInterval(() => setSeconds((prev) => prev + 1), 1000);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  if (!isOpen) return null;

  const startRecording = async () => {
    setTranscript("");
    setSeconds(0);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.start();
      recognitionRef.current?.start();
      setIsRecording(true);
    } catch (err: any) {
      alert("Không thể truy cập Microphone: " + (err.message || "Vui lòng cấp quyền Micro trong trình duyệt"));
    }
  };

  const stopRecording = async () => {
    setIsRecording(false);
    recognitionRef.current?.stop();
    mediaRecorderRef.current?.stop();

    // If audio blob available, send to Gemini multimodal voice-to-report
    if (audioChunksRef.current.length > 0) {
      setIsProcessing(true);
      try {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", audioBlob, "voice_memo.webm");

        const res = await api.ai.voiceToReport(formData);
        if (res.transcription) {
          setTranscript(res.transcription);
        }
      } catch (err: any) {
        console.warn("Audio processing fallback to browser speech API:", err);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleApply = () => {
    if (!transcript.trim()) return;
    onTranscriptComplete(transcript.trim());
    onClose();
  };

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-rose-50/40 via-white to-indigo-50/40 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-2xl bg-rose-600 text-white flex items-center justify-center shadow-md shadow-rose-100">
              <Mic className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Ghi Âm & Nhập Liệu Bằng Giọng Nói (AI Voice)</h3>
              <p className="text-xs text-slate-500">Nói tự do, Gemini sẽ tự động bóc băng và lập báo cáo</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-sm font-bold px-2 py-1 rounded-lg hover:bg-slate-100">
            ✕
          </button>
        </div>

        {/* Center Mic Button & Animation */}
        <div className="p-8 flex flex-col items-center justify-center space-y-5 text-center">
          <div className="relative">
            {isRecording && (
              <div className="absolute inset-0 rounded-full bg-rose-500/20 animate-ping" />
            )}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`relative h-20 w-20 rounded-full flex items-center justify-center text-white transition shadow-xl transform active:scale-95 ${
                isRecording ? "bg-rose-600 shadow-rose-200" : "bg-indigo-600 hover:bg-indigo-700 shadow-indigo-200"
              }`}
            >
              {isRecording ? <Square className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
            </button>
          </div>

          <div>
            <div className="font-mono text-xl font-black text-slate-800">
              {isRecording ? formatTimer(seconds) : "00:00"}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {isRecording ? "Đang lắng nghe... Bấm nút đỏ để dừng" : "Bấm nút Micro để bắt đầu nói ý tưởng của bạn"}
            </p>
          </div>

          {/* Transcript Box */}
          <div className="w-full text-left space-y-1">
            <span className="text-[11px] font-bold text-slate-600 uppercase">Nội dung ghi nhận được:</span>
            <div className="w-full h-32 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-800 overflow-y-auto leading-relaxed">
              {isProcessing ? (
                <div className="h-full flex items-center justify-center space-x-2 text-indigo-600">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Gemini Multimodal đang xử lý âm thanh...</span>
                </div>
              ) : transcript ? (
                <p>{transcript}</p>
              ) : (
                <p className="text-slate-400 italic text-center mt-8">Văn bản bóc băng sẽ hiển thị tại đây...</p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <button onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-xl">
            Hủy
          </button>
          <button
            onClick={handleApply}
            disabled={!transcript.trim()}
            className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl shadow-sm transition"
          >
            <Check className="h-4 w-4" />
            <span>Sử dụng nội dung này</span>
          </button>
        </div>
      </div>
    </div>
  );
}
