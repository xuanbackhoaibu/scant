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
import { isSidebarItemActive } from "@/lib/sidebarNav";
import { useTranslation } from "@/i18n/I18nContext";
import { useAuthStore } from "@/stores/useAuthStore";

export function Sidebar() {
  const pathname = usePathname() || "";
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
        "sticky top-14 z-30 flex h-[calc(100vh-3.5rem)] select-none flex-col justify-between border-r border-slate-200 bg-white/82 backdrop-blur-xl transition-all duration-200 dark:border-slate-800 dark:bg-slate-950/82",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="space-y-3 overflow-y-auto p-3">
        {/* Workspace header & collapse trigger */}
        <div className="flex items-center justify-between px-2 pt-1">
          {!collapsed && (
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              {t("navigation.workspace")}
            </span>
          )}
          <button
            onClick={toggleCollapse}
            title={collapsed ? t("common.expand") : t("common.collapse")}
            className="ml-auto rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = isSidebarItemActive(pathname, item.href);
            return (
              <Link
                key={item.key}
                href={item.href}
                prefetch={true}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all",
                  item.highlight && isActive
                    ? "mb-2 bg-slate-950 text-white font-bold shadow-xs hover:bg-slate-800 dark:bg-cyan-300 dark:text-slate-950"
                    : isActive
                    ? "bg-cyan-50 text-cyan-800 font-semibold ring-1 ring-cyan-100 dark:bg-cyan-400/10 dark:text-cyan-100 dark:ring-cyan-400/20"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-slate-100",
                  collapsed && "justify-center px-0"
                )}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    item.highlight && isActive
                      ? "text-white"
                      : isActive
                      ? "text-cyan-700 dark:text-cyan-200"
                      : "text-slate-400"
                  )}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer: Usage Quota & Profile */}
      <div className="space-y-2 border-t border-slate-100 bg-slate-50/70 p-3 dark:border-slate-800 dark:bg-slate-900/50">
        {!collapsed ? (
          <>
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1 font-medium">
                <Zap className="h-3 w-3 text-amber-500" />
                {t("navigation.usage")}
              </span>
              <span className="font-semibold text-slate-700">82%</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
              <div className="h-full w-[82%] rounded-full bg-cyan-500 dark:bg-cyan-300" />
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
