"use client";

import { useEffect, useState } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import TextAlign from "@tiptap/extension-text-align";
import Placeholder from "@tiptap/extension-placeholder";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import CharacterCount from "@tiptap/extension-character-count";
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  Heading1,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  Table as TableIcon,
  Sparkles,
} from "lucide-react";

interface TiptapEditorProps {
  content: any;
  onChange: (plainText: string, json: any) => void;
  onAskAi?: (selectedText: string) => void;
}

export function TiptapEditor({
  content,
  onChange,
  onAskAi,
}: TiptapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Underline,
      TextAlign.configure({
        types: ["heading", "paragraph"],
      }),
      Placeholder.configure({
        placeholder: "Nhập nội dung học thuật hoặc dùng AI để soạn thảo tự động...",
      }),
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
      CharacterCount,
    ],
    content: content || "",
    onUpdate: ({ editor }) => {
      const text = editor.getText();
      const json = editor.getJSON();
      onChange(text, json);
    },
    editorProps: {
      attributes: {
        class: "prose prose-slate max-w-none focus:outline-none min-h-[500px] text-[13pt] leading-[1.6] text-slate-900 font-serif",
      },
    },
  });

  // Sync external content update (e.g. from AI generation)
  useEffect(() => {
    if (editor && content) {
      const currentJson = JSON.stringify(editor.getJSON());
      const newJson = typeof content === "object" ? JSON.stringify(content) : null;
      if (newJson && currentJson !== newJson) {
        editor.commands.setContent(content);
      } else if (typeof content === "string" && editor.getText() !== content) {
        editor.commands.setContent(content);
      }
    }
  }, [content, editor]);

  if (!editor) return null;

  return (
    <div className="flex flex-col bg-white">
      {/* Floating / In-canvas Toolbar */}
      <div className="sticky top-14 z-20 flex flex-wrap items-center gap-1 p-2 bg-white/95 backdrop-blur border-b border-slate-200 text-slate-700 shadow-xs">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("bold") ? "bg-slate-200 text-indigo-700 font-bold" : ""}`}
          title="In đậm (⌘B)"
        >
          <Bold className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("italic") ? "bg-slate-200 text-indigo-700" : ""}`}
          title="In nghiêng (⌘I)"
        >
          <Italic className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("underline") ? "bg-slate-200 text-indigo-700" : ""}`}
          title="Gạch chân (⌘U)"
        >
          <UnderlineIcon className="h-4 w-4" />
        </button>

        <div className="h-4 w-px bg-slate-200 mx-1" />

        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("heading", { level: 1 }) ? "bg-slate-200 text-indigo-700 font-bold" : ""}`}
          title="Heading 1 (Chương)"
        >
          <Heading1 className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("heading", { level: 2 }) ? "bg-slate-200 text-indigo-700 font-bold" : ""}`}
          title="Heading 2 (Mục 1.1)"
        >
          <Heading2 className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("heading", { level: 3 }) ? "bg-slate-200 text-indigo-700 font-bold" : ""}`}
          title="Heading 3 (Mục 1.1.1)"
        >
          <Heading3 className="h-4 w-4" />
        </button>

        <div className="h-4 w-px bg-slate-200 mx-1" />

        <button
          onClick={() => editor.chain().focus().setTextAlign("left").run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive({ textAlign: "left" }) ? "bg-slate-200 text-indigo-700" : ""}`}
          title="Căn trái"
        >
          <AlignLeft className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().setTextAlign("center").run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive({ textAlign: "center" }) ? "bg-slate-200 text-indigo-700" : ""}`}
          title="Căn giữa"
        >
          <AlignCenter className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().setTextAlign("justify").run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive({ textAlign: "justify" }) ? "bg-slate-200 text-indigo-700" : ""}`}
          title="Căn đều 2 bên (Học thuật)"
        >
          <AlignJustify className="h-4 w-4" />
        </button>

        <div className="h-4 w-px bg-slate-200 mx-1" />

        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("bulletList") ? "bg-slate-200 text-indigo-700" : ""}`}
          title="Danh sách dấu chấm"
        >
          <List className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`p-1.5 rounded hover:bg-slate-100 ${editor.isActive("orderedList") ? "bg-slate-200 text-indigo-700" : ""}`}
          title="Danh sách số"
        >
          <ListOrdered className="h-4 w-4" />
        </button>

        <button
          onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
          className="p-1.5 rounded hover:bg-slate-100 text-slate-700"
          title="Chèn bảng (Table)"
        >
          <TableIcon className="h-4 w-4" />
        </button>

        {onAskAi && (
          <button
            onClick={() => {
              const selection = editor.state.doc.textBetween(
                editor.state.selection.from,
                editor.state.selection.to
              );
              if (selection) onAskAi(selection);
            }}
            className="ml-auto flex items-center gap-1 px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-colors"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Chỉnh sửa đoạn chọn với AI</span>
          </button>
        )}
      </div>

      {/* Editor Content Area */}
      <div className="p-8">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
