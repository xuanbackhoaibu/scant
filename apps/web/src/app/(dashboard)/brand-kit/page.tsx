"use client";

import { useState } from "react";
import { Palette, Check, Save } from "lucide-react";

export default function BrandKitPage() {
  const [primaryColor, setPrimaryColor] = useState("#1E3A8A");
  const [secondaryColor, setSecondaryColor] = useState("#0D9488");
  const [fontFamily, setFontFamily] = useState("Inter");
  const [headerText, setHeaderText] = useState("DOANH NGHIỆP • BÁO CÁO CHIẾN LƯỢC");
  const [confidentiality, setConfidentiality] = useState("STRICTLY CONFIDENTIAL");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Bộ Nhận Diện Thương Hiệu (Brand Kit)</h1>
        <p className="text-xs text-slate-500">Tùy biến màu sắc, kiểu chữ và header/footer xuất bản cho toàn bộ tài liệu</p>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6 text-xs">
        {/* Colors */}
        <div className="space-y-3">
          <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            <Palette className="h-4 w-4 text-indigo-600" />
            <span>Màu sắc thương hiệu</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-600 mb-1 font-medium">Màu chủ đạo (Primary Color)</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="h-9 w-9 rounded-lg border border-slate-200 cursor-pointer p-0.5"
                />
                <input
                  type="text"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="flex-1 h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none uppercase font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-600 mb-1 font-medium">Màu phụ (Secondary Color)</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  className="h-9 w-9 rounded-lg border border-slate-200 cursor-pointer p-0.5"
                />
                <input
                  type="text"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  className="flex-1 h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none uppercase font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Header & Footer */}
        <div className="space-y-3 pt-4 border-t border-slate-100">
          <h3 className="font-bold text-slate-800 text-sm">Header & Footer Mặc Định</h3>
          <div>
            <label className="block text-slate-600 mb-1 font-medium">Nội dung Header trang:</label>
            <input
              type="text"
              value={headerText}
              onChange={(e) => setHeaderText(e.target.value)}
              className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
            />
          </div>

          <div>
            <label className="block text-slate-600 mb-1 font-medium">Thông báo bảo mật:</label>
            <input
              type="text"
              value={confidentiality}
              onChange={(e) => setConfidentiality(e.target.value)}
              className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          {saved ? (
            <span className="text-emerald-600 font-bold flex items-center gap-1">
              <Check className="h-4 w-4" /> Đã lưu cài đặt Brand Kit
            </span>
          ) : (
            <span />
          )}

          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-xs transition-colors"
          >
            <Save className="h-4 w-4" />
            <span>Lưu thay đổi</span>
          </button>
        </div>
      </div>
    </div>
  );
}
