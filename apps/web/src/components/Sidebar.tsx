"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  Bookmark,
  Database,
  Search,
  Settings,
  Sparkles,
  Layers,
  GraduationCap,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

const mainNavItems = [
  { name: "Tổng quan", href: "/", icon: LayoutDashboard },
  { name: "Dự án & Báo cáo", href: "/projects", icon: FolderKanban },
  { name: "Thư viện Template", href: "/templates", icon: Layers },
  { name: "Kho Nguồn & Citation", href: "/sources", icon: Search },
];

const categoryShortcuts = [
  { name: "Bài tập lớn / Đồ án", href: "/projects?type=academic", icon: GraduationCap, color: "text-blue-500" },
  { name: "Báo cáo Dữ liệu & KPI", href: "/projects?type=data", icon: TrendingUp, color: "text-emerald-500" },
  { name: "Báo cáo AI Auto", href: "/projects?type=auto", icon: Sparkles, color: "text-purple-500" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between h-[calc(100vh-3.5rem)] sticky top-14">
      <div className="p-4 space-y-6">
        {/* Navigation Group */}
        <div>
          <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Không gian làm việc
          </p>
          <nav className="space-y-1">
            {mainNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-lg transition-colors",
                    isActive
                      ? "bg-indigo-50 text-indigo-700 font-semibold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-indigo-600" : "text-slate-400")} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Categories Group */}
        <div>
          <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Phân loại Báo cáo
          </p>
          <nav className="space-y-1">
            {categoryShortcuts.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
                >
                  <Icon className={cn("h-4 w-4", item.color)} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer Info / Storage */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
          <span>Hệ thống VIP PRO</span>
          <span className="font-semibold text-indigo-600">v1.0.0</span>
        </div>
        <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
          <div className="bg-indigo-600 h-full w-[24%]" />
        </div>
        <p className="text-[10px] text-slate-400 mt-1.5">
          Tối ưu hóa bởi Clean Architecture & Anti-Hallucination
        </p>
      </div>
    </aside>
  );
}
