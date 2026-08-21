"use client";

import { useState } from "react";
import { Clock, Play, Plus, RefreshCw, CheckCircle2, Calendar, AlertCircle, Sparkles } from "lucide-react";

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<any[]>([
    {
      id: "auto-1",
      name: "Weekly Executive Brief Automation",
      trigger_type: "schedule",
      cron_expression: "Mỗi thứ Hai lúc 08:00",
      report_pattern: "Báo cáo Ban Điều Hành Tuần {date}",
      formats: ["DOCX", "PDF"],
      last_run: "21/08/2026 08:00",
      status: "active",
      last_status: "success",
    },
    {
      id: "auto-2",
      name: "Monthly Financial Audit Auto-Run",
      trigger_type: "data_refresh",
      cron_expression: "Khi dữ liệu ERP được cập nhật",
      report_pattern: "Báo cáo Tài Chính Tháng {date}",
      formats: ["PDF"],
      last_run: "18/08/2026 15:30",
      status: "active",
      last_status: "success",
    },
  ]);

  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleTrigger = (id: string) => {
    setTriggeringId(id);
    setTimeout(() => {
      setTriggeringId(null);
      setSuccessMsg("Đã khởi chạy automation thành công! Báo cáo mới đã được tự động khởi tạo.");
      setTimeout(() => setSuccessMsg(null), 4000);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Tự Động Hóa Báo Cáo (Report Automations)</h1>
          <p className="text-xs text-slate-500">Cấu hình lịch trình định kỳ, làm mới dữ liệu và tự động xuất bản báo cáo</p>
        </div>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {automations.map((a) => (
          <div
            key={a.id}
            className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-all space-y-4 text-xs"
          >
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold text-[10px] uppercase flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>{a.trigger_type}</span>
              </span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-bold text-[10px]">
                Đang hoạt động
              </span>
            </div>

            <div className="space-y-1.5">
              <h3 className="text-sm font-bold text-slate-900">{a.name}</h3>
              <p className="text-slate-500 flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-slate-400" />
                <span>Điều kiện: {a.cron_expression}</span>
              </p>
              <p className="text-slate-500">Quy tắc đặt tên: <span className="font-mono text-slate-700">{a.report_pattern}</span></p>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">Lần chạy gần nhất: {a.last_run}</span>
              <button
                onClick={() => handleTrigger(a.id)}
                disabled={triggeringId === a.id}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-xs transition-colors disabled:opacity-50"
              >
                {triggeringId === a.id ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Đang chạy...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5" />
                    <span>Chạy ngay</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
