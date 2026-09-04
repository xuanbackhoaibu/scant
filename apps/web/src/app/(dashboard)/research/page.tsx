"use client";

import { useState } from "react";
import { Globe, Search, Sparkles, ExternalLink, CheckCircle2, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

export default function DeepResearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const res = await api.research.searchWeb(query, 6);
      setResults(res.results || []);
    } catch (err: any) {
      setError(err.message || "Không thể tìm kiếm nghiên cứu.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Deep Research & Xác Thực Nguồn</h1>
        <p className="text-xs text-slate-500">Tìm kiếm thông tin học thuật, báo cáo thị trường và trích xuất bằng chứng thật</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Nhập từ khóa nghiên cứu, ví dụ: Xu hướng xe điện Việt Nam 2026, Thị phần năng lượng tái tạo..."
            className="w-full h-10 pl-10 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-500 outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={searching || !query.trim()}
          className="px-6 h-10 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-xs transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          {searching ? <Sparkles className="h-4 w-4 animate-spin" /> : <Globe className="h-4 w-4" />}
          <span>Tìm kiếm sâu</span>
        </button>
      </form>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-semibold text-rose-700">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Kết quả nguồn uy tín ({results.length}):
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((r, i) => (
              <div key={i} className="p-4 bg-white rounded-2xl border border-slate-200 hover:border-indigo-300 transition-all space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-slate-100 text-[10px] font-bold text-slate-600 truncate max-w-[200px]">
                    {r.publisher || "Web Source"}
                  </span>
                  <span className="text-emerald-700 font-bold text-[10px] flex items-center gap-1">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>Độ tin cậy {(r.reliability_score * 100).toFixed(0)}%</span>
                  </span>
                </div>
                <h4 className="font-bold text-slate-900 line-clamp-2">{r.title}</h4>
                <p className="text-slate-500 line-clamp-3 leading-relaxed">{r.snippet}</p>
                <a
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] text-indigo-600 font-bold hover:underline pt-1"
                >
                  <span>Xem nguồn gốc</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
