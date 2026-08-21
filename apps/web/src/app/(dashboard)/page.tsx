"use client";

import { useEffect } from "react";
import Link from "next/link";
import {
  GraduationCap,
  TrendingUp,
  FileUp,
  Sparkles,
  Plus,
  ArrowRight,
  Clock,
  FileText,
  Search,
  CheckCircle2,
  FolderKanban,
  BookOpen,
} from "lucide-react";
import { useProjectStore } from "@/stores/useProjectStore";
import { useAuthStore } from "@/stores/useAuthStore";
import { formatDate } from "@/lib/utils";

const quickCards = [
  {
    title: "Bài tập lớn & Đồ án",
    tag: "Học thuật & Nghiên cứu",
    desc: "Đọc đề bài, trích xuất rubric, phân tích đề tài, research nguồn thật & sinh theo mẫu Word của trường.",
    icon: GraduationCap,
    href: "/projects/new?type=academic",
    color: "from-blue-600 to-indigo-600",
    badge: "Phổ biến nhất",
  },
  {
    title: "Báo cáo Dữ liệu & KPI",
    tag: "Doanh nghiệp & Tài chính",
    desc: "Tải Excel / CSV, tự động ánh xạ cột, tính toán KPI chính xác không hallucination, sinh biểu đồ trực quan.",
    icon: TrendingUp,
    href: "/projects/new?type=data",
    color: "from-emerald-600 to-teal-600",
    badge: "Data Branch",
  },
  {
    title: "Tải lên Mẫu Trường / Cty",
    tag: "Template Engine",
    desc: "Upload DOCX/PDF mẫu. Tự động nhận diện lề trang, font chữ, bìa, placeholder, heading & XML layout.",
    icon: FileUp,
    href: "/templates",
    color: "from-amber-600 to-orange-600",
    badge: "Smart Parse",
  },
  {
    title: "AI Auto Report",
    tag: "Siêu tốc độ",
    desc: "Chỉ cần nhập chủ đề & mô tả ngắn, AI tự động lập kế hoạch nghiên cứu, tìm nguồn và soạn thảo bản nháp.",
    icon: Sparkles,
    href: "/projects/new?type=auto",
    color: "from-purple-600 to-pink-600",
    badge: "Tự động 100%",
  },
];

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { projects, isLoading, fetchProjects } = useProjectStore();

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 p-8 text-white shadow-lg">
        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-indigo-300 backdrop-blur">
            <Sparkles className="h-3.5 w-3.5" />
            <span>AI Report Studio VIP Pro Edition</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Xin chào, {user?.name || "Kỹ sư"} 👋
          </h1>
          <p className="text-xs text-slate-300 leading-relaxed sm:text-sm">
            Hệ điều hành tài liệu thông minh kết hợp giữa Tiptap Editor A4, RAG kiểm chứng nguồn thật không Hallucination và bộ xuất bản DOCX giữ nguyên 100% định dạng trường học.
          </p>
        </div>
        <div className="absolute right-0 top-0 -mt-10 -mr-10 h-72 w-72 rounded-full bg-indigo-500/10 blur-3xl" />
      </div>

      {/* Creation Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Bắt đầu tạo báo cáo mới</h2>
            <p className="text-xs text-slate-500">Chọn phương thức phù hợp với mục đích của bạn</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.title}
                href={card.href}
                className="group relative flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md hover:border-indigo-300"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`h-10 w-10 rounded-lg bg-gradient-to-br ${card.color} text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform`}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                      {card.badge}
                    </span>
                  </div>

                  <p className="text-[11px] font-semibold uppercase tracking-wider text-indigo-600 mb-1">
                    {card.tag}
                  </p>
                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors mb-2">
                    {card.title}
                  </h3>
                  <p className="text-xs text-slate-500 line-clamp-3 leading-relaxed">
                    {card.desc}
                  </p>
                </div>

                <div className="mt-5 flex items-center gap-1 text-xs font-semibold text-indigo-600 group-hover:gap-2 transition-all">
                  <span>Khởi tạo ngay</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Projects */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Báo cáo gần đây</h2>
            <p className="text-xs text-slate-500">Các đề tài và tài liệu bạn đang thực hiện</p>
          </div>
          <Link
            href="/projects"
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
          >
            <span>Xem tất cả</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-40 rounded-xl bg-slate-100 animate-pulse border border-slate-200" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <div className="mx-auto h-12 w-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3">
              <FolderKanban className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">Chưa có báo cáo nào</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Bạn chưa khởi tạo dự án báo cáo nào. Hãy chọn một trong các hình thức ở trên để bắt đầu ngay!
            </p>
            <Link
              href="/projects/new"
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Tạo báo cáo đầu tiên</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.slice(0, 6).map((proj) => (
              <Link
                key={proj.id}
                href={`/projects/${proj.id}`}
                className="group flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold text-indigo-700 capitalize">
                      <BookOpen className="h-3 w-3" />
                      {proj.type}
                    </span>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(proj.updated_at)}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1 mb-1">
                    {proj.name}
                  </h3>
                  <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                    {proj.description || "Chưa có mô tả chi tiết."}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span>{proj.topic_details_json?.subject || "Chủ đề học phần"}</span>
                  <span className="font-semibold text-indigo-600 group-hover:underline">Mở Studio →</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
