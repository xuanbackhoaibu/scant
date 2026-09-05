/** @typedef {'direct-analysis' | 'docx-report' | null} AnalysisMode */
/** @returns {AnalysisMode} */
export function readAnalysisMode(params) {
  const mode = params.get('analysis');
  return mode === 'direct-analysis' || mode === 'docx-report' ? mode : null;
}
/** @param {string} query @param {AnalysisMode} mode */
export function analysisModeUrl(query, mode) {
  const params = new URLSearchParams(query);
  if (mode) params.set('analysis', mode);
  else params.delete('analysis');
  return `/projects/new?${params.toString()}`;
}
