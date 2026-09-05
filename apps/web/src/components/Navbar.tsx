"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { FileText, Search, Languages, Zap, Layers, Table } from "lucide-react";
import { useTranslation, Locale } from "@/i18n/I18nContext";
import { DarkModeToggle } from "@/components/DarkModeToggle";
import { useModeStore, ProjectWizardMode } from "@/stores/useModeStore";
import { cn } from "@/lib/utils";

export function Navbar() {
  const { locale, setLocale, t } = useTranslation();
  const { mode: currentMode, setMode: setStoreMode } = useModeStore();
  const router = useRouter();
  const pathname = usePathname() || "";

  const handleModeSelect = (targetMode: ProjectWizardMode) => {
    if (pathname === "/projects/new") {
      setStoreMode(targetMode);
    } else {
      setStoreMode(targetMode);
      router.push(`/projects/new?mode=${targetMode}`);
    }
  };

  const toggleLanguage = () => {
    const nextLocale: Locale = locale === "vi" ? "en" : "vi";
    setLocale(nextLocale);
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/90 shadow-[0_1px_0_rgba(15,23,42,0.03)] backdrop-blur-xl supports-[backdrop-filter]:bg-white/75 dark:border-slate-800 dark:bg-slate-950/85">
      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        {/* Left: Brand */}
        <div className="flex items-center gap-4 shrink-0">
          <Link href="/" aria-label={t("common.appName")} className="group flex items-center gap-2.5 font-semibold tracking-tight text-slate-900">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-950 text-cyan-200 shadow-sm ring-1 ring-slate-800 transition-transform group-hover:scale-105 dark:bg-cyan-300 dark:text-slate-950">
              <FileText className="h-4 w-4" />
            </div>
            <div className="hidden lg:flex lg:flex-col">
              <div className="flex items-center gap-1.5 leading-none">
                <span className="text-sm font-bold tracking-tight">{t("common.appName")}</span>
                <span className="rounded-md border border-cyan-200/70 bg-cyan-50 px-1.5 py-0.5 text-[10px] font-semibold text-cyan-700 dark:border-cyan-400/20 dark:bg-cyan-400/10 dark:text-cyan-200">
                  PRO
                </span>
              </div>
              <span className="text-[10px] text-slate-500 hidden sm:inline">{t("common.appTagline")}</span>
            </div>
          </Link>
        </div>

        {/* Middle: Search Command Palette Trigger */}
        <div className="min-w-0 flex-1 max-w-md mx-4 md:mx-6 hidden xl:block">
          <div
            onClick={() => {
              const event = new KeyboardEvent("keydown", { key: "k", metaKey: true });
              window.dispatchEvent(event);
            }}
            className="relative cursor-pointer"
          >
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <div className="flex h-9 w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50/90 pl-9 pr-4 text-xs text-slate-400 transition-all hover:border-slate-300 hover:bg-white dark:border-slate-800 dark:bg-slate-900/70">
              <span>{t("common.search")}</span>
              <kbd className="rounded border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-[10px] text-slate-500 shadow-2xs dark:border-slate-700 dark:bg-slate-950">
                ⌘K
              </kbd>
            </div>
          </div>
        </div>

        {/* Right: Segmented Mode Selector, CTA, Language, Dark Mode */}
        <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
          {/* 3 Modes Segmented Control */}
          <div className="inline-flex h-[38px] items-center rounded-xl border border-slate-200 bg-slate-100/90 p-1 text-xs dark:border-slate-800 dark:bg-slate-900/80">
            <button
              type="button"
              aria-label={locale === "vi" ? "Tự động" : "Auto"}
              onClick={() => handleModeSelect("auto")}
              className={cn(
                "inline-flex h-full items-center gap-1.5 rounded-lg px-3 py-1 font-semibold transition-all",
                currentMode === "auto"
                  ? "bg-white text-indigo-600 shadow-2xs dark:bg-slate-950 dark:text-cyan-300"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
              )}
            >
              <Zap className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{locale === "vi" ? "Tự động" : "Auto"}</span>
            </button>
            <button
              type="button"
              aria-label={locale === "vi" ? "Tùy chỉnh" : "Custom"}
              onClick={() => handleModeSelect("advanced")}
              className={cn(
                "inline-flex h-full items-center gap-1.5 rounded-lg px-3 py-1 font-semibold transition-all",
                currentMode === "advanced"
                  ? "bg-white text-indigo-600 shadow-2xs dark:bg-slate-950 dark:text-cyan-300"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
              )}
            >
              <Layers className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{locale === "vi" ? "Tùy chỉnh" : "Custom"}</span>
            </button>
            <button
              type="button"
              aria-label={locale === "vi" ? "Hàng loạt" : "Bulk"}
              onClick={() => handleModeSelect("bulk")}
              className={cn(
                "inline-flex h-full items-center gap-1.5 rounded-lg px-3 py-1 font-semibold transition-all",
                currentMode === "bulk"
                  ? "bg-white text-indigo-600 shadow-2xs dark:bg-slate-950 dark:text-cyan-300"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
              )}
            >
              <Table className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{locale === "vi" ? "Hàng loạt" : "Bulk"}</span>
            </button>
          </div>

          {/* Language Switcher */}
          <button
            onClick={toggleLanguage}
            title={locale === "vi" ? t("common.switchToEnglish") : t("common.switchToVietnamese")}
            className="flex h-8 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
          >
            <Languages className="h-3.5 w-3.5 text-slate-500" />
            <span className="uppercase">{locale}</span>
          </button>

          {/* Theme Toggle */}
          <DarkModeToggle />
        </div>
      </div>
    </header>
  );
}
