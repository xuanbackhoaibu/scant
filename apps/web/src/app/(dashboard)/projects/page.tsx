"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FolderKanban, Plus, Search, Clock, Trash2, ExternalLink } from "lucide-react";
import { useProjectStore } from "@/stores/useProjectStore";
import { formatDate } from "@/lib/utils";
import { useTranslation } from "@/i18n/I18nContext";
import { PreviewModal } from "@/components/PreviewModal";
import { api } from "@/lib/api";
import { selectProjectPreviewReport } from "@/lib/projectCards";
import { buildReportPreviewFrameSrcDoc } from "@/lib/reportPreviewFrame";
import { AnimatedCard } from "@/components/AnimatedCard";
import { SkeletonLoader } from "@/components/SkeletonLoader";

export default function ProjectsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { projects, isLoading, fetchProjects, deleteProject } = useProjectStore();
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [previewProject, setPreviewProject] = useState<any | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [reports, setReports] = useState<any[]>([]);
  const [projectPreviewFrames, setProjectPreviewFrames] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    let cancelled = false;
    async function loadReports() {
      try {
        const reportList = await api.reports.list();
        if (!cancelled) setReports(reportList);
      } catch {
        if (!cancelled) setReports([]);
      }
    }
    loadReports();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(search.toLowerCase()));
    const matchesType = filterType === "all" || p.type === filterType;
    return matchesSearch && matchesType;
  });
  const filteredProjectIdsKey = filteredProjects.map((p) => p.id).join("|");

  useEffect(() => {
    if (!filteredProjectIdsKey || reports.length === 0) return;
    let cancelled = false;
    const missing = filteredProjects
      .map((project) => ({ project, report: selectProjectPreviewReport(project, reports) }))
      .filter(({ project, report }) => report?.id && !projectPreviewFrames[project.id]);
    if (missing.length === 0) return;

    async function loadProjectPreviewFrames() {
      const loaded = await Promise.all(
        missing.slice(0, 24).map(async ({ project, report }) => {
          try {
            const preview = await api.exports.previewReportHtml(report.id);
            return [project.id, buildReportPreviewFrameSrcDoc(preview.html_document)] as const;
          } catch {
            return [project.id, ""] as const;
          }
        })
      );
      if (!cancelled) {
        setProjectPreviewFrames((prev) => ({
          ...prev,
          ...Object.fromEntries(loaded.filter(([, url]) => url)),
        }));
      }
    }

    loadProjectPreviewFrames();
    return () => {
      cancelled = true;
    };
  }, [filteredProjectIdsKey, reports, projectPreviewFrames]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirm(t("projects.confirmDelete"))) {
      await deleteProject(id);
    }
  };

  const openProjectPreview = async (project: any) => {
    setPreviewProject(project);
    setPreviewLoading(true);
    try {
      setPreviewProject(await api.projects.get(project.id));
    } catch {
      setPreviewProject(project);
    } finally {
      setPreviewLoading(false);
    }
  };

  const getProjectInfoRows = (project: any) => {
    const metadata = project?.metadata_json || {};
    const customFields = Array.isArray(metadata.custom_fields) ? metadata.custom_fields : [];
    const readable = (value: any) =>
      String(value || "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());

    const rows = [
      ["Loại tài liệu", readable(metadata.document_type || project?.type)],
      ["Hồ sơ báo cáo", readable(metadata.document_profile)],
      ["Đối tượng đọc", metadata.audience],
      ["Ngôn ngữ", metadata.language === "vi" ? "Tiếng Việt" : metadata.language === "en" ? "Tiếng Anh" : metadata.language],
      ...customFields
        .filter((field: any) => field?.value !== undefined && field?.value !== null && String(field.value).trim() !== "")
        .map((field: any) => [field.label || field.key, field.value]),
    ];

    return rows.filter(([, value]) => value !== undefined && value !== null && String(value).trim() !== "");
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{t("projects.title")}</h1>
          <p className="text-xs text-slate-500">{t("projects.subtitle")}</p>
        </div>
        <Link
          href="/projects/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition-colors self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>{t("projects.createProject")}</span>
        </Link>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-2xs">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("common.search")}
            className="w-full h-9 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-500 outline-none transition-all"
          />
        </div>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SkeletonLoader count={3} className="h-40" />
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center space-y-3">
          <FolderKanban className="mx-auto h-10 w-10 text-slate-400" />
          <h3 className="text-sm font-bold text-slate-800">{t("projects.emptyProjects")}</h3>
          <Link
            href="/projects/new"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition-colors shadow-xs"
          >
            <Plus className="h-4 w-4" />
            <span>{t("projects.createProject")}</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
          {filteredProjects.map((proj) => {
            const previewFrame = projectPreviewFrames[proj.id];
            const reportCount = reports.filter((report) => report.project_id === proj.id).length;
            return (
              <article
                key={proj.id}
                className="group"
              >
                <AnimatedCard className="overflow-hidden rounded-xl border border-slate-200 bg-white transition-all hover:border-indigo-300 hover:shadow-sm">
                  <button
                    type="button"
                    onClick={() => router.push(`/projects/${proj.id}`)}
                    className="block w-full bg-slate-100/70 px-4 py-4 text-left"
                  >
                    <div className="mx-auto aspect-[3/4] w-28 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm transition-transform group-hover:-translate-y-0.5">
                      {previewFrame ? (
                        <iframe
                          title={`Ảnh xem trước ${proj.name}`}
                          srcDoc={previewFrame}
                          className="h-full w-full border-0 bg-white"
                          tabIndex={-1}
                        />
                      ) : (
                        <div className="flex h-full flex-col p-3">
                          <div className="mb-2 h-1.5 w-12 rounded-full bg-slate-900" />
                          <div className="mb-3 h-1 w-16 rounded-full bg-indigo-200" />
                          <div className="space-y-1.5">
                            {[78, 92, 84, 66, 88, 72].map((width, index) => (
                              <div key={index} className="h-1 rounded-full bg-slate-200" style={{ width: `${width}%` }} />
                            ))}
                          </div>
                          <div className="mt-auto grid grid-cols-3 gap-1">
                            <div className="h-5 rounded-sm bg-indigo-50" />
                            <div className="h-5 rounded-sm bg-emerald-50" />
                            <div className="h-5 rounded-sm bg-slate-100" />
                          </div>
                        </div>
                      )}
                    </div>
                  </button>

                  <div className="space-y-3 p-4">
                  <div className="flex items-center justify-between gap-2">
                    <span className="rounded-md bg-indigo-50 px-2 py-1 text-[10px] font-bold uppercase text-indigo-700">
                      {proj.type || "Document"}
                    </span>
                    <button
                      onClick={(e) => handleDelete(e, proj.id)}
                      title={t("common.delete")}
                      className="rounded-lg p-1 text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <button type="button" onClick={() => router.push(`/projects/${proj.id}`)} className="block w-full text-left">
                    <h3 className="line-clamp-2 min-h-10 text-sm font-bold leading-relaxed text-slate-900 transition-colors group-hover:text-indigo-600">
                      {proj.name}
                    </h3>
                    <p className="mt-1 line-clamp-2 min-h-10 text-xs leading-relaxed text-slate-500">
                      {proj.description || t("common.noData")}
                    </p>
                  </button>

                  <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-[11px]">
                    <span className="flex min-w-0 items-center gap-1 text-slate-400">
                      <Clock className="h-3 w-3 shrink-0" />
                      <span className="truncate">{formatDate(proj.created_at)}</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => router.push(`/projects/${proj.id}`)}
                      className="inline-flex shrink-0 items-center gap-1 font-bold text-indigo-600 hover:text-indigo-700"
                    >
                      <span>{t("common.open")}</span>
                      <ExternalLink className="h-3 w-3" />
                    </button>
                  </div>
                  {reportCount > 0 && (
                    <div className="text-[10px] font-semibold text-slate-400">{reportCount} tài liệu trong dự án</div>
                  )}
                  </div>
                </AnimatedCard>
              </article>
            );
          })}
        </div>
      )}

      <PreviewModal
        isOpen={!!previewProject}
        onClose={() => setPreviewProject(null)}
        title={previewProject?.name || "Xem trước dự án"}
        subtitle={previewProject?.type}
        footer={
          <>
            <button
              type="button"
              onClick={() => setPreviewProject(null)}
              className="rounded-lg px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100"
            >
              {t("common.cancel")}
            </button>
            {previewProject && (
              <Link
                href={`/projects/${previewProject.id}`}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white hover:bg-indigo-700"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                <span>Mở dự án</span>
              </Link>
            )}
          </>
        }
      >
        {previewLoading ? (
          <div className="h-40 rounded-xl bg-slate-100 animate-pulse" />
        ) : (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="text-slate-400">Loại dự án</div>
                <div className="mt-1 font-bold text-slate-900">{previewProject?.type || "Document"}</div>
              </div>
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="text-slate-400">Ngày tạo</div>
                <div className="mt-1 font-bold text-slate-900">{previewProject?.created_at ? formatDate(previewProject.created_at) : "-"}</div>
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="font-bold text-slate-900">Mô tả</h3>
              <p className="mt-2 whitespace-pre-wrap leading-relaxed text-slate-600">
                {previewProject?.description || "Dự án này chưa có mô tả chi tiết."}
              </p>
            </div>
            {getProjectInfoRows(previewProject).length > 0 && (
              <div className="rounded-xl border border-slate-200 p-4">
                <h3 className="font-bold text-slate-900">Thông tin chính</h3>
                <div className="mt-3 divide-y divide-slate-100">
                  {getProjectInfoRows(previewProject).map(([label, value]) => (
                    <div key={String(label)} className="grid grid-cols-[150px_1fr] gap-3 py-2">
                      <span className="text-slate-400">{label}</span>
                      <span className="font-semibold leading-relaxed text-slate-800">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </PreviewModal>
    </div>
  );
}
