"use client";

import React from "react";
import {
  FileSpreadsheet,
  CheckCircle2,
  Table,
  Layers,
  RefreshCw,
  AlertCircle,
  Eye,
  Maximize2,
  ArrowRight,
} from "lucide-react";
import SpreadsheetPreview from "@/components/SpreadsheetPreview";
import {
  buildSelectedVisualWorkbook,
  resolveSelectedSheetName,
} from "@/lib/directAnalysisPreview";

export type AnalysisScopeMode = "workbook" | "sheet" | "sheets" | "range";

export interface LoadedWorkbookInfo {
  fileName: string;
  sheetCount: number;
  totalRows: number;
  totalCols: number;
  sheets: Array<{ name: string; row_count?: number; column_count?: number; records_count?: number }>;
  columns?: any[];
  rawPreview?: any;
}

interface DirectAnalysisPromptPanelProps {
  workbook: LoadedWorkbookInfo;
  sheetRange: string;
  onChangeSheetRange: (val: string) => void;
  selectedSheetName: string;
  onSelectSheet: (sheetName: string) => void;
  analysisScopeMode: AnalysisScopeMode;
  onChangeAnalysisScopeMode: (mode: AnalysisScopeMode) => void;
  selectedAnalysisSheets: string[];
  onChangeSelectedAnalysisSheets: (sheets: string[]) => void;
  analysisRange: string;
  onChangeAnalysisRange: (range: string) => void;
  analysisPrompt?: string;
  onChangeAnalysisPrompt?: (val: string) => void;
  onAnalyze?: (prompt: string, preferredSheet?: string) => void;
  isAnalyzing?: boolean;
  onOpenWorkspace: () => void;
  onChangeSource?: () => void;
  locale?: string;
}

