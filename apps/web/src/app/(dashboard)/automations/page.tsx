"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Clock,
  Play,
  Plus,
  RefreshCw,
  CheckCircle2,
  Calendar,
  AlertCircle,
  Sparkles,
  Search,
  Filter,
  Pause,
  Trash2,
  Edit3,
  ChevronRight,
  ChevronLeft,
  X,
  FileSpreadsheet,
  FileText,
  Download,
  ExternalLink,
  Layers,
  Settings,
  Check,
  Terminal,
  Activity,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { api } from "@/lib/api";

interface AutomationItem {
  id: string;
  project_id: string;
  project_name?: string;
  name: string;
  description?: string;
  trigger_type: string;
  cron_expression?: string;
  timezone?: string;
  data_source_id?: string;
  source_type?: string;
  source_config?: any;
  template_id?: string;
  analysis_prompt?: string;
  analysis_mode?: string;
  report_title_pattern: string;
  export_formats: string[];
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
  updated_at?: string;
}

interface AutomationRunItem {
  id: string;
  automation_id: string;
  report_id?: string;
  status: string;
  trigger_source: string;
  retry_count: number;
  duration_ms: number;
  source_snapshot?: any;
  output_files?: any[];
  failed_step?: string;
  error_message?: string;
  logs: string[];
  started_at: string;
  finished_at?: string;
}

const ANALYSIS_MODES = [
  {
    id: "comprehensive",
    title: "Toàn diện & Đa chiều",
    desc: "Đầy đủ 4 phần: Tổng quan, Chỉ số trọng yếu, Rà soát bất thường và Kế hoạch thực thi.",
    badge: "Tiêu chuẩn",
  },
  {
    id: "kpi_financial",
    title: "Chỉ số & Tài chính",
    desc: "Tập trung sâu vào bảng số liệu, tổng hợp quỹ lương, doanh số, biên độ và các cột số.",
    badge: "Tài chính / KPI",
  },
  {
    id: "summary",
    title: "Tóm lược Điều hành",
    desc: "Văn phong ngắn gọn, súc tích dành cho lãnh đạo và quản trị viên ra quyết định nhanh.",
    badge: "Executive",
  },
  {
    id: "academic",
    title: "Nghiên cứu & Học thuật",
    desc: "Phân tích phương pháp luận, dẫn chứng kiểm chứng và văn phong học thuật chuyên sâu.",
    badge: "Academic",
  },
];

