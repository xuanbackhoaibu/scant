"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { Check, Copy, Maximize2, AlertCircle, RefreshCw } from "lucide-react";

interface MermaidViewerProps {
  code: string;
  title?: string;
  className?: string;
}

export function MermaidViewer({ code, title, className = "" }: MermaidViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "neutral",
      securityLevel: "loose",
      fontFamily: "inherit",
    });

    async function renderDiagram() {
      if (!code || !code.trim()) return;
      const id = `mermaid_${Math.random().toString(36).substring(2, 9)}`;
      try {
        setError(null);
        const { svg } = await mermaid.render(id, code.trim());
        setSvgContent(svg);
      } catch (err: any) {
        setError(err.message || "Cú pháp Mermaid chưa hợp lệ.");
      }
    }

    renderDiagram();
  }, [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`my-4 border border-slate-200 rounded-2xl bg-white shadow-sm overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs text-slate-700">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-800">{title || "Sơ đồ Mermaid"}</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-600 font-medium transition"
            title="Sao chép mã Mermaid"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
            <span>{copied ? "Đã chép" : "Sao chép"}</span>
          </button>
          <button
            onClick={() => setIsModalOpen(true)}
            className="p-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-600 transition"
            title="Phóng to sơ đồ"
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="p-6 flex items-center justify-center overflow-x-auto min-h-[140px] bg-slate-50/40">
        {error ? (
          <div className="flex items-start space-x-2 text-rose-600 text-xs p-3 bg-rose-50 rounded-xl border border-rose-100 max-w-md">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Lỗi hiển thị sơ đồ</p>
              <p className="text-[11px] text-rose-500 font-mono mt-1">{error}</p>
            </div>
          </div>
        ) : svgContent ? (
          <div
            ref={containerRef}
            className="w-full flex justify-center [&>svg]:max-w-full [&>svg]:h-auto"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        ) : (
          <div className="flex items-center space-x-2 text-slate-400 text-xs">
            <RefreshCw className="h-4 w-4 animate-spin text-indigo-600" />
            <span>Đang vẽ sơ đồ đồ họa...</span>
          </div>
        )}
      </div>

      {/* Fullscreen Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="text-sm font-bold text-slate-900">{title || "Sơ đồ Mermaid (Phóng to)"}</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-sm font-bold px-2 py-1 rounded-lg hover:bg-slate-200"
              >
                ✕ Đóng
              </button>
            </div>
            <div className="p-8 overflow-auto flex-1 flex justify-center items-center bg-slate-50/30">
              <div
                className="w-full flex justify-center [&>svg]:max-w-full [&>svg]:h-auto scale-110 transform origin-center"
                dangerouslySetInnerHTML={{ __html: svgContent }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
