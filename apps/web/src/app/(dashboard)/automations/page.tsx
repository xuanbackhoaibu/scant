"use client";

import { useEffect, useState } from "react";
import { Clock, Play, Plus, RefreshCw, CheckCircle2, Calendar, AlertCircle, Sparkles } from "lucide-react";
import { api } from "@/lib/api";

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadAutomations = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      setAutomations(await api.automations.list());
    } catch (err: any) {
      setErrorMsg(err.message || "Không thể tải danh sách automation.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAutomations();
  }, []);

  const handleTrigger = async (id: string) => {
    setTriggeringId(id);
    setErrorMsg(null);
    try {
      await api.automations.trigger(id);
      setTriggeringId(null);
      setSuccessMsg("Đã khởi chạy automation thành công! Báo cáo mới đã được tự động khởi tạo.");
      setTimeout(() => setSuccessMsg(null), 4000);
      await loadAutomations();
    } catch (err: any) {
      setErrorMsg(err.message || "Không thể chạy automation.");
    } finally {
      setTriggeringId(null);
    }
  };

  const handleCreateQuickAutomation = async () => {
    setErrorMsg(null);
    try {
      const projects = await api.projects.list();
      const project = projects[0];
      if (!project) {
        setErrorMsg("Bạn cần tạo ít nhất một dự án trước khi lập automation.");
        return;
      }
      await api.automations.create({
        project_id: project.id,
        name: `Automation cho ${project.name}`,
        trigger_type: "manual",
        report_title_pattern: "Báo cáo Tự động {date}",
        export_formats: ["docx", "pdf"],
      });
      setSuccessMsg("Đã tạo automation thật cho dự án gần nhất.");
      await loadAutomations();
    } catch (err: any) {
      setErrorMsg(err.message || "Không thể tạo automation.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Tự Động Hóa Báo Cáo (Report Automations)</h1>
          <p className="text-xs text-slate-500">Cấu hình lịch trình định kỳ, làm mới dữ liệu và tự động xuất bản báo cáo</p>
        </div>
        <button
          onClick={handleCreateQuickAutomation}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          <span>Tạo automation thật</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-44 rounded-2xl bg-slate-100 animate-pulse" />
          ))}
        </div>
      ) : automations.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-slate-400" />
          <h3 className="mt-3 text-sm font-bold text-slate-900">Chưa có automation thật</h3>
          <p className="mt-1 text-xs text-slate-500">Tạo một automation từ dự án hiện có để chạy thử pipeline tự động.</p>
        </div>
      ) : (
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
                <span>Điều kiện: {a.cron_expression || "Chạy thủ công"}</span>
              </p>
              <p className="text-slate-500">Quy tắc đặt tên: <span className="font-mono text-slate-700">{a.report_title_pattern}</span></p>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">Lần chạy gần nhất: {a.last_run_at ? new Date(a.last_run_at).toLocaleString("vi-VN") : "Chưa chạy"}</span>
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
      )}
    </div>
  );
}