const SCHEDULE_PRESETS = [
  { label: "Hằng ngày lúc 08:00 sáng", cron: "0 8 * * *", type: "schedule" },
  { label: "Hằng tuần vào Thứ 2 lúc 08:00", cron: "0 8 * * 1", type: "schedule" },
  { label: "Hằng tháng vào ngày 01 lúc 08:00", cron: "0 8 1 * *", type: "schedule" },
  { label: "Định kỳ mỗi 30 phút", cron: "interval:30m", type: "schedule" },
  { label: "Định kỳ mỗi 1 giờ", cron: "interval:1h", type: "schedule" },
  { label: "Thủ công (Chỉ chạy khi bấm 'Chạy ngay')", cron: "", type: "manual" },
];

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<AutomationItem[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [projectFiles, setProjectFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTrigger, setFilterTrigger] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  // Multi-step Wizard Modal State
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [editingAutomationId, setEditingAutomationId] = useState<string | null>(null);
  const [wizardStep, setWizardStep] = useState(1);
  const [savingWizard, setSavingWizard] = useState(false);

  // Wizard Form Fields
  const [formProjectId, setFormProjectId] = useState("");
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formSourceType, setFormSourceType] = useState("file");
  const [formDataSourceId, setFormDataSourceId] = useState("");
  const [formSheetName, setFormSheetName] = useState("");
  const [formAnalysisMode, setFormAnalysisMode] = useState("comprehensive");
  const [formAnalysisPrompt, setFormAnalysisPrompt] = useState("");
  const [formTitlePattern, setFormTitlePattern] = useState("Báo cáo Tự động {date}");
  const [formExportDocx, setFormExportDocx] = useState(true);
  const [formExportPdf, setFormExportPdf] = useState(true);
  const [formTriggerType, setFormTriggerType] = useState("schedule");
  const [formCronExpression, setFormCronExpression] = useState("0 8 * * 1");
  const [formCustomCron, setFormCustomCron] = useState("");
  const [formTimezone, setFormTimezone] = useState("Asia/Ho_Chi_Minh");
  const [formIsActive, setFormIsActive] = useState(true);

  // History / Runs Modal State
  const [selectedAutoForHistory, setSelectedAutoForHistory] = useState<AutomationItem | null>(null);
  const [runsList, setRunsList] = useState<AutomationRunItem[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [selectedRun, setSelectedRun] = useState<AutomationRunItem | null>(null);
  const [retryingRunId, setRetryingRunId] = useState<string | null>(null);

  const loadInitialData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const [autos, projs] = await Promise.all([
        api.automations.list(),
        api.projects.list(),
      ]);
      setAutomations(autos);
      setProjects(projs);
      if (projs.length > 0 && !formProjectId) {
        setFormProjectId(projs[0].id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Không thể tải dữ liệu.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Fetch files whenever formProjectId changes
  useEffect(() => {
    if (!formProjectId) return;
    api.files.listByProject(formProjectId)
      .then((files) => setProjectFiles(files || []))
      .catch(() => setProjectFiles([]));
  }, [formProjectId]);

  // Actions
  const handleTrigger = async (id: string) => {
    setTriggeringId(id);
    setErrorMsg(null);
    try {
      const res = await api.automations.trigger(id);
      if (res.error) {
        setErrorMsg(res.error);
      } else {
        setSuccessMsg(`Đã chạy xong tự động hóa! Báo cáo "${res.report_title || ''}" và các tệp xuất bản đã sẵn sàng.`);
        setTimeout(() => setSuccessMsg(null), 5000);
      }
      await loadInitialData();
    } catch (err: any) {
      setErrorMsg(err.message || "Lỗi khi chạy automation.");
    } finally {
      setTriggeringId(null);
    }
  };

  const handleToggleActive = async (auto: AutomationItem) => {
    setErrorMsg(null);
    try {
      if (auto.is_active) {
        await api.automations.pause(auto.id);
        setSuccessMsg(`Đã tạm dừng lịch trình của "${auto.name}".`);
      } else {
        await api.automations.resume(auto.id);
        setSuccessMsg(`Đã kích hoạt lại lịch trình của "${auto.name}".`);
      }
      setTimeout(() => setSuccessMsg(null), 4000);
      await loadInitialData();
    } catch (err: any) {
      setErrorMsg(err.message || "Không thể thay đổi trạng thái.");
    }
  };

  const handleDelete = async (auto: AutomationItem) => {
    if (!confirm(`Bạn có chắc chắn muốn xóa Automation "${auto.name}" cùng toàn bộ lịch sử chạy?`)) {
      return;
    }
    setErrorMsg(null);
    try {
      await api.automations.delete(auto.id);
      setSuccessMsg(`Đã xóa thành công "${auto.name}".`);
      setTimeout(() => setSuccessMsg(null), 4000);
      await loadInitialData();
    } catch (err: any) {
      setErrorMsg(err.message || "Không thể xóa automation.");
    }
  };

  const handleOpenCreateModal = () => {
    setEditingAutomationId(null);
    setWizardStep(1);
    setFormName("");
    setFormDescription("");
    setFormSourceType("file");
    setFormDataSourceId("");
    setFormSheetName("");
    setFormAnalysisMode("comprehensive");
    setFormAnalysisPrompt("");
    setFormTitlePattern("Báo cáo Tự động {date}");
    setFormExportDocx(true);
    setFormExportPdf(true);
    setFormTriggerType("schedule");
    setFormCronExpression("0 8 * * 1");
    setFormCustomCron("");
    setFormIsActive(true);
    if (projects.length > 0) {
      setFormProjectId(projects[0].id);
    }
    setIsWizardOpen(true);
  };

  const handleOpenEditModal = (auto: AutomationItem) => {
    setEditingAutomationId(auto.id);
    setWizardStep(1);
    setFormProjectId(auto.project_id);
    setFormName(auto.name);
    setFormDescription(auto.description || "");
    setFormSourceType(auto.source_type || "file");
    setFormDataSourceId(auto.data_source_id || "");
    setFormSheetName((auto.source_config && auto.source_config.sheet_name) || "");
    setFormAnalysisMode(auto.analysis_mode || "comprehensive");
    setFormAnalysisPrompt(auto.analysis_prompt || "");
    setFormTitlePattern(auto.report_title_pattern || "Báo cáo Tự động {date}");
    setFormExportDocx((auto.export_formats || []).includes("docx"));
    setFormExportPdf((auto.export_formats || []).includes("pdf"));
    setFormTriggerType(auto.trigger_type || "schedule");
    setFormCronExpression(auto.cron_expression || "0 8 * * 1");
    setFormCustomCron(auto.cron_expression || "");
    setFormTimezone(auto.timezone || "Asia/Ho_Chi_Minh");
    setFormIsActive(auto.is_active);
    setIsWizardOpen(true);
  };

  const handleSaveWizard = async () => {
    if (!formName.trim()) {
      setErrorMsg("Vui lòng nhập tên Automation.");
      return;
    }
    if (!formProjectId) {
      setErrorMsg("Vui lòng chọn một dự án liên kết.");
      return;
    }

    const formats = [];
    if (formExportDocx) formats.push("docx");
    if (formExportPdf) formats.push("pdf");
    if (formats.length === 0) formats.push("docx");

    const cronExpr = formCustomCron.trim() || formCronExpression;

    const payload = {
      project_id: formProjectId,
      name: formName.trim(),
      description: formDescription.trim() || undefined,
      trigger_type: formTriggerType,
      cron_expression: formTriggerType === "schedule" ? cronExpr : undefined,
      timezone: formTimezone,
      data_source_id: formDataSourceId || undefined,
      source_type: formSourceType,
      source_config: formSheetName.trim() ? { sheet_name: formSheetName.trim() } : {},
      analysis_prompt: formAnalysisPrompt.trim() || undefined,
      analysis_mode: formAnalysisMode,
      report_title_pattern: formTitlePattern.trim() || "Báo cáo Tự động {date}",
      export_formats: formats,
      is_active: formIsActive,
    };

    setSavingWizard(true);
    setErrorMsg(null);
    try {
      if (editingAutomationId) {
        await api.automations.update(editingAutomationId, payload);
        setSuccessMsg(`Đã cập nhật cấu hình "${formName}" thành công.`);
      } else {
        await api.automations.create(payload);
        setSuccessMsg(`Đã khởi tạo Automation "${formName}" thành công.`);
      }
      setIsWizardOpen(false);
      setTimeout(() => setSuccessMsg(null), 4000);
      await loadInitialData();
    } catch (err: any) {
      setErrorMsg(err.message || "Lỗi khi lưu cấu hình automation.");
    } finally {
      setSavingWizard(false);
    }
  };

  // History modal handlers
  const handleOpenHistory = async (auto: AutomationItem) => {
    setSelectedAutoForHistory(auto);
    setLoadingRuns(true);
    try {
      const runs = await api.automations.runs(auto.id);
      setRunsList(runs || []);
      setSelectedRun(runs && runs.length > 0 ? runs[0] : null);
    } catch (err: any) {
      setErrorMsg("Không thể tải lịch sử chạy.");
    } finally {
      setLoadingRuns(false);
    }
  };

  const handleRetryRun = async (runId: string) => {
    setRetryingRunId(runId);
    setErrorMsg(null);
    try {
      const res = await api.automations.retryRun(runId);
      if (res.error) {
        setErrorMsg(res.error);
      } else {
        setSuccessMsg("Đã chạy lại thành công!");
      }
      if (selectedAutoForHistory) {
        const runs = await api.automations.runs(selectedAutoForHistory.id);
        setRunsList(runs || []);
        const updated = runs.find((r: any) => r.id === runId) || runs[0];
        setSelectedRun(updated);
      }
      await loadInitialData();
    } catch (err: any) {
      setErrorMsg(err.message || "Lỗi khi thử lại run.");
    } finally {
      setRetryingRunId(null);
    }
  };

  // Filtered list
  const filteredAutomations = useMemo(() => {
    return automations.filter((a) => {
      const matchesSearch =
        a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (a.description || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (a.project_name || "").toLowerCase().includes(searchQuery.toLowerCase());
      const matchesTrigger =
        filterTrigger === "all" ||
        (filterTrigger === "schedule" && a.trigger_type === "schedule") ||
        (filterTrigger === "manual" && a.trigger_type === "manual");
      const matchesStatus =
        filterStatus === "all" ||
        (filterStatus === "active" && a.is_active) ||
        (filterStatus === "paused" && !a.is_active);
      return matchesSearch && matchesTrigger && matchesStatus;
    });
  }, [automations, searchQuery, filterTrigger, filterStatus]);

  // Summary Metrics
  const stats = useMemo(() => {
    const total = automations.length;
    const active = automations.filter((a) => a.is_active).length;
    const scheduled = automations.filter((a) => a.trigger_type === "schedule").length;
    const nextDue = automations
      .filter((a) => a.is_active && a.next_run_at)
      .sort((a, b) => new Date(a.next_run_at!).getTime() - new Date(b.next_run_at!).getTime())[0];
    return { total, active, scheduled, nextDue };
  }, [automations]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Tự Động Hóa Báo Cáo (Report Automations Engine)
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700 uppercase">
              Production Ready
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Hệ thống lập lịch định kỳ, nạp dữ liệu Excel/CSV thật, phân tích số liệu chính xác và tự động xuất Word & PDF.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadInitialData}
            disabled={loading}
            className="p-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600 transition-colors"
            title="Làm mới dữ liệu"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={handleOpenCreateModal}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-indigo-700 transition-all hover:shadow-md"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo Automation Mới</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between shadow-xs animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 hover:text-emerald-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between shadow-xs animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
            <span className="font-medium">{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-rose-500 hover:text-rose-700">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-medium">
            <span>Tổng Automation</span>
            <Layers className="h-4 w-4 text-indigo-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{stats.total}</p>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Đã lưu trữ trong hệ thống</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-medium">
            <span>Đang Hoạt Động</span>
            <Activity className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-emerald-600 mt-2">{stats.active}</p>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Sẵn sàng kích hoạt</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-medium">
            <span>Theo Lịch Trình (Cron)</span>
            <Clock className="h-4 w-4 text-sky-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{stats.scheduled}</p>
          <span className="text-[10px] text-slate-400 mt-0.5 block">Chạy nền không cần mở web</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-[11px] font-medium">
            <span>Lần Chạy Kế Tiếp</span>
            <Calendar className="h-4 w-4 text-amber-500" />
          </div>
          <p className="text-xs font-bold text-slate-800 mt-2.5 truncate">
            {stats.nextDue && stats.nextDue.next_run_at
              ? new Date(stats.nextDue.next_run_at).toLocaleString("vi-VN", {
                  hour: "2-digit",
                  minute: "2-digit",
                  day: "2-digit",
                  month: "2-digit",
                })
              : "Chưa có lịch"}
          </p>
          <span className="text-[10px] text-slate-400 mt-1 block truncate">
            {stats.nextDue ? stats.nextDue.name : "Tất cả ở chế độ thủ công"}
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-3 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-xs">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm automation theo tên, mô tả hoặc tên dự án..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500 transition-all"
          />
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1 text-xs text-slate-600">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={filterTrigger}
              onChange={(e) => setFilterTrigger(e.target.value)}
              className="bg-transparent text-xs focus:outline-hidden"
            >
              <option value="all">Tất cả kiểu chạy</option>
              <option value="schedule">Theo lịch trình</option>
              <option value="manual">Chạy thủ công</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1 text-xs text-slate-600">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-transparent text-xs focus:outline-hidden"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="active">Đang hoạt động</option>
              <option value="paused">Đang tạm dừng</option>
            </select>
          </div>
        </div>
      </div>

      {/* Automations Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-48 rounded-2xl bg-white border border-slate-200 p-5 animate-pulse space-y-3">
              <div className="h-4 w-1/3 bg-slate-100 rounded-md" />
              <div className="h-6 w-2/3 bg-slate-100 rounded-md" />
              <div className="h-10 bg-slate-100 rounded-md" />
            </div>
          ))}
        </div>
      ) : filteredAutomations.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-xs">
          <Sparkles className="mx-auto h-10 w-10 text-indigo-400" />
          <h3 className="mt-3 text-sm font-bold text-slate-900">Không tìm thấy Automation phù hợp</h3>
          <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
            {searchQuery || filterTrigger !== "all" || filterStatus !== "all"
              ? "Hãy thử điều chỉnh lại bộ lọc hoặc từ khóa tìm kiếm."
              : "Khởi tạo Automation đầu tiên để thiết lập chu kỳ tự động phân tích dữ liệu và xuất báo cáo Word/PDF."}
          </p>
          <button
            onClick={handleOpenCreateModal}
            className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            <span>Tạo Automation</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredAutomations.map((a) => {
            const isTriggering = triggeringId === a.id;
            return (
              <div
                key={a.id}
                className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 hover:shadow-md transition-all flex flex-col justify-between space-y-4 text-xs"
              >
                <div className="space-y-3">
                  {/* Top Bar Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 font-bold text-[10px] uppercase flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>{a.trigger_type === "schedule" ? "Lịch Trình" : "Thủ Công"}</span>
                      </span>
                      {a.project_name && (
                        <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium text-[10px] truncate max-w-[140px]">
                          📁 {a.project_name}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleToggleActive(a)}
                      className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] transition-colors ${
                        a.is_active
                          ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                          : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                      }`}
                      title="Bấm để Tạm dừng / Tiếp tục"
                    >
                      {a.is_active ? "● Đang hoạt động" : "○ Đã tạm dừng"}
                    </button>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                      {a.name}
                    </h3>
                    <p className="text-slate-500 text-xs mt-1 line-clamp-2 leading-relaxed">
                      {a.description || "Tự động phân tích số liệu bảng tính và xuất báo cáo chuyên đề."}
                    </p>
                  </div>

                  {/* Settings Highlights */}
                  <div className="bg-slate-50 rounded-xl p-3 space-y-1.5 text-[11px] text-slate-600 border border-slate-100">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Lịch thực thi:</span>
                      <span className="font-mono font-medium text-slate-700">
                        {a.cron_expression || "Thủ công khi có yêu cầu"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Định dạng xuất:</span>
                      <div className="flex items-center gap-1 font-bold">
                        {(a.export_formats || ["docx"]).map((f) => (
                          <span
                            key={f}
                            className="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px] text-indigo-700 uppercase"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                    {a.next_run_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Lần chạy tới:</span>
                        <span className="text-emerald-700 font-medium">
                          {new Date(a.next_run_at).toLocaleString("vi-VN")}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom Card Actions */}
                <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                  <span className="text-[11px] text-slate-400 truncate">
                    {a.last_run_at
                      ? `Chạy gần nhất: ${new Date(a.last_run_at).toLocaleString("vi-VN")}`
                      : "Chưa từng thực thi"}
                  </span>

                  <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-auto">
                    <button
                      onClick={() => handleOpenHistory(a)}
                      className="px-2.5 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl font-medium transition-colors"
                      title="Xem nhật ký và lịch sử thực thi"
                    >
                      Chi tiết
                    </button>

                    <button
                      onClick={() => handleOpenEditModal(a)}
                      className="p-1.5 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-xl transition-colors"
                      title="Chỉnh sửa cấu hình"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>

                    <button
                      onClick={() => handleDelete(a)}
                      className="p-1.5 border border-slate-200 hover:bg-rose-50 text-rose-600 rounded-xl transition-colors"
                      title="Xóa Automation"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>

                    <button
                      onClick={() => handleTrigger(a.id)}
                      disabled={isTriggering}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-xs transition-all disabled:opacity-50"
                    >
                      {isTriggering ? (
                        <>
                          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          <span>Đang chạy...</span>
                        </>
                      ) : (
                        <>
                          <Play className="h-3.5 w-3.5 fill-current" />
                          <span>Chạy ngay</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MULTI-STEP CREATION & EDIT WIZARD MODAL */}
      {/* ========================================================================= */}
      {isWizardOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col my-8 animate-in fade-in zoom-in-95">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  {editingAutomationId ? "Chỉnh sửa Cấu hình Automation" : "Khởi tạo Report Automation Mới"}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">Bước {wizardStep} trên 5: Cấu hình động cơ báo cáo tự động</p>
              </div>
              <button
                onClick={() => setIsWizardOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Stepper Progress Indicator */}
            <div className="px-6 py-3 border-b border-slate-100 flex items-center justify-between bg-white text-[11px]">
              {[
                { step: 1, label: "Thông tin & Dự án" },
                { step: 2, label: "Nguồn dữ liệu" },
                { step: 3, label: "Chế độ AI" },
                { step: 4, label: "Mẫu & Xuất bản" },
                { step: 5, label: "Lịch trình" },
              ].map((s) => {
                const isActive = wizardStep === s.step;
                const isPassed = wizardStep > s.step;
                return (
                  <div key={s.step} className="flex items-center gap-1.5">
                    <div
                      className={`h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                        isPassed
                          ? "bg-emerald-600 text-white"
                          : isActive
                          ? "bg-indigo-600 text-white ring-2 ring-indigo-200"
                          : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      {isPassed ? <Check className="h-3 w-3" /> : s.step}
                    </div>
                    <span className={`hidden sm:inline ${isActive ? "font-bold text-slate-900" : "text-slate-500"}`}>
                      {s.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Modal Body: Steps */}
            <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
              {/* STEP 1: Thông tin chung & Dự án */}
              {wizardStep === 1 && (
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">
                      Chọn Dự án Liên kết <span className="text-rose-500">*</span>
                    </label>
                    <select
                      value={formProjectId}
                      onChange={(e) => setFormProjectId(e.target.value)}
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500"
                    >
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.type || "business_report"})
                        </option>
                      ))}
                    </select>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Báo cáo và các lần thực thi tự động sẽ được lưu trữ trực tiếp trong dự án này.
                    </p>
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">
                      Tên Automation <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      placeholder="Ví dụ: Tự động Báo cáo Quỹ lương Định kỳ"
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Mô tả / Mục đích</label>
                    <textarea
                      value={formDescription}
                      onChange={(e) => setFormDescription(e.target.value)}
                      rows={3}
                      placeholder="Mô tả tóm lược phạm vi và vai trò của automation này..."
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              )}

              {/* STEP 2: Nguồn Dữ liệu & Sheet Selection */}
              {wizardStep === 2 && (
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Loại Nguồn Dữ liệu</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setFormSourceType("file")}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          formSourceType === "file"
                            ? "border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold"
                            : "border-slate-200 bg-white hover:bg-slate-50 text-slate-600"
                        }`}
                      >
                        <FileSpreadsheet className="h-4 w-4 mb-1 text-indigo-600" />
                        <div>Tệp Bảng tính / Tài liệu</div>
                        <div className="text-[10px] font-normal text-slate-500">Excel, CSV, PDF đã nạp vào dự án</div>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setFormSourceType("all_project_files");
                          setFormDataSourceId("");
                        }}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          formSourceType === "all_project_files"
                            ? "border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold"
                            : "border-slate-200 bg-white hover:bg-slate-50 text-slate-600"
                        }`}
                      >
                        <Layers className="h-4 w-4 mb-1 text-sky-600" />
                        <div>Toàn bộ Tài liệu Dự án</div>
                        <div className="text-[10px] font-normal text-slate-500">Tự động chọn file mới nhất</div>
                      </button>
                    </div>
                  </div>

                  {formSourceType === "file" && (
                    <div>
                      <label className="block font-bold text-slate-700 mb-1">Chọn Tệp Dữ liệu Cụ thể</label>
                      {projectFiles.length === 0 ? (
                        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-[11px]">
                          Dự án này chưa có tệp tải lên nào. Bạn có thể chọn &quot;Toàn bộ Tài liệu Dự án&quot; hoặc tải file vào dự án trước.
                        </div>
                      ) : (
                        <select
                          value={formDataSourceId}
                          onChange={(e) => setFormDataSourceId(e.target.value)}
                          className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500"
                        >
                          <option value="">-- Tự động chọn tệp bảng tính mới nhất trong dự án --</option>
                          {projectFiles.map((f) => (
                            <option key={f.id} value={f.id}>
                              {f.original_name || f.filename} ({f.file_type || "file"})
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  )}

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">
                      Tên Sheet trong file Excel (Tùy chọn)
                    </label>
                    <input
                      type="text"
                      value={formSheetName}
                      onChange={(e) => setFormSheetName(e.target.value)}
                      placeholder="Ví dụ: Bang_luong, Chi_phi (để trống sẽ tự chọn sheet đầu tiên)"
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">
                      Hệ thống sẽ chạy phân tích thống kê 100% dòng dữ liệu trên sheet này để tính Sum, Mean, Min, Max, Outliers.
                    </p>
                  </div>
                </div>
              )}

              {/* STEP 3: Chế độ AI & Prompt */}
              {wizardStep === 3 && (
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block font-bold text-slate-700 mb-2">Chế độ Phân tích Báo cáo</label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {ANALYSIS_MODES.map((mode) => (
                        <button
                          key={mode.id}
                          type="button"
                          onClick={() => setFormAnalysisMode(mode.id)}
                          className={`p-3 rounded-xl border text-left transition-all ${
                            formAnalysisMode === mode.id
                              ? "border-indigo-600 bg-indigo-50/60 ring-1 ring-indigo-400 shadow-xs"
                              : "border-slate-200 bg-white hover:bg-slate-50"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-900">{mode.title}</span>
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                              {mode.badge}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-1">{mode.desc}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">
                      Chỉ đạo / Hướng dẫn Bổ sung cho AI (Prompt)
                    </label>
                    <textarea
                      value={formAnalysisPrompt}
                      onChange={(e) => setFormAnalysisPrompt(e.target.value)}
                      rows={3}
                      placeholder="Ví dụ: Nhấn mạnh vào tổng chi phí nhân sự, phân loại top 5 nhân viên có lương cao nhất và đề xuất giải pháp kiểm soát ngân sách..."
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">
                      AI sẽ dựa trên các con số thật đã tính bằng Pandas Engine và hướng dẫn của bạn để viết diễn giải sắc bén.
                    </p>
                  </div>
                </div>
              )}

              {/* STEP 4: Mẫu & Định dạng Xuất bản */}
              {wizardStep === 4 && (
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">
                      Quy tắc Đặt tên Báo cáo (Title Pattern) <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formTitlePattern}
                      onChange={(e) => setFormTitlePattern(e.target.value)}
                      placeholder="Báo cáo Tự động {date}"
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 font-mono"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">
                      Hỗ trợ placeholder: <code className="text-indigo-600 font-bold">&#123;date&#125;</code> (ngày thực thi),{" "}
                      <code className="text-indigo-600 font-bold">&#123;time&#125;</code> (giờ),{" "}
                      <code className="text-indigo-600 font-bold">&#123;project&#125;</code> (tên dự án).
                    </p>
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-2">Định dạng Xuất bản Tự động</label>
                    <div className="grid grid-cols-2 gap-3">
                      <label className="flex items-center gap-3 p-3 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formExportDocx}
                          onChange={(e) => setFormExportDocx(e.target.checked)}
                          className="h-4 w-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
                        />
                        <div>
                          <div className="font-bold text-slate-800">Microsoft Word (.docx)</div>
                          <div className="text-[10px] text-slate-500">Chuẩn A4, Heading, Bảng biểu & TOC</div>
                        </div>
                      </label>

                      <label className="flex items-center gap-3 p-3 border border-slate-200 rounded-xl bg-white hover:bg-slate-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formExportPdf}
                          onChange={(e) => setFormExportPdf(e.target.checked)}
                          className="h-4 w-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
                        />
                        <div>
                          <div className="font-bold text-slate-800">Tài liệu In ấn (.pdf)</div>
                          <div className="text-[10px] text-slate-500">Bản in tĩnh, phân trang chuẩn mực</div>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 5: Lịch trình & Múi giờ */}
              {wizardStep === 5 && (
                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Cơ chế Kích hoạt (Trigger)</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setFormTriggerType("schedule")}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          formTriggerType === "schedule"
                            ? "border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold"
                            : "border-slate-200 bg-white hover:bg-slate-50 text-slate-600"
                        }`}
                      >
                        <Clock className="h-4 w-4 mb-1 text-indigo-600" />
                        <div>Theo Lịch Trình (Schedule)</div>
                        <div className="text-[10px] font-normal text-slate-500">Tự động chạy định kỳ ở nền</div>
                      </button>

                      <button
                        type="button"
                        onClick={() => setFormTriggerType("manual")}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          formTriggerType === "manual"
                            ? "border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold"
                            : "border-slate-200 bg-white hover:bg-slate-50 text-slate-600"
                        }`}
                      >
                        <Play className="h-4 w-4 mb-1 text-emerald-600" />
                        <div>Thủ công (Manual Only)</div>
                        <div className="text-[10px] font-normal text-slate-500">Chỉ chạy khi bấm &quot;Chạy ngay&quot;</div>
                      </button>
                    </div>
                  </div>

                  {formTriggerType === "schedule" && (
                    <div className="space-y-3">
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">Chọn Tần suất Chu kỳ</label>
                        <select
                          value={formCronExpression}
                          onChange={(e) => {
                            setFormCronExpression(e.target.value);
                            setFormCustomCron("");
                          }}
                          className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500"
                        >
                          {SCHEDULE_PRESETS.filter((p) => p.type === "schedule").map((p) => (
                            <option key={p.cron} value={p.cron}>
                              {p.label} ({p.cron})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block font-bold text-slate-700 mb-1">
                          Hoặc Nhập Cron Expression Tùy Biến
                        </label>
                        <input
                          type="text"
                          value={formCustomCron}
                          onChange={(e) => setFormCustomCron(e.target.value)}
                          placeholder="Ví dụ: 0 9 * * 1-5 (9:00 từ Thứ 2 đến Thứ 6)"
                          className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 font-mono"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block font-bold text-slate-700 mb-1">Múi giờ</label>
                          <select
                            value={formTimezone}
                            onChange={(e) => setFormTimezone(e.target.value)}
                            className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                          >
                            <option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh (GMT+7)</option>
                            <option value="UTC">UTC (GMT+0)</option>
                          </select>
                        </div>

                        <div className="flex items-center pt-5">
                          <label className="flex items-center gap-2 cursor-pointer font-bold text-slate-800">
                            <input
                              type="checkbox"
                              checked={formIsActive}
                              onChange={(e) => setFormIsActive(e.target.checked)}
                              className="h-4 w-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
                            />
                            <span>Kích hoạt ngay</span>
                          </label>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer: Navigation */}
            <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between bg-slate-50/70">
              {wizardStep > 1 ? (
                <button
                  type="button"
                  onClick={() => setWizardStep((prev) => prev - 1)}
                  className="flex items-center gap-1.5 px-3.5 py-2 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold hover:bg-slate-100 transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span>Quay lại</span>
                </button>
              ) : (
                <div />
              )}

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsWizardOpen(false)}
                  className="px-3.5 py-2 text-slate-500 hover:text-slate-700 text-xs font-medium"
                >
                  Hủy bỏ
                </button>

                {wizardStep < 5 ? (
                  <button
                    type="button"
                    onClick={() => setWizardStep((prev) => prev + 1)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700 transition-colors shadow-xs"
                  >
                    <span>Tiếp theo</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSaveWizard}
                    disabled={savingWizard}
                    className="flex items-center gap-1.5 px-5 py-2 bg-emerald-600 text-white rounded-xl text-xs font-bold hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
                  >
                    {savingWizard ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        <span>Đang lưu...</span>
                      </>
                    ) : (
                      <>
                        <Check className="h-4 w-4" />
                        <span>{editingAutomationId ? "Cập nhật Automation" : "Khởi tạo Automation"}</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* RUN HISTORY & EXECUTION DETAIL MODAL */}
      {/* ========================================================================= */}
      {selectedAutoForHistory && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-4xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col my-6 animate-in fade-in zoom-in-95">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-slate-900">{selectedAutoForHistory.name}</h2>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-bold">
                    Lịch sử chạy
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Dự án: {selectedAutoForHistory.project_name || selectedAutoForHistory.project_id} · Tần suất:{" "}
                  {selectedAutoForHistory.cron_expression || "Thủ công"}
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedAutoForHistory(null);
                  setSelectedRun(null);
                }}
                className="p-1 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content: 2 Columns (Runs List & Run Details) */}
            <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-slate-100 max-h-[70vh] overflow-y-auto">
              {/* Column 1: Runs List */}
              <div className="p-4 space-y-2 bg-slate-50/30 overflow-y-auto">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Các phiên thực thi ({runsList.length})
                </div>

                {loadingRuns ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-14 rounded-xl bg-slate-100 animate-pulse" />
                    ))}
                  </div>
                ) : runsList.length === 0 ? (
                  <div className="text-center py-8 text-slate-400 text-xs">
                    Chưa có lịch sử chạy nào cho automation này.
                  </div>
                ) : (
                  runsList.map((r) => {
                    const isSelected = selectedRun && selectedRun.id === r.id;
                    const isSuccess = r.status === "completed";
                    const isFailed = r.status === "failed";
                    return (
                      <div
                        key={r.id}
                        onClick={() => setSelectedRun(r)}
                        className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                          isSelected
                            ? "bg-white border-indigo-500 shadow-xs ring-1 ring-indigo-200"
                            : "bg-white border-slate-200 hover:border-slate-300"
                        }`}
                      >
                        <div className="flex items-center justify-between text-[11px]">
                          <span
                            className={`font-bold px-1.5 py-0.5 rounded text-[10px] uppercase ${
                              isSuccess
                                ? "bg-emerald-100 text-emerald-800"
                                : isFailed
                                ? "bg-rose-100 text-rose-800"
                                : "bg-sky-100 text-sky-800"
                            }`}
                          >
                            {isSuccess ? "Hoàn thành" : isFailed ? "Thất bại" : "Đang chạy"}
                          </span>
                          <span className="text-slate-400 font-mono text-[10px]">
                            {r.duration_ms ? `${(r.duration_ms / 1000).toFixed(1)}s` : "--"}
                          </span>
                        </div>
                        <div className="mt-1.5 text-xs text-slate-800 font-medium truncate">
                          {new Date(r.started_at).toLocaleString("vi-VN")}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1">
                          <span>Nguồn: {r.trigger_source}</span>
                          {r.retry_count > 0 && <span>· Thử lại #{r.retry_count}</span>}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Column 2 & 3: Run Detail Viewer */}
              <div className="col-span-2 p-5 space-y-4 bg-white overflow-y-auto">
                {selectedRun ? (
                  <div className="space-y-4">
                    {/* Run Header Info */}
                    <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-900">Phiên #{selectedRun.id.slice(0, 8)}</span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              selectedRun.status === "completed"
                                ? "bg-emerald-100 text-emerald-800"
                                : selectedRun.status === "failed"
                                ? "bg-rose-100 text-rose-800"
                                : "bg-sky-100 text-sky-800"
                            }`}
                          >
                            {selectedRun.status === "completed" ? "Thành công 100%" : selectedRun.status}
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-400">
                          Bắt đầu: {new Date(selectedRun.started_at).toLocaleString("vi-VN")}
                          {selectedRun.finished_at && ` · Hoàn tất: ${new Date(selectedRun.finished_at).toLocaleString("vi-VN")}`}
                        </span>
                      </div>

                      {/* Actions for this run */}
                      <div className="flex items-center gap-2">
                        {selectedRun.status === "failed" && (
                          <button
                            onClick={() => handleRetryRun(selectedRun.id)}
                            disabled={retryingRunId === selectedRun.id}
                            className="flex items-center gap-1 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition-colors disabled:opacity-50"
                          >
                            <RotateCcw className={`h-3.5 w-3.5 ${retryingRunId === selectedRun.id ? "animate-spin" : ""}`} />
                            <span>Thử lại (Retry)</span>
                          </button>
                        )}
                        {selectedRun.report_id && (
                          <Link
                            href={`/reports/${selectedRun.report_id}`}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-colors shadow-xs"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                            <span>Mở Báo Cáo</span>
                          </Link>
                        )}
                      </div>
                    </div>

                    {/* Output Exports Download Buttons */}
                    {selectedRun.output_files && selectedRun.output_files.length > 0 && (
                      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-2">
                        <div className="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                          <Download className="h-3.5 w-3.5 text-indigo-600" />
                          <span>Tài liệu Kết xuất Đã sẵn sàng:</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {selectedRun.output_files.map((file: any, idx: number) => (
                            <a
                              key={idx}
                              href={file.download_url}
                              download
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-bold text-slate-800 hover:border-indigo-500 hover:text-indigo-600 shadow-xs transition-all"
                            >
                              <FileText className="h-3.5 w-3.5 text-indigo-600" />
                              <span>{file.name || file.filename}</span>
                              <span className="text-[10px] text-slate-400 font-normal">
                                ({Math.round((file.file_size || 0) / 1024)} KB)
                              </span>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Source Snapshot Card */}
                    {selectedRun.source_snapshot && Object.keys(selectedRun.source_snapshot).length > 0 && (
                      <div className="bg-white border border-slate-200 rounded-xl p-3 text-xs space-y-1.5">
                        <div className="text-[11px] font-bold text-slate-700 flex items-center gap-1.5">
                          <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />
                          <span>Thông tin Nguồn dữ liệu đã nạp:</span>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1">
                          <div className="bg-slate-50 p-2 rounded-lg">
                            <span className="text-slate-400 block text-[10px]">Tệp nguồn</span>
                            <span className="font-bold text-slate-800 truncate block">
                              {selectedRun.source_snapshot.file_name || "Dự án"}
                            </span>
                          </div>
                          {selectedRun.source_snapshot.sheet_name && (
                            <div className="bg-slate-50 p-2 rounded-lg">
                              <span className="text-slate-400 block text-[10px]">Sheet xử lý</span>
                              <span className="font-bold text-slate-800 truncate block">
                                {selectedRun.source_snapshot.sheet_name}
                              </span>
                            </div>
                          )}
                          {selectedRun.source_snapshot.total_rows !== undefined && (
                            <div className="bg-slate-50 p-2 rounded-lg">
                              <span className="text-slate-400 block text-[10px]">Tổng dòng</span>
                              <span className="font-bold text-emerald-700 block">
                                {selectedRun.source_snapshot.total_rows.toLocaleString()}
                              </span>
                            </div>
                          )}
                          {selectedRun.source_snapshot.total_columns !== undefined && (
                            <div className="bg-slate-50 p-2 rounded-lg">
                              <span className="text-slate-400 block text-[10px]">Tổng cột</span>
                              <span className="font-bold text-indigo-700 block">
                                {selectedRun.source_snapshot.total_columns}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Error Banner if Failed */}
                    {selectedRun.status === "failed" && (
                      <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-2">
                        <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                        <div>
                          <div className="font-bold">Lỗi xảy ra tại bước &apos;{selectedRun.failed_step || "hệ thống"}&apos;:</div>
                          <p className="mt-0.5 text-[11px] font-mono">{selectedRun.error_message}</p>
                        </div>
                      </div>
                    )}

                    {/* Terminal Log Console */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] text-slate-600">
                        <span className="font-bold flex items-center gap-1">
                          <Terminal className="h-3.5 w-3.5 text-slate-500" />
                          <span>Nhật ký Tiến trình Chi tiết (Live Execution Logs)</span>
                        </span>
                        <span className="text-slate-400">{selectedRun.logs.length} sự kiện</span>
                      </div>
                      <div className="bg-slate-900 text-slate-200 p-3 rounded-xl font-mono text-[11px] leading-relaxed max-h-56 overflow-y-auto space-y-1 select-text">
                        {selectedRun.logs.map((log: string, idx: number) => (
                          <div
                            key={idx}
                            className={`break-all ${
                              log.includes("[LỖI") || log.includes("FAILED")
                                ? "text-rose-400 font-bold"
                                : log.includes("Hoàn tất") || log.includes("thành công")
                                ? "text-emerald-400"
                                : log.includes("Bước")
                                ? "text-sky-300 font-semibold"
                                : "text-slate-300"
                            }`}
                          >
                            {log}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-400 text-xs">
                    Chọn một phiên thực thi từ danh sách bên trái để xem nhật ký chi tiết và tải tệp kết xuất.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
