"use client";

import React, { useState, useMemo, useRef, useEffect } from "react";
import {
  FileSpreadsheet,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Grid,
  ChevronLeft,
  ChevronRight,
  Eye,
  Info,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
} from "lucide-react";

export interface CellBorderSide {
  style?: string;
  color?: string;
}

export interface CellBorder {
  top?: CellBorderSide;
  bottom?: CellBorderSide;
  left?: CellBorderSide;
  right?: CellBorderSide;
}

export interface CellFont {
  name?: string;
  size?: number;
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  color?: string;
}

export interface CellFill {
  type?: string;
  color?: string;
}

export interface CellAlignment {
  horizontal?: string;
  vertical?: string;
  wrap_text?: boolean;
  text_rotation?: number;
}

export interface VisualCell {
  row: number;
  col: number;
  coordinate: string;
  value: any;
  display_value: string;
  formula?: string | null;
  number_format?: string;
  font?: CellFont | null;
  fill?: CellFill | null;
  border?: CellBorder | null;
  alignment?: CellAlignment | null;
  is_merged?: boolean;
  is_merged_slave?: boolean;
  row_span?: number;
  col_span?: number;
  merged_range?: string | null;
}

export interface VisualSheet {
  name: string;
  max_row: number;
  max_column: number;
  merged_cells?: Array<{
    range: string;
    start_row: number;
    start_col: number;
    end_row: number;
    end_col: number;
    row_span: number;
    col_span: number;
  }>;
  column_widths?: Record<string, number>;
  row_heights?: Record<string, number>;
  cells: VisualCell[][];
}

export interface VisualWorkbook {
  source_type?: string;
  file_name?: string;
  sheet_count?: number;
  active_sheet_index?: number;
  sheets: VisualSheet[];
}

export interface CellHighlightInfo {
  color?: string;
  reason?: string;
  label?: string;
  queryPrompt?: string;
  colorName?: string;
  layerId?: string;
}

interface SpreadsheetPreviewProps {
  workbook?: VisualWorkbook | null;
  legacyData?: {
    columns?: Array<{ name: string; type?: string }>;
    preview_rows?: Array<Record<string, any>>;
    sheets?: Array<{
      name: string;
      row_count?: number;
      column_count?: number;
      columns?: Array<{ name: string; type?: string }>;
      records?: Array<Record<string, any>>;
    }>;
    total_rows?: number;
    total_columns?: number;
  } | null;
  height?: string | number;
  className?: string;
  locale?: string;
  cellHighlights?: Record<string, CellHighlightInfo>;
  activeCell?: string | null;
  selectedRange?: string | null;
  onCellClick?: (cell: { address: string; row: number; col: number; value: any }) => void;
  onRangeSelect?: (rangeStr: string) => void;
  scrollToCellAddress?: string | null;
  activeSheetName?: string | null;
  onActiveSheetChange?: (sheetName: string) => void;
  sheetTabsAction?: React.ReactNode;
  allSheetsActive?: boolean;
}

function getColumnLetter(colIndex: number): string {
  let temp = colIndex;
  let letter = "";
  while (temp > 0) {
    const mod = (temp - 1) % 26;
    letter = String.fromCharCode(65 + mod) + letter;
    temp = Math.floor((temp - mod) / 26);
  }
  return letter || "A";
}

