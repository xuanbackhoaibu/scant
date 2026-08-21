"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, FileText, Database, ArrowRight, CheckCircle2, X } from "lucide-react";

export function OnboardingModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(1);
  const router = useRouter();

  useEffect(() => {
    const hasSeen = localStorage.getItem("has_seen_onboarding_v2");
    if (!hasSeen) {
      setIsOpen(true);
    }
  }, []);

  const handleComplete = () => {
    localStorage.setItem("has_seen_onboarding_v2", "true");
    setIsOpen(false);
  };

  const handleSkip = () => {
    localStorage.setItem("has_seen_onboarding_v2", "true");
    setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-200 p-6 space-y-6 relative">
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Progress header */}
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Khám phá nhanh AI Document Studio</span>
          <span className="font-bold text-indigo-600">Bước {step}/3</span>
        </div>

        {/* Step Content */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Sparkles className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-slate-900">1. Tạo Báo Cáo Tự Động Chỉ Bằng 1 Click</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Nhập đề tài bạn muốn nghiên cứu hoặc kéo thả tệp DOCX mẫu của bạn. Hệ thống AI Gateway và Model Router sẽ tự động phân tích cấu trúc, thu thập dữ liệu và sinh tài liệu chuẩn xác.
              </p>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Database className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-slate-900">2. Kết Nối Nguồn Dữ Liệu Đa Dạng</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Tích hợp trực tiếp PostgreSQL, MySQL, CSV và REST API. AI sẽ tự động ánh xạ lược đồ dữ liệu và tự làm mới nội dung khi dữ liệu nguồn thay đổi.
              </p>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-slate-900">3. Fact Inspector & Xuất File Chuẩn</h2>
              <p className="text-xs text-slate-500 leading-relaxed">
                Mọi số liệu và trích dẫn được kiểm chứng chéo với nguồn gốc. Xuất bản tài liệu chuẩn DOCX theo đúng định dạng mẫu của doanh nghiệp bạn.
              </p>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <button
            onClick={handleSkip}
            className="text-xs font-semibold text-slate-400 hover:text-slate-600"
          >
            Bỏ qua
          </button>
          <div className="flex items-center gap-2">
            {step < 3 ? (
              <button
                onClick={() => setStep((s) => s + 1)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl flex items-center gap-1.5 transition shadow-xs"
              >
                Tiếp theo <ArrowRight className="h-3.5 w-3.5" />
              </button>
            ) : (
              <button
                onClick={() => {
                  handleComplete();
                  router.push("/wizard");
                }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl flex items-center gap-1.5 transition shadow-xs"
              >
                Bắt đầu ngay <Sparkles className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
