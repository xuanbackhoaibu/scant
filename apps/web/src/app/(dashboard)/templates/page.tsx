"use client";

import { useState } from "react";
import { Layers, FileUp, Sparkles, CheckCircle2, Search, Building2, School } from "lucide-react";

const initialTemplates = [
  {
    id: "tpl_bkhn_cntt",
    name: "Mẫu Báo cáo Bài tập lớn / Đồ án CNTT - ĐH Bách Khoa",
    category: "academic",
    org: "Đại học Bách Khoa Hà Nội",
    paper: "A4 (Trái 30mm, Phải 20mm, Trên 20mm, Dưới 20mm)",
    font: "Times New Roman (13pt, Dãn dòng 1.5)",
    isSystem: true,
  },
  {
    id: "tpl_fpt_se",
    name: "Mẫu Khóa luận & Báo cáo Capstone Project - ĐH FPT",
    category: "academic",
    org: "Trường Đại học FPT",
    paper: "A4 (Trái 35mm, Phải 20mm, Trên 25mm, Dưới 25mm)",
    font: "Times New Roman (12pt, Dãn dòng 1.3)",
    isSystem: true,
  },
  {
    id: "tpl_uit_thesis",
    name: "Mẫu Báo cáo Đồ án Tốt nghiệp - ĐH CNTT ĐHQG-HCM (UIT)",
    category: "academic",
    org: "ĐH Công nghệ Thông tin - ĐHQG-HCM",
    paper: "A4 (Trái 30mm, Phải 20mm, Trên 20mm, Dưới 20mm)",
    font: "Times New Roman (13pt, Dãn dòng 1.5)",
    isSystem: true,
  },
  {
    id: "tpl_business_kpi",
    name: "Mẫu Báo cáo Doanh thu & Phân tích KPI Doanh nghiệp",
    category: "business",
    org: "Chuẩn Doanh nghiệp Standard",
    paper: "A4 (Trái 25mm, Phải 25mm, Trên 20mm, Dưới 20mm)",
    font: "Inter / Arial (11pt, Dãn dòng 1.25)",
    isSystem: true,
  },
];

export default function TemplatesPage() {
  const [search, setSearch] = useState("");

  const filtered = initialTemplates.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.org.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Thư viện Mẫu Báo Cáo (Templates)</h1>
          <p className="text-xs text-slate-500">
            Hỗ trợ tự động trích xuất lề, phông chữ, bìa và kiểu heading từ file Word .docx của các trường
          </p>
        </div>

        <button className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors self-start sm:self-auto">
          <FileUp className="h-4 w-4" />
          <span>Tải lên Mẫu Word (.docx)</span>
        </button>
      </div>

      <div className="bg-white p-3 rounded-xl border border-slate-200">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm mẫu theo tên trường, môn học..."
            className="w-full h-9 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none transition-all"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((tpl) => (
          <div
            key={tpl.id}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-indigo-300 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-700">
                  <School className="h-3.5 w-3.5 text-indigo-600" />
                  {tpl.org}
                </span>
                <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                  System Standard
                </span>
              </div>

              <h3 className="text-sm font-bold text-slate-900 mb-2">{tpl.name}</h3>

              <div className="space-y-1.5 text-xs text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-100">
                <p>
                  <strong className="text-slate-700">Căn lề:</strong> {tpl.paper}
                </p>
                <p>
                  <strong className="text-slate-700">Typography:</strong> {tpl.font}
                </p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">Đầy đủ Placeholder & XML Structure</span>
              <button className="text-xs font-semibold text-indigo-600 hover:text-indigo-700">
                Sử dụng mẫu này →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
