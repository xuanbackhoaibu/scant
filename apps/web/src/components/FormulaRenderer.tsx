"use client";

import { useEffect, useState } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

interface FormulaRendererProps {
  formula: string;
  block?: boolean;
  className?: string;
}

export function FormulaRenderer({ formula, block = false, className = "" }: FormulaRendererProps) {
  const [html, setHtml] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!formula) return;
    try {
      setError(null);
      const rendered = katex.renderToString(formula.trim(), {
        displayMode: block,
        throwOnError: false,
        output: "htmlAndMathml",
      });
      setHtml(rendered);
    } catch (err: any) {
      setError(err.message || "Công thức LaTeX chưa đúng cú pháp");
    }
  }, [formula, block]);

  if (error) {
    return <span className="text-rose-500 font-mono text-xs bg-rose-50 px-1 py-0.5 rounded">LaTeX Error: {error}</span>;
  }

  return (
    <span
      className={`${block ? "block my-3 text-center overflow-x-auto py-2" : "inline-block"} ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
