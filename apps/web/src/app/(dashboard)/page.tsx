"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  TrendingUp,
  Search,
  FileCode,
  FileSpreadsheet,
  FileText,
  Plus,
  ArrowRight,
  Sparkles,
  Clock,
  Layers,
  Paperclip,
  Code2,
  FolderKanban,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useTranslation } from "@/i18n/I18nContext";

export default function DashboardPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [heroPrompt, setHeroPrompt] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.projects.list();
        setProjects(data);
      } catch (err) {
        // User not yet authenticated
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleHeroSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!heroPrompt.trim()) return;
    router.push(`/projects/new?prompt=${encodeURIComponent(heroPrompt)}`);
  };

  const handleDemoProject = async () => {
    try {
      const res = await api.projects.create({
        name: "Báo Cáo Tăng Trưởng Doanh Số Mẫu (Demo)",
        type: "financial",
        description: "Dự án mẫu khám phá tính năng tạo báo cáo tự động và phân tích định lượng.",
      });
      router.push(`/projects/${res.id}`);
    } catch {
      router.push("/projects/new");
    }
  };

  const quickActions = [
    {
      type: "business_report",
      title: t("dashboard.createReport"),
      desc: t("dashboard.createReportDesc"),
      icon: Briefcase,
      color: "text-blue-600 bg-blue-50 border-blue-100 hover:border-blue-300",
    },
    {
      type: "data_analysis",
      title: t("dashboard.analyzeData"),
      desc: t("dashboard.analyzeDataDesc"),
      icon: TrendingUp,
      color: "text-emerald-600 bg-emerald-50 border-emerald-100 hover:border-emerald-300",
    },
    {
      type: "research",
      title: t("dashboard.deepResearch"),
      desc: t("dashboard.deepResearchDesc"),
      icon: Search,
      color: "text-indigo-600 bg-indigo-50 border-indigo-100 hover:border-indigo-300",
    },
    {
      type: "technical",
      title: t("dashboard.technicalDocs"),
      desc: t("dashboard.technicalDocsDesc"),
      icon: FileCode,
      color: "text-violet-600 bg-violet-50 border-violet-100 hover:border-violet-300",
    },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-4 px-2 sm:px-4">
      {/* Central Hero: What do you want to create? */}
      <section className="relative overflow-hidden rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 text-white shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold border border-indigo-500/30">
              <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
              Autonomous AI Document Studio
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            {t("dashboard.heroQuestion")}
          </h1>

          <form onSubmit={handleHeroSubmit} className="space-y-3 pt-2">
            <div className="relative bg-slate-800/90 rounded-2xl border border-slate-700/80 p-2 shadow-inner focus-within:border-indigo-500 transition-colors">
              <textarea
                value={heroPrompt}
                onChange={(e) => setHeroPrompt(e.target.value)}
                placeholder={t("dashboard.heroPlaceholder")}
                rows={3}
                className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-400 outline-none resize-none p-2"
              />

              {/* Bottom toolbar inside input */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-700/60 px-1">
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="text-[11px] font-medium mr-1">{t("dashboard.attachDoc")}:</span>
                  <Link
                    href="/projects/new"
                    className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                  >
                    <FileText className="h-3 w-3" />
                    <span>PDF / DOCX</span>
                  </Link>
                  <Link
                    href="/data"
                    className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                  >
                    <FileSpreadsheet className="h-3 w-3" />
                    <span>Excel</span>
                  </Link>
                  <Link
                    href="/templates"
                    className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                  >
                    <Layers className="h-3 w-3" />
                    <span>Template</span>
                  </Link>
                </div>

                <button
                  type="submit"
                  disabled={!heroPrompt.trim()}
                  className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-sm transition-all disabled:opacity-40"
                >
                  <span>{t("dashboard.generateAuto")}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </form>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            {t("dashboard.quickActions")}
          </h2>
          <button
            onClick={handleDemoProject}
            className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>{t("dashboard.demoProjectBtn")}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((qa) => {
            const Icon = qa.icon;
            return (
              <Link
                key={qa.type}
                href={`/projects/new?type=${qa.type}`}
                className={`p-5 rounded-2xl border transition-all duration-200 group bg-white shadow-2xs hover:shadow-xs flex flex-col justify-between ${qa.color}`}
              >
                <div className="space-y-2.5">
                  <div className="h-9 w-9 rounded-xl flex items-center justify-center bg-white shadow-2xs">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm group-hover:text-indigo-600 transition-colors">
                    {qa.title}
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed">{qa.desc}</p>
                </div>
                <div className="pt-4 flex items-center text-xs font-semibold text-indigo-600 gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>{t("common.create")}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Recent Projects */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            {t("dashboard.recentProjects")}
          </h2>
          <Link href="/projects" className="text-xs font-semibold text-indigo-600 hover:text-indigo-700">
            {t("dashboard.viewAll")}
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 rounded-2xl bg-slate-100 animate-pulse border border-slate-200" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center space-y-2">
            <FolderKanban className="mx-auto h-8 w-8 text-slate-400" />
            <h3 className="text-xs font-bold text-slate-800">{t("dashboard.noProjectsYet")}</h3>
            <p className="text-xs text-slate-500">{t("dashboard.noProjectsDesc")}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {projects.slice(0, 6).map((proj) => (
              <Link
                key={proj.id}
                href={`/projects/${proj.id}`}
                className="p-4 rounded-2xl bg-white border border-slate-200 hover:border-indigo-300 hover:shadow-xs transition-all space-y-2.5 block group"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-[10px] font-bold text-indigo-700 uppercase">
                    {proj.type || "Report"}
                  </span>
                  <span className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDate(proj.created_at)}
                  </span>
                </div>
                <h4 className="font-bold text-slate-900 text-xs truncate group-hover:text-indigo-600 transition-colors">
                  {proj.name}
                </h4>
                <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                  {proj.description || t("common.noData")}
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
