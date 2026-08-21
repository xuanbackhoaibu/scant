"use client";

import { useState } from "react";
import { ShieldCheck, Users, Cpu, Activity, DollarSign, Database, AlertTriangle, RefreshCw } from "lucide-react";

export default function AdminConsolePage() {
  const [metrics, setMetrics] = useState({
    total_users: 142,
    active_users: 118,
    total_projects: 384,
    reports_generated: 712,
    ai_requests_total: 4890,
    ai_tokens_consumed: 12450000,
    total_ai_cost_usd: 14.85,
    avg_ai_latency_ms: 220,
    failed_jobs_count: 0,
    storage_used_mb: 142.5,
  });

  const [users, setUsers] = useState<any[]>([
    { id: "usr-1", email: "ceo@corp.com", name: "CEO Executive", plan_tier: "enterprise", is_active: true },
    { id: "usr-2", email: "lead@agency.com", name: "Agency Lead", plan_tier: "pro", is_active: true },
    { id: "usr-3", email: "analyst@bank.vn", name: "Financial Analyst", plan_tier: "team", is_active: true },
    { id: "usr-4", email: "guest@freemail.com", name: "Guest User", plan_tier: "free", is_active: false },
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Bảng Điều Khiển Quản Trị (Admin Console)</h1>
            <p className="text-xs text-slate-500">Giám sát hạ tầng AI, vận hành người dùng và tối ưu chi phí SaaS</p>
          </div>
        </div>
        <span className="px-3 py-1 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-full border border-emerald-200 flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-emerald-500" />
          Hệ thống ổn định 100%
        </span>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <Users className="h-3.5 w-3.5 text-slate-400" /> Tổng người dùng
          </p>
          <p className="text-lg font-bold text-slate-900">{metrics.total_users}</p>
          <span className="text-[11px] text-emerald-600 font-semibold">{metrics.active_users} đang hoạt động</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <Cpu className="h-3.5 w-3.5 text-slate-400" /> Tổng AI Requests
          </p>
          <p className="text-lg font-bold text-slate-900">{metrics.ai_requests_total.toLocaleString()}</p>
          <span className="text-[11px] text-slate-500">{metrics.avg_ai_latency_ms}ms avg latency</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <DollarSign className="h-3.5 w-3.5 text-slate-400" /> Chi phí AI tháng
          </p>
          <p className="text-lg font-bold text-slate-900">${metrics.total_ai_cost_usd} USD</p>
          <span className="text-[11px] text-indigo-600 font-semibold">{(metrics.ai_tokens_consumed / 1000000).toFixed(1)}M tokens</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-1">
          <p className="text-slate-400 font-medium flex items-center gap-1">
            <Database className="h-3.5 w-3.5 text-slate-400" /> Dung lượng lưu trữ
          </p>
          <p className="text-lg font-bold text-slate-900">{metrics.storage_used_mb} MB</p>
          <span className="text-[11px] text-emerald-600 font-semibold">{metrics.reports_generated} tài liệu</span>
        </div>
      </div>

      {/* User Governance Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4 text-xs">
        <h3 className="text-sm font-bold text-slate-900">Quản Lý Người Dùng & Gói Dịch Vụ</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 font-semibold pb-2">
                <th className="pb-2">Người dùng</th>
                <th className="pb-2">Email</th>
                <th className="pb-2">Gói hiện tại</th>
                <th className="pb-2">Trạng thái</th>
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
                      <span className="text-emerald-600 font-semibold text-[11px]">Hoạt động</span>
                    ) : (
                      <span className="text-rose-500 font-semibold text-[11px]">Tạm khóa</span>
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
