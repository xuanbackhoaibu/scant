"use client";

import { useEffect, useState } from "react";
import { Database, Upload, FileSpreadsheet, Table, BarChart2, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function DataWorkspacePage() {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const projects = await api.projects.list();
        const files: any[] = [];
        for (const p of projects) {
          if (p.files) {
            const dataFiles = p.files.filter((f: any) =>
              ["excel", "csv", "xlsx", "xls"].includes(f.file_type) ||
              f.original_name.endsWith(".csv") ||
              f.original_name.endsWith(".xlsx")
            );
            files.push(...dataFiles);
          }
        }
        setDatasets(files);
      } catch {
        // empty
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Không gian Dữ liệu (Data Workspace)</h1>
        <p className="text-xs text-slate-500">Quản lý tập dữ liệu CSV/Excel, thống kê và cấu hình biểu đồ trực quan</p>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-800">Tập dữ liệu đã kết nối ({datasets.length})</h2>
          </div>
        </div>

        {loading ? (
          <div className="h-32 bg-slate-100 rounded-xl animate-pulse" />
        ) : datasets.length === 0 ? (
          <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-xl space-y-2">
            <FileSpreadsheet className="h-8 w-8 text-slate-400 mx-auto" />
            <h3 className="text-xs font-bold text-slate-700">Chưa có tập dữ liệu CSV/Excel nào</h3>
            <p className="text-[11px] text-slate-400">
              Hãy tải lên tệp Excel hoặc CSV trong khi tạo báo cáo để phân tích số liệu tự động.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {datasets.map((d, i) => (
              <div key={i} className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                  <div>
                    <h4 className="font-bold text-slate-800">{d.original_name}</h4>
                    <span className="text-slate-400">{(d.file_size / 1024).toFixed(1)} KB</span>
                  </div>
                </div>
                <span className="px-2 py-1 bg-emerald-100 text-emerald-800 font-bold rounded-md text-[10px]">
                  Đã đồng bộ
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
