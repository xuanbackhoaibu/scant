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
  BookOpen,
  Building,
  User,
  Layers,
  Search,
  ExternalLink,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const router = useRouter();

  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const proj = await api.projects.get(projectId);
        setProject(proj);
        setLoading(false);
      } catch {
        setLoading(false);
      }
    }
    loadData();
  }, [projectId]);

  if (loading) {
    return (
      <div className="space-y-4 max-w-5xl mx-auto py-8">
        <div className="h-28 bg-slate-100 rounded-2xl animate-pulse border border-slate-200" />
        <div className="h-64 bg-slate-100 rounded-2xl animate-pulse border border-slate-200" />
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

  return (
    <div className="max-w-5xl mx-auto py-6 space-y-6">
      {/* Project Overview Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-0.5 text-[11px] font-bold text-indigo-700 uppercase tracking-wider">
                {project.type}
              </span>
              <span className="text-xs text-slate-400">Tạo ngày {formatDate(project.created_at)}</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">{project.name}</h1>
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

      {/* Files Summary */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
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
