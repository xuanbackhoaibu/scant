# AI REPORT STUDIO VIP PRO 🚀

> **Document Operating System** — Nền tảng tạo và biên tập báo cáo học thuật, đồ án và dữ liệu thông minh cao cấp kết hợp giữa Tiptap Editor A4 Canvas, Research Engine chống Hallucination và bộ xuất bản DOCX chuẩn XML trường học.

---

## 🏛️ Kiến Trúc Hệ Thống (Clean Architecture)

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, TailwindCSS, shadcn/ui, Tiptap, Zustand, TanStack Query.
- **Backend API**: FastAPI (Python 3.11+ / 3.14), SQLAlchemy 2.0 Async, Pydantic v2.
- **Database**: SQLite (Async aiosqlite cho Dev) / PostgreSQL 16 (AsyncPG cho Production).
- **Core Modules**:
  - `Document Parser`: PyMuPDF (PDF), python-docx (Word XML & placeholder extraction), openpyxl/pandas (Excel).
  - `Research Engine`: Search Provider abstraction (Tavily, Brave, SerpAPI), real web crawler & fact extractor.
  - `Citation Engine`: IEEE, APA 7, Harvard, MLA; Anti-hallucination claim-to-evidence verification mapping.
  - `AI Provider Engine`: Abstraction hỗ trợ Gemini, OpenAI, Anthropic, Ollama.
  - `Export Engine`: High-fidelity DOCX & PDF generation.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy

### 1. Khởi chạy Backend API

```bash
# Di chuyển vào thư mục API
cd apps/api

# Kích hoạt virtual environment
source venv/bin/activate

# Cài đặt dependencies (nếu chưa cài)
pip install -r requirements.txt

# Chạy server
uvicorn app.main:app --reload --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 2. Khởi chạy Frontend Web

```bash
# Di chuyển vào thư mục Web
cd apps/web

# Cài đặt dependencies (nếu chưa cài)
npm install

# Chạy Next.js development server
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

### 3. Chạy Test Suite

```bash
# Backend Pytest
PYTHONPATH=apps/api ./apps/api/venv/bin/pytest apps/api/tests

# Frontend Typecheck & Build
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
```
