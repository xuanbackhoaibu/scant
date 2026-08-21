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
  Bot,
  User,
  Wand2,
  ArrowDownToLine,
} from "lucide-react";
import { api } from "@/lib/api";

interface AiAssistantPanelProps {
  projectId: string;
  reportId: string;
  activeSection: any;
  onApplyDraft: (text: string, tiptapJson: any) => void;
}

interface ChatMessage {
  role: "user" | "copilot";
  content: string;
  actionPayload?: any;
}

export function AiAssistantPanel({
  projectId,
  reportId,
  activeSection,
  onApplyDraft,
}: AiAssistantPanelProps) {
  const [panelMode, setPanelMode] = useState<"writer" | "copilot">("writer");

  // Writer Mode State
  const [instruction, setInstruction] = useState("");
  const [tone, setTone] = useState("professional");
  const [isDrafting, setIsDrafting] = useState(false);
  const [lastDraft, setLastDraft] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Copilot Chat Mode State
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "copilot",
      content:
        "Xin chào! Tôi là AI Project Copilot. Bạn có thể yêu cầu tôi viết tiếp, tóm tắt điều hành (Executive Summary), rà soát dữ liệu, tạo bảng so sánh hoặc tinh chỉnh văn phong theo chuẩn chuyên nghiệp.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatting, setIsChatting] = useState(false);

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
      onApplyDraft(res.text, res.tiptap_json);
    } catch (err: any) {
      setError(err.message || "Lỗi khi sinh nội dung. Vui lòng thử lại.");
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSendCopilotMessage = async (customMsg?: string) => {
    const msg = customMsg || chatInput;
    if (!msg.trim()) return;

    const userMsg: ChatMessage = { role: "user", content: msg };
    setChatMessages((prev) => [...prev, userMsg]);
    if (!customMsg) setChatInput("");
    setIsChatting(true);

    try {
      const res = await api.ai.copilot({
        project_id: projectId,
        report_id: reportId,
        section_id: activeSection?.id,
        message: msg,
      });

      setChatMessages((prev) => [
        ...prev,
        {
          role: "copilot",
          content: res.reply,
          actionPayload: res.payload,
        },
      ]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "copilot",
          content: "Rất tiếc, đã có lỗi xảy ra trong quá trình xử lý yêu cầu.",
        },
      ]);
    } finally {
      setIsChatting(false);
    }
  };

  const quickPrompts = [
    "Soạn thảo nội dung chuyên sâu và đầy đủ luận điểm",
    "Tạo tóm tắt điều hành (Executive Summary)",
    "Tạo bảng số liệu so sánh & đánh giá",
    "Chuyển đổi sang văn phong Executive cao cấp",
  ];

  return (
    <div className="flex flex-col h-full bg-white text-xs">
      {/* Top Mode Bar */}
      <div className="p-2 border-b border-slate-100 bg-slate-50 flex items-center gap-1">
        <button
          onClick={() => setPanelMode("writer")}
          className={`flex-1 py-1.5 rounded-lg font-bold text-center transition-all ${
            panelMode === "writer"
              ? "bg-white text-indigo-700 shadow-xs border border-slate-200"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          Section Writer
        </button>
        <button
          onClick={() => setPanelMode("copilot")}
          className={`flex-1 py-1.5 rounded-lg font-bold text-center transition-all flex items-center justify-center gap-1 ${
            panelMode === "copilot"
              ? "bg-white text-indigo-700 shadow-xs border border-slate-200"
              : "text-slate-500 hover:text-slate-900"
          }`}
        >
          <Bot className="h-3.5 w-3.5" />
          <span>AI Copilot</span>
        </button>
      </div>

      {/* WRITER MODE */}
      {panelMode === "writer" && (
        <>
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
              <label className="block text-slate-700 font-semibold mb-1.5">Văn phong báo cáo:</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "professional", label: "Executive & Quản trị" },
                  { id: "technical", label: "Kỹ thuật & Dữ liệu" },
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
                placeholder="Ví dụ: Phân tích kỹ các rủi ro vận hành và lập bảng ma trận đánh giá..."
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

            {lastDraft && (
              <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-xl space-y-2">
                <div className="flex items-center gap-1.5 text-emerald-800 font-bold">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Soạn thảo & Kiểm chứng thành công</span>
                </div>
                <p className="text-[11px] text-emerald-700">
                  Nội dung đã được cập nhật trực tiếp vào văn bản A4.
                </p>
              </div>
            )}
          </div>

          <div className="p-3.5 border-t border-slate-100 bg-slate-50/50">
            <button
              onClick={handleDraftSection}
              disabled={isDrafting || !activeSection}
              className="w-full h-10 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 shadow-xs transition-colors disabled:opacity-50"
            >
              {isDrafting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>AI đang soạn thảo...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Soạn thảo mục này với AI</span>
                </>
              )}
            </button>
          </div>
        </>
      )}

      {/* COPILOT CHAT MODE */}
      {panelMode === "copilot" && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2 text-xs ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "copilot" && (
                  <div className="h-6 w-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="h-3.5 w-3.5" />
                  </div>
                )}

                <div
                  className={`p-3 rounded-2xl max-w-[85%] space-y-2 ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : "bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200/60"
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                  {msg.actionPayload?.text && (
                    <button
                      onClick={() => {
                        if (activeSection) {
                          const newText = `${activeSection.plain_text || ""}\n\n${msg.actionPayload.text}`;
                          onApplyDraft(newText, null);
                        }
                      }}
                      className="flex items-center gap-1 text-[11px] font-bold text-indigo-700 hover:text-indigo-900 bg-white px-2 py-1 rounded shadow-xs transition-colors"
                    >
                      <ArrowDownToLine className="h-3 w-3" />
                      <span>Chèn vào vị trí hiện tại</span>
                    </button>
                  )}
                </div>
              </div>
            ))}

            {isChatting && (
              <div className="flex items-center gap-2 text-xs text-slate-400 p-2 italic">
                <Sparkles className="h-3.5 w-3.5 animate-spin text-indigo-600" />
                <span>Copilot đang phân tích và soạn câu trả lời...</span>
              </div>
            )}
          </div>

          {/* Quick Action Chips */}
          <div className="px-3 py-1.5 border-t border-slate-100 bg-slate-50/50 flex gap-1.5 overflow-x-auto no-scrollbar">
            {["Tạo Executive Summary", "Chèn bảng dữ liệu", "Viết tiếp"].map((q, i) => (
              <button
                key={i}
                onClick={() => handleSendCopilotMessage(q)}
                className="px-2 py-1 rounded bg-white hover:bg-slate-100 border border-slate-200 text-[10px] text-slate-600 shrink-0 font-medium transition-colors"
              >
                + {q}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div className="p-3 border-t border-slate-100 bg-white">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendCopilotMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Hỏi hoặc chỉ đạo Copilot..."
                className="flex-1 h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs outline-none focus:bg-white focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={isChatting || !chatInput.trim()}
                className="h-9 w-9 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg flex items-center justify-center shrink-0 transition-colors disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
