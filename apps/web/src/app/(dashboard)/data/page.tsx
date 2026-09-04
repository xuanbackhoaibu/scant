"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BarChart2, Database, FileSpreadsheet, GitCompare, Layers3, Table, Upload } from "lucide-react";
import { api } from "@/lib/api";
import { PreviewModal } from "@/components/PreviewModal";
import SpreadsheetPreview from "@/components/SpreadsheetPreview";
import { datasetComparison, groupDatasetsForDisplay } from "@/lib/datasetGroups";

export default function DataWorkspacePage() {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewDataset, setPreviewDataset] = useState<any | null>(null);
  const [profile, setProfile] = useState<any | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [activeSheet, setActiveSheet] = useState(0);

  useEffect(() => {
    async function loadData() {
      try {
        const files = await api.files.list();
        setDatasets(
          files.filter((f: any) => {
            const name = (f.original_name || "").toLowerCase();
            return ["excel", "csv", "xlsx", "xls"].includes(f.file_type) || name.endsWith(".csv") || name.endsWith(".xlsx") || name.endsWith(".xls") || name.endsWith(".xlsm");
          })
        );
      } catch {
        // empty
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const openDatasetPreview = async (dataset: any) => {
    setPreviewDataset(dataset);
    setProfile(null);
    setActiveSheet(0);
    setPreviewLoading(true);
    try {
      setProfile(await api.data.profile(dataset.id));
    } catch (err: any) {
      setProfile({ error: err.message || "Không thể đọc dữ liệu mẫu." });
    } finally {
      setPreviewLoading(false);
    }
  };
  const datasetGroups = groupDatasetsForDisplay(datasets);

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Không gian Dữ liệu</h1>
            <p className="text-xs text-slate-500">Tải Excel/CSV, kiểm tra số liệu thật và tạo báo cáo phân tích có bảng, biểu đồ.</p>
          </div>
          <Link
            href="/projects/new?mode=auto&type=data_analysis&workflow=data"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700"
          >
            <Upload className="h-4 w-4" />
            Tải dữ liệu & tạo báo cáo
          </Link>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-800">Tập dữ liệu đã kết nối ({datasetGroups.length} nhóm / {datasets.length} file)</h2>
          </div>
          <Link
            href="/projects/new?mode=auto&type=data_analysis&workflow=data"
            className="hidden items-center gap-1 text-xs font-bold text-emerald-700 hover:text-emerald-800 sm:inline-flex"
          >
            Tạo phân tích mới
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="h-32 bg-slate-100 rounded-xl animate-pulse" />
        ) : datasetGroups.length === 0 ? (
          <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-xl space-y-2">
            <FileSpreadsheet className="h-8 w-8 text-slate-400 mx-auto" />
            <h3 className="text-xs font-bold text-slate-700">Chưa có tập dữ liệu CSV/Excel nào</h3>
            <p className="text-[11px] text-slate-400">
              Hãy tải lên tệp Excel hoặc CSV trong khi tạo báo cáo để phân tích số liệu tự động.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {datasetGroups.map((group) => {
              const d = group.primary;
              const comparison = datasetComparison(d);
              const profile = d?.metadata_json?.dataset_profile || {};
              return (
                <div key={group.id} className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <button type="button" onClick={() => openDatasetPreview(d)} className="min-w-0 flex-1 text-left">
                      <div className="flex items-start gap-3">
                        <FileSpreadsheet className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="font-bold text-slate-800">{d.original_name}</h4>
                            <span className="rounded-md bg-emerald-100 px-2 py-1 text-[10px] font-bold text-emerald-800">Bản chính</span>
                            {group.hiddenDuplicateCount > 0 ? (
                              <span className="inline-flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-1 text-[10px] font-bold text-emerald-800">
                                <Layers3 className="h-3 w-3" />
                                Ẩn {group.hiddenDuplicateCount} bản trùng
                              </span>
                            ) : group.variants.length > 0 ? (
                              <span className="inline-flex items-center gap-1 rounded-md bg-amber-100 px-2 py-1 text-[10px] font-bold text-amber-800">
                                <GitCompare className="h-3 w-3" />
                                {group.variants.length} bản tương tự
                              </span>
                            ) : null}
                          </div>
                          <p className="mt-1 text-slate-500">
                            {(d.file_size / 1024).toFixed(1)} KB
                            {profile?.total_rows ? ` · ${profile.total_rows} dòng` : ""}
                            {profile?.total_columns ? ` · ${profile.total_columns} cột` : ""}
                            {comparison?.schema_signature ? " · đã lập dấu vân tay dữ liệu" : ""}
                          </p>
                          <p className="mt-2 text-[11px] leading-5 text-slate-500">
                            Bấm để xem sheet, verified facts, thống kê cột và dòng dữ liệu mẫu.
                          </p>
                        </div>
                      </div>
                    </button>
                    <Link href="/projects/new?mode=auto&type=data_analysis&workflow=data" className="inline-flex items-center justify-center gap-2 rounded-lg border border-emerald-200 bg-white px-3 py-2 text-xs font-bold text-emerald-700 hover:bg-emerald-50">
                      Phân tích
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                  {group.hiddenDuplicateCount > 0 ? (
                    <div className="mt-3 inline-flex items-center gap-2 rounded-lg border border-emerald-100 bg-white px-3 py-2 text-[11px] font-semibold text-emerald-800">
                      <Layers3 className="h-3.5 w-3.5" />
                      Đã ẩn {group.hiddenDuplicateCount} bản trùng hoàn toàn, chỉ dùng bản chính khi tạo báo cáo.
                    </div>
                  ) : group.variants.length > 0 ? (
                    <div className="mt-3 rounded-lg border border-amber-100 bg-white">
                      <div className="flex items-center gap-2 border-b border-amber-100 px-3 py-2 font-bold text-amber-900">
                        <Layers3 className="h-3.5 w-3.5" />
                        Các bản giống nhau nhiều, không dùng lặp khi tạo báo cáo
                      </div>
                      <div className="divide-y divide-slate-100">
                        {group.variants.map((variant: any) => {
                          const variantComparison = datasetComparison(variant);
                          const score = Math.round((variantComparison.similarity_score || 0) * 100);
                          return (
                            <button key={variant.id} type="button" onClick={() => openDatasetPreview(variant)} className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-slate-50">
                              <span className="min-w-0 truncate font-semibold text-slate-700">{variant.original_name}</span>
                              <span className="shrink-0 rounded-md bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">Giống {score || "-"}%</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <PreviewModal
        isOpen={!!previewDataset}
        onClose={() => setPreviewDataset(null)}
        title={previewDataset?.original_name || "Xem trước dữ liệu"}
        subtitle={previewDataset ? `${(previewDataset.file_size / 1024).toFixed(1)} KB` : undefined}
        footer={
          <>
            <button
              type="button"
              onClick={() => setPreviewDataset(null)}
              className="rounded-lg px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100"
            >
              Đóng
            </button>
            {previewDataset && (
              <Link
                href="/projects/new?mode=auto&type=data_analysis&workflow=data"
                className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white hover:bg-emerald-700"
              >
                Tạo báo cáo phân tích
              </Link>
            )}
          </>
        }
      >
        {previewLoading ? (
          <div className="h-52 rounded-xl bg-slate-100 animate-pulse" />
        ) : profile?.error ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-700">
            {profile.error}
          </div>
        ) : (
          <div className="space-y-4 text-xs">
            {(() => {
              const sheets = profile?.sheets || [];
              const sheet = sheets[activeSheet] || sheets[0] || {};
              const missing = sheets.reduce((sum: number, s: any) => sum + (s.statistics?.missing_values_count || 0), 0);
              const duplicates = sheets.reduce((sum: number, s: any) => sum + (s.statistics?.duplicate_rows_count || 0), 0);
              const rows = sheet.records || profile?.preview_rows || [];
              const columns = sheet.columns || profile?.columns || [];
              const facts = profile?.verified_facts || [];
              return (
                <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="text-slate-400">Số dòng</div>
                <div className="mt-1 font-bold text-slate-900">{profile?.total_rows ?? "-"}</div>
              </div>
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="text-slate-400">Số cột</div>
                <div className="mt-1 font-bold text-slate-900">{profile?.total_columns ?? "-"}</div>
              </div>
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="text-slate-400">Số sheet</div>
                <div className="mt-1 font-bold text-slate-900">{profile?.sheet_count ?? sheets.length ?? "-"}</div>
              </div>
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="text-slate-400">Thiếu / trùng</div>
                <div className="mt-1 font-bold text-slate-900">{missing} / {duplicates}</div>
              </div>
            </div>

            {sheets.length > 1 && (
              <div className="flex gap-2 overflow-x-auto">
                {sheets.map((sheetItem: any, index: number) => (
                  <button
                    key={sheetItem.name || index}
                    type="button"
                    onClick={() => setActiveSheet(index)}
                    className={`rounded-lg px-3 py-2 text-xs font-bold ${
                      activeSheet === index ? "bg-emerald-600 text-white" : "border border-slate-200 bg-white text-slate-600"
                    }`}
                  >
                    {sheetItem.name || `Sheet ${index + 1}`}
                  </button>
                ))}
              </div>
            )}

            {facts.length > 0 && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="flex items-center gap-2 border-b border-emerald-100 px-4 py-3 font-bold text-emerald-900">
                  <BarChart2 className="h-4 w-4" />
                  Số liệu đã kiểm chứng
                </div>
                <div className="max-h-52 overflow-y-auto divide-y divide-emerald-100">
                  {facts.slice(0, 18).map((fact: any) => (
                    <div key={fact.id} className="grid grid-cols-[80px_1fr_1fr] gap-3 px-4 py-2">
                      <span className="font-mono font-bold text-emerald-700">{fact.id}</span>
                      <span className="font-semibold text-slate-800">{fact.fact}</span>
                      <span className="text-slate-600">{typeof fact.value === "object" ? JSON.stringify(fact.value) : String(fact.value ?? "-")}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-xl border border-slate-200">
              <div className="border-b border-slate-100 px-4 py-3 font-bold text-slate-900">Cột dữ liệu {sheet.name ? `- ${sheet.name}` : ""}</div>
              <div className="max-h-40 overflow-y-auto divide-y divide-slate-100">
                {columns.map((col: any) => (
                  <div key={col.name} className="grid grid-cols-[1fr_auto_auto] gap-3 px-4 py-2">
                    <span className="font-semibold text-slate-800">{col.name}</span>
                    <span className="text-slate-500">{col.type}</span>
                    <span className="text-slate-400">{col.unique_count} giá trị</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3 font-bold text-slate-900">
                <Table className="h-4 w-4" />
                Bản xem trước bảng tính
              </div>
              <div className="p-2">
                <SpreadsheetPreview
                  workbook={profile?.visual_workbook}
                  legacyData={profile}
                  height={420}
                />
              </div>
            </div>
                </>
              );
            })()}
          </div>
        )}
      </PreviewModal>
    </div>
  );
}
