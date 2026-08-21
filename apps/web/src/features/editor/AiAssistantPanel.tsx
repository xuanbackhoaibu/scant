"use client";

import { useState } from "react";
import {
  Sparkles,
  Send,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Copy,
  PlusCircle,
  FileCheck,
  ShieldCheck,
} from "lucide-react";
import { api } from "@/lib/api";

interface AiAssistantPanelProps {
  projectId: string;
  reportId: string;
  activeSection: any;
  onApplyDraft: (text: string, tiptapJson: any) => void;
}

export function AiAssistantPanel({
  projectId,
  reportId,
  activeSection,
  onApplyDraft,
}: AiAssistantPanelProps) {
  const [instruction, setInstruction] = useState("");
  const [tone, setTone] = useState("academic");
  const [isDrafting, setIsDrafting] = useState(false);
  const [lastDraft, setLastDraft] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDraftSection = async () => {
    if (!activeSection) return;
    setIsDrafting(true);
    setError(null);
    try {
      const res = await api.ai.draftSection({
        project_id: projectId,
        report_id: reportId,
        section_id: activeSection.id,
        instruction: instruction || undefined,
        tone,
      });
      setLastDraft(res);
      // Auto apply to canvas
      onApplyDraft(res.text, res.tiptap_json);
    } catch (err: any) {
      setError(err.message || "Lỗi khi sinh nội dung. Vui lòng thử lại.");
    } finally {
      setIsDrafting(false);
    }
  };

  const quickPrompts = [
    "Soạn thảo học thuật chuyên sâu và đầy đủ luận điểm",
    "Phân tích ưu nhược điểm & so sánh công nghệ",
    "Tạo bảng thống kê & đặc tả chức năng",
    "Giải thích luồng kiến trúc & cơ chế xử lý",
  ];

  return (
    <div className="flex flex-col h-full bg-white text-xs">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-600" />
          <span className="font-bold text-slate-800">Trợ Lý Viết AI (Section Writer)</span>
        </div>
        <span className="px-2 py-0.5 rounded bg-indigo-50 text-[10px] font-semibold text-indigo-700">
          Anti-Hallucination
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeSection ? (
          <div className="p-3 bg-indigo-50/60 rounded-xl border border-indigo-100">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 block mb-0.5">
              Mục đang chọn (Heading {activeSection.level})
            </span>
            <p className="font-bold text-slate-900 line-clamp-2">{activeSection.title}</p>
          </div>
        ) : (
          <div className="p-3 bg-slate-50 rounded-xl text-slate-400 text-center italic">
            Chọn một mục bên trái để bắt đầu soạn thảo.
          </div>
        )}

        {/* Tone Selector */}
        <div>
          <label className="block text-slate-700 font-semibold mb-1.5">Giọng điệu văn phong:</label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { id: "academic", label: "Học thuật (Chuẩn luận văn)" },
              { id: "technical", label: "Kỹ thuật chuyên sâu" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTone(t.id)}
                className={`py-1.5 px-2 rounded-lg border text-center font-medium transition-all ${
                  tone === t.id
                    ? "border-indigo-600 bg-indigo-50 text-indigo-700 font-bold"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Custom Instruction */}
        <div>
          <label className="block text-slate-700 font-semibold mb-1.5">Chỉ đạo chi tiết cho AI:</label>
          <textarea
            rows={3}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Ví dụ: Tập trung phân tích cơ chế Middleware và xác thực JWT..."
            className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none text-xs"
          />
        </div>

        {/* Quick Prompts */}
        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Gợi ý nhanh:
          </span>
          <div className="space-y-1">
            {quickPrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => setInstruction(p)}
                className="w-full text-left p-2 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition-colors truncate block"
              >
                + {p}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs">
            {error}
          </div>
        )}

        {/* Last Draft Verification Summary */}
        {lastDraft && (
          <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-xl space-y-2">
            <div className="flex items-center gap-1.5 text-emerald-800 font-bold">
              <ShieldCheck className="h-4 w-4" />
              <span>Kiểm chứng nguồn thành công</span>
            </div>
            <p className="text-[11px] text-emerald-700">
              Đã trích xuất {lastDraft.claims_verified?.length || 0} luận điểm có căn cứ thực tế và tự động đồng bộ vào bản thảo.
            </p>
          </div>
        )}
      </div>

      {/* Footer Action */}
      <div className="p-3.5 border-t border-slate-100 bg-slate-50/50">
        <button
          onClick={handleDraftSection}
          disabled={isDrafting || !activeSection}
          className="w-full h-10 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors disabled:opacity-50"
        >
          {isDrafting ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>AI đang soạn thảo & kiểm chứng...</span>
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              <span>Soạn thảo mục này với AI</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
