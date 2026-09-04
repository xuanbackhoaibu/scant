# AI REPORT STUDIO 

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

### Chạy nhanh local demo

```bash
# Tạo/cập nhật dữ liệu demo, có thể chạy lại nhiều lần không bị trùng
PYTHONPATH=apps/api ./apps/api/venv/bin/python apps/api/app/seed_sample.py

# Chạy Backend API + Frontend Web cùng lúc
bash scripts/dev.sh
```

- Web Application: [http://localhost:3050](http://localhost:3050)
- API Docs: [http://localhost:8050/docs](http://localhost:8050/docs)

Kiểm tra nhanh sau khi server đã lên:

```bash
bash scripts/smoke-local.sh
bash scripts/smoke-demo-flow.sh
```

### 0. Cấu hình biến môi trường

Không commit file `.env.development`, `.env.production`, `.env.staging` hoặc API key thật lên Git.

```bash
cp .env.example .env.development
```

Sau đó tự điền key thật vào `.env.development` trên máy local hoặc cấu hình qua secret manager khi deploy.

Khi chạy production, bắt buộc đặt:

- `JWT_SECRET`: chuỗi ngẫu nhiên mạnh, không dùng giá trị mẫu.
- `CORS_ORIGINS`: JSON array các domain frontend được phép, ví dụ `["https://app.example.com"]`; không dùng `"*"`.
- `DEBUG=false`.

### 1. Khởi chạy Backend API

```bash
# Di chuyển vào thư mục API
cd apps/api

# Kích hoạt virtual environment
source venv/bin/activate

# Cài đặt dependencies (nếu chưa cài)
pip install -r requirements.txt

# Chạy server API trên cổng 8050
uvicorn app.main:app --reload --port 8050
```
- API Docs: [http://localhost:8050/docs](http://localhost:8050/docs)
- Health Check: [http://localhost:8050/api/v1/health](http://localhost:8050/api/v1/health)

### 2. Khởi chạy Frontend Web

```bash
# Di chuyển vào thư mục Web
cd apps/web

# Cài đặt dependencies (nếu chưa cài)
npm install

# Chạy Next.js development server trên cổng 3050
npm run dev
```
- Web Application: [http://localhost:3050](http://localhost:3050)

### 3. Chạy Test Suite

```bash
# Backend Pytest
PYTHONPATH=apps/api ./apps/api/venv/bin/pytest apps/api/tests

# Frontend Typecheck & Build
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
```

### 4. Kiểm tra an toàn trước khi commit/push

Chạy lệnh này trước mỗi lần commit hoặc push:

```bash
bash scripts/check-secrets.sh
```

Script sẽ chặn các lỗi phổ biến:

- Commit nhầm `.env.*`.
- Commit nhầm database, file upload, file export DOCX/HTML hoặc cache.
- Commit nhầm API key kiểu OpenAI, Gemini, Google OAuth, GitHub token, AWS key.

Quy trình đề xuất:

```bash
git status --short
bash scripts/check-secrets.sh
git add .gitignore .env.example scripts/check-secrets.sh README.md
git commit -m "chore(security): prevent committing secrets and generated files"
```
