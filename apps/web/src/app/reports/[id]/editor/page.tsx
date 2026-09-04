"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  ArrowLeft,
  Sparkles,
  Globe,
  Download,
  ShieldCheck,
  Clock,
  Eye,
  Edit3,
  RefreshCw,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";
import { api } from "@/lib/api";
import { OutlineSidebar } from "@/features/editor/OutlineSidebar";
import { AiAssistantPanel } from "@/features/editor/AiAssistantPanel";
import { ResearchPanel } from "@/features/editor/ResearchPanel";
import { TiptapEditor } from "@/features/editor/TiptapEditor";
import { QualityCheckModal } from "@/features/editor/QualityCheckModal";
import { ExportModal } from "@/features/editor/ExportModal";
import { textToTiptapJson } from "@/lib/documentContent";

export default function ReportEditorPage() {
  const params = useParams();
  const reportId = params?.id as string;
  const router = useRouter();

  // Core State
  const [report, setReport] = useState<any>(null);
  const [sections, setSections] = useState<any[]>([]);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"ai" | "research">("ai");
  const [studioView, setStudioView] = useState<"edit" | "template">("edit");
  const [isOutlineHidden, setIsOutlineHidden] = useState(false);
  const [isAssistantHidden, setIsAssistantHidden] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [templatePreview, setTemplatePreview] = useState<any | null>(null);
  const [templatePreviewLoading, setTemplatePreviewLoading] = useState(false);
  const [templatePreviewError, setTemplatePreviewError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Autosave & Status
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "unsaved">("saved");
  const [lastSavedTime, setLastSavedTime] = useState<string>("Vừa xong");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const editablePreviewFrameRef = useRef<HTMLIFrameElement | null>(null);

  // Modals
  const [isQcOpen, setIsQcOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Load Report & Sections
  const loadReport = useCallback(async () => {
    setLoadError(null);
    try {
      const data = await api.reports.get(reportId);
      setReport(data);
      setSections(data.sections || []);
      if (data.sections?.length > 0 && !activeSectionId) {
        setActiveSectionId(data.sections[0].id);
      }
    } catch (err: any) {
      setLoadError(err.message || "Không thể tải báo cáo. Vui lòng kiểm tra lại kết nối.");
    }
  }, [reportId, activeSectionId]);

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

  const handleApplyAiDraft = async (text: string, tiptapJson: any) => {
    if (!activeSectionId) return;
    const contentJson = tiptapJson || textToTiptapJson(text);
    const wordCount = text.split(/\s+/).filter(Boolean).length;

    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    setSaveStatus("saving");
    setSections((prev) =>
      prev.map((s) =>
        s.id === activeSectionId
          ? {
              ...s,
              plain_text: text,
              content_json: contentJson,
              word_count: wordCount,
              status: "draft",
            }
          : s
      )
    );

    try {
      await api.reports.updateSection(activeSectionId, {
        plain_text: text,
        content_json: contentJson,
        word_count: wordCount,
        status: "draft",
      });
      setSaveStatus("saved");
      setLastSavedTime(new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }));
    } catch {
      setSaveStatus("unsaved");
    }
  };

  const saveCurrentSectionNow = async () => {
    if (!activeSection) return;
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    setSaveStatus("saving");
    setSaveError(null);
    try {
      await api.reports.updateSection(activeSection.id, {
        plain_text: activeSection.plain_text || "",
        content_json: activeSection.content_json || textToTiptapJson(activeSection.plain_text || ""),
        word_count: (activeSection.plain_text || "").split(/\s+/).filter(Boolean).length,
        status: "draft",
      });
      setSaveStatus("saved");
      setLastSavedTime(new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }));
    } catch (err: any) {
      setSaveError(err.message || "Không thể lưu nội dung hiện tại.");
      setSaveStatus("unsaved");
    }
  };

  const normalizeSectionTitle = (value: string) =>
    (value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/Đ/g, "D")
      .toUpperCase()
      .replace(/[^A-Z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const sectionTitleMatches = (renderedTitle: string, sectionTitle: string) => {
    const rendered = normalizeSectionTitle(renderedTitle);
    const section = normalizeSectionTitle(sectionTitle);
    if (!rendered || !section) return false;
    if (rendered === section) return true;
    if (section.startsWith("LOI MO DAU")) {
      return rendered.startsWith("LOI MO DAU") || rendered.startsWith("LOI NOI DAU");
    }
    if (section.startsWith("TAI LIEU THAM KHAO")) {
      return rendered.includes("TAI LIEU THAM KHAO");
    }
    return rendered.includes(section) || section.includes(rendered);
  };

  const cleanEditableText = (text: string) =>
    (text || "")
      .replace(/Trang\s+\d+\s*\/\s*\d+/g, "")
      .replace(/\u00a0/g, " ")
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();

  const preserveVisualMarkers = (editedText: string, originalText: string) => {
    const markers = (originalText || "").match(/\[\[(?:CHART|IMAGE)\s*:.*?\]\]/gis) || [];
    const missingMarkers = markers.filter((marker) => !editedText.includes(marker));
    return missingMarkers.length ? `${editedText}\n\n${missingMarkers.join("\n\n")}`.trim() : editedText;
  };

  const enableEditablePreview = () => {
    const applyEditableMode = () => {
      const frame = editablePreviewFrameRef.current;
      const doc = frame?.contentDocument;
      if (!doc) return;
      doc.designMode = "on";
      doc.body?.setAttribute("contenteditable", "true");
      doc.body?.setAttribute("spellcheck", "true");
      doc.querySelectorAll(".page, .page-content, .docx-block").forEach((node) => {
        (node as HTMLElement).setAttribute("contenteditable", "true");
      });
      doc.body?.addEventListener("input", () => setSaveStatus("unsaved"));
    };

    applyEditableMode();
    window.setTimeout(applyEditableMode, 150);
    window.setTimeout(applyEditableMode, 600);
  };

  const extractEditableSectionUpdates = (doc: Document) => {
    const pageRoot = doc.querySelector("#docx-pages") || doc.body;
    const blocks = Array.from(pageRoot.querySelectorAll(".docx-block")) as HTMLElement[];
    if (!blocks.length) {
      const fallbackText = preserveVisualMarkers(cleanEditableText(doc.body.innerText || ""), activeSection?.plain_text || "");
      const wordCount = fallbackText.split(/\s+/).filter(Boolean).length;
      return activeSection && fallbackText && wordCount > 10
        ? [{ section: activeSection, text: fallbackText, wordCount }]
        : [];
    }

    const matched = sections
      .map((section) => {
        const headingIndex = blocks.findIndex(
          (block) => block.classList.contains("docx-heading") && sectionTitleMatches(block.innerText, section.title || "")
        );
        let fallbackIndex = -1;
        for (let idx = blocks.length - 1; idx >= 0; idx -= 1) {
          if (sectionTitleMatches(blocks[idx].innerText, section.title || "")) {
            fallbackIndex = idx;
            break;
          }
        }
        const blockIndex = headingIndex >= 0 ? headingIndex : fallbackIndex;
        return blockIndex >= 0 ? { section, blockIndex } : null;
      })
      .filter(Boolean) as Array<{ section: any; blockIndex: number }>;

    const updates = matched
      .sort((a, b) => a.blockIndex - b.blockIndex)
      .map((item, index, ordered) => {
        const nextIndex = ordered[index + 1]?.blockIndex ?? blocks.length;
        const text = cleanEditableText(
          blocks
            .slice(item.blockIndex, nextIndex)
            .map((block) => block.innerText)
            .join("\n\n")
        );
        const textWithVisuals = preserveVisualMarkers(text, item.section.plain_text || "");
        const wordCount = textWithVisuals.split(/\s+/).filter(Boolean).length;
        const originalWords = Number(item.section.word_count || 0);
        const titleOnlyWords = (item.section.title || "").split(/\s+/).filter(Boolean).length + 8;
        const isUnsafeShrink = originalWords >= 80 && wordCount < Math.max(40, Math.floor(originalWords * 0.25));
        if (!textWithVisuals || wordCount <= titleOnlyWords || isUnsafeShrink) return null;
        return { section: item.section, text: textWithVisuals, wordCount };
      })
      .filter(Boolean) as Array<{ section: any; text: string; wordCount: number }>;

    if (updates.length) return updates;

    const fallbackText = preserveVisualMarkers(cleanEditableText(doc.body.innerText || ""), activeSection?.plain_text || "");
    const wordCount = fallbackText.split(/\s+/).filter(Boolean).length;
    return activeSection && fallbackText && wordCount > 10
      ? [{ section: activeSection, text: fallbackText, wordCount }]
      : [];
  };

  const saveEditableTemplate = async () => {
    const doc = editablePreviewFrameRef.current?.contentDocument;
    if (!doc?.body?.innerText?.trim()) return;

    setSaveStatus("saving");
    setSaveError(null);
    try {
      const updates = extractEditableSectionUpdates(doc);
      if (!updates.length) {
        throw new Error("Không tìm thấy nội dung chương hợp lệ để lưu.");
      }

      await Promise.all(updates.map(({ section, text, wordCount }) =>
        api.reports.updateSection(section.id, {
          plain_text: text,
          content_json: textToTiptapJson(text),
          word_count: wordCount,
          status: "draft",
        })
      ));

      setSections((prev) => prev.map((section) => {
        const found = updates.find((item) => item.section.id === section.id);
        if (!found) return section;
        return {
          ...section,
          plain_text: found.text,
          content_json: textToTiptapJson(found.text),
          word_count: found.wordCount,
          status: "draft",
        };
      }));
      setSaveStatus("saved");
      setLastSavedTime(new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }));
      setTemplatePreviewError(null);
    } catch (err: any) {
      console.error("Không thể lưu bản soạn thảo theo mẫu", err);
      setSaveError(err.message || "Không thể lưu bản soạn thảo theo mẫu.");
      setSaveStatus("unsaved");
    }
  };

  const loadTemplatePreview = useCallback(async () => {
    setTemplatePreviewLoading(true);
    setTemplatePreviewError(null);
    try {
      const preview = await api.exports.previewReportHtml(reportId);
      setTemplatePreview(preview);
    } catch (err: any) {
      setTemplatePreviewError(err.message || "Không thể tải bản xem theo mẫu.");
    } finally {
      setTemplatePreviewLoading(false);
    }
  }, [reportId]);

  const rebuildTemplatePreviewSafely = async () => {
    if (saveStatus === "unsaved") {
      await saveEditableTemplate();
    }
    await loadTemplatePreview();
  };

  useEffect(() => {
    if ((studioView === "template" || studioView === "edit") && !templatePreview && !templatePreviewLoading && !templatePreviewError) {
      loadTemplatePreview();
    }
  }, [studioView, templatePreview, templatePreviewLoading, templatePreviewError, loadTemplatePreview]);

  const totalWords = sections.reduce((acc, s) => acc + (s.word_count || 0), 0);
  const estPages = Math.max(1, Math.ceil(totalWords / 300));

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
        <div className="max-w-md w-full p-6 bg-white rounded-2xl border border-slate-200 shadow-sm text-center space-y-4">
          <div className="h-12 w-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto">
            <FileText className="h-6 w-6" />
          </div>
          <h2 className="text-sm font-bold text-slate-800">Không thể tải báo cáo</h2>
          <p className="text-xs text-slate-500">{loadError}</p>
          <div className="flex gap-2 justify-center pt-2">
            <button
              onClick={() => loadReport()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
            >
              Thử tải lại
            </button>
            <Link
              href="/projects"
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
            >
              Về danh sách dự án
            </Link>
          </div>
        </div>
      </div>
    );
  }

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
    <div className="min-h-screen flex flex-col bg-[#f6f8fb]">
      {/* Top Studio Bar */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        {/* Left: Back & Title */}
        <div className="flex min-h-16 items-center justify-between gap-3 px-4 lg:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <Link
              href="/projects"
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-900"
              title="Về danh sách dự án"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="min-w-0">
              <div className="flex min-w-0 items-center gap-2">
                <h1 className="truncate text-sm font-bold text-slate-950 sm:max-w-md lg:max-w-xl">
                  {report.title}
                </h1>
                <span className="hidden rounded-md border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-slate-500 sm:inline-flex">
                  {report.report_type || "report"}
                </span>
              </div>
              <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-500">
                <span className="hidden sm:inline">Mục: {activeSection?.title || "Chưa chọn"}</span>
                <span className="hidden text-slate-300 sm:inline">/</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {saveStatus === "saving" ? (
                    <span className="font-semibold text-amber-600">Đang lưu...</span>
                  ) : saveStatus === "saved" ? (
                    <span className="font-medium text-emerald-600">Đã lưu {lastSavedTime}</span>
                  ) : (
                    <span className="font-medium text-rose-600">Có thay đổi chưa lưu</span>
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* Center: Compact live stats */}
          <div className="hidden items-center gap-2 text-[11px] font-semibold text-slate-500 xl:flex">
            <span>{totalWords.toLocaleString("vi-VN")} từ</span>
            <span className="text-slate-300">•</span>
            <span>~{estPages} trang</span>
            <span className="text-slate-300">•</span>
            <span>{sections.length} mục</span>
          </div>

          {/* Right: Actions */}
          <div className="flex shrink-0 items-center gap-2">
            <div className="hidden items-center gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1 sm:flex">
            <button
              onClick={() => setStudioView("edit")}
              className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-bold transition ${
                studioView === "edit" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Edit3 className="h-3.5 w-3.5" />
              <span>Soạn thảo</span>
            </button>
            <button
              onClick={() => setStudioView("template")}
              className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-bold transition ${
                studioView === "template" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Eye className="h-3.5 w-3.5" />
              <span>Theo mẫu</span>
            </button>
          </div>

          <button
            onClick={() => setIsAssistantHidden((value) => !value)}
            className="hidden h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 hover:text-indigo-700 lg:inline-flex"
            title={isAssistantHidden ? "Hiện trợ lý AI" : "Ẩn trợ lý AI"}
          >
            {isAssistantHidden ? <PanelRightOpen className="h-4 w-4" /> : <PanelRightClose className="h-4 w-4" />}
          </button>

          {/* Quality check button */}
          <button
            onClick={() => setIsQcOpen(true)}
            className="flex h-8 items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-2.5 text-xs font-semibold text-indigo-700 transition-colors hover:bg-indigo-100"
          >
            <ShieldCheck className="h-4 w-4" />
            <span className="hidden md:inline">Kiểm tra</span>
          </button>

          {/* Export Button */}
          <button
            onClick={() => setIsExportOpen(true)}
            className="flex h-8 items-center gap-1.5 rounded-lg bg-indigo-600 px-3 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            <Download className="h-4 w-4" />
            <span>Xuất</span>
          </button>
          </div>
        </div>
      </header>

      {/* Main Studio Work Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Outline Navigation */}
        {!isOutlineHidden && (
          <OutlineSidebar
            sections={sections}
            activeSectionId={activeSectionId}
            onSelectSection={(id) => setActiveSectionId(id)}
            onHide={() => setIsOutlineHidden(true)}
          />
        )}
        {isOutlineHidden && (
          <button
            onClick={() => setIsOutlineHidden(false)}
            className="sticky top-20 z-20 m-3 inline-flex h-9 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-bold text-slate-600 shadow-sm transition hover:text-indigo-700"
            title="Hiện cấu trúc báo cáo"
          >
            <PanelLeftOpen className="h-4 w-4" />
            <span className="hidden xl:inline">Cấu trúc</span>
          </button>
        )}

        {/* Middle: Genuine A4 Document Canvas */}
        <main className="flex min-w-0 flex-1 flex-col items-center overflow-y-auto bg-[#eef2f7] p-3 sm:p-4 lg:p-5">
          {studioView === "template" ? (
            <div className="w-full max-w-[1180px] space-y-3">
              <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-bold text-slate-900">Bản xem theo file mẫu</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    Hiển thị bản DOCX đã áp mẫu, bao gồm bìa, ảnh/logo, bảng và nội dung đã sinh.
                  </p>
                </div>
                <button
                  onClick={loadTemplatePreview}
                  disabled={templatePreviewLoading}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-200 disabled:opacity-60"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${templatePreviewLoading ? "animate-spin" : ""}`} />
                  <span>Làm mới bản xem</span>
                </button>
              </div>

              {templatePreviewLoading ? (
                <div className="flex h-[720px] items-center justify-center rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-500">
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin text-indigo-600" />
                  Đang dựng bản xem theo mẫu...
                </div>
              ) : templatePreviewError ? (
                <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-700">
                  {templatePreviewError}
                </div>
              ) : templatePreview?.html_document ? (
                <div className="h-[calc(100vh-10rem)] min-h-[720px] overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
                  <iframe
                    title="Bản xem báo cáo theo mẫu"
                    srcDoc={templatePreview.html_document}
                    className="h-full w-full bg-slate-100"
                    onLoad={enableEditablePreview}
                  />
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-xs text-slate-500">
                  Chưa có bản xem theo mẫu. Bấm “Làm mới bản xem” để dựng lại.
                </div>
              )}
            </div>
          ) : (
            <div className="w-full max-w-[1180px] space-y-3">
                {saveError && (
                  <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[11px] font-semibold text-red-700">
                    {saveError}
                  </p>
                )}

                {activeSection ? (
                  <TiptapEditor
                    key={activeSection.id}
                    content={activeSection.content_json || textToTiptapJson(activeSection.plain_text || "")}
                    onChange={handleEditorChange}
                    onSaveNow={saveCurrentSectionNow}
                    projectId={report?.project_id}
                    reportId={reportId}
                    reportTitle={report?.title || ""}
                    sectionTitle={activeSection.title || ""}
                    onAskAi={(selectedText) => {
                      setActiveTab("ai");
                      console.log("Selected text for AI:", selectedText);
                    }}
                  />
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-xs text-slate-500">
                    Chọn một mục trong cấu trúc báo cáo để bắt đầu soạn thảo.
                  </div>
                )}
            </div>
          )}
        </main>

        {/* Right: AI Writing Assistant & Research Panel */}
        {!isAssistantHidden && (
        <aside className="hidden w-[360px] shrink-0 flex-col border-l border-slate-200 bg-white lg:flex xl:w-[390px]">
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
        )}
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
