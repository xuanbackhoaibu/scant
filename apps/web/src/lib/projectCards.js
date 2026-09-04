export function selectProjectPreviewReport(project, reports) {
  const projectReports = (reports || []).filter((report) => report?.project_id === project?.id);
  if (projectReports.length === 0) return null;

  return [...projectReports].sort((a, b) => {
    const aTime = new Date(a.updated_at || a.created_at || 0).getTime();
    const bTime = new Date(b.updated_at || b.created_at || 0).getTime();
    return bTime - aTime;
  })[0];
}
