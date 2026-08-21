"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  GraduationCap,
  TrendingUp,
  Sparkles,
  FileUp,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Plus,
  Trash2,
  Edit2,
  BookOpen,
  Layers,
  FileText,
  School,
  Building,
  Upload,
} from "lucide-react";
import { api } from "@/lib/api";
import { useProjectStore } from "@/stores/useProjectStore";

interface OutlineItemUI {
  title: string;
  level: number;
  position: number;
  section_number?: string;
  description?: string;
  children: OutlineItemUI[];
}

function NewProjectWizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialType = searchParams.get("type") || "academic";

  const [step, setStep] = useState(1);
  const [projectType, setProjectType] = useState(initialType);

  // Form Fields (Step 1)
  const [topicName, setTopicName] = useState("Xây dựng Website Thương mại Điện tử ASP.NET Core MVC");
  const [subject, setSubject] = useState("Lập trình Web & Kiến trúc Ứng dụng");
  const [major, setMajor] = useState("Công nghệ Thông tin");
  const [university, setUniversity] = useState("Đại học Bách Khoa");
  const [instructor, setInstructor] = useState("TS. Nguyễn Văn B");
  const [studentName, setStudentName] = useState("Nguyễn Văn A");
  const [studentId, setStudentId] = useState("20210001");
  const [className, setClassName] = useState("K66-CNTT-01");
  const [academicYear, setAcademicYear] = useState("2025 - 2026");
  const [description, setDescription] = useState(
    "Đề tài nghiên cứu và phát triển website bán hàng trực tuyến toàn diện, áp dụng kiến trúc Clean Architecture, ASP.NET Core MVC, Entity Framework Core, SQL Server, thanh toán trực tuyến và phân quyền bảo mật JWT."
  );

  // Uploaded Files (Step 2 & 4)
  const [requirementFiles, setRequirementFiles] = useState<File[]>([]);
  const [knowledgeFiles, setKnowledgeFiles] = useState<File[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("tpl_bkhn_cntt");

  // AI Planning (Step 5)
  const [isGeneratingOutline, setIsGeneratingOutline] = useState(false);
  const [projectUnderstanding, setProjectUnderstanding] = useState("");
  const [objectives, setObjectives] = useState<string[]>([]);
  const [scope, setScope] = useState("");
  const [suggestedMethodology, setSuggestedMethodology] = useState("");
  const [outline, setOutline] = useState<OutlineItemUI[]>([]);

  // Submitting state
  const [isCreatingReport, setIsCreatingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateOutline = async () => {
    setIsGeneratingOutline(true);
    setError(null);
    try {
      // 1. Create temporary or final Project in DB first
      const project = await api.projects.create({
        name: topicName,
        type: projectType,
        description,
        topic_details: {
          topic_name: topicName,
          subject,
          major,
          university,
          instructor,
          student_name: studentName,
          student_id: studentId,
          class_name: className,
          academic_year: academicYear,
        },
      });

      // 2. Upload any requirement files
      for (const file of requirementFiles) {
        const fd = new FormData();
        fd.append("project_id", project.id);
        fd.append("document_type", "requirement");
        fd.append("file", file);
        await api.files.upload(fd);
      }

      // 3. Upload any knowledge files
      for (const file of knowledgeFiles) {
        const fd = new FormData();
        fd.append("project_id", project.id);
        fd.append("document_type", "reference");
        fd.append("file", file);
        await api.files.upload(fd);
      }

      // 4. Request AI Outline
      const outlineRes = await api.ai.generateOutline({
        project_id: project.id,
        topic_name: topicName,
        topic_description: description,
        subject,
        major,
        target_chapters_count: 6,
      });

      setProjectUnderstanding(outlineRes.project_understanding);
      setObjectives(outlineRes.objectives);
      setScope(outlineRes.scope);
      setSuggestedMethodology(outlineRes.suggested_methodology);
      setOutline(outlineRes.outline);

      // Store created project id
      (window as any).__created_project_id = project.id;
      setStep(5);
    } catch (err: any) {
      setError(err.message || "Không thể phân tích đề tài. Vui lòng thử lại.");
    } finally {
      setIsGeneratingOutline(false);
    }
  };

  const handleCreateAndOpenStudio = async () => {
    setIsCreatingReport(true);
    setError(null);
    try {
      const projectId = (window as any).__created_project_id;
      if (!projectId) {
        throw new Error("Project ID is missing. Please restart wizard.");
      }

      const reportRes = await api.reports.create({
        project_id: projectId,
        title: `Báo cáo: ${topicName}`,
        report_type: projectType,
        outline: outline,
      });

      router.push(`/reports/${reportRes.id}/editor`);
    } catch (err: any) {
      setError(err.message || "Không thể tạo báo cáo.");
      setIsCreatingReport(false);
    }
  };

  // Section Tree manipulation helpers
  const handleAddChapter = () => {
    const newPos = outline.length + 1;
    setOutline([
      ...outline,
      {
        title: `CHƯƠNG ${newPos}: MỤC MỚI BỔ SUNG`,
        level: 1,
        position: newPos,
        section_number: String(newPos),
        description: "Mô tả nội dung chương...",
        children: [],
      },
    ]);
  };

  const handleDeleteSection = (index: number) => {
    const updated = outline.filter((_, i) => i !== index);
    setOutline(updated);
  };

  const handleUpdateTitle = (index: number, newTitle: string) => {
    const updated = [...outline];
    updated[index].title = newTitle;
    setOutline(updated);
  };

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-8">
      {/* Wizard Step Progress */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Khởi tạo Báo cáo Học thuật & Đồ án</h1>
          <p className="text-xs text-slate-500">Quy trình chuẩn hóa 5 bước từ yêu cầu đến bản thảo hoàn chỉnh</p>
        </div>

        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5].map((s) => (
            <div
              key={s}
              className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                step === s
                  ? "bg-indigo-600 text-white shadow-sm"
                  : step > s
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-slate-100 text-slate-400"
              }`}
            >
              {step > s ? "✓" : s}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* STEP 1: Thông tin đề tài */}
      {step === 1 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600 mb-1">
              Bước 1: Thông tin Đề tài & Bìa Báo Cáo
            </h2>
            <p className="text-xs text-slate-500">
              Các thông tin này sẽ được tự động ánh xạ vào trang bìa và phần mở đầu theo mẫu chuẩn.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Tên Đề tài *</label>
              <input
                type="text"
                required
                value={topicName}
                onChange={(e) => setTopicName(e.target.value)}
                className="w-full h-10 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Môn học / Học phần</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Trường Đại học / Viện</label>
              <input
                type="text"
                value={university}
                onChange={(e) => setUniversity(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Giảng viên Hướng dẫn</label>
              <input
                type="text"
                value={instructor}
                onChange={(e) => setInstructor(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Sinh viên Thực hiện</label>
              <input
                type="text"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Mã số Sinh viên (MSSV)</label>
              <input
                type="text"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Lớp học phần</label>
              <input
                type="text"
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Mô tả Đề tài & Yêu cầu</label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Nhập tóm tắt mô tả chức năng, công nghệ áp dụng..."
                className="w-full p-3 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:border-indigo-500 outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <span>Tiếp tục: Upload Yêu Cầu</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Upload Yêu Cầu / Đề Bài */}
      {step === 2 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600 mb-1">
              Bước 2: Upload Đề Bài, Rubric & Tiêu Chí Chấm
            </h2>
            <p className="text-xs text-slate-500">
              AI sẽ đọc file PDF/DOCX để trích xuất mục tiêu bắt buộc, rubric thang điểm và tiêu chuẩn số trang.
            </p>
          </div>

          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50/50 transition-colors">
            <Upload className="h-10 w-10 text-indigo-600 mx-auto mb-3" />
            <h3 className="text-xs font-bold text-slate-800">Kéo thả file Đề bài / Rubric vào đây</h3>
            <p className="text-[11px] text-slate-400 mt-1">Hỗ trợ PDF, DOCX, TXT, MD (Tối đa 50MB)</p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.doc,.txt,.md"
              onChange={(e) => {
                if (e.target.files) {
                  setRequirementFiles(Array.from(e.target.files));
                }
              }}
              className="hidden"
              id="req-file-input"
            />
            <label
              htmlFor="req-file-input"
              className="mt-4 inline-block px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold cursor-pointer transition-colors"
            >
              Chọn file từ máy tính
            </label>
          </div>

          {requirementFiles.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-slate-700">File đã chọn:</p>
              {requirementFiles.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                  <span className="font-medium text-slate-700">{file.name}</span>
                  <span className="text-slate-400">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              ))}
            </div>
          )}

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
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <span>Tiếp tục: Chọn Mẫu Word</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Chọn Template */}
      {step === 3 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600 mb-1">
              Bước 3: Chọn Mẫu Word (Template) của Trường
            </h2>
            <p className="text-xs text-slate-500">
              Chọn một trong các mẫu chuẩn hệ thống hoặc tiếp tục với định dạng học thuật tiêu chuẩn.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { id: "tpl_bkhn_cntt", name: "ĐH Bách Khoa Hà Nội", desc: "A4, Lề trái 30mm, Times New Roman 13pt" },
              { id: "tpl_fpt_se", name: "Đại học FPT", desc: "A4, Lề trái 35mm, Times New Roman 12pt" },
              { id: "tpl_uit_thesis", name: "ĐH CNTT - ĐHQG HCM", desc: "A4, Lề trái 30mm, Dãn dòng 1.5" },
            ].map((tpl) => (
              <div
                key={tpl.id}
                onClick={() => setSelectedTemplate(tpl.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  selectedTemplate === tpl.id
                    ? "border-indigo-600 bg-indigo-50/50 shadow-sm"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <School className="h-4 w-4 text-indigo-600" />
                  {selectedTemplate === tpl.id && <CheckCircle2 className="h-4 w-4 text-indigo-600" />}
                </div>
                <h4 className="text-xs font-bold text-slate-900">{tpl.name}</h4>
                <p className="text-[11px] text-slate-500 mt-1">{tpl.desc}</p>
              </div>
            ))}
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Quay lại</span>
            </button>
            <button
              onClick={() => setStep(4)}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <span>Tiếp tục: Tài liệu tham khảo</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Tài liệu & Source Code */}
      {step === 4 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600 mb-1">
              Bước 4: Upload Tài liệu Tham Khảo & Source Code
            </h2>
            <p className="text-xs text-slate-500">
              Tài liệu này sẽ trở thành Knowledge Base cục bộ của báo cáo để AI trích xuất sự thật chính xác.
            </p>
          </div>

          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50/50 transition-colors">
            <Upload className="h-10 w-10 text-indigo-600 mx-auto mb-3" />
            <h3 className="text-xs font-bold text-slate-800">Kéo thả tài liệu / ZIP source code vào đây</h3>
            <p className="text-[11px] text-slate-400 mt-1">Hỗ trợ PDF, DOCX, ZIP project, TXT</p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.zip,.txt,.md"
              onChange={(e) => {
                if (e.target.files) {
                  setKnowledgeFiles(Array.from(e.target.files));
                }
              }}
              className="hidden"
              id="know-file-input"
            />
            <label
              htmlFor="know-file-input"
              className="mt-4 inline-block px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold cursor-pointer transition-colors"
            >
              Chọn file từ máy tính
            </label>
          </div>

          {knowledgeFiles.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-slate-700">Tài liệu đã chọn ({knowledgeFiles.length}):</p>
              {knowledgeFiles.map((file, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                  <span className="font-medium text-slate-700">{file.name}</span>
                  <span className="text-slate-400">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setStep(3)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Quay lại</span>
            </button>
            <button
              onClick={handleGenerateOutline}
              disabled={isGeneratingOutline}
              className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
            >
              {isGeneratingOutline ? (
                <>
                  <Sparkles className="h-4 w-4 animate-spin" />
                  <span>AI đang phân tích & lập đề cương...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>AI Phân Tích & Tạo Đề Cương</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: Visual Outline Tree Editor */}
      {step === 5 && (
        <div className="space-y-6 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-indigo-600">
                Bước 5: Duyệt & Chỉnh Sửa Đề Cương Báo Cáo
              </h2>
              <button
                onClick={handleAddChapter}
                className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 px-2.5 py-1 rounded-lg transition-colors border border-indigo-200"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Thêm chương</span>
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Bạn có thể tự do đổi tên, thêm hoặc xóa bớt các chương mục trước khi bắt đầu soạn thảo.
            </p>
          </div>

          {/* AI Project Understanding Card */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
            <div>
              <span className="font-bold text-slate-800">Thấu hiểu Đề tài (Project Understanding):</span>
              <p className="text-slate-600 mt-1">{projectUnderstanding}</p>
            </div>
            <div>
              <span className="font-bold text-slate-800">Mục tiêu cốt lõi:</span>
              <ul className="list-disc list-inside text-slate-600 mt-1 space-y-0.5">
                {objectives.map((obj, i) => (
                  <li key={i}>{obj}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Outline Tree */}
          <div className="space-y-3">
            <p className="text-xs font-semibold text-slate-700">Cấu trúc các chương mục ({outline.length} phần):</p>
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
                      onChange={(e) => handleUpdateTitle(idx, e.target.value)}
                      className="w-full text-xs font-bold text-slate-800 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-indigo-500 focus:bg-slate-50 px-1 py-0.5 outline-none rounded"
                    />
                  </div>
                  <button
                    onClick={() => handleDeleteSection(idx)}
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
              onClick={() => setStep(4)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Quay lại</span>
            </button>
            <button
              onClick={handleCreateAndOpenStudio}
              disabled={isCreatingReport}
              className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
            >
              {isCreatingReport ? (
                <span>Đang khởi tạo Report Studio...</span>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Hoàn tất & Mở Report Studio Canvas</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function NewProjectWizardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Đang tải wizard...</div>}>
      <NewProjectWizardContent />
    </Suspense>
  );
}
