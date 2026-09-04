"use client";

import { useState } from "react";
import {
  BookOpen,
  Plus,
  CheckCircle2,
  PanelLeftClose,
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
  onHide?: () => void;
}

export function OutlineSidebar({
  sections,
  activeSectionId,
  onSelectSection,
  onAddSection,
  onHide,
}: OutlineSidebarProps) {
  const draftedCount = sections.filter((sec) => sec.status === "draft" || (sec.word_count && sec.word_count > 40)).length;

  return (
    <aside className="hidden w-[280px] shrink-0 flex-col border-r border-slate-200 bg-white lg:flex xl:w-[304px]">
      {/* Header */}
      <div className="border-b border-slate-100 p-3.5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <BookOpen className="h-4 w-4 text-indigo-600" />
            <span className="truncate text-xs font-bold text-slate-900">Cấu trúc báo cáo</span>
          </div>
          <div className="flex items-center gap-1">
            {onAddSection && (
              <button
                onClick={onAddSection}
                title="Thêm mục"
                className="rounded p-1 text-slate-500 transition-colors hover:bg-slate-100 hover:text-indigo-600"
              >
                <Plus className="h-4 w-4" />
              </button>
            )}
            {onHide && (
              <button
                onClick={onHide}
                title="Ẩn cấu trúc báo cáo"
                className="rounded p-1 text-slate-500 transition-colors hover:bg-slate-100 hover:text-indigo-600"
              >
                <PanelLeftClose className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2 text-[11px] font-semibold text-slate-500">
          <div>
            <p className="text-sm font-bold text-slate-900">{sections.length}</p>
            <p>Tổng mục</p>
          </div>
          <div>
            <p className="text-sm font-bold text-emerald-700">{draftedCount}</p>
            <p>Đã có nội dung</p>
          </div>
        </div>
      </div>

      {/* Sections Tree */}
      <div className="flex-1 space-y-1 overflow-y-auto p-2">
        {sections.map((sec) => {
          const isActive = activeSectionId === sec.id;
          const isDrafted = sec.status === "draft" || (sec.word_count && sec.word_count > 40);

          return (
            <button
              key={sec.id}
              onClick={() => onSelectSection(sec.id)}
              className={cn(
                "group flex w-full items-start gap-2.5 rounded-lg px-3 py-2 text-left text-xs transition-all",
                isActive
                  ? "border border-indigo-200/70 bg-indigo-50/90 font-bold text-indigo-950 shadow-xs"
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
      <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/60 p-3 text-[11px] text-slate-500">
        <span>Tổng số mục:</span>
        <span className="font-bold text-slate-700">{sections.length} phần</span>
      </div>
    </aside>
  );
}
