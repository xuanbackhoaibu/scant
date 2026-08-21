"use client";

import { useState } from "react";
import { Settings, Cpu, ShieldCheck, Key, Save, Check } from "lucide-react";

export default function SettingsPage() {
  const [provider, setProvider] = useState("gemini");
  const [model, setModel] = useState("gemini-2.5-flash");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Cài Đặt Hệ Thống (Settings)</h1>
        <p className="text-xs text-slate-500">Cấu hình kết nối AI Provider, kiểm định chất lượng và thông số hệ thống</p>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6 text-xs">
        <div className="space-y-3">
          <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-600" />
            <span>AI Model & Provider</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-600 mb-1 font-medium">Nhà cung cấp AI mặc định:</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
              >
                <option value="gemini">Google Gemini (Khuyên dùng)</option>
                <option value="openai">OpenAI (GPT-4o / O3-Mini)</option>
                <option value="anthropic">Anthropic Claude (Sonnet 3.7)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-600 mb-1 font-medium">Mô hình AI:</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          {saved ? (
            <span className="text-emerald-600 font-bold flex items-center gap-1">
              <Check className="h-4 w-4" /> Đã lưu cấu hình
            </span>
          ) : (
            <span />
          )}

          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold shadow-xs transition-colors"
          >
            <Save className="h-4 w-4" />
            <span>Lưu cài đặt</span>
          </button>
        </div>
      </div>
    </div>
  );
}
