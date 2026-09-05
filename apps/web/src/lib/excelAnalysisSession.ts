export const EXCEL_ANALYSIS_SESSION_PREFIX = "ai_report_studio:excel_analysis_session";

type ExcelAnalysisSessionKeyInput = {
  fileName?: string | null;
  fileId?: string | null;
  dataSourceUrl?: string | null;
};

type ExcelAnalysisSnapshotInput = {
  activeSheetName?: string;
  analysisPrompt?: string;
  activeHighlightColor?: string;
  analysisActionStatus?: string | null;
  chatScopeMode?: "sheet" | "sheets" | "workbook";
  selectedAnalysisSheets?: string[];
  analysisHistory?: unknown[];
  analysisBySheet?: Record<string, unknown>;
  analysisLayersBySheet?: Record<string, unknown>;
  lastAnalysisResultBySheet?: Record<string, unknown>;
};

export type ExcelAnalysisSnapshot = Required<ExcelAnalysisSnapshotInput> & {
  version?: number;
  savedAt?: string;
};

export function buildExcelAnalysisSessionKey({ fileName, fileId, dataSourceUrl }: ExcelAnalysisSessionKeyInput) {
  const sourceId = fileId || dataSourceUrl || fileName || "unknown";
  return `${EXCEL_ANALYSIS_SESSION_PREFIX}:${encodeURIComponent(String(sourceId))}`;
}

export function createExcelAnalysisSnapshot({
  activeSheetName,
  analysisPrompt,
  activeHighlightColor,
  analysisActionStatus,
  chatScopeMode,
  selectedAnalysisSheets,
  analysisHistory,
  analysisBySheet,
  analysisLayersBySheet,
  lastAnalysisResultBySheet,
}: ExcelAnalysisSnapshotInput): ExcelAnalysisSnapshot {
  return {
    version: 1,
    savedAt: new Date().toISOString(),
    activeSheetName: activeSheetName || "",
    analysisPrompt: analysisPrompt || "",
    activeHighlightColor: activeHighlightColor || "#FEF08A",
    analysisActionStatus: analysisActionStatus || null,
    chatScopeMode: chatScopeMode === "workbook" ? "workbook" : chatScopeMode === "sheets" ? "sheets" : "sheet",
    selectedAnalysisSheets: Array.isArray(selectedAnalysisSheets) ? selectedAnalysisSheets : [],
    analysisHistory: Array.isArray(analysisHistory) ? analysisHistory.slice(0, 8) : [],
    analysisBySheet: analysisBySheet || {},
    analysisLayersBySheet: analysisLayersBySheet || {},
    lastAnalysisResultBySheet: lastAnalysisResultBySheet || {},
  };
}

export function parseExcelAnalysisSnapshot(raw: unknown): ExcelAnalysisSnapshot | null {
  if (!raw) return null;
  try {
    const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (!parsed || typeof parsed !== "object" || (parsed as { version?: number }).version !== 1) return null;
    const snapshot = parsed as ExcelAnalysisSnapshotInput;
    return {
      activeSheetName: typeof snapshot.activeSheetName === "string" ? snapshot.activeSheetName : "",
      analysisPrompt: typeof snapshot.analysisPrompt === "string" ? snapshot.analysisPrompt : "",
      activeHighlightColor: typeof snapshot.activeHighlightColor === "string" ? snapshot.activeHighlightColor : "#FEF08A",
      analysisActionStatus: typeof snapshot.analysisActionStatus === "string" ? snapshot.analysisActionStatus : null,
      chatScopeMode: snapshot.chatScopeMode === "workbook" ? "workbook" : snapshot.chatScopeMode === "sheets" ? "sheets" : "sheet",
      selectedAnalysisSheets: Array.isArray(snapshot.selectedAnalysisSheets) ? snapshot.selectedAnalysisSheets.filter((name: unknown) => typeof name === "string") : [],
      analysisHistory: Array.isArray(snapshot.analysisHistory) ? snapshot.analysisHistory : [],
      analysisBySheet:
        snapshot.analysisBySheet && typeof snapshot.analysisBySheet === "object"
          ? snapshot.analysisBySheet
          : {},
      analysisLayersBySheet:
        snapshot.analysisLayersBySheet && typeof snapshot.analysisLayersBySheet === "object"
          ? snapshot.analysisLayersBySheet
          : {},
      lastAnalysisResultBySheet:
        snapshot.lastAnalysisResultBySheet && typeof snapshot.lastAnalysisResultBySheet === "object"
          ? snapshot.lastAnalysisResultBySheet
          : {},
    };
  } catch {
    return null;
  }
}
