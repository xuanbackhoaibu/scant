"use client";

import { useEffect, useState } from "react";
import { CommandPalette } from "@/components/CommandPalette";
import { Navbar } from "@/components/Navbar";
import { OnboardingModal } from "@/components/OnboardingModal";
import { Sidebar } from "@/components/Sidebar";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

const SIDEBAR_COLLAPSED_STORAGE_KEY = "sidebar_collapsed";

type DashboardShellProps = {
  children: React.ReactNode;
  contentClassName?: string;
};

export function DashboardShell({ children, contentClassName }: DashboardShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY);
    if (saved) setCollapsed(saved === "true");
  }, []);

  const handleCollapsedChange = (next: boolean) => {
    setCollapsed(next);
    localStorage.setItem(SIDEBAR_COLLAPSED_STORAGE_KEY, String(next));
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Navbar />
      <div className="min-w-0 flex-1 overflow-x-hidden">
        {mobileNavOpen && <button type="button" aria-label="Đóng điều hướng" onClick={() => setMobileNavOpen(false)} className="fixed inset-0 top-14 z-20 bg-black/20 md:hidden" />}
        <div className={mobileNavOpen ? "block" : "hidden md:block"}><Sidebar collapsed={collapsed} onCollapsedChange={handleCollapsedChange} /></div>
        <button type="button" aria-label={mobileNavOpen ? "Đóng điều hướng" : "Mở điều hướng"} aria-expanded={mobileNavOpen} onClick={() => setMobileNavOpen(!mobileNavOpen)} className="fixed bottom-4 left-4 z-40 flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-sm focus-visible:ring-2 focus-visible:ring-indigo-500 md:hidden">{mobileNavOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}</button>
        <main
          className={cn(
            "min-w-0 overflow-x-hidden overflow-y-auto transition-[margin] duration-200",
            collapsed ? "ml-0 md:ml-16" : "ml-0 md:ml-[268px]"
          )}
        >
          <div className={contentClassName}>{children}</div>
        </main>
      </div>
      <CommandPalette />
      <OnboardingModal />
    </div>
  );
}
