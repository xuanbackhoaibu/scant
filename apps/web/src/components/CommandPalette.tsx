"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Sparkles,
  FileText,
  Database,
  Layers,
  Settings,
  ShieldCheck,
  Zap,
  Download,
  CheckSquare,
} from "lucide-react";

interface CommandItem {
  id: string;
  title: string;
  category: string;
  icon: any;
  action: () => void;
}

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      } else if (e.key === "Escape") {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const commands: CommandItem[] = [
    {
      id: "auto-create",
      title: "One-Click Auto Report (Tạo Báo Cáo Tự Động 1-Click)",
      category: "AI Actions",
      icon: Sparkles,
      action: () => {
        router.push("/wizard?mode=auto");
        setIsOpen(false);
      },
    },
    {
      id: "new-doc",
      title: "Tạo tài liệu mới từ Wizard (Đa năng)",
      category: "Documents",
      icon: FileText,
      action: () => {
        router.push("/wizard");
        setIsOpen(false);
      },
    },
    {
      id: "templates",
      title: "Thư viện Mẫu Báo cáo & Marketplace",
      category: "Templates",
      icon: Layers,
      action: () => {
        router.push("/templates");
        setIsOpen(false);
      },
    },
    {
      id: "data-connectors",
      title: "Kết nối Dữ liệu (PostgreSQL, MySQL, CSV, REST API)",
      category: "Data Workspace",
      icon: Database,
      action: () => {
        router.push("/data");
        setIsOpen(false);
      },
    },
    {
      id: "automations",
      title: "Tự Động Hóa & Lập Lịch Báo Cáo Định Kỳ",
      category: "Automations",
      icon: Zap,
      action: () => {
        router.push("/automations");
        setIsOpen(false);
      },
    },
    {
      id: "admin",
      title: "Bảng Điều Khiển Quản Trị Hệ Thống (Admin Console)",
      category: "Administration",
      icon: ShieldCheck,
      action: () => {
        router.push("/admin");
        setIsOpen(false);
      },
    },
    {
      id: "settings",
      title: "Cài đặt Workspace & Bộ Nhận Diện Thương Hiệu (Brand Kit)",
      category: "Settings",
      icon: Settings,
      action: () => {
        router.push("/settings");
        setIsOpen(false);
      },
    },
  ];

  const filteredCommands = commands.filter(
    (c) =>
      c.title.toLowerCase().includes(query.toLowerCase()) ||
      c.category.toLowerCase().includes(query.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Search input header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100">
          <Search className="h-5 w-5 text-slate-400" />
          <input
            autoFocus
            type="text"
            placeholder="Tìm kiếm lệnh, tác vụ, hoặc tài liệu (hoặc gõ để lọc)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-hidden"
          />
          <kbd className="px-2 py-0.5 text-[10px] font-bold text-slate-400 bg-slate-100 rounded-md border border-slate-200">
            ESC
          </kbd>
        </div>

        {/* Command list */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              Không tìm thấy lệnh hoặc chức năng phù hợp.
            </div>
          ) : (
            filteredCommands.map((c) => {
              const Icon = c.icon;
              return (
                <button
                  key={c.id}
                  onClick={c.action}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-indigo-50/70 text-left group transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-100 text-slate-600 rounded-lg group-hover:bg-indigo-100 group-hover:text-indigo-700 transition">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-800 group-hover:text-indigo-900">
                        {c.title}
                      </p>
                      <p className="text-[10px] text-slate-400">{c.category}</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 font-medium">
                    ↵ Chọn
                  </span>
                </button>
              );
            })
          )}
        </div>

        {/* Footer hints */}
        <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span>AI Universal Document Workspace</span>
          <span>Dùng phím ↑ ↓ để di chuyển</span>
        </div>
      </div>
    </div>
  );
}
