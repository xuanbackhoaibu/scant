"use client";

import { ArrowRight, BarChart3, FileText } from "lucide-react";

export type DataAnalysisMode = "direct-analysis" | "docx-report";

export function DataAnalysisModeSelection({ locale, onSelect }: {
  locale: "vi" | "en";
  onSelect: (mode: DataAnalysisMode) => void;
}) {
  const vi = locale === "vi";
  return (
    <section aria-label={vi ? "Chọn chế độ phân tích" : "Choose analysis mode"} className="mx-auto grid w-full max-w-4xl gap-4 sm:grid-cols-2">
      {[
        { mode: "direct-analysis" as const, icon: BarChart3, title: vi ? "Phân tích trực tiếp" : "Direct analysis", description: vi ? "Phân tích Excel / Google Sheets / CSV, xem KPI, biểu đồ và nhận xét AI trực tiếp trên web." : "Analyze Excel / Google Sheets / CSV with KPIs, charts and AI insights on the web." },
        { mode: "docx-report" as const, icon: FileText, title: vi ? "Tạo báo cáo DOCX" : "Create DOCX report", description: vi ? "AI phân tích dữ liệu và tạo báo cáo Word. Có thể sử dụng mẫu tài liệu của bạn." : "Analyze your data with AI and create a Word report, optionally using your own template." },
      ].map(({ mode, icon: Icon, title, description }) => (
        <button key={mode} type="button" onClick={() => onSelect(mode)} className="group rounded-lg border border-slate-200 bg-white p-5 text-left transition hover:border-emerald-500 hover:bg-emerald-50/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500">
          <Icon className="mb-3 h-6 w-6 text-emerald-700" />
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
          <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-emerald-700">{vi ? "Bắt đầu" : "Get started"}<ArrowRight className="h-4 w-4" /></span>
        </button>
      ))}
    </section>
  );
}
