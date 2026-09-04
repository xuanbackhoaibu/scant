"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileText, LogOut, Plus, Search, Languages } from "lucide-react";
import { useAuthStore } from "@/stores/useAuthStore";
import { useTranslation, Locale } from "@/i18n/I18nContext";
import { DarkModeToggle } from "@/components/DarkModeToggle";

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const { locale, setLocale, t } = useTranslation();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const toggleLanguage = () => {
    const nextLocale: Locale = locale === "vi" ? "en" : "vi";
    setLocale(nextLocale);
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/88 shadow-[0_1px_0_rgba(15,23,42,0.03)] backdrop-blur-xl supports-[backdrop-filter]:bg-white/70 dark:border-slate-800 dark:bg-slate-950/86">
      <div className="flex h-14 items-center justify-between px-4 sm:px-6">
        {/* Left: Brand */}
        <div className="flex items-center gap-4">
          <Link href="/" className="group flex items-center gap-2.5 font-semibold tracking-tight text-slate-900">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-950 text-cyan-200 shadow-sm ring-1 ring-slate-800 transition-transform group-hover:scale-105 dark:bg-cyan-300 dark:text-slate-950">
              <FileText className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
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
        <div className="flex-1 max-w-md mx-4 md:mx-8 hidden md:block">
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

        {/* Right: Language Switcher, Action Button & Profile */}
        <div className="flex items-center gap-2.5">
          {/* Language Switcher */}
          <button
            onClick={toggleLanguage}
            title={locale === "vi" ? t("common.switchToEnglish") : t("common.switchToVietnamese")}
            className="flex h-8 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-100 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-900"
          >
            <Languages className="h-3.5 w-3.5 text-slate-500" />
            <span className="uppercase">{locale}</span>
          </button>
          <DarkModeToggle />

          {/* New Project CTA */}
          <Link
            href="/projects/new"
            className="hidden h-8 items-center gap-1.5 rounded-lg bg-slate-950 px-3 text-xs font-medium text-white shadow-sm transition-colors hover:bg-slate-800 sm:flex dark:bg-cyan-300 dark:text-slate-950 dark:hover:bg-cyan-200"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>{t("projects.createProject")}</span>
          </Link>

          {/* User Auth state */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2 pl-2 sm:pl-3 border-l border-slate-200">
              <Link href="/settings" className="flex items-center gap-2 group">
                <div className="h-8 w-8 rounded-full bg-indigo-100 border border-indigo-200 text-indigo-700 flex items-center justify-center font-semibold text-xs transition-transform group-hover:scale-105">
                  {user.name ? user.name[0].toUpperCase() : "U"}
                </div>
                <div className="hidden xl:flex flex-col text-left">
                  <span className="text-xs font-medium text-slate-800 leading-tight group-hover:text-indigo-600 transition-colors">{user.name}</span>
                  <span className="text-[10px] text-indigo-600 font-medium capitalize">{user.plan}</span>
                </div>
              </Link>
              <button
                onClick={handleLogout}
                title={t("navigation.logout")}
                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="px-3 py-1.5 text-xs font-medium text-slate-700 hover:text-slate-900 rounded-lg transition-colors"
              >
                {t("auth.signIn")}
              </Link>
              <Link
                href="/register"
                className="px-3 py-1.5 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors"
              >
                {t("auth.signUp")}
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
