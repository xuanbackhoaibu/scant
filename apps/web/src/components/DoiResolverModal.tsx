"use client";

import { useState } from "react";
import { Search, BookOpen, Check, Copy, RefreshCw, Link2, ExternalLink, Plus } from "lucide-react";
import { api } from "@/lib/api";

interface DoiResolverModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSourceAdded?: () => void;
}

export function DoiResolverModal({ projectId, isOpen, onClose, onSourceAdded }: DoiResolverModalProps) {
  const [inputVal, setInputVal] = useState("");
  const [resolved, setResolved] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [copiedBibtex, setCopiedBibtex] = useState(false);
  const [selectedStyle, setSelectedStyle] = useState<"ieee" | "apa" | "harvard" | "mla">("ieee");

  if (!isOpen) return null;

  const handleResolve = async () => {
    if (!inputVal.trim()) return;
    setIsLoading(true);
    try {
      const res = await api.research.resolveIdentifier(inputVal.trim());
      setResolved(res);
    } catch (err: any) {
      alert("Không tìm thấy thông tin bài báo: " + (err.message || "Vui lòng kiểm tra lại mã DOI hoặc link ArXiv"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddSource = async () => {
    if (!resolved || !projectId) return;
    setIsSaving(true);
    try {
      await api.research.addSource({
        project_id: projectId,
        title: resolved.title,
        url: resolved.url,
        authors: resolved.authors,
        publisher: resolved.publisher,
        published_date: resolved.published_date,
        source_type: resolved.source_type || "journal_article",
        reliability_score: 0.98,
        summary: resolved.abstract || resolved.title,
        content_extracted: resolved.abstract || resolved.title,
        metadata: {
          doi: resolved.doi,
          arxiv_id: resolved.arxiv_id,
          bibtex: resolved.bibtex,
        },
      });
      alert("Đã thêm bài báo vào danh mục Tài liệu Tham khảo thành công!");
      onSourceAdded?.();
      onClose();
    } catch (err: any) {
      alert("Lỗi lưu tài liệu: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCopyBibtex = () => {
    if (!resolved?.bibtex) return;
    navigator.clipboard.writeText(resolved.bibtex);
    setCopiedBibtex(true);
    setTimeout(() => setCopiedBibtex(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl border border-slate-200 max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-indigo-50/40 via-white to-blue-50/40 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-100">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">DOI & ArXiv Smart Citation Resolver</h3>
              <p className="text-xs text-slate-500">Tự động trích xuất metadata, BibTeX và định dạng trích dẫn chuẩn quốc tế</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-sm font-bold px-2 py-1 rounded-lg hover:bg-slate-100">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Input Bar */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
              Nhập mã DOI, ID/Link ArXiv hoặc URL bài báo
            </label>
            <div className="flex items-center space-x-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleResolve()}
                  placeholder="Ví dụ: 10.1145/3290605.3300898 hoặc arxiv:2301.07041"
                  className="w-full pl-3.5 pr-10 py-2.5 text-xs text-slate-800 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
              </div>
              <button
                onClick={handleResolve}
                disabled={isLoading || !inputVal.trim()}
                className="flex items-center space-x-1.5 px-4 py-2.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl shadow-sm transition shrink-0"
              >
                {isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                <span>Tra cứu</span>
              </button>
            </div>
            <p className="text-[11px] text-slate-400">
              Hỗ trợ: CrossRef DOI (10.xxxx), ArXiv (arXiv.org), Semantic Scholar và các trang web học thuật.
            </p>
          </div>

          {/* Result Card */}
          {resolved && (
            <div className="p-5 rounded-2xl border border-indigo-100 bg-indigo-50/20 space-y-4 animate-in fade-in">
              <div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-700">
                  {resolved.source_type}
                </span>
                <h4 className="text-sm font-bold text-slate-900 mt-2">{resolved.title}</h4>
                <p className="text-xs text-slate-600 mt-1">
                  <b>Tác giả:</b> {resolved.authors}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  <b>Nhà xuất bản/Tạp chí:</b> {resolved.publisher} ({resolved.published_date})
                </p>
                {resolved.url && (
                  <a
                    href={resolved.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-1 text-xs text-indigo-600 hover:underline font-semibold mt-1.5"
                  >
                    <span>Mở bài báo gốc</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>

              {/* Citation Format Switcher */}
              <div className="space-y-2 pt-2 border-t border-indigo-100">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>Trích dẫn định dạng:</span>
                  <div className="flex items-center space-x-1">
                    {(["ieee", "apa", "harvard", "mla"] as const).map((fmt) => (
                      <button
                        key={fmt}
                        onClick={() => setSelectedStyle(fmt)}
                        className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase transition ${
                          selectedStyle === fmt ? "bg-indigo-600 text-white" : "bg-white text-slate-600 border border-slate-200"
                        }`}
                      >
                        {fmt}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 font-serif italic">
                  {resolved[`${selectedStyle}_formatted`]}
                </div>
              </div>

              {/* BibTeX Section */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>Mã BibTeX:</span>
                  <button
                    onClick={handleCopyBibtex}
                    className="flex items-center space-x-1 text-[11px] text-indigo-600 hover:underline font-bold"
                  >
                    {copiedBibtex ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    <span>{copiedBibtex ? "Đã chép" : "Sao chép BibTeX"}</span>
                  </button>
                </div>
                <pre className="p-3 rounded-xl bg-slate-900 text-slate-200 text-[11px] font-mono overflow-x-auto">
                  {resolved.bibtex}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <button onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-xl">
            Đóng
          </button>
          {resolved && (
            <button
              onClick={handleAddSource}
              disabled={isSaving}
              className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl shadow-sm transition"
            >
              {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              <span>Thêm vào Tài liệu Tham khảo</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
