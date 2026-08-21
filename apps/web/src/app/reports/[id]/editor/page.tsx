"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  ArrowLeft,
  Sparkles,
  Search,
  Globe,
  Download,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ChevronRight,
  BookOpen,
  School,
  Layers,
  Save,
} from "lucide-react";
import { api } from "@/lib/api";
import { OutlineSidebar } from "@/features/editor/OutlineSidebar";
import { AiAssistantPanel } from "@/features/editor/AiAssistantPanel";
import { ResearchPanel } from "@/features/editor/ResearchPanel";
import { TiptapEditor } from "@/features/editor/TiptapEditor";
import { QualityCheckModal } from "@/features/editor/QualityCheckModal";
import { ExportModal } from "@/features/editor/ExportModal";

export default function ReportEditorPage() {
  const params = useParams();
  const reportId = params.id as string;
  const router = useRouter();

  // Core State
  const [report, setReport] = useState<any>(null);
  const [sections, setSections] = useState<any[]>([]);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"ai" | "research">("ai");

  // Autosave & Status
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "unsaved">("saved");
  const [lastSavedTime, setLastSavedTime] = useState<string>("Vừa xong");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Modals
  const [isQcOpen, setIsQcOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Load Report & Sections
  const loadReport = useCallback(async () => {
    try {
      const data = await api.reports.get(reportId);
      setReport(data);
      setSections(data.sections || []);
      if (data.sections?.length > 0 && !activeSectionId) {
        setActiveSectionId(data.sections[0].id);
      }
    } catch {
      router.push("/projects");
    }
  }, [reportId, activeSectionId, router]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const activeSection = sections.find((s) => s.id === activeSectionId) || sections[0] || null;

  // Handle text edits with 1.5s debounced autosave
  const handleEditorChange = (plainText: string, json: any) => {
    if (!activeSectionId) return;

    setSaveStatus("unsaved");

    // Update local state immediately
    setSections((prev) =>
      prev.map((s) =>
        s.id === activeSectionId
          ? {
              ...s,
              plain_text: plainText,
              content_json: json,
              word_count: plainText.split(/\s+/).filter(Boolean).length,
              status: "draft",
            }
          : s
      )
    );

    // Debounce save to database
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(async () => {
      setSaveStatus("saving");
      try {
        await api.reports.updateSection(activeSectionId, {
          plain_text: plainText,
          content_json: json,
          word_count: plainText.split(/\s+/).filter(Boolean).length,
          status: "draft",
        });
        setSaveStatus("saved");
        setLastSavedTime(
          new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })
        );
      } catch {
        setSaveStatus("unsaved");
      }
    }, 1500);
  };

  const handleApplyAiDraft = (text: string, tiptapJson: any) => {
    if (!activeSectionId) return;
    handleEditorChange(text, tiptapJson);
  };

  const totalWords = sections.reduce((acc, s) => acc + (s.word_count || 0), 0);
  const estPages = Math.max(1, Math.ceil(totalWords / 300));

  if (!report) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-600">
          <Sparkles className="h-4 w-4 animate-spin text-indigo-600" />
          <span>Đang tải không gian Report Studio...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-100/70">
      {/* Top Studio Bar */}
      <header className="h-14 border-b border-slate-200 bg-white sticky top-0 z-30 flex items-center justify-between px-4">
        {/* Left: Back & Title */}
        <div className="flex items-center gap-3">
          <Link
            href="/projects"
            className="p-1.5 hover:bg-slate-100 text-slate-500 hover:text-slate-900 rounded-lg transition-colors"
            title="Về danh sách dự án"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>

          <div className="flex flex-col">
            <h1 className="text-xs font-bold text-slate-900 max-w-sm truncate">
              {report.title}
            </h1>
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <span>{report.report_type?.toUpperCase()}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {saveStatus === "saving" ? (
                  <span className="text-amber-600 font-semibold animate-pulse">Đang lưu...</span>
                ) : saveStatus === "saved" ? (
                  <span className="text-emerald-600 font-medium">Đã lưu ({lastSavedTime})</span>
                ) : (
                  <span className="text-slate-500">Chưa lưu</span>
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Center: Live Stats */}
        <div className="hidden md:flex items-center gap-4 text-xs font-medium text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200/80">
          <div>
            <span className="text-slate-400">Số từ: </span>
            <strong className="text-slate-800">{totalWords.toLocaleString()}</strong>
          </div>
          <div className="h-3 w-px bg-slate-200" />
          <div>
            <span className="text-slate-400">Trang A4: </span>
            <strong className="text-slate-800">~{estPages} trang</strong>
          </div>
          <div className="h-3 w-px bg-slate-200" />
          <div>
            <span className="text-slate-400">Nguồn: </span>
            <strong className="text-slate-800">{report.sources_count || 0}</strong>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Quality check button */}
          <button
            onClick={() => setIsQcOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors border border-indigo-200"
          >
            <ShieldCheck className="h-4 w-4" />
            <span className="hidden sm:inline">Kiểm tra Báo cáo</span>
          </button>

          {/* Export Button */}
          <button
            onClick={() => setIsExportOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
          >
            <Download className="h-4 w-4" />
            <span>Xuất Báo Cáo</span>
          </button>
        </div>
      </header>

      {/* Main Studio Work Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Outline Navigation */}
        <OutlineSidebar
          sections={sections}
          activeSectionId={activeSectionId}
          onSelectSection={(id) => setActiveSectionId(id)}
        />

        {/* Middle: Genuine A4 Document Canvas */}
        <main className="flex-1 overflow-y-auto p-6 flex flex-col items-center bg-slate-100/80">
          <div className="a4-page canvas-view-white min-h-[1120px] max-w-[850px] w-full">
            {/* Header info for Section */}
            {activeSection && (
              <div className="mb-4 pb-3 border-b border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold uppercase tracking-wider text-indigo-600">
                  {activeSection.title}
                </span>
                <span>Trang A4 chuẩn ĐH Bách Khoa / FPT</span>
              </div>
            )}

            {/* Tiptap Rich-Text Editor */}
            {activeSection ? (
              <TiptapEditor
                key={activeSection.id}
                content={activeSection.content_json || activeSection.plain_text}
                onChange={handleEditorChange}
              />
            ) : (
              <div className="text-center py-20 text-slate-400">
                Hãy chọn hoặc thêm một chương mục từ Outline bên trái để bắt đầu soạn thảo.
              </div>
            )}
          </div>
        </main>

        {/* Right: AI Writing Assistant & Research Panel */}
        <aside className="w-80 border-l border-slate-200 bg-white flex flex-col h-[calc(100vh-3.5rem)] sticky top-14">
          {/* Tab Switcher */}
          <div className="grid grid-cols-2 p-1.5 bg-slate-100 border-b border-slate-200 gap-1 text-xs">
            <button
              onClick={() => setActiveTab("ai")}
              className={`py-1.5 rounded-md font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === "ai"
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Trợ lý AI</span>
            </button>

            <button
              onClick={() => setActiveTab("research")}
              className={`py-1.5 rounded-md font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === "research"
                  ? "bg-white text-indigo-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Globe className="h-3.5 w-3.5" />
              <span>Research</span>
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === "ai" ? (
              <AiAssistantPanel
                projectId={report.project_id}
                reportId={report.id}
                activeSection={activeSection}
                onApplyDraft={handleApplyAiDraft}
              />
            ) : (
              <ResearchPanel
                projectId={report.project_id}
                onInsertCitation={(citKey) => {
                  if (activeSection) {
                    const newText = `${activeSection.plain_text || ""} ${citKey}`;
                    handleEditorChange(newText, activeSection.content_json);
                  }
                }}
              />
            )}
          </div>
        </aside>
      </div>

      {/* Quality Check Modal */}
      <QualityCheckModal
        reportId={report.id}
        isOpen={isQcOpen}
        onClose={() => setIsQcOpen(false)}
        onOpenExport={() => setIsExportOpen(true)}
      />

      {/* Export Modal */}
      <ExportModal
        reportId={report.id}
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
      />
    </div>
  );
}
