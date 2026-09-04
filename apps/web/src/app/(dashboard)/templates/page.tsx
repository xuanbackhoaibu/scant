"use client";

import { useEffect, useState } from "react";
import { Search, ArrowRight, Star, X, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/i18n/I18nContext";

const CATEGORIES = [
  "all",
  "business",
  "financial",
  "technical",
  "academic",
  "research",
  "data",
  "proposal",
  "marketing",
  "operations",
  "custom",
];

export default function TemplatesPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [templates, setTemplates] = useState<any[]>([]);
  const [scope, setScope] = useState<"public" | "workspace" | "my">("public");
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [previewTemplate, setPreviewTemplate] = useState<any | null>(null);

  useEffect(() => {
    async function loadTemplates() {
      setLoading(true);
      try {
        const res = await api.templates.list({ scope, category, search });
        setTemplates(res || []);
      } catch {
        setTemplates([]);
      } finally {
        setLoading(false);
      }
    }
    loadTemplates();
  }, [scope, category, search]);

  const handleUseTemplate = async (tpl: any) => {
    if (tpl.is_external && tpl.source_url) {
      window.open(tpl.source_url, "_blank", "noopener,noreferrer");
      return;
    }

    try {
      await api.templates.use(tpl.id);
    } catch {
      // Navigation should still work if usage tracking fails.
    }
    router.push(`/projects/new?template=${tpl.id}`);
  };

  const getCategoryLabel = (categoryName: string) => {
    const key = categoryName?.toLowerCase() || "custom";
    const translated = t(`templates.categories.${key}`);
    return translated.startsWith("templates.categories.") ? categoryName : translated;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{t("templates.title")}</h1>
          <p className="text-xs text-slate-500">{t("templates.subtitle")}</p>
        </div>
      </div>

      {/* Tabs & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex bg-slate-100 p-1 rounded-xl w-full sm:w-auto">
          {[
            { id: "public", label: t("templates.scopes.public") },
            { id: "workspace", label: t("templates.scopes.workspace") },
            { id: "my", label: t("templates.scopes.my") },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setScope(t.id as any)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                scope === t.id ? "bg-white text-indigo-600 shadow-xs" : "text-slate-500 hover:text-slate-900"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("templates.searchPlaceholder")}
            className="w-full h-8 pl-8 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-none"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {CATEGORIES.map((categoryId) => (
          <button
            key={categoryId}
            onClick={() => setCategory(categoryId)}
            className={`px-3 py-1 rounded-full text-xs font-semibold shrink-0 transition-colors ${
              category === categoryId ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {t(`templates.categories.${categoryId}`)}
          </button>
        ))}
      </div>

      {/* Template Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-slate-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : templates.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
          <h3 className="text-sm font-bold text-slate-900">{t("templates.emptyTitle")}</h3>
          <p className="mt-1 text-xs text-slate-500">{t("templates.emptyTemplates")}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {templates.map((tpl) => (
            <button
              key={tpl.id}
              type="button"
              onClick={() => setPreviewTemplate(tpl)}
              className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-xs transition-all flex flex-col justify-between space-y-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="px-2 py-0.5 rounded bg-indigo-50 text-[10px] font-bold text-indigo-700 uppercase truncate">
                      {getCategoryLabel(tpl.category)}
                    </span>
                    {tpl.is_external && (
                      <span className="px-2 py-0.5 rounded bg-emerald-50 text-[10px] font-bold text-emerald-700">
                        {t("templates.realSource")}
                      </span>
                    )}
                  </div>
                  <span className="flex items-center gap-1 text-[11px] font-bold text-amber-600 shrink-0">
                    <Star className="h-3 w-3 fill-amber-500 text-amber-500" />
                    <span>{Number(tpl.rating || 0).toFixed(1).replace(".0", "")}</span>
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 leading-snug">{tpl.name}</h3>
                <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">
                  {tpl.description || t("templates.noDescription")}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-400">
                  {t("templates.usageCount", { count: tpl.usage_count || 0 })}
                </span>
                <span className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 text-white rounded-lg font-bold text-xs shadow-xs">
                  <span>{t("templates.preview")}</span>
                  <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {previewTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white shadow-xl">
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 p-5">
              <div className="min-w-0 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-indigo-50 text-[10px] font-bold text-indigo-700 uppercase">
                    {getCategoryLabel(previewTemplate.category)}
                  </span>
                  {previewTemplate.is_external && (
                    <span className="px-2 py-0.5 rounded bg-emerald-50 text-[10px] font-bold text-emerald-700">
                      {t("templates.realSource")}
                    </span>
                  )}
                </div>
                <h2 className="text-base font-bold text-slate-950">{previewTemplate.name}</h2>
                <p className="text-xs leading-relaxed text-slate-500">
                  {previewTemplate.description || t("templates.noDescription")}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPreviewTemplate(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                aria-label={t("common.close")}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid gap-5 p-5 sm:grid-cols-[1.2fr_0.8fr]">
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase text-slate-400">{t("templates.previewStructure")}</h3>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  {(previewTemplate.preview_sections?.length
                    ? previewTemplate.preview_sections
                    : [t("templates.noPreview")]
                  ).map((section: string, index: number) => (
                    <div
                      key={`${section}-${index}`}
                      className="flex items-center gap-3 border-b border-slate-200/70 py-2 last:border-0"
                    >
                      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white text-[11px] font-bold text-indigo-600 ring-1 ring-slate-200">
                        {index + 1}
                      </span>
                      <span className="text-xs font-medium text-slate-700">{section}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase text-slate-400">{t("templates.sourceInfo")}</h3>
                <div className="rounded-xl border border-slate-200 p-3 text-xs">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500">{t("templates.provider")}</span>
                    <span className="font-bold text-slate-900">{previewTemplate.author_name}</span>
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-3">
                    <span className="text-slate-500">{t("templates.rating")}</span>
                    <span className="font-bold text-amber-600">
                      {Number(previewTemplate.rating || 0).toFixed(1).replace(".0", "")}
                    </span>
                  </div>
                  {previewTemplate.source_url && (
                    <a
                      href={previewTemplate.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      {t("templates.openOriginal")}
                    </a>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-slate-100 p-4">
              <button
                type="button"
                onClick={() => setPreviewTemplate(null)}
                className="rounded-lg px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                {t("common.cancel")}
              </button>
              <button
                type="button"
                onClick={() => handleUseTemplate(previewTemplate)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white hover:bg-indigo-700"
              >
                {previewTemplate.is_external ? <ExternalLink className="h-3.5 w-3.5" /> : <ArrowRight className="h-3.5 w-3.5" />}
                <span>{t("templates.useTemplate")}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
