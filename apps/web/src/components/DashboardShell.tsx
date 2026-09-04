"use client";

import { useEffect, useState } from "react";
import { CommandPalette } from "@/components/CommandPalette";
import { Navbar } from "@/components/Navbar";
import { OnboardingModal } from "@/components/OnboardingModal";
import { Sidebar } from "@/components/Sidebar";
import { cn } from "@/lib/utils";

const SIDEBAR_COLLAPSED_STORAGE_KEY = "sidebar_collapsed";

type DashboardShellProps = {
  children: React.ReactNode;
  contentClassName?: string;
};

export function DashboardShell({ children, contentClassName }: DashboardShellProps) {
  const [collapsed, setCollapsed] = useState(false);

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
        <Sidebar collapsed={collapsed} onCollapsedChange={handleCollapsedChange} />
        <main
          className={cn(
            "min-w-0 overflow-x-hidden overflow-y-auto transition-[margin] duration-200",
            collapsed ? "ml-16" : "ml-64"
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
