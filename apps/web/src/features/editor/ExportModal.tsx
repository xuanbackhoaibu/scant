"use client";

import { useState } from "react";
import {
  Download,
  FileText,
  FileCheck,
  CheckCircle2,
  X,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { api, API_BASE } from "@/lib/api";

interface ExportModalProps {
  reportId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExportModal({ reportId, isOpen, onClose }: ExportModalProps) {
  const [format, setFormat] = useState("docx");
  const [includeCover, setIncludeCover] = useState(true);
  const [includeToc, setIncludeToc] = useState(true);
  const [includeReferences, setIncludeReferences] = useState(true);
  const [citationStyle, setCitationStyle] = useState("IEEE");

  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const resolveDownloadUrl = (downloadUrl?: string) => {
    if (!downloadUrl) return "#";
    if (downloadUrl.startsWith("http")) return downloadUrl;
    const apiOrigin = API_BASE.replace(/\/api\/v1\/?$/, "");
    return `${apiOrigin}${downloadUrl.startsWith("/") ? downloadUrl : `/${downloadUrl}`}`;
  };

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    try {
      let res;
      if (format === "docx") {
        res = await api.exports.exportDocx({
          report_id: reportId,
          export_format: "docx",
          include_cover: includeCover,
          include_toc: includeToc,
          include_references: includeReferences,
          citation_style: citationStyle,
        });
      } else {
        res = await api.exports.exportPdf({
          report_id: reportId,
          export_format: "pdf",
          include_cover: includeCover,
          include_toc: includeToc,
          include_references: includeReferences,
          citation_style: citationStyle,
        });
      }
      setExportResult(res);
    } catch (err: any) {
      setError(err.message || "Lỗi khi xuất tài liệu. Vui lòng thử lại.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="bg-white w-full max-w-lg rounded-2xl border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Download className="h-5 w-5 text-indigo-600" />
            <h3 className="font-bold text-sm text-slate-900">Xuất Báo Cáo Hoàn Chỉnh</h3>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 rounded">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Form */}
        <div className="p-6 space-y-5 text-xs">
          {/* Format selection */}
          <div>
            <label className="block text-slate-700 font-bold mb-2">Định dạng tệp xuất:</label>
            <div className="grid grid-cols-2 gap-3">
              <div
                onClick={() => setFormat("docx")}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-center gap-3 ${
                  format === "docx"
                    ? "border-indigo-600 bg-indigo-50/50 shadow-xs"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="h-8 w-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
                  W
                </div>
                <div>
                  <h4 className="font-bold text-slate-900">Microsoft Word (.docx)</h4>
                  <p className="text-[10px] text-slate-500">Giữ nguyên 100% style & XML trường</p>
                </div>
              </div>

              <div
                onClick={() => setFormat("pdf")}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-center gap-3 ${
                  format === "pdf"
                    ? "border-indigo-600 bg-indigo-50/50 shadow-xs"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="h-8 w-8 rounded-lg bg-red-100 text-red-700 flex items-center justify-center font-bold">
                  PDF
                </div>
                <div>
                  <h4 className="font-bold text-slate-900">Bản in A4 (PDF / HTML)</h4>
                  <p className="text-[10px] text-slate-500">Sẵn sàng in ấn & nộp bài</p>
                </div>
              </div>
            </div>
          </div>

          {/* Options */}
          <div className="space-y-2">
            <label className="block text-slate-700 font-bold">Tùy chọn cấu trúc kèm theo:</label>
            <div className="space-y-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeCover}
                  onChange={(e) => setIncludeCover(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="font-medium text-slate-800">Trang bìa chính thức (University Cover Page)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeToc}
                  onChange={(e) => setIncludeToc(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="font-medium text-slate-800">Mục lục tự động (Table of Contents)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeReferences}
                  onChange={(e) => setIncludeReferences(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="font-medium text-slate-800">Danh mục Tài liệu Tham khảo (References)</span>
              </label>
            </div>
          </div>

          {/* Citation Style */}
          <div>
            <label className="block text-slate-700 font-bold mb-1.5">Chuẩn trích dẫn:</label>
            <div className="flex items-center gap-2">
              {["IEEE", "APA", "HARVARD"].map((s) => (
                <button
                  type="button"
                  key={s}
                  onClick={() => setCitationStyle(s)}
                  className={`px-3 py-1.5 rounded-lg border font-semibold ${
                    citationStyle === s
                      ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {error && <div className="p-2.5 bg-red-50 text-red-700 rounded-lg">{error}</div>}

          {exportResult && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-2 text-emerald-800 font-bold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Xuất tệp thành công!</span>
              </div>
              <a
                href={resolveDownloadUrl(exportResult.download_url)}
                target="_blank"
                download
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold flex items-center gap-1.5 shadow-sm transition-colors"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Tải về máy</span>
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-slate-100 bg-slate-50/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded-lg"
          >
            Đóng
          </button>

          <button
            onClick={handleExport}
            disabled={isExporting}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-sm transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isExporting ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Đang xử lý xuất tệp...</span>
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                <span>Tạo file {format.toUpperCase()}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
