"use client";

import { useEffect, useState } from "react";
import { LayoutTemplate, Plus, Search, Filter, Copy, Globe, Lock, ArrowRight, Star } from "lucide-react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

const CATEGORIES = [
  { id: "all", label: "Tất cả" },
  { id: "business", label: "Business" },
  { id: "financial", label: "Financial" },
  { id: "technical", label: "Technical" },
  { id: "research", label: "Research" },
  { id: "data", label: "Data" },
  { id: "proposal", label: "Proposal" },
  { id: "marketing", label: "Marketing" },
  { id: "operations", label: "Operations" },
  { id: "custom", label: "Custom" },
];

export default function TemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<any[]>([]);
  const [scope, setScope] = useState<"public" | "workspace" | "my">("public");
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadTemplates() {
      setLoading(true);
      try {
        const res = await api.templates.list();
        setTemplates(res || []);
      } catch {
        // empty
      } finally {
        setLoading(false);
      }
    }
    loadTemplates();
  }, [scope, category]);

  const handleUseTemplate = (tplId: string) => {
    router.push(`/projects/new?template=${tplId}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Thư Viện Mẫu (Template Marketplace)</h1>
          <p className="text-xs text-slate-500">Kho mẫu báo cáo chuẩn quốc tế, tài liệu kỹ thuật & mẫu doanh nghiệp</p>
        </div>
      </div>

      {/* Tabs & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex bg-slate-100 p-1 rounded-xl w-full sm:w-auto">
          {[
            { id: "public", label: "Public Marketplace" },
            { id: "workspace", label: "Workspace" },
            { id: "my", label: "My Templates" },
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
            placeholder="Tìm mẫu báo cáo..."
            className="w-full h-8 pl-8 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-none"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            onClick={() => setCategory(c.id)}
            className={`px-3 py-1 rounded-full text-xs font-semibold shrink-0 transition-colors ${
              category === c.id ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {c.label}
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
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              id: "tpl_corp_standard",
              name: "Executive Business Report",
              category: "Business",
              desc: "Báo cáo chiến lược doanh nghiệp, kế hoạch phát triển thị trường và phân bổ nguồn lực.",
              author: "AI Studio Official",
              usage: 1240,
              rating: 4.9,
            },
            {
              id: "tpl_technical_doc",
              name: "Technical Architecture Whitepaper",
              category: "Technical",
              desc: "Mẫu tài liệu kiến trúc kỹ thuật phần mềm, đặc tả API và thiết kế hạ tầng Cloud.",
              author: "Cloud Architects",
              usage: 830,
              rating: 5.0,
            },
            {
              id: "tpl_financial_kpi",
              name: "Financial Audit & KPI Review",
              category: "Financial",
              desc: "Báo cáo tài chính chi tiết với bảng đối soát doanh thu, chi phí, EBITDA và dòng tiền.",
              author: "Finance Expert",
              usage: 950,
              rating: 4.8,
            },
            {
              id: "tpl_market_research",
              name: "Comprehensive Market Research",
              category: "Marketing",
              desc: "Khảo sát quy mô thị trường, phân tích đối thủ cạnh tranh, chân dung khách hàng mục tiêu.",
              author: "Market Insights",
              usage: 620,
              rating: 4.9,
            },
          ].map((tpl) => (
            <div
              key={tpl.id}
              className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-xs transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-indigo-50 text-[10px] font-bold text-indigo-700 uppercase">
                    {tpl.category}
                  </span>
                  <span className="flex items-center gap-1 text-[11px] font-bold text-amber-600">
                    <Star className="h-3 w-3 fill-amber-500 text-amber-500" />
                    <span>{tpl.rating}</span>
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 leading-snug">{tpl.name}</h3>
                <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">{tpl.desc}</p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-400">{tpl.usage} lượt sử dụng</span>
                <button
                  onClick={() => handleUseTemplate(tpl.id)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-xs shadow-xs transition-colors"
                >
                  <span>Sử dụng mẫu</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
