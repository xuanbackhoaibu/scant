"use client";

import { useState, useEffect } from "react";
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
  ChevronLeft,
  ChevronRight,
  Shield,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/i18n/I18nContext";
import { useAuthStore } from "@/stores/useAuthStore";

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("sidebar_collapsed");
    if (saved) setCollapsed(saved === "true");
  }, []);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("sidebar_collapsed", String(next));
  };

  const navItems = [
    { key: "home", href: "/", icon: LayoutDashboard, label: t("navigation.home") },
    { key: "new", href: "/projects/new", icon: PlusCircle, label: t("navigation.new"), highlight: true },
    { key: "projects", href: "/projects", icon: FolderKanban, label: t("navigation.projects") },
    { key: "documents", href: "/documents", icon: FileText, label: t("navigation.documents") },
    { key: "templates", href: "/templates", icon: Layers, label: t("navigation.templates") },
    { key: "data", href: "/data", icon: Database, label: t("navigation.data") },
    { key: "automations", href: "/automations", icon: Sparkles, label: t("navigation.automations") },
    { key: "sources", href: "/sources", icon: Search, label: t("navigation.sources") },
    { key: "research", href: "/research", icon: Globe, label: t("navigation.research") },
    { key: "brandKit", href: "/brand-kit", icon: Palette, label: t("navigation.brandKit") },
    { key: "settings", href: "/settings", icon: Settings, label: t("navigation.settings") },
  ];

  if (user?.is_superuser || user?.role === "admin") {
    navItems.push({ key: "admin", href: "/admin", icon: Shield, label: t("navigation.admin") });
  }

  return (
    <aside
      className={cn(
        "border-r border-slate-200 bg-white flex flex-col justify-between h-[calc(100vh-3.5rem)] sticky top-14 transition-all duration-200 select-none z-30",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="p-3 space-y-3 overflow-y-auto">
        {/* Workspace header & collapse trigger */}
        <div className="flex items-center justify-between px-2 pt-1">
          {!collapsed && (
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              {t("navigation.workspace")}
            </span>
          )}
          <button
            onClick={toggleCollapse}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors ml-auto"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.key}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-xl transition-all",
                  item.highlight
                    ? "bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow-xs mb-2"
                    : isActive
                    ? "bg-indigo-50 text-indigo-700 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50",
                  collapsed && "justify-center px-0"
                )}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    item.highlight ? "text-white" : isActive ? "text-indigo-600" : "text-slate-400"
                  )}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer: Usage Quota & Profile */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50 space-y-2">
        {!collapsed ? (
          <>
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1 font-medium">
                <Zap className="h-3 w-3 text-amber-500" />
                {t("navigation.usage")}
              </span>
              <span className="font-semibold text-slate-700">82%</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div className="bg-indigo-600 h-full rounded-full w-[82%]" />
            </div>
          </>
        ) : (
          <div className="flex justify-center" title={t("navigation.usage")}>
            <Zap className="h-4 w-4 text-amber-500" />
          </div>
        )}
      </div>
    </aside>
  );
}
