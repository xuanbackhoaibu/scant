"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Plus, Search, Filter, Clock, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function DocumentsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function loadReports() {
      try {
        const projects = await api.projects.list();
        const allReports: any[] = [];
        for (const p of projects) {
          if (p.reports) {
            allReports.push(...p.reports);
          }
        }
        setReports(allReports);
      } catch {
        // user might not have reports yet
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  const filtered = reports.filter((r) =>
    r.title?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Quản lý Tài liệu & Báo cáo</h1>
          <p className="text-xs text-slate-500">Tất cả tài liệu được tạo và quản lý trong hệ thống</p>
        </div>
        <Link
          href="/projects/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Tạo tài liệu mới</span>
        </Link>
      </div>

      <div className="flex items-center gap-3 bg-white p-3 rounded-xl border border-slate-200">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm kiếm tài liệu..."
            className="w-full h-9 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-36 rounded-xl bg-slate-100 animate-pulse border border-slate-200" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center space-y-3">
          <FileText className="mx-auto h-10 w-10 text-slate-400" />
          <h3 className="text-sm font-bold text-slate-800">Chưa có tài liệu nào</h3>
          <p className="text-xs text-slate-500">Bắt đầu bằng việc tạo một báo cáo hoặc tài liệu mới.</p>
          <Link
            href="/projects/new"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo mới ngay</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {filtered.map((rep) => (
            <Link
              key={rep.id}
              href={`/reports/${rep.id}/editor`}
              className="p-4 bg-white rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-xs transition-all space-y-2 block"
            >
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-[10px] font-bold text-indigo-700 uppercase">
                  {rep.report_type}
                </span>
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(rep.created_at)}
                </span>
              </div>
              <h4 className="text-xs font-bold text-slate-900 truncate">{rep.title}</h4>
              <div className="flex items-center gap-1 text-[11px] text-indigo-600 font-bold pt-1">
                <span>Mở trong Studio</span>
                <ArrowRight className="h-3 w-3" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