export default function SpreadsheetPreview({
  workbook,
  legacyData,
  height = "100%",
  className = "",
  locale = "vi",
  cellHighlights = {},
  activeCell = null,
  selectedRange = null,
  onCellClick,
  onRangeSelect,
  scrollToCellAddress = null,
  activeSheetName = null,
  onActiveSheetChange,
  sheetTabsAction,
  allSheetsActive = false,
}: SpreadsheetPreviewProps) {
  const [activeSheetIndex, setActiveSheetIndex] = useState(workbook?.active_sheet_index ?? 0);
  const [zoom, setZoom] = useState(100);
  const [showGridlines, setShowGridlines] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentSelectionStart, setCurrentSelectionStart] = useState<{ row: number; col: number; addr: string } | null>(null);
  const [internalSelectedRange, setInternalSelectedRange] = useState<string | null>(selectedRange);
  const [gridSearchFilter, setGridSearchFilter] = useState("");
  const [sortColumnIndex, setSortColumnIndex] = useState<number | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc" | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);

  const handleToggleSort = (colIdx: number) => {
    if (sortColumnIndex !== colIdx) {
      setSortColumnIndex(colIdx);
      setSortDirection("asc");
    } else if (sortDirection === "asc") {
      setSortDirection("desc");
    } else {
      setSortColumnIndex(null);
      setSortDirection(null);
    }
  };

  // Sync external active sheet index from workbook
  useEffect(() => {
    if (workbook?.active_sheet_index !== undefined && workbook.active_sheet_index !== activeSheetIndex) {
      setActiveSheetIndex(workbook.active_sheet_index);
    }
  }, [workbook?.active_sheet_index]);

  // Sync external selectedRange
  useEffect(() => {
    if (selectedRange !== undefined) {
      setInternalSelectedRange(selectedRange);
    }
  }, [selectedRange]);

  // Reset scroll position on sheet switch
  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTo({ top: 0, left: 0, behavior: "instant" as any });
    }
  }, [activeSheetIndex]);

  // Handle scrollToCellAddress inside internal viewport
  useEffect(() => {
    const targetAddr = scrollToCellAddress || activeCell;
    if (!targetAddr) return;

    const timer = setTimeout(() => {
      const el = document.getElementById(`cell-node-${targetAddr}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
        el.classList.add("animate-pulse");
        setTimeout(() => el.classList.remove("animate-pulse"), 2000);
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [scrollToCellAddress, activeCell]);

  // Normalize data: convert legacy data to VisualWorkbook if workbook is missing
  const normalizedWorkbook: VisualWorkbook = useMemo(() => {
    if (workbook && workbook.sheets && workbook.sheets.length > 0) {
      return workbook;
    }

    if (legacyData) {
      const sheetsList: VisualSheet[] = [];
      const rawSheets = legacyData.sheets && legacyData.sheets.length > 0
        ? legacyData.sheets
        : [{
            name: "Sheet1",
            columns: legacyData.columns || [],
            records: legacyData.preview_rows || [],
            row_count: legacyData.total_rows,
            column_count: legacyData.total_columns,
          }];

      for (const s of rawSheets) {
        const cols = (s.columns || []).map((c: any) => (typeof c === "string" ? c : c.name || ""));
        const records = s.records || [];
        const maxR = records.length + 1;
        const maxC = Math.max(cols.length, 1);

        const colWidths: Record<string, number> = {};
        for (let c = 1; c <= maxC; c++) {
          const colName = cols[c - 1] || `Column ${c}`;
          let maxLen = colName.length;
          for (let r = 0; r < Math.min(records.length, 30); r++) {
            const rowVal = records[r]?.[colName];
            if (rowVal !== null && rowVal !== undefined) {
              const strVal = String(rowVal).trim();
              for (const line of strVal.split("\n")) {
                maxLen = Math.max(maxLen, line.length);
              }
            }
          }
          colWidths[String(c)] = Math.max(Math.min(Math.round(maxLen * 8.5 + 28), 340), 90);
        }

        const rowHeights: Record<string, number> = {};
        for (let r = 1; r <= maxR; r++) {
          rowHeights[String(r)] = r === 1 ? 28 : 24;
        }

        const cellsMatrix: VisualCell[][] = [];

        // Row 1: Headers
        const headerRow: VisualCell[] = [];
        for (let c = 1; c <= maxC; c++) {
          const colName = cols[c - 1] || `Column ${c}`;
          headerRow.push({
            row: 1,
            col: c,
            coordinate: `${getColumnLetter(c)}1`,
            value: colName,
            display_value: colName,
            font: { name: "Arial", size: 11, bold: true, color: "#1E293B" },
            fill: { type: "solid", color: "#F1F5F9" },
            border: {
              top: { style: "thin", color: "#CBD5E1" },
              bottom: { style: "medium", color: "#94A3B8" },
              left: { style: "thin", color: "#CBD5E1" },
              right: { style: "thin", color: "#CBD5E1" },
            },
            alignment: { horizontal: "center", vertical: "center", wrap_text: false },
            is_merged: false,
            is_merged_slave: false,
            row_span: 1,
            col_span: 1,
          });
        }
        cellsMatrix.push(headerRow);

        // Data rows
        for (let r = 0; r < records.length; r++) {
          const record = records[r] || {};
          const rowCells: VisualCell[] = [];
          for (let c = 1; c <= maxC; c++) {
            const colName = cols[c - 1] || "";
            const val = record[colName];
            const valStr = val === null || val === undefined ? "" : String(val);
            rowCells.push({
              row: r + 2,
              col: c,
              coordinate: `${getColumnLetter(c)}${r + 2}`,
              value: val,
              display_value: valStr,
              font: { name: "Arial", size: 11, bold: false, color: "#334155" },
              fill: null,
              border: {
                top: { style: "thin", color: "#E2E8F0" },
                bottom: { style: "thin", color: "#E2E8F0" },
                left: { style: "thin", color: "#E2E8F0" },
                right: { style: "thin", color: "#E2E8F0" },
              },
              alignment: {
                horizontal: typeof val === "number" ? "right" : "left",
                vertical: "center",
                wrap_text: true,
              },
              is_merged: false,
              is_merged_slave: false,
              row_span: 1,
              col_span: 1,
            });
          }
          cellsMatrix.push(rowCells);
        }

        sheetsList.push({
          name: s.name || "Sheet1",
          max_row: maxR,
          max_column: maxC,
          column_widths: colWidths,
          row_heights: rowHeights,
          cells: cellsMatrix,
        });
      }

      return {
        source_type: "excel",
        sheet_count: sheetsList.length,
        active_sheet_index: 0,
        sheets: sheetsList,
      };
    }

    return {
      sheets: [],
    };
  }, [workbook, legacyData]);

  const currentSheet: VisualSheet | undefined = useMemo(() => {
    if (!normalizedWorkbook?.sheets || normalizedWorkbook.sheets.length === 0) return undefined;
    if (activeSheetName) {
      const matched = normalizedWorkbook.sheets.find(
        (sheet) => sheet.name?.toLowerCase().trim() === activeSheetName.toLowerCase().trim()
      );
      if (matched) return matched;
    }
    return normalizedWorkbook.sheets[activeSheetIndex] || normalizedWorkbook.sheets[0];
  }, [normalizedWorkbook.sheets, activeSheetIndex, activeSheetName]);

  useEffect(() => {
    if (!activeSheetName || !normalizedWorkbook.sheets.length) return;
    const idx = normalizedWorkbook.sheets.findIndex(
      (sheet) => sheet.name?.toLowerCase().trim() === activeSheetName.toLowerCase().trim()
    );
    if (idx >= 0 && idx !== activeSheetIndex) {
      setActiveSheetIndex(idx);
    }
  }, [activeSheetName, normalizedWorkbook.sheets, activeSheetIndex]);

  const handleZoom = (delta: number) => {
    setZoom((prev) => Math.min(Math.max(prev + delta, 50), 200));
  };

  const getBorderWidth = (style?: string): string => {
    switch (style) {
      case "medium":
        return "2px";
      case "thick":
        return "3px";
      case "double":
        return "3px";
      case "dashed":
      case "dotted":
        return "1px";
      default:
        return "1px";
    }
  };

  if (!currentSheet || !currentSheet.cells || currentSheet.cells.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-slate-500">
        <FileSpreadsheet className="h-10 w-10 text-slate-400 mb-2 stroke-[1.5]" />
        <p className="text-sm font-medium">
          {locale === "vi" ? "Chưa có dữ liệu xem trước bảng tính." : "No spreadsheet preview available."}
        </p>
      </div>
    );
  }

  const maxCols = currentSheet.max_column || currentSheet.cells[0]?.length || 1;
  const maxRows = currentSheet.max_row || currentSheet.cells.length || 1;

  // Exact sum of column widths in pixels
  const totalSheetWidth = useMemo(() => {
    let sum = 46; // Row numbers sticky column
    for (let c = 1; c <= maxCols; c++) {
      const w = currentSheet.column_widths?.[String(c)] || 90;
      sum += Math.max(w, 45);
    }
    return sum;
  }, [currentSheet, maxCols]);

  const processedRows = useMemo(() => {
    if (!currentSheet?.cells || currentSheet.cells.length === 0) return [];
    const headerRow = currentSheet.cells[0] || [];
    let dataRows = currentSheet.cells.slice(1);

    if (gridSearchFilter.trim()) {
      const q = gridSearchFilter.toLowerCase().trim();
      dataRows = dataRows.filter((row) =>
        row.some((c) => String(c.display_value || c.value || "").toLowerCase().includes(q))
      );
    }

    if (sortColumnIndex !== null && sortDirection) {
      dataRows = [...dataRows].sort((a, b) => {
        const cellA = a.find((c) => c.col === sortColumnIndex);
        const cellB = b.find((c) => c.col === sortColumnIndex);
        const valA = cellA?.value ?? cellA?.display_value ?? "";
        const valB = cellB?.value ?? cellB?.display_value ?? "";

        const numA = typeof valA === "number" ? valA : parseFloat(String(valA).replace(/,/g, ""));
        const numB = typeof valB === "number" ? valB : parseFloat(String(valB).replace(/,/g, ""));

        if (!isNaN(numA) && !isNaN(numB)) {
          return sortDirection === "asc" ? numA - numB : numB - numA;
        }
        return sortDirection === "asc"
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
    }

    return [headerRow, ...dataRows];
  }, [currentSheet?.cells, gridSearchFilter, sortColumnIndex, sortDirection]);

  return (
    <div
      ref={containerRef}
      className={`flex flex-col rounded-xl border border-slate-300 bg-white shadow-sm font-sans h-full min-h-0 min-w-0 overflow-hidden ${
        isFullscreen ? "fixed inset-4 z-50 shadow-2xl !h-[calc(100vh-32px)]" : ""
      } ${className}`}
      style={{
        height: isFullscreen ? "calc(100vh - 32px)" : typeof height === "number" ? `${height}px` : height,
        maxWidth: "100%",
        contain: "inline-size",
      }}
    >
      {/* 1. Spreadsheet Header Bar & Toolbar (Fixed at top, not scrolled) */}
      <div className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-slate-100/90 px-3 py-2 text-xs">
        <div className="flex items-center gap-2 text-slate-700 font-semibold">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-emerald-600 text-white font-bold shadow-sm">
            <FileSpreadsheet className="h-3.5 w-3.5" />
          </div>
          <span className="truncate max-w-[180px]" title={currentSheet.name}>
            {currentSheet.name}
          </span>
          <span className="rounded bg-slate-200/80 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
            {maxRows.toLocaleString()} {locale === "vi" ? "dòng" : "rows"} × {maxCols} {locale === "vi" ? "cột" : "cols"}
          </span>
          {internalSelectedRange && (
            <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-bold text-blue-800 ring-1 ring-blue-300">
              {locale === "vi" ? "Vùng chọn:" : "Selection:"} {internalSelectedRange}
            </span>
          )}
          {Object.keys(cellHighlights).length > 0 && (
            <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-[10px] font-bold text-yellow-800 ring-1 ring-yellow-300">
              ✨ {Object.keys(cellHighlights).length} {locale === "vi" ? "ô đánh dấu" : "highlighted"}
            </span>
          )}
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-1.5">
          {/* Quick Search Filter */}
          <div className="relative flex items-center">
            <Search className="pointer-events-none absolute left-2 top-1.5 h-3 w-3 text-slate-400" />
            <input
              type="text"
              value={gridSearchFilter}
              onChange={(e) => setGridSearchFilter(e.target.value)}
              placeholder={locale === "vi" ? "Lọc nhanh dòng..." : "Filter rows..."}
              className="h-6 w-28 sm:w-36 rounded-md border border-slate-300 bg-white pl-6 pr-5 text-[11px] font-medium text-slate-700 placeholder:text-slate-400 focus:border-emerald-500 focus:w-48 transition-all"
            />
            {gridSearchFilter && (
              <button
                type="button"
                onClick={() => setGridSearchFilter("")}
                className="absolute right-1.5 top-1 text-[10px] text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            )}
          </div>
          {gridSearchFilter && (
            <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 ring-1 ring-emerald-200 shrink-0">
              {processedRows.length - 1}/{currentSheet.cells.length - 1} {locale === "vi" ? "dòng" : "rows"}
            </span>
          )}

          <div className="mx-1 h-3.5 w-[1px] bg-slate-300" />

          <button
            type="button"
            onClick={() => handleZoom(-10)}
            className="rounded p-1 text-slate-600 hover:bg-slate-200/70 active:scale-95"
            title={locale === "vi" ? "Thu nhỏ" : "Zoom out"}
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <span className="w-10 text-center font-mono text-[11px] font-semibold text-slate-700 select-none">
            {zoom}%
          </span>
          <button
            type="button"
            onClick={() => handleZoom(10)}
            className="rounded p-1 text-slate-600 hover:bg-slate-200/70 active:scale-95"
            title={locale === "vi" ? "Phóng to" : "Zoom in"}
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>

          <div className="mx-1 h-3.5 w-[1px] bg-slate-300" />

          <button
            type="button"
            onClick={() => setShowGridlines((v) => !v)}
            className={`flex items-center gap-1 rounded px-1.5 py-1 text-[11px] font-medium transition-colors ${
              showGridlines ? "bg-slate-200 text-slate-800 font-semibold" : "text-slate-600 hover:bg-slate-200/60"
            }`}
            title={locale === "vi" ? "Bật/Tắt đường lưới" : "Toggle gridlines"}
          >
            <Grid className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{locale === "vi" ? "Lưới" : "Grid"}</span>
          </button>

          <button
            type="button"
            onClick={() => setIsFullscreen((v) => !v)}
            className="rounded p-1 text-slate-600 hover:bg-slate-200/70 active:scale-95 ml-1"
            title={isFullscreen ? (locale === "vi" ? "Thu nhỏ" : "Exit fullscreen") : (locale === "vi" ? "Toàn màn hình" : "Fullscreen")}
          >
            {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* 2. Main Spreadsheet Viewport with Horizontal & Vertical Scrolling (Internal bounded scroll) */}
      <div ref={viewportRef} className="relative flex-1 min-h-0 min-w-0 max-w-full overflow-auto bg-slate-100/40 select-text p-1">
        <div
          style={{
            transform: zoom !== 100 ? `scale(${zoom / 100})` : undefined,
            transformOrigin: "top left",
            width: `${totalSheetWidth * zoom / 100}px`,
          }}
        >
          <table
            className="border-separate border-spacing-0 bg-white shadow-xs"
            style={{
              fontFamily: 'Calibri, Arial, "Noto Sans", sans-serif',
              tableLayout: "fixed",
              width: `${totalSheetWidth}px`,
              minWidth: `${totalSheetWidth}px`,
            }}
          >
            {/* Column Width Sizers */}
            <colgroup>
              {/* Header Row Numbers Column */}
              <col style={{ width: "46px", minWidth: "46px" }} />
              {Array.from({ length: maxCols }).map((_, colIdx) => {
                const cNum = colIdx + 1;
                const widthPx = currentSheet.column_widths?.[String(cNum)] || 90;
                const minPx = Math.max(widthPx, 45);
                return (
                  <col
                    key={`col-def-${cNum}`}
                    style={{
                      width: `${minPx}px`,
                      minWidth: `${minPx}px`,
                    }}
                  />
                );
              })}
            </colgroup>

            {/* Column Alphabet Headers: A, B, C, D... with sorting */}
            <thead>
              <tr className="sticky top-0 z-20 bg-slate-200 text-slate-600 font-semibold text-[11px]">
                {/* Top-Left Corner Cell */}
                <th className="sticky left-0 top-0 z-30 w-[46px] border-b border-r border-slate-300 bg-slate-200 p-0 text-center font-normal text-slate-400">
                  <div className="flex h-6 items-center justify-center">
                    <span className="text-[9px]">◢</span>
                  </div>
                </th>
                {Array.from({ length: maxCols }).map((_, colIdx) => {
                  const cNum = colIdx + 1;
                  const letter = getColumnLetter(cNum);
                  const isSorted = sortColumnIndex === cNum;
                  return (
                    <th
                      key={`col-hdr-${letter}`}
                      onClick={() => handleToggleSort(cNum)}
                      className={`border-b border-r border-slate-300 px-1 py-1 text-center font-semibold select-none cursor-pointer transition hover:bg-slate-300 ${
                        isSorted ? "bg-indigo-100 text-indigo-900 font-bold" : "bg-slate-200 text-slate-700"
                      }`}
                      style={{ height: "24px" }}
                      title={locale === "vi" ? `Bấm để sắp xếp cột ${letter}` : `Click to sort column ${letter}`}
                    >
                      <div className="inline-flex items-center justify-center gap-0.5">
                        <span>{letter}</span>
                        {isSorted ? (
                          sortDirection === "asc" ? <ArrowUp className="h-2.5 w-2.5 text-indigo-600" /> : <ArrowDown className="h-2.5 w-2.5 text-indigo-600" />
                        ) : null}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>

            {/* Spreadsheet Body */}
            <tbody>
              {processedRows.map((rowCells, rIdx) => {
                const rowNum = rowCells[0]?.row || rIdx + 1;
                const rowHeightPx = currentSheet.row_heights?.[String(rowNum)] || 24;

                return (
                  <tr
                    key={`row-${rowNum}`}
                    style={{
                      height: `${rowHeightPx}px`,
                      minHeight: `${rowHeightPx}px`,
                    }}
                  >
                    {/* Sticky Row Number: 1, 2, 3... */}
                    <td className="sticky left-0 z-10 w-[46px] border-b border-r border-slate-300 bg-slate-200 px-1 text-center font-mono text-[10px] font-semibold text-slate-600 select-none">
                      {rowNum}
                    </td>

                    {/* Cell Items */}
                    {rowCells.map((cell, cIdx) => {
                      // If cell is part of merged range and NOT the top-left master, skip rendering <td>
                      if (cell.is_merged_slave) {
                        return null;
                      }

                      const coordUpper = cell.coordinate ? cell.coordinate.toUpperCase().trim() : "";
                      const highlight = cellHighlights && coordUpper ? (cellHighlights[coordUpper] || cellHighlights[cell.coordinate]) : null;
                      const isFocused = activeCell === cell.coordinate;

                      const hasFill = cell.fill && cell.fill.color;
                      const originalBg = hasFill ? cell.fill!.color : "transparent";
                      const isOriginalYellow = hasFill && isYellowishColor(originalBg);
                      const requestedHighlightColor = highlight ? (highlight.color || "#FEF08A") : null;
                      // Smart contrast: if original cell is already yellow, use distinct bright orange/coral
                      const effectiveBg = highlight
                        ? (isOriginalYellow && isYellowishColor(requestedHighlightColor) ? "#FED7AA" : (requestedHighlightColor || "#FEF08A"))
                        : originalBg;

                      const font = cell.font || {};
                      const highlightFontColor = isOriginalYellow && isYellowishColor(requestedHighlightColor) ? "#7C2D12" : "#713F12";
                      const fontColor = highlight
                        ? highlightFontColor
                        : (font.color || (hasFill && isDarkColor(originalBg) ? "#FFFFFF" : "#0F172A"));
                      const fontWeight = highlight ? "700" : (font.bold ? "700" : "400");
                      const fontStyle = font.italic ? "italic" : "normal";
                      const textDecoration = font.underline ? "underline" : "none";
                      const fontSize = font.size ? `${Math.max(font.size, 10)}px` : "12px";

                      const align = cell.alignment || {};
                      const textAlign = align.horizontal
                        ? align.horizontal === "general"
                          ? isNumeric(cell.display_value) ? "right" : "left"
                          : (align.horizontal as any)
                        : isNumeric(cell.display_value)
                        ? "right"
                        : "left";
                      const verticalAlign = align.vertical ? (align.vertical as any) : "middle";
                      const isWrap = Boolean(align.wrap_text || cell.display_value?.includes("\n"));
                      const colWidth = Math.max(currentSheet.column_widths?.[String(cell.col)] || 90, 45);

                      // Borders
                      const border = cell.border || {};
                      const topBorder = border.top
                        ? `${getBorderWidth(border.top.style)} ${border.top.style || "solid"} ${border.top.color || "#000000"}`
                        : showGridlines ? "1px solid #E2E8F0" : "none";
                      const bottomBorder = border.bottom
                        ? `${getBorderWidth(border.bottom.style)} ${border.bottom.style || "solid"} ${border.bottom.color || "#000000"}`
                        : showGridlines ? "1px solid #E2E8F0" : "none";
                      const leftBorder = border.left
                        ? `${getBorderWidth(border.left.style)} ${border.left.style || "solid"} ${border.left.color || "#000000"}`
                        : showGridlines ? "1px solid #E2E8F0" : "none";
                      const rightBorder = border.right
                        ? `${getBorderWidth(border.right.style)} ${border.right.style || "solid"} ${border.right.color || "#000000"}`
                        : showGridlines ? "1px solid #E2E8F0" : "none";

                      const handleCellClickInternal = (e: React.MouseEvent) => {
                        if (!cell.coordinate) return;
                        onCellClick?.({
                          address: cell.coordinate,
                          row: cell.row,
                          col: cell.col,
                          value: cell.value,
                        });

                        if (e.shiftKey && currentSelectionStart) {
                          // Define range from currentSelectionStart to this cell
                          const minR = Math.min(currentSelectionStart.row, cell.row);
                          const maxR = Math.max(currentSelectionStart.row, cell.row);
                          const minC = Math.min(currentSelectionStart.col, cell.col);
                          const maxC = Math.max(currentSelectionStart.col, cell.col);
                          const rangeBox = `${getColumnLetter(minC)}${minR}:${getColumnLetter(maxC)}${maxR}`;
                          setInternalSelectedRange(rangeBox);
                          onRangeSelect?.(rangeBox);
                        } else {
                          setCurrentSelectionStart({ row: cell.row, col: cell.col, addr: cell.coordinate });
                          setInternalSelectedRange(cell.coordinate);
                          onRangeSelect?.(cell.coordinate);
                        }
                      };

                      return (
                        <td
                          id={cell.coordinate ? `cell-node-${cell.coordinate}` : undefined}
                          key={cell.coordinate || `cell-${rIdx}-${cIdx}`}
                          rowSpan={cell.row_span && cell.row_span > 1 ? cell.row_span : undefined}
                          colSpan={cell.col_span && cell.col_span > 1 ? cell.col_span : undefined}
                          onClick={handleCellClickInternal}
                          className={`cursor-pointer transition-all duration-150 ${
                            isFocused ? "ring-2 ring-blue-500 z-10" : ""
                          }`}
                          style={{
                            width: cell.col_span && cell.col_span > 1 ? undefined : `${colWidth}px`,
                            maxWidth: cell.col_span && cell.col_span > 1 ? undefined : `${colWidth}px`,
                            backgroundColor: effectiveBg,
                            color: fontColor,
                            fontWeight,
                            fontStyle,
                            textDecoration,
                            fontSize,
                            textAlign,
                            verticalAlign,
                            whiteSpace: isWrap ? "normal" : "nowrap",
                            wordBreak: "normal",
                            overflowWrap: "normal",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            borderTop: topBorder,
                            borderBottom: bottomBorder,
                            borderLeft: leftBorder,
                            borderRight: rightBorder,
                            padding: "3px 6px",
                            lineHeight: "1.35",
                            boxShadow: isFocused
                              ? "inset 0 0 0 2px #2563EB"
                              : highlight
                              ? `inset 0 0 0 2px ${isOriginalYellow ? "#EA580C" : "#CA8A04"}, 0 1px 2px rgba(0,0,0,0.12)`
                              : undefined,
                          }}
                          title={
                            cell.coordinate
                              ? `${cell.coordinate}: ${cell.display_value || "(trống)"}${
                                  highlight
                                    ? `\n🎨 ${highlight.colorName ? `[Màu ${highlight.colorName}] ` : ""}${
                                        highlight.queryPrompt ? `Thuộc câu hỏi: "${highlight.queryPrompt}"` : ""
                                      }${highlight.reason ? ` (${highlight.reason})` : ""}`
                                    : ""
                                }`
                              : undefined
                          }
                        >
                          <div className="flex items-center justify-between gap-1 w-full overflow-hidden">
                            <span className="truncate">{cell.display_value}</span>
                            {highlight && (
                              <span
                                className="inline-block h-1.5 w-1.5 rounded-full ring-1 ring-white/90 shrink-0"
                                style={{ backgroundColor: isOriginalYellow ? "#EA580C" : "#CA8A04" }}
                                title={highlight.reason || "AI Highlight"}
                              />
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Excel-Style Bottom Sheet Tabs */}
      {normalizedWorkbook.sheets.length > 0 && (
        <div className="flex shrink-0 items-center justify-between border-t border-slate-200 bg-slate-100 px-2 py-1.5 text-xs">
          <div className="flex items-center gap-1 overflow-x-auto py-0.5 no-scrollbar max-w-[80%]">
            {normalizedWorkbook.sheets.map((sheet, sIdx) => {
              const isActive = sIdx === activeSheetIndex;
              const isVisuallyActive = allSheetsActive || isActive;
              return (
                <button
                  key={`sheet-tab-${sheet.name}-${sIdx}`}
                  type="button"
                  onClick={() => {
                    setActiveSheetIndex(sIdx);
                    onActiveSheetChange?.(sheet.name);
                  }}
                  className={`flex items-center gap-1.5 whitespace-nowrap rounded-t-md px-3 py-1.5 font-semibold text-xs transition-all ${
                    isVisuallyActive
                      ? "border-t-2 border-emerald-600 bg-white text-emerald-800 shadow-sm ring-1 ring-slate-200"
                      : "text-slate-600 hover:bg-slate-200/80 hover:text-slate-800"
                  }`}
                >
                  <FileSpreadsheet className={`h-3.5 w-3.5 ${isVisuallyActive ? "text-emerald-600" : "text-slate-400"}`} />
                  <span>{sheet.name}</span>
                  <span className={`text-[10px] font-normal ${isVisuallyActive ? "text-emerald-700/80" : "text-slate-400"}`}>
                    ({sheet.max_row || sheet.cells.length})
                  </span>
                </button>
              );
            })}
            {sheetTabsAction && <div className="ml-1 shrink-0">{sheetTabsAction}</div>}
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-500 shrink-0 font-medium">
            <span>
              {locale === "vi" ? "Trang tính" : "Sheet"} {activeSheetIndex + 1} / {normalizedWorkbook.sheets.length}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function isNumeric(val: any): boolean {
  if (val === null || val === undefined || val === "") return false;
  if (typeof val === "number") return true;
  const str = String(val).trim().replace(/,/g, "").replace(/\./g, "");
  return !isNaN(Number(str)) && str.length > 0;
}

function isDarkColor(hexColor?: string | null): boolean {
  if (!hexColor || !hexColor.startsWith("#")) return false;
  const hex = hexColor.replace("#", "");
  if (hex.length !== 6) return false;
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance < 0.5;
}

function isYellowishColor(color?: string | null): boolean {
  if (!color || color === "transparent") return false;
  const c = color.trim().toLowerCase();
  if (
    c.includes("yellow") ||
    c === "#ffff00" ||
    c === "#ffeb3b" ||
    c === "#fde047" ||
    c === "#facc15" ||
    c === "#fef08a" ||
    c === "#fff59d"
  ) {
    return true;
  }
  if (c.startsWith("#") && (c.length === 7 || c.length === 4)) {
    let r = 0, g = 0, b = 0;
    if (c.length === 7) {
      r = parseInt(c.substring(1, 3), 16) || 0;
      g = parseInt(c.substring(3, 5), 16) || 0;
      b = parseInt(c.substring(5, 7), 16) || 0;
    } else {
      r = parseInt(c[1] + c[1], 16) || 0;
      g = parseInt(c[2] + c[2], 16) || 0;
      b = parseInt(c[3] + c[3], 16) || 0;
    }
    if (r > 190 && g > 180 && b < 160) return true;
  }
  return false;
}
