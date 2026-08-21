"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileText, Sparkles, User as UserIcon, LogOut, Bell, Plus, Search } from "lucide-react";
import { useAuthStore } from "@/stores/useAuthStore";

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="flex h-14 items-center justify-between px-6">
        {/* Left: Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight text-slate-900 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm transition-transform group-hover:scale-105">
              <FileText className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5 leading-none">
                <span className="text-sm font-bold tracking-tight">AI REPORT STUDIO</span>
                <span className="rounded bg-indigo-50 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-700 border border-indigo-200/60">
                  VIP PRO
                </span>
              </div>
              <span className="text-[11px] text-slate-500">Document Operating System</span>
            </div>
          </Link>
        </div>

        {/* Middle: Search */}
        <div className="flex-1 max-w-md mx-8 hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm kiếm báo cáo, tài liệu, trích dẫn... (⌘K)"
              className="w-full h-9 pl-9 pr-4 text-xs bg-slate-100/80 hover:bg-slate-100 focus:bg-white border border-transparent focus:border-indigo-500 rounded-lg outline-none transition-all"
            />
          </div>
        </div>

        {/* Right: Actions & User Profile */}
        <div className="flex items-center gap-3">
          <Link
            href="/projects/new"
            className="flex items-center gap-1.5 h-8 px-3 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Tạo báo cáo mới</span>
          </Link>

          {isAuthenticated && user ? (
            <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-indigo-100 border border-indigo-200 text-indigo-700 flex items-center justify-center font-semibold text-xs">
                  {user.name ? user.name[0].toUpperCase() : "U"}
                </div>
                <div className="hidden lg:flex flex-col text-left">
                  <span className="text-xs font-medium text-slate-800 leading-tight">{user.name}</span>
                  <span className="text-[10px] text-indigo-600 font-medium capitalize">{user.plan} Edition</span>
                </div>
              </div>
              <button
                onClick={handleLogout}
                title="Đăng xuất"
                className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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
                Đăng nhập
              </Link>
              <Link
                href="/register"
                className="px-3 py-1.5 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors"
              >
                Đăng ký
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
