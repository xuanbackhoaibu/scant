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
  DollarSign,
  PieChart,
  FileText,
  Plus,
  ArrowRight,
  Sparkles,
  Clock,
  Layers,
  Wand2,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const QUICK_CARDS = [
  {
    type: "business_report",
    title: "Business Report",
    desc: "Báo cáo quản trị, chiến lược phát triển, kế hoạch kinh doanh và phân tích hoạt động.",
    icon: Briefcase,
    color: "text-blue-600 bg-blue-50 border-blue-100",
  },
  {
    type: "data_analysis",
    title: "Data Analysis",
    desc: "Phân tích tập dữ liệu Excel/CSV, trích xuất insight thống kê và biểu đồ trực quan.",
    icon: TrendingUp,
    color: "text-emerald-600 bg-emerald-50 border-emerald-100",
  },
  {
    type: "research",
    title: "Research Report",
    desc: "Báo cáo nghiên cứu thị trường, luận chứng khoa học kèm trích dẫn kiểm chứng thật.",
    icon: Search,
    color: "text-indigo-600 bg-indigo-50 border-indigo-100",
  },
  {
    type: "technical",
    title: "Technical Documentation",
    desc: "Tài liệu kiến trúc hệ thống, đặc tả kỹ thuật phần mềm, API và sơ đồ luồng.",
    icon: FileCode,
    color: "text-violet-600 bg-violet-50 border-violet-100",
  },
  {
    type: "proposal",
    title: "Proposal & RFP",
    desc: "Hồ sơ đề xuất dự án, chào thầu khách hàng, dự toán ngân sách và kế hoạch triển khai.",
    icon: FileSpreadsheet,
    color: "text-amber-600 bg-amber-50 border-amber-100",
  },
  {
    type: "financial",
    title: "Financial Report",
    desc: "Báo cáo tài chính định kỳ, phân tích dòng tiền, chi phí và dự báo doanh thu.",
    icon: DollarSign,
    color: "text-teal-600 bg-teal-50 border-teal-100",
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [heroPrompt, setHeroPrompt] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.projects.list();
        setProjects(data);
      } catch (err) {
        // user might not be logged in or token empty
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

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-6 px-4">
      {/* Hero: What do you want to create? */}
      <section className="relative overflow-hidden rounded-3xl bg-linear-to-br from-indigo-900 via-indigo-950 to-slate-950 p-8 sm:p-10 text-white shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-md border border-white/15 text-indigo-200">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Universal AI Document & Report Studio</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-black tracking-tight leading-tight">
            Bạn muốn tạo báo cáo hoặc tài liệu gì hôm nay?
          </h1>

          <p className="text-xs sm:text-sm text-indigo-200/90 leading-relaxed max-w-2xl">
            Nhập ý tưởng, chọn mẫu template hoặc tải lên dữ liệu. AI sẽ phân tích mục tiêu, thiết kế đề cương, kiểm chứng nguồn và khởi tạo văn bản hoàn chỉnh.
          </p>

          <form onSubmit={handleHeroSubmit} className="pt-2 flex flex-col sm:flex-row gap-2 max-w-2xl">
            <input
              type="text"
              value={heroPrompt}
              onChange={(e) => setHeroPrompt(e.target.value)}
              placeholder="Ví dụ: Phân tích thị trường xe điện 2026 và đề xuất chiến lược thâm nhập..."
              className="flex-1 h-11 px-4 text-xs sm:text-sm bg-white/10 text-white placeholder-indigo-300/70 border border-white/20 rounded-xl focus:outline-none focus:bg-white/15 focus:border-indigo-400 backdrop-blur-md"
            />
            <button
              type="submit"
              className="h-11 px-6 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-xs sm:text-sm font-bold shadow-md transition-all flex items-center justify-center gap-2 shrink-0"
            >
              <Wand2 className="h-4 w-4" />
              <span>Bắt đầu ngay</span>
            </button>
          </form>
        </div>
      </section>

      {/* Quick Launch Cards */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Phân loại Tài liệu & Báo cáo Chuyên sâu
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {QUICK_CARDS.map((card) => {
            const Icon = card.icon;
            return (
              <Link
                key={card.type}
                href={`/projects/new?type=${card.type}`}
                className="group relative flex flex-col justify-between p-5 bg-white rounded-2xl border border-slate-200/90 hover:border-indigo-300 hover:shadow-md transition-all space-y-3"
              >
                <div className="space-y-2">
                  <div className={`h-10 w-10 rounded-xl flex items-center justify-center border ${card.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {card.title}
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed">{card.desc}</p>
                </div>

                <div className="flex items-center gap-1 text-xs font-bold text-indigo-600 group-hover:translate-x-1 transition-transform">
                  <span>Khởi tạo báo cáo</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Recent Projects */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Dự án Gần Đây ({projects.length})
          </h2>
          <Link href="/projects" className="text-xs text-indigo-600 font-semibold hover:underline">
            Xem tất cả
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="h-28 bg-slate-100 rounded-2xl animate-pulse" />
            <div className="h-28 bg-slate-100 rounded-2xl animate-pulse" />
          </div>
        ) : projects.length === 0 ? (
          <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 space-y-3">
            <Layers className="h-10 w-10 text-slate-400 mx-auto" />
            <h3 className="text-xs font-bold text-slate-700">Chưa có dự án nào</h3>
            <p className="text-[11px] text-slate-400">Hãy chọn một loại tài liệu ở trên để bắt đầu soạn thảo.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {projects.slice(0, 4).map((p) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}`}
                className="p-4 bg-white rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-xs transition-all space-y-2 block"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded-full bg-slate-100 text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                    {p.type}
                  </span>
                  <span className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDate(p.created_at)}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-900 truncate">{p.name}</h4>
                <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">{p.description}</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
