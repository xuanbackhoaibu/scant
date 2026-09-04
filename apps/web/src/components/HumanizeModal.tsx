"use client";

import { useState } from "react";
import { Sparkles, Check, ArrowRight, RefreshCw, BookOpen, Briefcase, Zap, Smile, Copy } from "lucide-react";
import { api } from "@/lib/api";

interface HumanizeModalProps {
  initialText: string;
  isOpen: boolean;
  onClose: () => void;
  onApply: (newText: string) => void;
}

const STYLES = [
  { id: "academic", name: "Học thuật chuẩn", desc: "Giàu chiều sâu, văn phong nghiên cứu, giữ nguyên trích dẫn", icon: BookOpen },
  { id: "executive", name: "Điều hành & Doanh nghiệp", desc: "Sắc bén, hướng đến quyết định và hành động", icon: Briefcase },
  { id: "concise", name: "Súc tích & Tối giản", desc: "Loại bỏ từ thừa, tăng mật độ thông tin", icon: Zap },
  { id: "natural", name: "Tự nhiên bản ngữ", desc: "Mượt mà, loại bỏ cảm giác dịch thuật AI", icon: Smile },
];

export function HumanizeModal({ initialText, isOpen, onClose, onApply }: HumanizeModalProps) {
  const [text, setText] = useState(initialText);
  const [style, setStyle] = useState("academic");
  const [customPrompt, setCustomPrompt] = useState("");
  const [result, setResult] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleHumanize = async () => {
    if (!text.trim()) return;
    setIsLoading(true);
    try {
      const res = await api.ai.humanize({
        text,
        style,
        custom_instructions: customPrompt.trim() || undefined,
      });
      setResult(res);
    } catch (err: any) {
      alert("Lỗi khi tối ưu hóa văn bản: " + (err.message || "Vui lòng thử lại"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result?.humanized_text) return;
    navigator.clipboard.writeText(result.humanized_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl border border-slate-200 max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-indigo-50/50 via-white to-purple-50/50 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-100">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">AI Text Humanizer & Stylometry Upgrade</h3>
              <p className="text-xs text-slate-500">Loại bỏ dấu vết AI máy móc, nâng cấp văn phong mượt mà tự nhiên 100%</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-sm font-bold px-2 py-1 rounded-lg hover:bg-slate-100">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Style Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">
              Chọn Phong Cách Diễn Đạt Mục Tiêu
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              {STYLES.map((s) => {
                const Icon = s.icon;
                const isSel = style === s.id;
                return (
                  <button
                    key={s.id}
                    onClick={() => setStyle(s.id)}
                    className={`p-3 rounded-2xl border text-left transition flex flex-col justify-between ${
                      isSel
                        ? "border-indigo-600 bg-indigo-50/60 shadow-sm"
                        : "border-slate-200 hover:border-slate-300 bg-white"
                    }`}
                  >
                    <div className="flex items-center space-x-2 mb-1">
                      <Icon className={`h-4 w-4 ${isSel ? "text-indigo-600" : "text-slate-500"}`} />
                      <span className={`text-xs font-bold ${isSel ? "text-indigo-900" : "text-slate-800"}`}>{s.name}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 leading-relaxed">{s.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Text Areas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Input */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs text-slate-600 font-semibold">
                <span>Văn bản gốc ({text.split(/\s+/).filter(Boolean).length} từ)</span>
              </div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Dán hoặc nhập đoạn văn bản cần làm mượt..."
                className="w-full h-56 p-3.5 text-xs text-slate-800 rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 resize-none font-sans leading-relaxed"
              />
            </div>

            {/* Output */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs text-slate-600 font-semibold">
                <span>Văn bản đã Humanize {result ? `(${result.humanized_word_count} từ)` : ""}</span>
                {result?.humanized_text && (
                  <button
                    onClick={handleCopy}
                    className="flex items-center space-x-1 text-[11px] text-indigo-600 font-bold hover:underline"
                  >
                    {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    <span>{copied ? "Đã sao chép" : "Sao chép"}</span>
                  </button>
                )}
              </div>
              <div className="w-full h-56 p-3.5 text-xs text-slate-800 rounded-2xl border border-indigo-100 bg-indigo-50/20 overflow-y-auto font-sans leading-relaxed">
                {isLoading ? (
                  <div className="h-full flex flex-col items-center justify-center space-y-2 text-indigo-600">
                    <RefreshCw className="h-6 w-6 animate-spin" />
                    <span className="text-xs font-semibold">AI đang tinh chỉnh và làm mượt câu từ...</span>
                  </div>
                ) : result?.humanized_text ? (
                  <p className="whitespace-pre-wrap">{result.humanized_text}</p>
                ) : (
                  <p className="text-slate-400 italic text-center mt-20">
                    Bấm nút "Tối ưu hóa ngay" bên dưới để xem văn bản sau khi nâng cấp
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-200"
          >
            Hủy bỏ
          </button>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleHumanize}
              disabled={isLoading || !text.trim()}
              className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl shadow-sm transition"
            >
              {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              <span>{result ? "Tối ưu hóa lại" : "Tối ưu hóa ngay"}</span>
            </button>
            {result?.humanized_text && (
              <button
                onClick={() => {
                  onApply(result.humanized_text);
                  onClose();
                }}
                className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition"
              >
                <Check className="h-4 w-4" />
                <span>Áp dụng vào tài liệu</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
