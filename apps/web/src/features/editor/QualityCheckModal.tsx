"use client";

import { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  X,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { api } from "@/lib/api";

interface QualityCheckModalProps {
  reportId: string;
  isOpen: boolean;
  onClose: () => void;
  onOpenExport: () => void;
}

export function QualityCheckModal({
  reportId,
  isOpen,
  onClose,
  onOpenExport,
}: QualityCheckModalProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  const handleRunCheck = async () => {
    setLoading(true);
    try {
      const res = await api.ai.checkReport(reportId);
      setData(res);
    } catch {}
    finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="bg-white w-full max-w-xl rounded-2xl border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-indigo-600" />
            <h3 className="font-bold text-sm text-slate-900">Kiểm Tra Chất Lượng Học Thuật (Quality Gates)</h3>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 rounded">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto text-xs">
          {!data && !loading && (
            <div className="text-center py-8 space-y-3">
              <ShieldCheck className="h-12 w-12 text-indigo-500 mx-auto" />
              <h4 className="font-bold text-sm text-slate-800">Sẵn sàng kiểm định tài liệu</h4>
              <p className="text-slate-500 max-w-sm mx-auto">
                Hệ thống sẽ quét toàn bộ {`cấu trúc, độ dài, tính đầy đủ của các chương, trích dẫn chuẩn IEEE và chống lỗi định dạng.`}
              </p>
              <button
                onClick={handleRunCheck}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-sm transition-colors"
              >
                Bắt đầu kiểm tra báo cáo
              </button>
            </div>
          )}

          {loading && (
            <div className="text-center py-10 space-y-3">
              <Sparkles className="h-8 w-8 text-indigo-600 animate-spin mx-auto" />
              <p className="font-medium text-slate-700">Đang rà soát chất lượng học thuật và trích dẫn...</p>
            </div>
          )}

          {data && (
            <div className="space-y-4">
              {/* Score card */}
              <div className="p-4 bg-indigo-50/80 rounded-xl border border-indigo-100 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-bold text-indigo-600 uppercase tracking-wider">
                    Điểm đánh giá chất lượng
                  </span>
                  <h4 className="text-2xl font-bold text-indigo-950 mt-0.5">
                    {data.overall_score} / 100 điểm
                  </h4>
                  <p className="text-slate-600 mt-1">{data.summary}</p>
                </div>
                <div className="h-14 w-14 rounded-full bg-white border-2 border-indigo-600 flex items-center justify-center font-bold text-lg text-indigo-600 shadow-sm">
                  {data.overall_score}%
                </div>
              </div>

              {/* Checks */}
              <div className="space-y-2">
                <span className="font-bold text-slate-700">Tiêu chuẩn kiểm định:</span>
                {data.checks?.map((c: any, i: number) => (
                  <div
                    key={i}
                    className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-start gap-3"
                  >
                    {c.status === "pass" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : c.status === "warning" ? (
                      <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                    )}

                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">{c.name}</span>
                        <span
                          className={`text-[10px] font-semibold uppercase px-1.5 py-0.2 rounded ${
                            c.status === "pass"
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-amber-100 text-amber-700"
                          }`}
                        >
                          {c.status}
                        </span>
                      </div>
                      <p className="text-slate-600">{c.message}</p>
                      {c.suggestion && (
                        <p className="text-[11px] text-slate-500 italic">💡 Gợi ý: {c.suggestion}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
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

          {data && (
            <button
              onClick={() => {
                onClose();
                onOpenExport();
              }}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <span>Tiến hành Xuất Báo Cáo</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
