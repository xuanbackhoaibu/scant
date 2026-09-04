"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FolderKanban,
  FileText,
  Clock,
  Plus,
  ArrowRight,
  ArrowLeft,
  BookOpen,
  Building,
  User,
  Layers,
  Search,
  ExternalLink,
  FileCheck2,
  ScrollText,
  RefreshCw,
  ShieldCheck,
  Wand2,
  AlertTriangle,
  Download,
  ListChecks,
  Bug,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const resolveDownloadUrl = (url?: string) => {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return `${api.exports.getDownloadUrl("").replace(/\/exports\/download\/$/, "")}${url}`;
};

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const router = useRouter();

  const [project, setProject] = useState<any>(null);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [templatePreviews, setTemplatePreviews] = useState<Record<string, any>>({});
  const [previewLoadingByReport, setPreviewLoadingByReport] = useState<Record<string, boolean>>({});
  const [qualityAudits, setQualityAudits] = useState<Record<string, any>>({});
  const [qualityLoadingByReport, setQualityLoadingByReport] = useState<Record<string, boolean>>({});
  const [repairingByReport, setRepairingByReport] = useState<Record<string, boolean>>({});
  const [repairingSectionById, setRepairingSectionById] = useState<Record<string, boolean>>({});
  const [exportingByReport, setExportingByReport] = useState<Record<string, boolean>>({});
  const [exportResults, setExportResults] = useState<Record<string, any>>({});
  const [groundingDebugByReport, setGroundingDebugByReport] = useState<Record<string, any>>({});
  const [groundingLoadingByReport, setGroundingLoadingByReport] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function loadData() {
      try {
        const [proj, reportList] = await Promise.all([
          api.projects.get(projectId),
          api.reports.list(),
        ]);
        setProject(proj);
        const projectReports = (reportList || []).filter((report: any) => report.project_id === projectId);
        const detailedReports = await Promise.all(
          projectReports.map(async (report: any) => {
            try {
              return await api.reports.get(report.id);
            } catch {
              return report;
            }
          })
        );
        setReports(detailedReports);
      } catch {
        setProject(null);
      } finally {
        setLoading(false);
        setReportsLoading(false);
      }
    }
    loadData();
  }, [projectId]);

  const loadTemplatePreview = async (reportId: string) => {
    setPreviewLoadingByReport((prev) => ({ ...prev, [reportId]: true }));
    try {
      const preview = await api.exports.previewReportHtml(reportId);
      setTemplatePreviews((prev) => ({ ...prev, [reportId]: preview }));
    } catch (err: any) {
      setTemplatePreviews((prev) => ({
        ...prev,
        [reportId]: { error: err?.message || "Không thể dựng bản xem theo mẫu." },
      }));
    } finally {
      setPreviewLoadingByReport((prev) => ({ ...prev, [reportId]: false }));
    }
  };

  const loadQualityAudit = async (reportId: string) => {
    setQualityLoadingByReport((prev) => ({ ...prev, [reportId]: true }));
    try {
      const audit = await api.reports.qualityAudit(reportId);
      setQualityAudits((prev) => ({ ...prev, [reportId]: audit }));
    } catch (err: any) {
      setQualityAudits((prev) => ({
        ...prev,
        [reportId]: { error: err?.message || "Không thể kiểm tra chất lượng báo cáo." },
      }));
    } finally {
      setQualityLoadingByReport((prev) => ({ ...prev, [reportId]: false }));
    }
  };

  const repairReport = async (reportId: string) => {
    setRepairingByReport((prev) => ({ ...prev, [reportId]: true }));
    try {
      const result = await api.reports.qualityRepair(reportId);
      setQualityAudits((prev) => ({ ...prev, [reportId]: result.after || result }));
      const refreshed = await api.reports.get(reportId);
      setReports((prev) => prev.map((report) => (report.id === reportId ? refreshed : report)));
      setTemplatePreviews((prev) => {
        const next = { ...prev };
        delete next[reportId];
        return next;
      });
      await loadTemplatePreview(reportId);
    } catch (err: any) {
      setQualityAudits((prev) => ({
        ...prev,
        [reportId]: { error: err?.message || "Không thể tự sửa báo cáo." },
      }));
    } finally {
      setRepairingByReport((prev) => ({ ...prev, [reportId]: false }));
    }
  };

  const repairSection = async (reportId: string, sectionId: string) => {
    setRepairingSectionById((prev) => ({ ...prev, [sectionId]: true }));
    try {
      const result = await api.reports.qualityRepairSection(reportId, sectionId);
      setQualityAudits((prev) => ({ ...prev, [reportId]: result.audit }));
      const refreshed = await api.reports.get(reportId);
      setReports((prev) => prev.map((report) => (report.id === reportId ? refreshed : report)));
      setTemplatePreviews((prev) => {
        const next = { ...prev };
        delete next[reportId];
        return next;
      });
      await loadTemplatePreview(reportId);
    } catch (err: any) {
      setQualityAudits((prev) => ({
        ...prev,
        [reportId]: { ...(prev[reportId] || {}), error: err?.message || "Không thể sửa mục này." },
      }));
    } finally {
      setRepairingSectionById((prev) => ({ ...prev, [sectionId]: false }));
    }
  };

  const exportDocx = async (reportId: string) => {
    setExportingByReport((prev) => ({ ...prev, [reportId]: true }));
    try {
      const result = await api.exports.exportDocx({
        report_id: reportId,
        export_format: "docx",
        include_cover: true,
        include_toc: true,
        include_references: true,
        citation_style: "IEEE",
      });
      setExportResults((prev) => ({ ...prev, [reportId]: result }));
      if (result.download_url) {
        window.open(resolveDownloadUrl(result.download_url), "_blank");
      }
    } catch (err: any) {
      setExportResults((prev) => ({
        ...prev,
        [reportId]: { error: err?.message || "Không thể xuất DOCX." },
      }));
    } finally {
      setExportingByReport((prev) => ({ ...prev, [reportId]: false }));
    }
  };

  const loadGroundingDebug = async (reportId: string) => {
    setGroundingLoadingByReport((prev) => ({ ...prev, [reportId]: true }));
    try {
      const result = await api.reports.groundingDebug(reportId);
      setGroundingDebugByReport((prev) => ({ ...prev, [reportId]: result }));
    } catch (err: any) {
      setGroundingDebugByReport((prev) => ({
        ...prev,
        [reportId]: { error: err?.message || "Không thể tải debug dữ liệu." },
      }));
    } finally {
      setGroundingLoadingByReport((prev) => ({ ...prev, [reportId]: false }));
    }
  };

  useEffect(() => {
    if (reports.length === 0) return;
    reports.forEach((report) => {
      if (!templatePreviews[report.id] && !previewLoadingByReport[report.id]) {
        loadTemplatePreview(report.id);
      }
      if (!qualityAudits[report.id] && !qualityLoadingByReport[report.id]) {
        loadQualityAudit(report.id);
      }
    });
  }, [reports]);

  if (loading) {
    return (
      <div className="mx-auto max-w-[1500px] space-y-4 px-4 py-8 sm:px-6 lg:px-8">
        <div className="h-28 animate-pulse rounded-xl border border-slate-200 bg-slate-100" />
        <div className="h-64 animate-pulse rounded-xl border border-slate-200 bg-slate-100" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-sm font-bold text-slate-800">Không tìm thấy dự án</h2>
        <Link href="/projects" className="text-xs text-indigo-600 hover:underline mt-2 inline-block">
          Quay lại danh sách
        </Link>
      </div>
    );
  }

  const meta = project.metadata_json || {};
  const customFields: any[] = meta.custom_fields || [];
  const totalWords = reports.reduce((sum, report) => sum + Number(report.total_words || 0), 0);
  const totalSections = reports.reduce((sum, report) => sum + (report.sections?.length || 0), 0);

  return (
    <div className="mx-auto max-w-[1500px] space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Project Overview Card */}
      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="flex items-start gap-3">
            <button
              type="button"
              onClick={() => router.push("/projects")}
              className="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
              title="Quay lại danh sách dự án"
              aria-label="Quay lại danh sách dự án"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-[11px] font-bold text-indigo-700 uppercase tracking-wider">
                  {project.type}
                </span>
                <span className="text-xs text-slate-400">Tạo ngày {formatDate(project.created_at)}</span>
              </div>
              <h1 className="text-xl font-bold text-slate-900">{project.name}</h1>
            </div>
          </div>

          <button
            onClick={() => router.push(`/projects/new?type=${project.type}`)}
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo báo cáo mới</span>
          </button>
        </div>

        {/* Dynamic Metadata Grid */}
        {customFields.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs bg-slate-50 p-4 rounded-xl border border-slate-100">
            {customFields.map((field, idx) => (
              <div key={idx}>
                <span className="text-slate-400 block font-medium">{field.label}:</span>
                <span className="font-semibold text-slate-800">{field.value || "—"} {field.unit || ""}</span>
              </div>
            ))}
          </div>
        )}

        <p className="text-xs text-slate-600 leading-relaxed">{project.description}</p>
      </div>

      {/* Reports */}
      <div className="space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-3 border-b border-slate-100 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Báo cáo trong dự án ({reports.length})</h2>
            <p className="mt-1 text-xs text-slate-500">
              {totalSections} mục · {totalWords.toLocaleString("vi-VN")} từ
            </p>
          </div>
          {reports[0] && (
            <button
              onClick={() => router.push(`/reports/${reports[0].id}/editor`)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-xs transition hover:bg-indigo-700"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span>Mở báo cáo trong Studio</span>
            </button>
          )}
        </div>

        {reportsLoading ? (
          <div className="space-y-3">
            <div className="h-28 rounded-xl border border-slate-200 bg-slate-100 animate-pulse" />
            <div className="h-48 rounded-xl border border-slate-200 bg-slate-100 animate-pulse" />
          </div>
        ) : reports.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
            <ScrollText className="mx-auto h-9 w-9 text-slate-400" />
            <h3 className="mt-3 text-sm font-bold text-slate-800">Chưa có báo cáo nào trong dự án này</h3>
            <p className="mt-1 text-xs text-slate-500">Bạn có thể tạo báo cáo mới từ đề tài và dữ liệu của dự án.</p>
          </div>
        ) : (
          <div className="space-y-5">
            {reports.map((report) => (
              <article key={report.id} className="rounded-xl border border-slate-200 bg-white">
                <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold uppercase text-emerald-700">
                        <FileCheck2 className="h-3 w-3" />
                        {report.status || "draft"}
                      </span>
                      <span className="text-[11px] font-semibold text-slate-400">
                        {report.sections?.length || 0} mục · {Number(report.total_words || 0).toLocaleString("vi-VN")} từ
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-slate-950">{report.title}</h3>
                    <p className="mt-1 text-xs text-slate-500">
                      Cập nhật {report.updated_at ? formatDate(report.updated_at) : "-"}
                    </p>
                    {exportResults[report.id]?.download_url && (
                      <a
                        href={resolveDownloadUrl(exportResults[report.id].download_url)}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-2 inline-flex items-center gap-1 text-[11px] font-bold text-indigo-600 hover:text-indigo-700"
                      >
                        <Download className="h-3 w-3" />
                        Tải file vừa xuất
                      </a>
                    )}
                    {exportResults[report.id]?.error && (
                      <p className="mt-2 text-[11px] font-semibold text-red-600">{exportResults[report.id].error}</p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => exportDocx(report.id)}
                      disabled={!!exportingByReport[report.id]}
                      className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-white px-3 py-2 text-xs font-bold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50 disabled:opacity-60"
                    >
                      <Download className={`h-3.5 w-3.5 ${exportingByReport[report.id] ? "animate-pulse" : ""}`} />
                      <span>{exportingByReport[report.id] ? "Đang xuất" : "Xuất DOCX"}</span>
                    </button>
                    <button
                      onClick={() => router.push(`/reports/${report.id}/editor`)}
                      className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-200"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      <span>Mở Studio</span>
                    </button>
                  </div>
                </div>

                <div className="p-4">
                  <div className="mb-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-900">
                            <ShieldCheck className="h-4 w-4 text-indigo-600" />
                            Kiểm định chất lượng
                          </span>
                          {qualityLoadingByReport[report.id] ? (
                            <span className="text-[11px] font-semibold text-slate-500">Đang kiểm tra...</span>
                          ) : qualityAudits[report.id]?.score ? (
                            <span
                              className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                                qualityAudits[report.id].score >= 82
                                  ? "bg-emerald-100 text-emerald-700"
                                  : qualityAudits[report.id].score >= 65
                                    ? "bg-amber-100 text-amber-700"
                                    : "bg-red-100 text-red-700"
                              }`}
                            >
                              {qualityAudits[report.id].score}/100
                            </span>
                          ) : null}
                        </div>

                        {qualityAudits[report.id]?.error ? (
                          <p className="mt-2 text-xs font-semibold text-red-700">{qualityAudits[report.id].error}</p>
                        ) : qualityAudits[report.id]?.summary ? (
                          <div className="mt-2 space-y-2">
                            <p className="text-xs leading-relaxed text-slate-600">{qualityAudits[report.id].summary}</p>
                            {qualityAudits[report.id].issues_count > 0 && (
                              <div className="flex flex-wrap gap-2 text-[11px] font-semibold">
                                <span className="inline-flex items-center gap-1 rounded-md bg-white px-2 py-1 text-slate-600 ring-1 ring-slate-200">
                                  <AlertTriangle className="h-3 w-3 text-amber-600" />
                                  {qualityAudits[report.id].issues_count} điểm cần sửa
                                </span>
                                <span className="rounded-md bg-white px-2 py-1 text-slate-600 ring-1 ring-slate-200">
                                  {qualityAudits[report.id].high_issues_count || 0} lỗi nặng
                                </span>
                              </div>
                            )}
                            {qualityAudits[report.id].recommendations?.length > 0 && (
                              <p className="text-[11px] leading-relaxed text-slate-500">
                                {qualityAudits[report.id].recommendations[0]}
                              </p>
                            )}
                            {qualityAudits[report.id].issues?.length > 0 && (
                              <div className="mt-3 overflow-hidden rounded-lg border border-slate-200 bg-white">
                                <div className="flex items-center gap-1.5 border-b border-slate-100 px-3 py-2 text-[11px] font-bold text-slate-700">
                                  <ListChecks className="h-3.5 w-3.5 text-indigo-600" />
                                  Các mục cần chú ý
                                </div>
                                <div className="max-h-56 divide-y divide-slate-100 overflow-auto">
                                  {qualityAudits[report.id].issues.slice(0, 8).map((issue: any, idx: number) => (
                                    <div key={`${issue.section_id || issue.title}-${idx}`} className="flex flex-col gap-2 px-3 py-2 sm:flex-row sm:items-center sm:justify-between">
                                      <div className="min-w-0">
                                        <p className="truncate text-[11px] font-bold text-slate-800">{issue.title}</p>
                                        <p className="mt-0.5 text-[11px] text-slate-500">{issue.issues?.[0]}</p>
                                      </div>
                                      {issue.section_id && (
                                        <button
                                          type="button"
                                          onClick={() => repairSection(report.id, issue.section_id)}
                                          disabled={!!repairingSectionById[issue.section_id]}
                                          className="inline-flex shrink-0 items-center justify-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-700 transition hover:bg-slate-200 disabled:opacity-60"
                                        >
                                          <Wand2 className="h-3 w-3" />
                                          <span>{repairingSectionById[issue.section_id] ? "Đang sửa" : "Sửa mục"}</span>
                                        </button>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="mt-2 text-xs text-slate-500">Chưa có kết quả kiểm định cho báo cáo này.</p>
                        )}
                      </div>

                      <div className="flex shrink-0 flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => loadQualityAudit(report.id)}
                          disabled={!!qualityLoadingByReport[report.id] || !!repairingByReport[report.id]}
                          className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-white px-3 py-2 text-xs font-bold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-100 disabled:opacity-60"
                        >
                          <RefreshCw className={`h-3.5 w-3.5 ${qualityLoadingByReport[report.id] ? "animate-spin" : ""}`} />
                          <span>Kiểm tra</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => repairReport(report.id)}
                          disabled={!!repairingByReport[report.id]}
                          className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white transition hover:bg-indigo-700 disabled:opacity-60"
                        >
                          <Wand2 className={`h-3.5 w-3.5 ${repairingByReport[report.id] ? "animate-pulse" : ""}`} />
                          <span>{repairingByReport[report.id] ? "Đang sửa" : "Tự sửa báo cáo"}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => loadGroundingDebug(report.id)}
                          disabled={!!groundingLoadingByReport[report.id]}
                          className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-slate-900 px-3 py-2 text-xs font-bold text-white transition hover:bg-slate-800 disabled:opacity-60"
                        >
                          <Bug className={`h-3.5 w-3.5 ${groundingLoadingByReport[report.id] ? "animate-pulse" : ""}`} />
                          <span>{groundingLoadingByReport[report.id] ? "Đang tải" : "Debug dữ liệu"}</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  {groundingDebugByReport[report.id] && (
                    <div className="mb-4 rounded-xl border border-slate-200 bg-white">
                      <div className="flex flex-col gap-2 border-b border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-xs font-bold text-slate-900">Grounding Debug</p>
                          <p className="mt-0.5 text-[11px] text-slate-500">Facts used, source cells, validation result và repair count từng mục.</p>
                        </div>
                        {groundingDebugByReport[report.id]?.final_quality_gate && (
                          <span
                            className={`rounded-md px-2.5 py-1 text-[11px] font-bold ${
                              groundingDebugByReport[report.id].final_quality_gate.final
                                ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100"
                                : "bg-red-50 text-red-700 ring-1 ring-red-100"
                            }`}
                          >
                            {groundingDebugByReport[report.id].final_quality_gate.final ? "FINAL PASS" : "NEEDS REVIEW"}
                          </span>
                        )}
                      </div>
                      {groundingDebugByReport[report.id]?.error ? (
                        <div className="p-4 text-xs font-semibold text-red-600">{groundingDebugByReport[report.id].error}</div>
                      ) : (
                        <div className="space-y-3 p-4">
                          {groundingDebugByReport[report.id]?.final_quality_gate?.scores && (
                            <div className="grid gap-2 sm:grid-cols-5">
                              {Object.entries(groundingDebugByReport[report.id].final_quality_gate.scores).map(([key, value]) => (
                                <div key={key} className="rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
                                  <p className="truncate text-[10px] font-bold uppercase tracking-wide text-slate-400">{key}</p>
                                  <p className="mt-1 text-sm font-bold text-slate-900">{String(value)}</p>
                                </div>
                              ))}
                            </div>
                          )}
                          <div className="max-h-80 overflow-auto rounded-lg border border-slate-200">
                            <table className="min-w-full text-left text-[11px]">
                              <thead className="sticky top-0 bg-slate-50 text-slate-500">
                                <tr>
                                  <th className="border-b border-slate-200 px-3 py-2 font-bold">Mục</th>
                                  <th className="border-b border-slate-200 px-3 py-2 font-bold">Trạng thái</th>
                                  <th className="border-b border-slate-200 px-3 py-2 font-bold">Facts</th>
                                  <th className="border-b border-slate-200 px-3 py-2 font-bold">Nguồn</th>
                                  <th className="border-b border-slate-200 px-3 py-2 font-bold">Lỗi</th>
                                  <th className="border-b border-slate-200 px-3 py-2 font-bold">Repair</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100">
                                {(groundingDebugByReport[report.id]?.sections || []).map((section: any) => {
                                  const errors = section.validation?.errors || [];
                                  return (
                                    <tr key={section.id} className="align-top hover:bg-slate-50">
                                      <td className="max-w-[240px] px-3 py-2 font-bold text-slate-800">{section.title}</td>
                                      <td className="px-3 py-2">
                                        <span className={`rounded-md px-2 py-0.5 font-bold ${section.validation?.valid !== false ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                                          {section.validation?.valid !== false ? "pass" : "fail"}
                                        </span>
                                      </td>
                                      <td className="max-w-[180px] px-3 py-2 text-slate-600">{(section.facts_used || []).slice(0, 8).join(", ") || "-"}</td>
                                      <td className="max-w-[220px] px-3 py-2 text-slate-500">{(section.source_ranges || []).slice(0, 5).join(", ") || "-"}</td>
                                      <td className="max-w-[240px] px-3 py-2 text-red-600">{errors.length ? errors.map((e: any) => e.type).join(", ") : "-"}</td>
                                      <td className="px-3 py-2 text-slate-600">{section.repair_count || 0}</td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-xs font-bold text-slate-900">Bản xem theo mẫu</p>
                      <p className="mt-0.5 text-[11px] text-slate-500">
                        Hiển thị bìa, logo, bảng, ảnh và bố cục DOCX đang áp cho báo cáo.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {templatePreviews[report.id]?.download_url && (
                        <a
                          href={resolveDownloadUrl(templatePreviews[report.id].download_url)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-white px-3 py-2 text-xs font-bold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50"
                        >
                          <Download className="h-3.5 w-3.5" />
                          <span>Tải bản DOCX</span>
                        </a>
                      )}
                      <button
                        type="button"
                        onClick={() => loadTemplatePreview(report.id)}
                        disabled={!!previewLoadingByReport[report.id]}
                        className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-200 disabled:opacity-60"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${previewLoadingByReport[report.id] ? "animate-spin" : ""}`} />
                        <span>Làm mới bản theo mẫu</span>
                      </button>
                    </div>
                  </div>

                  {previewLoadingByReport[report.id] ? (
                    <div className="flex h-[560px] items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-500">
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin text-indigo-600" />
                      Đang dựng bản xem theo mẫu...
                    </div>
                  ) : templatePreviews[report.id]?.error ? (
                    <div className="space-y-3 rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-700">
                      <p className="font-bold">Không thể dựng bản xem theo mẫu</p>
                      <p className="leading-relaxed">{templatePreviews[report.id].error}</p>
                      <div className="flex flex-wrap gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => loadTemplatePreview(report.id)}
                          className="inline-flex items-center gap-1 rounded-md bg-white px-2.5 py-1.5 text-[11px] font-bold text-red-700 ring-1 ring-red-200"
                        >
                          <RefreshCw className="h-3 w-3" />
                          Thử lại preview
                        </button>
                        <button
                          type="button"
                          onClick={() => router.push(`/reports/${report.id}/editor`)}
                          className="inline-flex items-center gap-1 rounded-md bg-white px-2.5 py-1.5 text-[11px] font-bold text-red-700 ring-1 ring-red-200"
                        >
                          <ExternalLink className="h-3 w-3" />
                          Mở Studio
                        </button>
                      </div>
                    </div>
                  ) : templatePreviews[report.id]?.html_document ? (
                    <div className="h-[720px] overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
                      <iframe
                        title={`Bản xem theo mẫu ${report.title}`}
                        srcDoc={templatePreviews[report.id].html_document}
                        className="h-full w-full bg-slate-100"
                      />
                    </div>
                  ) : (
                    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-xs text-slate-500">
                      Chưa có bản xem theo mẫu. Bấm “Làm mới bản theo mẫu” để dựng lại.
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {/* Files Summary */}
      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900">Tài liệu đã tải lên ({project.files?.length || 0})</h2>
        {project.files && project.files.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {project.files.map((file: any) => (
              <div key={file.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <FileText className="h-4 w-4 text-indigo-600" />
                  <span className="font-medium text-slate-800">{file.original_name}</span>
                </div>
                <span className="text-slate-400">{(file.file_size / 1024).toFixed(1)} KB</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic">Chưa có tài liệu tham khảo nào được tải lên.</p>
        )}
      </div>
    </div>
  );
}
