"use client";

import { useState } from "react";
import {
  BookOpen,
  ChevronRight,
  ChevronDown,
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  FileText,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Section {
  id: string;
  report_id: string;
  parent_id?: string | null;
  title: string;
  position: number;
  level: number;
  section_number?: string;
  status: string;
  word_count: number;
  plain_text?: string;
}

interface OutlineSidebarProps {
  sections: Section[];
  activeSectionId: string | null;
  onSelectSection: (id: string) => void;
  onAddSection?: () => void;
}

export function OutlineSidebar({
  sections,
  activeSectionId,
  onSelectSection,
  onAddSection,
}: OutlineSidebarProps) {
  return (
    <aside className="w-72 border-r border-slate-200 bg-white flex flex-col h-[calc(100vh-3.5rem)] sticky top-14">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-indigo-600" />
          <span className="text-xs font-bold text-slate-800">Cấu trúc Báo Cáo</span>
        </div>
        {onAddSection && (
          <button
            onClick={onAddSection}
            title="Thêm mục"
            className="p-1 hover:bg-slate-100 rounded text-slate-500 hover:text-indigo-600 transition-colors"
          >
            <Plus className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Sections Tree */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sections.map((sec) => {
          const isActive = activeSectionId === sec.id;
          const isDrafted = sec.status === "draft" || (sec.word_count && sec.word_count > 40);

          return (
            <button
              key={sec.id}
              onClick={() => onSelectSection(sec.id)}
              className={cn(
                "w-full text-left flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs transition-all group",
                isActive
                  ? "bg-indigo-50/90 text-indigo-950 font-bold shadow-xs border border-indigo-200/60"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                sec.level === 2 && "pl-6 text-[11px]",
                sec.level === 3 && "pl-9 text-[11px]"
              )}
            >
              <div className="mt-0.5 shrink-0">
                {isDrafted ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                ) : (
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      isActive ? "bg-indigo-600" : "bg-slate-300 group-hover:bg-slate-400"
                    )}
                  />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <span className="truncate block leading-snug">{sec.title}</span>
                <span className="text-[10px] text-slate-400 font-normal">
                  {sec.word_count ? `${sec.word_count} từ` : "Chưa có nội dung"}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/60 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Tổng số mục:</span>
        <span className="font-bold text-slate-700">{sections.length} phần</span>
      </div>
    </aside>
  );
}
