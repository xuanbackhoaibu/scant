"use client";

import { useState, Suspense } from "react";
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

  const [step, setStep] = useState(1);
  const [projectType, setProjectType] = useState(initialType);

  // Step 1: Describe
  const [userPrompt, setUserPrompt] = useState(
    "Phân tích thị trường xe điện Việt Nam năm 2026 và đề xuất chiến lược thâm nhập thị trường cho dòng xe điện phân khúc phổ thông."
  );
  const [isAnalyzingIntent, setIsAnalyzingIntent] = useState(false);
  const [topicName, setTopicName] = useState("Báo cáo Chiến lược Thị trường Xe Điện 2026");
  const [description, setDescription] = useState(
    "Báo cáo phân tích thực trạng bối cảnh thị trường ô tô điện, thị phần đối thủ và xây dựng chiến lược phát triển mạng lưới trạm sạc cùng chính sách giá tối ưu."
  );
  const [audience, setAudience] = useState("Hội đồng Quản trị & Ban Điều hành");
  const [customFields, setCustomFields] = useState<CustomFieldItem[]>([
    { key: "company_name", label: "Tên Doanh nghiệp", type: "text", required: true, value: "VinFast Auto" },
    { key: "department", label: "Phòng ban phụ trách", type: "text", required: false, value: "Khối Chiến lược & Phát triển" },
    { key: "lead_author", label: "Người lập báo cáo", type: "text", required: true, value: "Trần Tuấn Anh" },
    { key: "target_timeline", label: "Kỳ kế hoạch", type: "text", required: false, value: "Q1/2026 - Q4/2027" },
  ]);

  // Step 2 & 3: Template & Knowledge
  const [selectedTemplate, setSelectedTemplate] = useState("tpl_corp_standard");
  const [knowledgeFiles, setKnowledgeFiles] = useState<File[]>([]);

  // Step 4: AI Plan
  const [isGeneratingOutline, setIsGeneratingOutline] = useState(false);
  const [projectUnderstanding, setProjectUnderstanding] = useState("");
  const [objectives, setObjectives] = useState<string[]>([]);
  const [scope, setScope] = useState("");
  const [suggestedMethodology, setSuggestedMethodology] = useState("");
  const [outline, setOutline] = useState<OutlineItemUI[]>([]);

  // Execution state
  const [isCreatingReport, setIsCreatingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // AI Smart Intent Analysis
  const handleAnalyzeIntent = async () => {
    if (!userPrompt.trim()) return;
    setIsAnalyzingIntent(true);
    setError(null);
    try {
      const res = await api.ai.analyzeIntent({
        user_prompt: userPrompt,
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
      setError(err.message || "Không thể phân tích ý tưởng. Bạn có thể tiếp tục nhập thủ công.");
    } finally {
      setIsAnalyzingIntent(false);
    }
  };

  const handleAddField = () => {
    const key = `custom_field_${customFields.length + 1}`;
    setCustomFields([
      ...customFields,
      { key, label: `Trường bổ sung ${customFields.length + 1}`, type: "text", required: false, value: "" },
    ]);
  };

  const handleRemoveField = (idx: number) => {
    setCustomFields(customFields.filter((_, i) => i !== idx));
  };

  const handleFieldChange = (idx: number, fieldKey: keyof CustomFieldItem, val: any) => {
    const updated = [...customFields];
    (updated[idx] as any)[fieldKey] = val;
    setCustomFields(updated);
  };

  const handleGenerateOutline = async () => {
    setIsGeneratingOutline(true);
    setError(null);
    try {
      // 1. Create Project in DB
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

      // 2. Upload any knowledge files
      for (const file of knowledgeFiles) {
        const fd = new FormData();
        fd.append("project_id", project.id);
        fd.append("document_type", "reference");
        fd.append("file", file);
        await api.files.upload(fd);
      }

      // 3. Request AI Outline
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
      setScope(outlineRes.scope);
      setSuggestedMethodology(outlineRes.suggested_methodology);
      setOutline(outlineRes.outline);

      (window as any).__created_project_id = project.id;
      setStep(4);
    } catch (err: any) {
      setError(err.message || "Lỗi khi sinh cấu trúc tài liệu. Vui lòng thử lại.");
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
    <div className="max-w-5xl mx-auto py-8 px-4 space-y-8">
      {/* Header Progress */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Khởi Tạo Báo Cáo & Tài Liệu Thông Minh</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Quy trình tạo lập tự động: Phân tích Ý tưởng → Template → Tri thức → Đề cương → Studio
          </p>
        </div>

        {/* Steps badge */}
        <div className="flex items-center gap-2">
          {["Ý tưởng", "Template", "Tri thức", "Đề cương"].map((label, idx) => {
            const s = idx + 1;
            const isCurr = step === s;
            const isDone = step > s;
            return (
              <div key={s} className="flex items-center gap-1.5">
                <div
                  className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    isCurr
                      ? "bg-indigo-600 text-white shadow-sm"
                      : isDone
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  {isDone ? "✓" : s}
                </div>
                <span className={`text-xs font-medium hidden md:inline ${isCurr ? "text-indigo-600 font-bold" : "text-slate-500"}`}>
                  {label}
                </span>
                {idx < 3 && <div className="h-px w-3 bg-slate-200" />}
              </div>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: Describe & Smart Intent Analysis */}
      {step === 1 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          {/* Hero Input */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Wand2 className="h-4 w-4 text-indigo-600" />
                <span>Bạn muốn tạo báo cáo hoặc tài liệu gì?</span>
              </label>
              <button
                onClick={handleAnalyzeIntent}
                disabled={isAnalyzingIntent}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{isAnalyzingIntent ? "AI đang phân tích ý tưởng..." : "AI Tự Động Phân Tích"}</span>
              </button>
            </div>

            <textarea
              rows={3}
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="Nhập mô tả ý tưởng, ví dụ: Báo cáo phân tích đối thủ cạnh tranh thị trường SaaS 2026, đề xuất bảng tính giá và KPI mở rộng..."
              className="w-full p-3.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none leading-relaxed"
            />
          </div>

          {/* Quick Categories */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-700">Hoặc chọn phân loại tài liệu nhanh:</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {PROJECT_TYPE_CARDS.map((card) => {
                const Icon = card.icon;
                const isSelected = projectType === card.id;
                return (
                  <div
                    key={card.id}
                    onClick={() => setProjectType(card.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? "border-indigo-600 bg-indigo-50/60 shadow-xs"
                        : "border-slate-200 hover:border-slate-300 bg-white"
                    }`}
                  >
                    <div className={`h-7 w-7 rounded-lg flex items-center justify-center mb-2 ${card.color}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <h4 className="text-xs font-bold text-slate-900 truncate">{card.name}</h4>
                    <p className="text-[10px] text-slate-500 line-clamp-2 mt-0.5">{card.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Project Details & Dynamic Metadata */}
          <div className="pt-4 border-t border-slate-100 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tên Tiêu Đề Báo Cáo *</label>
                <input
                  type="text"
                  value={topicName}
                  onChange={(e) => setTopicName(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Đối Tượng Độc Giả (Audience)</label>
                <input
                  type="text"
                  value={audience}
                  onChange={(e) => setAudience(e.target.value)}
                  placeholder="Ví dụ: Ban Điều hành, Khách hàng, Nhà đầu tư..."
                  className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
                />
              </div>
            </div>

            {/* Custom Metadata Fields */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-800">
                  Thông tin bìa & Metadata tùy biến ({customFields.length} trường)
                </label>
                <button
                  type="button"
                  onClick={handleAddField}
                  className="flex items-center gap-1 text-[11px] font-bold text-indigo-600 hover:text-indigo-800"
                >
                  <Plus className="h-3 w-3" />
                  <span>Thêm trường metadata</span>
                </button>
              </div>

              <div className="space-y-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
                {customFields.map((field, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={field.label}
                      onChange={(e) => handleFieldChange(idx, "label", e.target.value)}
                      placeholder="Tên trường (Nhãn)"
                      className="w-1/3 h-8 px-2.5 text-xs bg-white border border-slate-200 rounded-lg outline-none focus:border-indigo-500"
                    />
                    <input
                      type="text"
                      value={field.value || ""}
                      onChange={(e) => handleFieldChange(idx, "value", e.target.value)}
                      placeholder="Giá trị nhập"
                      className="flex-1 h-8 px-2.5 text-xs bg-white border border-slate-200 rounded-lg outline-none focus:border-indigo-500"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveField(idx)}
                      className="p-1.5 text-slate-400 hover:text-red-500 rounded"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
            >
              <span>Tiếp tục: Chọn Mẫu Template</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Template Selection */}
      {step === 2 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600 mb-1">
              Bước 2: Chọn Mẫu Định Dạng (Template)
            </h2>
            <p className="text-xs text-slate-500">
              Chọn mẫu tài liệu doanh nghiệp chuẩn mực hoặc sử dụng mẫu Word tùy biến.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { id: "tpl_corp_standard", name: "Executive Business Report", desc: "A4, Lề 25mm, Font Inter/Arial, Bìa Doanh nghiệp hiện đại" },
              { id: "tpl_technical_doc", name: "Technical Whitepaper", desc: "A4, Font Roboto/Consolas, Khung code & bảng thông số" },
              { id: "tpl_financial_kpi", name: "Financial & KPI Summary", desc: "A4, Bảng số liệu đối soát, chỉ số tài chính nổi bật" },
            ].map((tpl) => (
              <div
                key={tpl.id}
                onClick={() => setSelectedTemplate(tpl.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  selectedTemplate === tpl.id
                    ? "border-indigo-600 bg-indigo-50/50 shadow-xs"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <Layers className="h-4 w-4 text-indigo-600" />
                  {selectedTemplate === tpl.id && <CheckCircle2 className="h-4 w-4 text-indigo-600" />}
                </div>
                <h4 className="text-xs font-bold text-slate-900">{tpl.name}</h4>
                <p className="text-[11px] text-slate-500 mt-1">{tpl.desc}</p>
              </div>
            ))}
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Quay lại</span>
            </button>
            <button
              onClick={() => setStep(3)}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
            >
              <span>Tiếp tục: Tài liệu Tri thức</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Knowledge Base Upload */}
      {step === 3 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600 mb-1">
              Bước 3: Tải Lên Tri Thức & Dữ Liệu Nguồn (Knowledge Base)
            </h2>
            <p className="text-xs text-slate-500">
              Hỗ trợ đa định dạng: PDF, DOCX, XLSX, CSV, PPTX, TXT, MD, hình ảnh và ZIP source code.
            </p>
          </div>

          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50/50 transition-colors">
            <Upload className="h-10 w-10 text-indigo-600 mx-auto mb-3" />
            <h3 className="text-xs font-bold text-slate-800">Kéo thả tệp dữ liệu vào đây</h3>
            <p className="text-[11px] text-slate-400 mt-1">PDF, DOCX, XLSX, CSV, PPTX, TXT, ZIP</p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.xlsx,.csv,.pptx,.txt,.md,.zip"
              onChange={(e) => {
                if (e.target.files) {
                  setKnowledgeFiles(Array.from(e.target.files));
                }
              }}
              className="hidden"
              id="know-file-input-universal"
            />
            <label
              htmlFor="know-file-input-universal"
              className="mt-4 inline-block px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold cursor-pointer transition-colors"
            >
              Chọn tệp từ máy tính
            </label>
          </div>

          {knowledgeFiles.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-slate-700">Tài liệu đã chọn ({knowledgeFiles.length}):</p>
              {knowledgeFiles.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                  <span className="font-medium text-slate-700 truncate max-w-md">{file.name}</span>
                  <span className="text-slate-400">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Quay lại</span>
            </button>
            <button
              onClick={handleGenerateOutline}
              disabled={isGeneratingOutline}
              className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
            >
              {isGeneratingOutline ? (
                <>
                  <Sparkles className="h-4 w-4 animate-spin" />
                  <span>AI đang thiết kế cấu trúc đề cương...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>AI Lập Cấu Trúc Đề Cương</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Visual Outline Tree */}
      {step === 4 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600">
                Bước 4: Duyệt & Tùy Chỉnh Đề Cương Báo Cáo
              </h2>
              <button
                onClick={() => {
                  setOutline([
                    ...outline,
                    {
                      title: `PHẦN ${outline.length + 1}: MỤC BỔ SUNG`,
                      level: 1,
                      position: outline.length + 1,
                      children: [],
                    },
                  ]);
                }}
                className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 px-2.5 py-1 rounded-lg transition-colors border border-indigo-200"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Thêm phần</span>
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Bạn có thể tự do đổi tên, thêm hoặc xóa bớt các phần trước khi chuyển sang Studio.
            </p>
          </div>

          {/* AI Project Understanding Card */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
            <div>
              <span className="font-bold text-slate-800">Thấu hiểu Tài liệu (Project Understanding):</span>
              <p className="text-slate-600 mt-1">{projectUnderstanding}</p>
            </div>
            <div>
              <span className="font-bold text-slate-800">Mục tiêu trọng tâm:</span>
              <ul className="list-disc list-inside text-slate-600 mt-1 space-y-0.5">
                {objectives.map((obj, i) => (
                  <li key={i}>{obj}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Outline Tree */}
          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-700">Cấu trúc các phần ({outline.length} phần):</p>
            {outline.map((item, idx) => (
              <div
                key={idx}
                className="p-3.5 bg-white rounded-xl border border-slate-200 hover:border-indigo-300 transition-all space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1">
                    <span className="h-6 w-6 rounded-md bg-indigo-50 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {idx + 1}
                    </span>
                    <input
                      type="text"
                      value={item.title}
                      onChange={(e) => {
                        const updated = [...outline];
                        updated[idx].title = e.target.value;
                        setOutline(updated);
                      }}
                      className="w-full text-xs font-bold text-slate-800 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-indigo-500 focus:bg-slate-50 px-1 py-0.5 outline-none rounded"
                    />
                  </div>
                  <button
                    onClick={() => setOutline(outline.filter((_, i) => i !== idx))}
                    className="p-1 text-slate-400 hover:text-red-600 rounded transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                {item.children.length > 0 && (
                  <div className="pl-8 space-y-1.5 border-l-2 border-slate-100 ml-3">
                    {item.children.map((child, cIdx) => (
                      <div key={cIdx} className="text-xs text-slate-600 flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                        <span>{child.title}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(3)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Quay lại</span>
            </button>
            <button
              onClick={handleCreateAndOpenStudio}
              disabled={isCreatingReport}
              className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
            >
              {isCreatingReport ? (
                <span>Đang khởi tạo Report Studio...</span>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Hoàn tất & Mở Studio Canvas</span>
                </>
              )}
            </button>
          </div>
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
