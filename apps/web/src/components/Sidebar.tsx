"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PlusCircle,
  FolderKanban,
  FileText,
  Layers,
  Database,
  Search,
  Globe,
  Palette,
  Settings,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const mainNavItems = [
  { name: "Tổng quan (Home)", href: "/", icon: LayoutDashboard },
  { name: "Tạo mới (New)", href: "/projects/new", icon: PlusCircle, highlight: true },
  { name: "Dự án (Projects)", href: "/projects", icon: FolderKanban },
  { name: "Tài liệu (Documents)", href: "/documents", icon: FileText },
  { name: "Thư viện Mẫu (Templates)", href: "/templates", icon: Layers },
  { name: "Dữ liệu (Data)", href: "/data", icon: Database },
  { name: "Tự động hóa (Automations)", href: "/automations", icon: Sparkles },
  { name: "Nguồn trích dẫn (Sources)", href: "/sources", icon: Search },
  { name: "Deep Research", href: "/research", icon: Globe },
  { name: "Brand Kit", href: "/brand-kit", icon: Palette },
  { name: "Cài đặt (Settings)", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between h-[calc(100vh-3.5rem)] sticky top-14">
      <div className="p-3.5 space-y-4">
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
                    "flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-xl transition-all",
                    item.highlight
                      ? "bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow-xs mb-2"
                      : isActive
                      ? "bg-indigo-50 text-indigo-700 font-semibold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  )}
                >
                  <Icon className={cn("h-4 w-4", item.highlight ? "text-white" : isActive ? "text-indigo-600" : "text-slate-400")} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
          <span>Universal Studio</span>
          <span className="font-semibold text-indigo-600">v2.0 PRO</span>
        </div>
        <p className="text-[10px] text-slate-400">
          Clean Architecture • Multi-Provider AI • Anti-Hallucination
        </p>
      </div>
    </aside>
  );
}
