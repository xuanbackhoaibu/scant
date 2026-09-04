"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, AlertTriangle, CheckCircle2, Sparkles, RefreshCw, BarChart2, Activity, Zap } from "lucide-react";
import { api } from "@/lib/api";

interface StylometryCheckerModalProps {
  text: string;
  isOpen: boolean;
  onClose: () => void;
  onOpenHumanize: () => void;
}

export function StylometryCheckerModal({ text, isOpen, onClose, onOpenHumanize }: StylometryCheckerModalProps) {
  const [data, setData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen || !text.trim()) return;

    async function analyze() {
      setIsLoading(true);
      try {
        const res = await api.ai.inspectStylometry({ text });
        setData(res);
      } catch (err: any) {
        alert("Lỗi phân tích văn phong: " + err.message);
      } finally {
        setIsLoading(false);
      }
    }

    analyze();
  }, [isOpen, text]);

  if (!isOpen) return null;

  const humanProb = data?.human_probability ?? 85;
  const isHighQuality = humanProb >= 70;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl border border-slate-200 max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-indigo-50/30 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-100">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">AI Stylometry & Chống Đạo Văn</h3>
              <p className="text-xs text-slate-500">Đánh giá độ phong phú từ vựng, tính tự nhiên và nhịp điệu câu văn</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-sm font-bold px-2 py-1 rounded-lg hover:bg-slate-100">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {isLoading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-3 text-indigo-600">
              <RefreshCw className="h-8 w-8 animate-spin" />
              <p className="text-xs font-semibold text-slate-600">Đang tính toán entropy từ vựng và chỉ số Burstiness...</p>
            </div>
          ) : data ? (
            <>
              {/* Top Score Banner */}
              <div className={`p-5 rounded-3xl border flex items-center justify-between ${
                isHighQuality ? "bg-emerald-50/50 border-emerald-200" : "bg-amber-50/50 border-amber-200"
              }`}>
                <div className="flex items-center space-x-4">
                  <div className={`h-16 w-16 rounded-2xl flex items-center justify-center text-xl font-black ${
                    isHighQuality ? "bg-emerald-600 text-white shadow-lg shadow-emerald-200" : "bg-amber-500 text-white shadow-lg shadow-amber-200"
                  }`}>
                    {humanProb}%
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      {isHighQuality ? "Văn phong tự nhiên xuất sắc" : "Có dấu hiệu cấu trúc câu lặp lại"}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {isHighQuality
                        ? "Văn bản có tính biến thiên nhịp điệu cao, đáp ứng chuẩn mực học thuật."
                        : "Phát hiện một số mẫu câu đều đặn thường thấy trong văn bản AI tự động sinh."}
                    </p>
                  </div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-2xl border border-slate-100 bg-slate-50 text-center">
                  <div className="text-[11px] font-bold text-slate-500 uppercase">Nhịp điệu câu (Burstiness)</div>
                  <div className="text-lg font-black text-slate-900 mt-1">{data.burstiness_score}/100</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Biến thiên độ dài câu</div>
                </div>
                <div className="p-3.5 rounded-2xl border border-slate-100 bg-slate-50 text-center">
                  <div className="text-[11px] font-bold text-slate-500 uppercase">Độ giàu từ vựng</div>
                  <div className="text-lg font-black text-slate-900 mt-1">{data.vocabulary_richness}/100</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Tỷ lệ từ đơn độc bản (TTR)</div>
                </div>
                <div className="p-3.5 rounded-2xl border border-slate-100 bg-slate-50 text-center">
                  <div className="text-[11px] font-bold text-slate-500 uppercase">Từ nối máy móc</div>
                  <div className="text-lg font-black text-slate-900 mt-1">{data.robotic_phrases_count} cụm</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Mẫu câu chuyển đoạn AI</div>
                </div>
              </div>

              {/* Found phrases alert */}
              {data.found_phrases && data.found_phrases.length > 0 && (
                <div className="p-4 rounded-2xl border border-amber-100 bg-amber-50/40 space-y-2">
                  <div className="flex items-center space-x-2 text-xs font-bold text-amber-800">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <span>Các từ nối lặp lại cần lưu ý:</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.found_phrases.map((p: any, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded-lg bg-white border border-amber-200 text-amber-900 text-xs font-medium">
                        "{p.phrase}" ({p.count} lần)
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              <div className="space-y-2">
                <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Đề xuất cải thiện từ chuyên gia</h5>
                <ul className="space-y-1.5 text-xs text-slate-600">
                  {data.recommendations?.map((r: string, idx: number) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-indigo-600 shrink-0 mt-0.5" />
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <button onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-xl">
            Đóng
          </button>
          <button
            onClick={() => {
              onClose();
              onOpenHumanize();
            }}
            className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm transition"
          >
            <Sparkles className="h-4 w-4" />
            <span>Mở công cụ Humanize AI</span>
          </button>
        </div>
      </div>
    </div>
  );
}
