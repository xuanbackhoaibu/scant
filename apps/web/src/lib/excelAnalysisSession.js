export const EXCEL_ANALYSIS_SESSION_PREFIX = "ai_report_studio:excel_analysis_session";

export function buildExcelAnalysisSessionKey({ fileName, fileId, dataSourceUrl }) {
  const sourceId = fileId || dataSourceUrl || fileName || "unknown";
  return `${EXCEL_ANALYSIS_SESSION_PREFIX}:${encodeURIComponent(String(sourceId))}`;
}

export function createExcelAnalysisSnapshot({
  activeSheetName,
  analysisPrompt,
  activeHighlightColor,
  analysisActionStatus,
  chatScopeMode,
  analysisHistory,
  analysisBySheet,
  analysisLayersBySheet,
  lastAnalysisResultBySheet,
}) {
  return {
    version: 1,
    savedAt: new Date().toISOString(),
    activeSheetName: activeSheetName || "",
    analysisPrompt: analysisPrompt || "",
    activeHighlightColor: activeHighlightColor || "#FEF08A",
    analysisActionStatus: analysisActionStatus || null,
    chatScopeMode: chatScopeMode === "workbook" ? "workbook" : "sheet",
    analysisHistory: Array.isArray(analysisHistory) ? analysisHistory.slice(0, 8) : [],
    analysisBySheet: analysisBySheet || {},
    analysisLayersBySheet: analysisLayersBySheet || {},
    lastAnalysisResultBySheet: lastAnalysisResultBySheet || {},
  };
}

export function parseExcelAnalysisSnapshot(raw) {
  if (!raw) return null;
  try {
    const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (!parsed || parsed.version !== 1) return null;
    return {
      activeSheetName: typeof parsed.activeSheetName === "string" ? parsed.activeSheetName : "",
      analysisPrompt: typeof parsed.analysisPrompt === "string" ? parsed.analysisPrompt : "",
      activeHighlightColor: typeof parsed.activeHighlightColor === "string" ? parsed.activeHighlightColor : "#FEF08A",
      analysisActionStatus: typeof parsed.analysisActionStatus === "string" ? parsed.analysisActionStatus : null,
      chatScopeMode: parsed.chatScopeMode === "workbook" ? "workbook" : "sheet",
      analysisHistory: Array.isArray(parsed.analysisHistory) ? parsed.analysisHistory : [],
      analysisBySheet: parsed.analysisBySheet && typeof parsed.analysisBySheet === "object" ? parsed.analysisBySheet : {},
      analysisLayersBySheet: parsed.analysisLayersBySheet && typeof parsed.analysisLayersBySheet === "object" ? parsed.analysisLayersBySheet : {},
      lastAnalysisResultBySheet: parsed.lastAnalysisResultBySheet && typeof parsed.lastAnalysisResultBySheet === "object" ? parsed.lastAnalysisResultBySheet : {},
    };
  } catch {
    return null;
  }
}
