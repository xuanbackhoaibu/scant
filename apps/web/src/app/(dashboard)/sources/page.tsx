"use client";

import { useState } from "react";
import { Search, ShieldCheck, ExternalLink, BookmarkCheck, Globe, BookOpen } from "lucide-react";

export default function SourcesPage() {
  const [query, setQuery] = useState("");

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Kho Nguồn & Kiểm Chứng Citation</h1>
          <p className="text-xs text-slate-500">
            Hệ thống quản lý nguồn nghiên cứu thực tế (Official Docs, IEEE/ACM Papers, Sách) & chống Hallucination
          </p>
        </div>
      </div>

      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm kiếm tài liệu học thuật, documentation, IEEE papers..."
            className="w-full h-10 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none transition-all"
          />
        </div>
        <button className="h-10 px-5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors shrink-0">
          Tìm kiếm Nghiên cứu
        </button>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50/60 border border-blue-200/80 rounded-xl p-5 text-xs text-blue-900 flex items-start gap-3.5">
        <div className="p-2 bg-blue-100 rounded-lg text-blue-700 shrink-0">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <h4 className="font-bold text-sm text-blue-950 mb-1">Cam kết Nghiên cứu không Bịa đặt (Zero-Hallucination)</h4>
          <p className="leading-relaxed text-blue-800/90">
            Mọi trích dẫn (ví dụ <code>[1]</code>, <code>[2]</code>) sinh ra trong báo cáo đều được lập bản đồ (Evidence Mapping) trực tiếp với URL, tác giả, năm phát hành và đoạn trích dẫn gốc. Bạn có thể bấm vào từng trích dẫn trong Report Studio để xem đối chiếu tức thì.
          </p>
        </div>
      </div>
    </div>
  );
}
