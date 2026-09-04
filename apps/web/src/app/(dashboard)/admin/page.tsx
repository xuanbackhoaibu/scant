"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, Users, Cpu, Activity, DollarSign, Database, AlertTriangle, RefreshCw } from "lucide-react";
import { useTranslation } from "@/i18n/I18nContext";
import { api, ApiError } from "@/lib/api";

export default function AdminConsolePage() {
  const { t } = useTranslation();
  const [metrics, setMetrics] = useState<any | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAdmin() {
      setLoading(true);
      setError(null);
      try {
        const [dashboard, userRows] = await Promise.all([
          api.admin.dashboard(),
          api.admin.users(),
        ]);
        setMetrics(dashboard);
        setUsers(userRows);
      } catch (err: any) {
        if (err instanceof ApiError && err.status === 403) {
          setError("Tài khoản hiện tại chưa có quyền quản trị hệ thống.");
        } else {
          setError(err.message || "Không thể tải dữ liệu quản trị.");
        }
      } finally {
        setLoading(false);
      }
    }
    loadAdmin();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white p-5 text-xs font-semibold text-slate-600">
        <RefreshCw className="h-4 w-4 animate-spin text-indigo-600" />
        <span>Đang tải dữ liệu quản trị thật...</span>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        <div className="flex items-center gap-2 font-bold">
          <AlertTriangle className="h-4 w-4" />
          <span>Không thể mở bảng quản trị</span>
        </div>
        <p className="mt-2 text-xs">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">{t("admin.title")}</h1>
            <p className="text-xs text-slate-500">{t("admin.subtitle")}</p>
          </div>
        </div>
        <span className="px-3 py-1 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-full border border-emerald-200 flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-emerald-500" />
          {t("admin.systemStable")}
        </span>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <Users className="h-3.5 w-3.5 text-slate-400" /> {t("admin.totalUsers")}
          </p>
          <p className="text-lg font-bold text-slate-900">{metrics.total_users}</p>
          <span className="text-[11px] text-emerald-600 font-semibold">{metrics.active_users} {t("admin.activeUsers")}</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <Cpu className="h-3.5 w-3.5 text-slate-400" /> {t("admin.totalAiRequests")}
          </p>
          <p className="text-lg font-bold text-slate-900">{metrics.ai_requests_total.toLocaleString()}</p>
          <span className="text-[11px] text-slate-500">{metrics.avg_ai_latency_ms}ms {t("admin.avgLatency")}</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <DollarSign className="h-3.5 w-3.5 text-slate-400" /> {t("admin.monthlyAiCost")}
          </p>
          <p className="text-lg font-bold text-slate-900">${metrics.total_ai_cost_usd} USD</p>
          <span className="text-[11px] text-indigo-600 font-semibold">{(metrics.ai_tokens_consumed / 1000000).toFixed(1)}M tokens</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <Database className="h-3.5 w-3.5 text-slate-400" /> {t("admin.storageUsed")}
          </p>
          <p className="text-lg font-bold text-slate-900">{metrics.storage_used_mb} MB</p>
          <span className="text-[11px] text-emerald-600 font-semibold">{metrics.reports_generated} {t("admin.documents")}</span>
        </div>
      </div>

      {/* User Governance Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4 text-xs">
        <h3 className="text-sm font-bold text-slate-900">{t("admin.userGovernance")}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 font-semibold pb-2">
                <th className="pb-2">{t("admin.user")}</th>
                <th className="pb-2">Email</th>
                <th className="pb-2">{t("admin.currentPlan")}</th>
                <th className="pb-2">{t("admin.status")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.id} className="py-2.5">
                  <td className="py-2.5 font-bold text-slate-900">{u.name}</td>
                  <td className="py-2.5 text-slate-500 font-mono">{u.email}</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded-full uppercase text-[10px] font-bold bg-indigo-50 text-indigo-700">
                      {u.plan_tier}
                    </span>
                  </td>
                  <td className="py-2.5">
                    {u.is_active ? (
                      <span className="text-emerald-600 font-semibold text-[11px]">{t("admin.active")}</span>
                    ) : (
                      <span className="text-rose-500 font-semibold text-[11px]">{t("admin.suspended")}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