export default function DirectAnalysisPromptPanel({
  workbook,
  sheetRange,
  onChangeSheetRange,
  selectedSheetName,
  onSelectSheet,
  analysisScopeMode,
  onChangeAnalysisScopeMode,
  selectedAnalysisSheets,
  onChangeSelectedAnalysisSheets,
  analysisRange,
  onChangeAnalysisRange,
  analysisPrompt,
  onChangeAnalysisPrompt,
  onAnalyze,
  isAnalyzing,
  onOpenWorkspace,
  onChangeSource,
  locale = "vi",
}: DirectAnalysisPromptPanelProps) {
  const activeSheetName = resolveSelectedSheetName(workbook.rawPreview || workbook, selectedSheetName, sheetRange);
  const selectedVisual = buildSelectedVisualWorkbook(workbook.rawPreview, activeSheetName);
  const selectedSheetMeta = workbook.sheets?.find((sheet) => sheet.name === activeSheetName);
  const sheetOptions = workbook.sheets || [];

  return (
    <div className="min-w-0 space-y-4 overflow-hidden">
      {/* BƯỚC 2: DỮ LIỆU ĐÃ ĐỌC THÀNH CÔNG */}
      <div className="rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50/90 via-white to-teal-50/40 p-4 sm:p-5 shadow-xs space-y-3.5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-xs">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[11px] font-bold text-emerald-800">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  {locale === "vi" ? "Đã đọc dữ liệu thành công" : "Dataset successfully read"}
                </span>
              </div>
              <h3 className="mt-1 text-sm font-bold text-slate-900 truncate max-w-md" title={workbook.fileName}>
                {workbook.fileName}
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                <span className="font-semibold text-emerald-700">{workbook.sheetCount} sheet</span> •{" "}
                <span className="font-semibold text-slate-700">{workbook.totalRows.toLocaleString()} dòng tổng</span>
                {workbook.totalCols > 0 && ` • ${locale === "vi" ? "tối đa" : "max"} ${workbook.totalCols} ${locale === "vi" ? "cột" : "cols"}`}
              </p>
            </div>
          </div>

          {onChangeSource && (
            <button
              type="button"
              onClick={onChangeSource}
              className="inline-flex items-center gap-1.5 self-start rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50 shadow-2xs transition"
            >
              <RefreshCw className="h-3.5 w-3.5 text-slate-500" />
              <span>{locale === "vi" ? "Đổi nguồn khác" : "Change source"}</span>
            </button>
          )}
        </div>

        {/* Sheet Badges List */}
        {workbook.sheets && workbook.sheets.length > 0 && (
          <div className="pt-1">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
              {locale === "vi" ? "Danh sách Sheet trong file:" : "Sheets in workbook:"}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {workbook.sheets.map((s, idx) => {
                const isSelected = activeSheetName === s.name;
                return (
                  <button
                    key={s.name || idx}
                    type="button"
                    onClick={() => {
                      onSelectSheet(s.name);
                      onChangeSheetRange(s.name);
                    }}
                    className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                      isSelected
                        ? "bg-emerald-600 text-white shadow-2xs ring-1 ring-emerald-700"
                        : "bg-white text-slate-700 border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50"
                    }`}
                    title={s.row_count ? `${s.row_count} dòng` : s.name}
                  >
                    <Table className="h-3 w-3" />
                    <span>{s.name}</span>
                    {s.row_count !== undefined && s.row_count > 0 && (
                      <span className={`text-[10px] ${isSelected ? "text-emerald-100" : "text-slate-400"}`}>
                        ({s.row_count})
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

      </div>

      {/* BƯỚC 3: BẢN XEM TRƯỚC DỮ LIỆU */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs min-w-0 overflow-hidden">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h3 className="flex min-w-0 items-center gap-2 text-sm font-bold text-slate-900">
              <Eye className="h-4 w-4 shrink-0 text-emerald-600" />
              <span className="min-w-0 truncate">
                {locale === "vi" ? "Bản xem trước" : "Preview"} — {activeSheetName || (locale === "vi" ? "Sheet đã chọn" : "Selected sheet")}
              </span>
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              {(selectedVisual.sheet?.max_row || selectedSheetMeta?.row_count || 0).toLocaleString()} {locale === "vi" ? "dòng" : "rows"} •{" "}
              {selectedVisual.sheet?.max_column || selectedSheetMeta?.column_count || 0} {locale === "vi" ? "cột" : "cols"}
            </p>
          </div>
          <button
            type="button"
            onClick={onOpenWorkspace}
            className="inline-flex items-center justify-center gap-1.5 self-start rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-2xs transition hover:bg-slate-50 active:scale-95 sm:self-auto"
          >
            <Maximize2 className="h-3.5 w-3.5 text-slate-500" />
            <span>{locale === "vi" ? "Mở lớn" : "Open large"}</span>
          </button>
        </div>

        <div className="h-[clamp(360px,45vh,520px)] min-h-0 min-w-0 max-w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
          {selectedVisual.workbook ? (
            <SpreadsheetPreview
              workbook={selectedVisual.workbook}
              height="100%"
              locale={locale}
              activeSheetName={activeSheetName}
              onActiveSheetChange={(sheetName) => {
                onSelectSheet(sheetName);
                onChangeSheetRange(sheetName);
              }}
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
              <AlertCircle className="h-5 w-5 text-amber-600" />
              <p className="text-sm font-bold text-slate-800">
                {selectedVisual.mismatch
                  ? locale === "vi"
                    ? "Không thể hiển thị bản xem trước của sheet này."
                    : "Could not show preview for this sheet."
                  : locale === "vi"
                  ? "Workbook đã sẵn sàng nhưng chưa có dữ liệu xem trước trực quan."
                  : "Workbook is ready but visual preview data is not available."}
              </p>
              <p className="max-w-md text-xs leading-5 text-slate-500">
                {locale === "vi"
                  ? "Hãy thử đọc lại nguồn dữ liệu hoặc mở Workspace để kiểm tra workbook."
                  : "Try reading the data source again or open the workspace to inspect the workbook."}
              </p>
            </div>
          )}
        </div>

        <p className="mt-2 text-[11px] text-slate-500">
          {activeSheetName || (locale === "vi" ? "Sheet" : "Sheet")} • {locale === "vi" ? "xem trước dữ liệu" : "data preview"}
        </p>
      </div>

      {/* BƯỚC 4: PHẠM VI PHÂN TÍCH */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs space-y-3.5">
        <div className="flex flex-col gap-1">
          <h3 className="flex items-center gap-2 text-sm font-bold text-slate-900">
            <Layers className="h-4 w-4 text-emerald-600" />
            <span>{locale === "vi" ? "Phạm vi phân tích" : "Analysis scope"}</span>
          </h3>
          <p className="text-xs text-slate-500">
            {sheetOptions.length <= 1
              ? locale === "vi"
                ? `Workbook này có 1 sheet · ${activeSheetName}`
                : `This workbook has 1 sheet · ${activeSheetName}`
              : locale === "vi"
              ? "Chọn một sheet, nhiều sheet, một vùng cụ thể hoặc toàn bộ workbook."
              : "Choose one sheet, multiple sheets, a range, or the whole workbook."}
          </p>
        </div>

        <div className="grid gap-2 sm:grid-cols-2">
          {[
            { id: "workbook" as const, label: locale === "vi" ? "Toàn bộ workbook" : "Whole workbook", detail: `${sheetOptions.length || 1} sheet` },
            { id: "sheet" as const, label: locale === "vi" ? "Sheet hiện tại" : "Current sheet", detail: activeSheetName },
            { id: "sheets" as const, label: locale === "vi" ? "Chọn nhiều sheet" : "Multiple sheets", detail: `${selectedAnalysisSheets.length || 0} selected` },
            { id: "range" as const, label: locale === "vi" ? "Sheet / vùng cụ thể" : "Sheet / range", detail: analysisRange || "A1:..." },
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onChangeAnalysisScopeMode(item.id)}
              className={`rounded-lg border p-3 text-left transition ${
                analysisScopeMode === item.id
                  ? "border-emerald-500 bg-emerald-50 text-emerald-950 ring-2 ring-emerald-500/15"
                  : "border-slate-200 bg-slate-50 text-slate-700 hover:border-emerald-300 hover:bg-white"
              }`}
            >
              <span className="block text-xs font-bold">{item.label}</span>
              <span className="mt-1 block truncate text-[11px] text-slate-500">{item.detail}</span>
            </button>
          ))}
        </div>

        {analysisScopeMode === "sheet" && sheetOptions.length > 1 && (
          <select
            value={activeSheetName}
            onChange={(e) => {
              onSelectSheet(e.target.value);
              onChangeSheetRange(e.target.value);
            }}
            className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-xs font-bold text-slate-800 outline-none focus:border-emerald-500 focus:bg-white focus:ring-2 focus:ring-emerald-100"
          >
            {sheetOptions.map((sheet) => (
              <option key={sheet.name} value={sheet.name}>
                {sheet.name} · {sheet.row_count || sheet.records_count || 0} dòng × {sheet.column_count || 0} cột
              </option>
            ))}
          </select>
        )}

        {analysisScopeMode === "sheets" && sheetOptions.length > 1 && (
          <div className="grid gap-2 sm:grid-cols-2">
            {sheetOptions.map((sheet) => {
              const checked = selectedAnalysisSheets.includes(sheet.name);
              return (
                <label key={sheet.name} className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-white">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => {
                      const next = e.target.checked
                        ? [...selectedAnalysisSheets, sheet.name]
                        : selectedAnalysisSheets.filter((name) => name !== sheet.name);
                      onChangeSelectedAnalysisSheets(next);
                    }}
                    className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span className="min-w-0 truncate">{sheet.name}</span>
                </label>
              );
            })}
          </div>
        )}

        {analysisScopeMode === "range" && (
          <div className="grid gap-3 sm:grid-cols-[220px_minmax(0,1fr)]">
            <select
              value={activeSheetName}
              onChange={(e) => onSelectSheet(e.target.value)}
              className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-xs font-bold text-slate-800 outline-none focus:border-emerald-500 focus:bg-white focus:ring-2 focus:ring-emerald-100"
            >
              {sheetOptions.map((sheet) => (
                <option key={sheet.name} value={sheet.name}>{sheet.name}</option>
              ))}
            </select>
            <input
              type="text"
              value={analysisRange}
              onChange={(e) => onChangeAnalysisRange(e.target.value)}
              placeholder={locale === "vi" ? "Để trống = toàn bộ used range, ví dụ A1:Q300" : "Blank = used range, e.g. A1:Q300"}
              className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-xs font-semibold text-slate-800 outline-none focus:border-emerald-500 focus:bg-white focus:ring-2 focus:ring-emerald-100"
            />
          </div>
        )}

        {/* BƯỚC 5: NÚT TIẾP THEO CHUYỂN SANG MÀN PHÂN TÍCH */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3.5 pt-4 border-t border-slate-200">
          <div>
            <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>{locale === "vi" ? "Dữ liệu đã sẵn sàng để phân tích" : "Dataset ready for analysis"}</span>
            </h4>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {locale === "vi"
                ? "Bấm Tiếp theo để mở màn phân tích trực tiếp, bôi màu số liệu, xem KPI và trò chuyện cùng AI."
                : "Click Next to open the interactive analysis workspace with cell highlights and AI insights."}
            </p>
          </div>

          <button
            type="button"
            onClick={onOpenWorkspace}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-xs font-extrabold text-white shadow-md hover:bg-emerald-700 active:scale-95 transition shrink-0 group"
          >
            <span>{locale === "vi" ? "Tiếp theo: Mở màn phân tích →" : "Next: Open Analysis Workspace →"}</span>
            <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
}
