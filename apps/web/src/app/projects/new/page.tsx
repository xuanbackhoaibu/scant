"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Briefcase,
  TrendingUp,
  Search,
  FileCode,
  FileSpreadsheet,
  DollarSign,
  PieChart,
  FileText,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Plus,
  Trash2,
  Upload,
  Layers,
  Building,
  Wand2,
  Play,
  Pause,
  RotateCcw,
  XCircle,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";

interface CustomFieldItem {
  key: string;
  label: string;
  type: string;
  required: boolean;
  value: any;
  unit?: string;
}

interface OutlineItemUI {
  title: string;
  level: number;
  position: number;
  section_number?: string;
  description?: string;
  children: OutlineItemUI[];
}

const PROJECT_TYPE_CARDS = [
  { id: "business_report", name: "Business Report", desc: "Chiến lược, kế hoạch kinh doanh, phân tích hoạt động", icon: Briefcase, color: "text-blue-600 bg-blue-50" },
  { id: "data_analysis", name: "Data Analysis", desc: "Phân tích số liệu, KPI, đối soát và trực quan hóa", icon: TrendingUp, color: "text-emerald-600 bg-emerald-50" },
  { id: "research", name: "Research Report", desc: "Nghiên cứu thị trường, khoa học, phân tích chuyên sâu", icon: Search, color: "text-indigo-600 bg-indigo-50" },
  { id: "technical", name: "Technical Documentation", desc: "Kiến trúc hệ thống, API, đặc tả sản phẩm phần mềm", icon: FileCode, color: "text-violet-600 bg-violet-50" },
  { id: "proposal", name: "Proposal & RFP", desc: "Hồ sơ đề xuất dự án, chào thầu, dự toán ngân sách", icon: FileSpreadsheet, color: "text-amber-600 bg-amber-50" },
  { id: "financial", name: "Financial Report", desc: "Báo cáo tài chính, dòng tiền, dự báo doanh thu", icon: DollarSign, color: "text-teal-600 bg-teal-50" },
  { id: "market_research", name: "Market Research", desc: "Khảo sát thị trường, đối thủ cạnh tranh & khách hàng", icon: PieChart, color: "text-rose-600 bg-rose-50" },
  { id: "custom", name: "Custom Document", desc: "Tài liệu tùy chỉnh linh hoạt cho mọi nhu cầu", icon: FileText, color: "text-slate-600 bg-slate-50" },
];

function UniversalProjectWizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialType = searchParams.get("type") || "business_report";
  const initialPrompt = searchParams.get("prompt") || "";

  // Mode Selection: "auto" vs "advanced"
  const [mode, setMode] = useState<"auto" | "advanced">("auto");

  // AUTO CREATE STATE
  const [autoPrompt, setAutoPrompt] = useState(
    initialPrompt || "Phân tích thị trường xe điện Việt Nam năm 2026 và đề xuất chiến lược thâm nhập thị trường cho dòng xe điện phân khúc phổ thông."
  );
  const [autoFiles, setAutoFiles] = useState<File[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<number>(0);
  const [jobStatusMsg, setJobStatusMsg] = useState<string>("");
  const [jobStatus, setJobStatus] = useState<string>("");
  const [createdReportId, setCreatedReportId] = useState<string | null>(null);
  const [isAutoSubmitting, setIsAutoSubmitting] = useState(false);

  // ADVANCED WIZARD STATE
  const [step, setStep] = useState(1);
  const [projectType, setProjectType] = useState(initialType);
  const [isAnalyzingIntent, setIsAnalyzingIntent] = useState(false);
  const [topicName, setTopicName] = useState("Báo cáo Chiến lược Doanh nghiệp 2026");
  const [description, setDescription] = useState("Báo cáo phân tích thực trạng và xây dựng chiến lược phát triển tối ưu.");
  const [audience, setAudience] = useState("Hội đồng Quản trị & Ban Điều hành");
  const [customFields, setCustomFields] = useState<CustomFieldItem[]>([
    { key: "company_name", label: "Tên Doanh nghiệp", type: "text", required: true, value: "VinFast Auto" },
    { key: "department", label: "Phòng ban phụ trách", type: "text", required: false, value: "Khối Chiến lược" },
    { key: "lead_author", label: "Người lập báo cáo", type: "text", required: true, value: "Alex Nguyen" },
  ]);
  const [selectedTemplate, setSelectedTemplate] = useState("tpl_corp_standard");
  const [knowledgeFiles, setKnowledgeFiles] = useState<File[]>([]);
  const [isGeneratingOutline, setIsGeneratingOutline] = useState(false);
  const [projectUnderstanding, setProjectUnderstanding] = useState("");
  const [objectives, setObjectives] = useState<string[]>([]);
  const [outline, setOutline] = useState<OutlineItemUI[]>([]);
  const [isCreatingReport, setIsCreatingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Polling Job Status for Auto Mode
  useEffect(() => {
    if (!activeJobId) return;

    const interval = setInterval(async () => {
      try {
        const job = await api.reports.getJob(activeJobId);
        setJobProgress(job.progress_percent);
        setJobStatusMsg(job.status_message);
        setJobStatus(job.status);

        const repId = (job.metadata && job.metadata.report_id) || (job.payload && job.payload.report_id);
        if (repId && !createdReportId) {
          setCreatedReportId(repId);
        }

        if (job.status === "completed") {
          clearInterval(interval);
          if (repId) {
            setTimeout(() => router.push(`/reports/${repId}/editor`), 1200);
          }
        } else if (job.status === "failed" || job.status === "cancelled") {
          clearInterval(interval);
        }
      } catch {
        // ignore polling transient errors
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJobId, createdReportId, router]);

  // Handle One-Click Auto Report Submit
  const handleAutoCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!autoPrompt.trim()) return;
    setIsAutoSubmitting(true);
    setError(null);

    try {
      const fd = new FormData();
      fd.append("prompt", autoPrompt);
      for (const f of autoFiles) {
        fd.append("files", f);
      }

      const res = await api.reports.autoCreate(fd);
      setActiveJobId(res.job_id);
      setCreatedReportId(res.report_id);
      setJobStatus("running");
      setJobProgress(10);
      setJobStatusMsg("Đang khởi tạo quy trình One-Click Auto Report...");
    } catch (err: any) {
      setError(err.message || "Không thể khởi động One-Click Auto Report.");
    } finally {
      setIsAutoSubmitting(false);
    }
  };

  const handlePauseJob = async () => {
    if (!activeJobId) return;
    await api.reports.pauseJob(activeJobId);
    setJobStatus("paused");
  };

  const handleResumeJob = async () => {
    if (!activeJobId) return;
    await api.reports.resumeJob(activeJobId);
    setJobStatus("running");
  };

  const handleCancelJob = async () => {
    if (!activeJobId) return;
    await api.reports.cancelJob(activeJobId);
    setJobStatus("cancelled");
  };

  const handleRetryJob = async () => {
    if (!activeJobId) return;
    await api.reports.retryJob(activeJobId);
    setJobStatus("running");
    setJobProgress(10);
  };

  // ADVANCED MODE HANDLERS
  const handleAnalyzeIntent = async () => {
    if (!autoPrompt.trim()) return;
    setIsAnalyzingIntent(true);
    setError(null);
    try {
      const res = await api.ai.analyzeIntent({
        user_prompt: autoPrompt,
        selected_type: projectType,
      });

      setTopicName(res.suggested_title);
      setProjectType(res.suggested_type);
      setAudience(res.target_audience);
      setDescription(res.objective);
      if (res.suggested_custom_fields && res.suggested_custom_fields.length > 0) {
        setCustomFields(
          res.suggested_custom_fields.map((f: any) => ({
            key: f.key,
            label: f.label,
            type: f.type || "text",
            required: !!f.required,
            value: f.value || "",
            unit: f.unit,
          }))
        );
      }
    } catch (err: any) {
      setError(err.message || "Không thể phân tích ý tưởng.");
    } finally {
      setIsAnalyzingIntent(false);
    }
  };

  const handleGenerateOutline = async () => {
    setIsGeneratingOutline(true);
    setError(null);
    try {
      const project = await api.projects.create({
        name: topicName,
        type: projectType,
        description,
        metadata: {
          document_type: projectType,
          document_profile: projectType,
          audience,
          custom_fields: customFields,
        },
      });

      for (const file of knowledgeFiles) {
        const fd = new FormData();
        fd.append("project_id", project.id);
        fd.append("document_type", "reference");
        fd.append("file", file);
        await api.files.upload(fd);
      }

      const outlineRes = await api.ai.generateOutline({
        project_id: project.id,
        topic_name: topicName,
        project_type: projectType,
        topic_description: description,
        audience,
        target_chapters_count: 5,
      });

      setProjectUnderstanding(outlineRes.project_understanding);
      setObjectives(outlineRes.objectives);
      setOutline(outlineRes.outline);
      (window as any).__created_project_id = project.id;
      setStep(4);
    } catch (err: any) {
      setError(err.message || "Lỗi khi sinh đề cương.");
    } finally {
      setIsGeneratingOutline(false);
    }
  };

  const handleCreateAndOpenStudio = async () => {
    setIsCreatingReport(true);
    setError(null);
    try {
      const projectId = (window as any).__created_project_id;
      if (!projectId) throw new Error("Missing Project ID");

      const reportRes = await api.reports.create({
        project_id: projectId,
        title: topicName,
        report_type: projectType,
        outline: outline,
      });

      router.push(`/reports/${reportRes.id}/editor`);
    } catch (err: any) {
      setError(err.message || "Không thể tạo báo cáo.");
      setIsCreatingReport(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      {/* Header & Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Khởi Tạo Báo Cáo & Tài Liệu Thông Minh</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Lựa chọn chế độ tạo tự động bằng AI (One-Click) hoặc tùy chỉnh từng bước chi tiết (Advanced)
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="flex bg-slate-100 p-1 rounded-xl self-start sm:self-auto border border-slate-200">
          <button
            onClick={() => { setMode("auto"); setActiveJobId(null); }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              mode === "auto" ? "bg-white text-indigo-600 shadow-xs" : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Auto Create (One-Click)</span>
          </button>
          <button
            onClick={() => { setMode("advanced"); setStep(1); }}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              mode === "advanced" ? "bg-white text-indigo-600 shadow-xs" : "text-slate-500 hover:text-slate-900"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Tùy chỉnh (Advanced)</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* MODE 1: ONE-CLICK AUTO REPORT */}
      {mode === "auto" && (
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xs space-y-6">
          {!activeJobId ? (
            <form onSubmit={handleAutoCreateSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Wand2 className="h-4 w-4 text-indigo-600" />
                  <span>Bạn muốn tạo báo cáo hoặc tài liệu gì?</span>
                </label>
                <textarea
                  rows={4}
                  value={autoPrompt}
                  onChange={(e) => setAutoPrompt(e.target.value)}
                  placeholder="Ví dụ: Báo cáo phân tích thị trường ô tô điện Việt Nam 2026, đánh giá chính sách thuế, dung lượng trạm sạc và chiến lược giá..."
                  className="w-full p-4 text-xs bg-slate-50 border border-slate-200 rounded-2xl focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none leading-relaxed"
                />
              </div>

              {/* Optional Attachments */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700">Tài liệu tham khảo & Dataset đính kèm (Tùy chọn):</label>
                <div className="border-2 border-dashed border-slate-200 rounded-2xl p-6 text-center hover:bg-slate-50 transition-colors">
                  <Upload className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-xs font-bold text-slate-700">Kéo thả file PDF, DOCX, XLSX, CSV vào đây</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">AI sẽ tự động đọc hiểu và phân tích số liệu</p>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.docx,.xlsx,.csv,.txt"
                    onChange={(e) => {
                      if (e.target.files) setAutoFiles(Array.from(e.target.files));
                    }}
                    className="hidden"
                    id="auto-file-input"
                  />
                  <label
                    htmlFor="auto-file-input"
                    className="mt-3 inline-block px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold cursor-pointer transition-colors"
                  >
                    Chọn file
                  </label>
                </div>

                {autoFiles.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    {autoFiles.map((f, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg text-xs border border-slate-200">
                        <span className="font-medium text-slate-700 truncate max-w-sm">{f.name}</span>
                        <span className="text-slate-400">{(f.size / 1024).toFixed(1)} KB</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isAutoSubmitting || !autoPrompt.trim()}
                  className="w-full h-12 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isAutoSubmitting ? (
                    <>
                      <Sparkles className="h-4 w-4 animate-spin" />
                      <span>Đang khởi động Agentic Pipeline...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      <span>Khởi Tạo Báo Cáo Tự Động (One-Click)</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          ) : (
            /* REALTIME PIPELINE PROGRESS */
            <div className="space-y-6 py-4">
              <div className="text-center space-y-2">
                <div className="inline-flex p-3 rounded-2xl bg-indigo-50 text-indigo-600">
                  <Sparkles className="h-8 w-8 animate-spin" />
                </div>
                <h3 className="text-base font-bold text-slate-900">AI Đang Tự Động Xây Dựng Báo Cáo</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">{jobStatusMsg}</p>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>Tiến độ thực thi:</span>
                  <span className="text-indigo-600">{jobProgress}%</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                  <div
                    className="h-full bg-linear-to-r from-indigo-500 to-indigo-600 transition-all duration-500 rounded-full"
                    style={{ width: `${jobProgress}%` }}
                  />
                </div>
              </div>

              {/* Control Actions: Pause, Resume, Cancel, Retry */}
              <div className="flex items-center justify-center gap-3 pt-2">
                {jobStatus === "running" && (
                  <button
                    onClick={handlePauseJob}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-colors"
                  >
                    <Pause className="h-3.5 w-3.5" />
                    <span>Tạm dừng</span>
                  </button>
                )}

                {jobStatus === "paused" && (
                  <button
                    onClick={handleResumeJob}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition-colors"
                  >
                    <Play className="h-3.5 w-3.5" />
                    <span>Tiếp tục</span>
                  </button>
                )}

                {jobStatus !== "completed" && jobStatus !== "cancelled" && (
                  <button
                    onClick={handleCancelJob}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-xs font-bold transition-colors"
                  >
                    <XCircle className="h-3.5 w-3.5" />
                    <span>Hủy bỏ</span>
                  </button>
                )}

                {(jobStatus === "failed" || jobStatus === "cancelled") && (
                  <button
                    onClick={handleRetryJob}
                    className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition-colors"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Thực hiện lại (Retry)</span>
                  </button>
                )}

                {createdReportId && (
                  <button
                    onClick={() => router.push(`/reports/${createdReportId}/editor`)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-colors"
                  >
                    <span>Mở trực tiếp trong Studio</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* MODE 2: ADVANCED STEP-BY-STEP */}
      {mode === "advanced" && (
        <div className="space-y-6">
          {step === 1 && (
            <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-bold text-slate-900">Mục tiêu tài liệu:</label>
                  <button
                    onClick={handleAnalyzeIntent}
                    disabled={isAnalyzingIntent}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>{isAnalyzingIntent ? "Đang phân tích..." : "AI Tự Động Phân Tích"}</span>
                  </button>
                </div>
                <textarea
                  rows={3}
                  value={autoPrompt}
                  onChange={(e) => setAutoPrompt(e.target.value)}
                  className="w-full p-3 text-xs bg-slate-50 border border-slate-200 rounded-xl outline-none"
                />
              </div>

              {/* Quick Categories */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {PROJECT_TYPE_CARDS.map((card) => {
                  const Icon = card.icon;
                  return (
                    <div
                      key={card.id}
                      onClick={() => setProjectType(card.id)}
                      className={`p-3 rounded-xl border cursor-pointer ${
                        projectType === card.id ? "border-indigo-600 bg-indigo-50/60" : "border-slate-200"
                      }`}
                    >
                      <Icon className="h-4 w-4 text-indigo-600 mb-1.5" />
                      <h4 className="text-xs font-bold text-slate-900">{card.name}</h4>
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-100">
                <button
                  onClick={() => setStep(2)}
                  className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
                >
                  <span>Tiếp tục: Mẫu Template</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900">Bước 2: Chọn Mẫu Định Dạng</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[
                  { id: "tpl_corp_standard", name: "Executive Business Report" },
                  { id: "tpl_technical_doc", name: "Technical Whitepaper" },
                  { id: "tpl_financial_kpi", name: "Financial & KPI Summary" },
                ].map((tpl) => (
                  <div
                    key={tpl.id}
                    onClick={() => setSelectedTemplate(tpl.id)}
                    className={`p-4 rounded-xl border cursor-pointer ${
                      selectedTemplate === tpl.id ? "border-indigo-600 bg-indigo-50/50" : "border-slate-200"
                    }`}
                  >
                    <h4 className="text-xs font-bold text-slate-900">{tpl.name}</h4>
                  </div>
                ))}
              </div>
              <div className="flex justify-between pt-4 border-t border-slate-100">
                <button onClick={() => setStep(1)} className="px-4 py-2 text-xs text-slate-600">Quay lại</button>
                <button onClick={() => setStep(3)} className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold">Tiếp tục: Tri thức</button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900">Bước 3: Tải Lên Tri Thức & Dữ Liệu</h2>
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center">
                <Upload className="h-8 w-8 text-indigo-600 mx-auto mb-2" />
                <input
                  type="file"
                  multiple
                  onChange={(e) => e.target.files && setKnowledgeFiles(Array.from(e.target.files))}
                  className="hidden"
                  id="adv-file-in"
                />
                <label htmlFor="adv-file-in" className="px-4 py-2 bg-slate-100 rounded-lg text-xs font-semibold cursor-pointer">
                  Chọn tệp dữ liệu
                </label>
              </div>
              <div className="flex justify-between pt-4 border-t border-slate-100">
                <button onClick={() => setStep(2)} className="px-4 py-2 text-xs text-slate-600">Quay lại</button>
                <button
                  onClick={handleGenerateOutline}
                  disabled={isGeneratingOutline}
                  className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
                >
                  {isGeneratingOutline ? "Đang lập đề cương..." : "AI Lập Cấu Trúc Đề Cương"}
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900">Bước 4: Duyệt Đề Cương Báo Cáo</h2>
              <div className="space-y-2">
                {outline.map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs font-bold">
                    {idx + 1}. {item.title}
                  </div>
                ))}
              </div>
              <div className="flex justify-between pt-4 border-t border-slate-100">
                <button onClick={() => setStep(3)} className="px-4 py-2 text-xs text-slate-600">Quay lại</button>
                <button
                  onClick={handleCreateAndOpenStudio}
                  disabled={isCreatingReport}
                  className="px-6 py-2.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold"
                >
                  {isCreatingReport ? "Đang mở Studio..." : "Hoàn tất & Mở Studio"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function UniversalProjectWizardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Đang tải wizard...</div>}>
      <UniversalProjectWizardContent />
    </Suspense>
  );
}
