# MASTER PROMPT — XÂY DỰNG ADMIN DASHBOARD HOÀN CHỈNH CHO DỰ ÁN

Bạn đang làm việc trực tiếp trên source code của dự án hiện tại.

Nhiệm vụ của bạn là **đọc, phân tích và nâng cấp toàn bộ khu vực Admin thành một Admin Dashboard hoàn chỉnh, hoạt động bằng dữ liệu thật**, liên kết trực tiếp với hệ thống đăng ký/đăng nhập, người dùng, AI, báo cáo, phân tích dữ liệu, quota, billing, project, document, automation và các chức năng hiện có của dự án.

Đây không phải nhiệm vụ dựng giao diện demo.

Không được tạo một trang Admin chứa các card số liệu giả.

Không được hard-code số lượng user, token, chi phí, job, storage hoặc system health.

Không được thay thế backend thật bằng mock data nếu backend hiện đã có dữ liệu.

Mọi thống kê Admin phải có nguồn dữ liệu thực tế hoặc phải ghi rõ `Unavailable / Not configured` nếu hệ thống chưa thu thập được dữ liệu.

---

# 1. MỤC TIÊU KIẾN TRÚC

Hiện tại dự án đã có frontend chính cho người dùng và API backend.

Hãy giữ kiến trúc:

```text
apps/
├── web/
│   ├── User Application
│   └── Admin Application Area
│
└── api/
    ├── Auth
    ├── Users
    ├── Projects
    ├── Documents
    ├── AI
    ├── Usage
    ├── Billing
    ├── Admin
    └── ...
```

KHÔNG tạo một frontend/project Admin hoàn toàn độc lập trừ khi kiến trúc hiện tại bắt buộc.

Admin phải là một **khu vực độc lập về giao diện và routing**, nhưng vẫn nằm trong frontend hiện tại để có thể tái sử dụng:

* authentication;
* API client;
* types;
* shared components;
* design system;
* session;
* error handling;
* notification;
* utilities.

Ví dụ route:

```text
/admin
/admin/users
/admin/users/[id]
/admin/ai-jobs
/admin/ai-jobs/[id]
/admin/usage
/admin/quotas
/admin/projects
/admin/documents
/admin/templates
/admin/automations
/admin/integrations
/admin/billing
/admin/payments
/admin/audit-logs
/admin/system
/admin/ai-config
/admin/settings
```

Admin phải có:

```text
AdminLayout
├── AdminSidebar
├── AdminHeader
├── AdminBreadcrumb
├── MainContent
└── Optional Detail Drawer
```

Không sử dụng sidebar của User Dashboard để chứa toàn bộ menu Admin.

Khi Admin chuyển từ User Dashboard sang `/admin`, giao diện phải thể hiện rõ đây là **Admin Console**.

---

# 2. ĐỌC SOURCE CODE TRƯỚC KHI THAY ĐỔI

Trước khi viết code:

1. Đọc cấu trúc repository.
2. Xác định framework frontend/backend.
3. Đọc authentication flow.
4. Đọc User model.
5. Đọc role/permission.
6. Đọc Admin API hiện tại.
7. Đọc Usage/AI Usage model.
8. Đọc Billing/Plan model.
9. Đọc Job/task model.
10. Đọc Project/Document model.
11. Đọc Template model.
12. Đọc Automation/Integration model nếu có.
13. Đọc API client frontend.
14. Đọc sidebar hiện tại.
15. Đọc route protection.
16. Kiểm tra migrations/schema database.
17. Kiểm tra worker/background jobs nếu có.

Không được đoán field/model khi chưa tìm source code.

Tận dụng implementation hiện tại thay vì tạo trùng chức năng.

---

# 3. SỬA QUYỀN ADMIN TRƯỚC

Hiện dự án có dấu hiệu không thống nhất giữa:

```text
role === "admin"
```

và:

```text
is_superuser
```

Hãy audit toàn bộ authorization.

Xác định một nguồn sự thật duy nhất.

Ví dụ có thể chuẩn hóa:

```text
User
├── role
├── is_active
└── is_superuser
```

Hoặc permission-based RBAC nếu dự án phù hợp.

Phải đảm bảo:

* user thường không truy cập Admin;
* không chỉ ẩn menu;
* backend phải luôn kiểm tra quyền;
* request trực tiếp tới `/api/admin/*` cũng phải bị chặn;
* user bị khóa không tiếp tục sử dụng API;
* Admin và Super Admin được phân biệt nếu cần.

Có thể xây:

```text
USER
ADMIN
SUPER_ADMIN
```

Quyền ví dụ:

```text
USER
- sử dụng sản phẩm

ADMIN
- xem dashboard
- quản lý user
- xem jobs
- xem usage
- quản lý quota
- xem audit logs

SUPER_ADMIN
- tất cả quyền ADMIN
- cấu hình AI
- cấu hình provider
- cấu hình billing
- thay đổi system settings
- cấp/revoke quyền Admin
```

Không tin tưởng role gửi từ frontend.

Authorization phải được xác minh phía API.

---

# 4. LIÊN KẾT ADMIN VỚI ĐĂNG KÝ / ĐĂNG NHẬP

Admin phải sử dụng chung hệ thống Authentication hiện tại.

Flow:

```text
REGISTER
   ↓
LOGIN
   ↓
AUTH SESSION/JWT
   ↓
GET CURRENT USER
   ↓
CHECK ROLE/PERMISSION
   ↓
User → User Dashboard
Admin → có quyền truy cập Admin Console
```

Không tạo form login Admin riêng nếu không thật sự cần thiết.

Trang login hiện tại phải đăng nhập được cho:

* User;
* Admin;
* Super Admin.

Sau đăng nhập:

User bình thường:

```text
/dashboard
```

Admin:

có thể vào User Dashboard nhưng có nút:

```text
Admin Console
```

Super Admin tương tự.

Nếu user thường nhập:

```text
/admin
```

phải redirect hoặc hiển thị 403 đúng chuẩn.

Không render Admin UI rồi mới chặn.

---

# 5. ADMIN LAYOUT MỚI

Thiết kế Admin theo phong cách SaaS hiện đại:

* clean;
* professional;
* data-oriented;
* enterprise;
* ít màu gây rối;
* responsive;
* dark/light compatible nếu hệ thống đang hỗ trợ;
* ưu tiên readability.

Sidebar:

```text
ADMIN CONSOLE

Overview

MANAGEMENT
Users
AI Jobs
Projects
Documents
Templates

USAGE & BILLING
AI Usage
Quotas
Plans
Payments

OPERATIONS
Automations
Integrations
System Health
Audit Logs

CONFIGURATION
AI Models
Providers
System Settings
```

Menu không nên quá dày.

Cho phép collapse sidebar.

Header:

```text
Breadcrumb
Global Search
System Status
Notification
Admin Account
Return to User App
```

---

# 6. MODULE 1 — ADMIN OVERVIEW

Route:

```text
/admin
```

Đây phải là **Operations Dashboard thật**.

## KPI chính

Card:

```text
Total Users
Active Users
New Users
AI Jobs Today
Successful Jobs
Failed Jobs
Reports Generated
Documents Processed
Tokens Used
Estimated AI Cost
Storage Used
Active Automations
```

Mỗi card nên có:

* giá trị;
* % tăng/giảm;
* kỳ so sánh;
* tooltip giải thích;
* loading state;
* error state.

Ví dụ:

```text
Users
12,481
+8.4% vs previous 30 days
```

Không tính `Active Users = Total Users`.

Active User phải dựa vào tiêu chí thực:

```text
last_login_at
last_activity_at
usage event
job execution
```

và định nghĩa rõ.

---

# 7. BIỂU ĐỒ ADMIN OVERVIEW

Xây nhiều visualization hữu ích.

## User Growth

Line chart:

```text
New Users
Active Users
```

Filter:

```text
7 days
30 days
90 days
This year
Custom
```

## AI Usage Trend

Line/area chart:

```text
Input Tokens
Output Tokens
Total Tokens
```

Theo:

```text
hour/day/week/month
```

## AI Cost

Bar/line chart:

```text
Estimated Cost
```

Theo ngày/tháng.

Có breakdown:

```text
Model
Feature
User
Provider
```

## AI Job Status

Donut/pie:

```text
Completed
Running
Queued
Failed
Cancelled
```

## Feature Usage

Horizontal bar:

```text
Generate Report
Excel Analysis
Google Sheets Analysis
Deep Research
OCR
DOCX Export
Document Chat
Automation
```

## Top Models

```text
Gemini
OpenAI
Claude
...
```

Hiển thị:

```text
requests
tokens
cost
latency
error rate
```

Nếu provider nào chưa tích hợp thì không giả dữ liệu.

---

# 8. MODULE 2 — USERS MANAGEMENT

Route:

```text
/admin/users
```

Xây bảng quản lý user chuyên nghiệp.

Columns:

```text
User
Email
Role
Plan
Status
Usage
Quota
Projects
Last Active
Created At
Actions
```

Tính năng:

* search;
* pagination;
* sort;
* filter;
* server-side query;
* export CSV nếu phù hợp.

Filters:

```text
Role
Plan
Status
Registration Date
Last Active
Quota Status
```

Actions:

```text
View
Lock
Unlock
Change Plan
Adjust Quota
Reset Quota
Grant Admin
Revoke Admin
```

Các action nguy hiểm phải confirmation.

Ví dụ:

```text
Lock account?

User will immediately lose access to protected features.

Reason:
[________________]

Cancel      Lock Account
```

Reason phải được ghi vào Audit Log.

---

# 9. USER DETAIL

Route:

```text
/admin/users/[id]
```

Đây là một trong những màn quan trọng nhất.

Header:

```text
Avatar
Name
Email
Status
Role
Plan
Created
Last Active
```

Tabs:

```text
Overview
Usage
Projects
Documents
AI Jobs
Billing
Audit History
```

## Overview

Hiển thị:

```text
Plan
Quota
AI requests
Tokens
Storage
Reports
Projects
Documents
Last login
Last activity
```

## Usage

Biểu đồ:

```text
Requests over time
Tokens over time
Cost over time
Usage by feature
Usage by model
```

## Projects

Các project thuộc user.

## Documents

Các tài liệu user upload.

Không cho Admin tự động đọc nội dung tài liệu nếu chưa có permission phù hợp.

Metadata và nội dung phải phân biệt rõ.

## Jobs

Hiển thị job history.

## Billing

Plan + payment history.

## Audit

Các thao tác Admin liên quan đến user.

---

# 10. MODULE 3 — AI JOBS

Route:

```text
/admin/ai-jobs
```

Admin cần theo dõi toàn bộ task AI.

Job types:

```text
REPORT_GENERATION
DATA_ANALYSIS
SPREADSHEET_ANALYSIS
GOOGLE_SHEETS_ANALYSIS
OCR
DEEP_RESEARCH
DOCX_EXPORT
DOCUMENT_PROCESSING
AUTOMATION
```

Table:

```text
Job ID
Type
User
Project
Model
Status
Progress
Duration
Tokens
Cost
Created
Actions
```

Status:

```text
QUEUED
RUNNING
COMPLETED
FAILED
CANCELLED
RETRYING
```

Filter:

```text
Status
Job Type
Model
Provider
User
Date
Duration
```

Search:

```text
Job ID
User email
Project
```

---

# 11. AI JOB DETAIL

Route:

```text
/admin/ai-jobs/[id]
```

Hiển thị:

```text
Job ID
User
Feature
Provider
Model
Created
Started
Finished
Duration
Status
Retry count
Tokens
Estimated cost
```

Timeline:

```text
Queued
↓
Started
↓
Processing
↓
AI call
↓
Post processing
↓
Completed
```

Error:

```text
Error Type
Error Message
Stack/technical detail
Provider response
Retry count
```

Không hiển thị secret/API key.

Actions:

```text
Cancel
Retry
```

Chỉ cho phép nếu trạng thái phù hợp.

Không retry mù.

Phải kiểm tra job có idempotency hoặc duplicate protection.

---

# 12. MODULE 4 — AI USAGE

Route:

```text
/admin/usage
```

Đây là trang phân tích chi tiết chi phí AI.

KPI:

```text
Total Requests
Input Tokens
Output Tokens
Total Tokens
Estimated Cost
Average Latency
Success Rate
Error Rate
```

Filter:

```text
Date Range
Provider
Model
Feature
User
```

Biểu đồ:

### Token trend

```text
Input Token
Output Token
```

### Cost trend

```text
Daily Cost
```

### Usage by Model

Bar chart.

### Usage by Feature

Bar chart.

### Provider Distribution

Pie/donut.

### Cost by User

Top users.

Table:

```text
User
Requests
Tokens
Cost
Most Used Model
Most Used Feature
```

---

# 13. CHI PHÍ AI PHẢI TÍNH ĐÚNG

Không hard-code tổng lịch sử khi UI chọn tháng.

Backend query phải nhận:

```text
from
to
model
provider
feature
user
```

Cost phải dựa trên usage record.

Nếu hệ thống chưa có bảng pricing model, cân nhắc:

```text
AIModelPricing
- provider
- model
- input_price
- output_price
- effective_from
- effective_to
```

Không hard-code giá trong React component.

Lưu usage nguyên bản để khi pricing thay đổi vẫn truy vết được.

---

# 14. MODULE 5 — QUOTA

Route:

```text
/admin/quotas
```

Quản lý:

```text
AI Requests
Tokens
Reports
Data Analyses
OCR pages
Research jobs
Storage
Automation executions
```

Hiển thị:

```text
User
Plan
Used
Limit
Remaining
Reset Date
Status
```

Status:

```text
Normal
Near Limit
Exceeded
Unlimited
```

Admin có thể:

```text
Add quota
Reduce quota
Reset quota
Temporary bonus
```

Mọi chỉnh sửa phải:

* yêu cầu lý do;
* ghi Audit Log;
* lưu before/after.

---

# 15. MODULE 6 — PROJECTS

Route:

```text
/admin/projects
```

Dùng để hỗ trợ vận hành, không phải để Admin tùy tiện xem dữ liệu cá nhân.

Columns:

```text
Project
Owner
Documents
Reports
Storage
AI Jobs
Status
Created
Last Updated
```

Filter:

```text
Owner
Status
Date
Storage
```

Project detail:

```text
Metadata
Usage
Documents
Reports
Jobs
Errors
```

---

# 16. MODULE 7 — DOCUMENTS & STORAGE

Route:

```text
/admin/documents
```

Quản lý:

```text
file metadata
owner
project
type
size
processing status
OCR status
storage location
created
```

Statuses:

```text
Uploaded
Processing
Ready
Failed
Orphaned
Deleted
```

Cho phép phát hiện:

```text
orphan files
failed uploads
failed parsing
storage record missing
database record missing
```

Không cho Admin download/read file nhạy cảm mặc định.

Nếu có chức năng đó, phải permission riêng và Audit Log.

---

# 17. STORAGE DASHBOARD

Cards:

```text
Total Storage
Uploads Today
Average File Size
Failed Files
Orphaned Files
```

Charts:

```text
Storage growth over time
Storage by file type
Storage by user
Storage by project
```

Không hard-code storage.

Nếu storage provider không hỗ trợ lấy số liệu thì hiển thị:

```text
Storage metrics unavailable
```

---

# 18. MODULE 8 — TEMPLATES

Route:

```text
/admin/templates
```

Quản lý:

```text
Word Templates
Report Templates
Shared Templates
System Templates
```

Fields:

```text
Name
Category
Version
Status
Created By
Usage Count
Last Updated
```

Status:

```text
Draft
Published
Hidden
Deprecated
Error
```

Actions:

```text
Preview
Publish
Unpublish
Create Version
Archive
Validate
```

Validation:

* DOCX structure;
* placeholder;
* template variables;
* corrupted file;
* incompatible format.

---

# 19. MODULE 9 — AUTOMATIONS

Route:

```text
/admin/automations
```

Admin xem:

```text
Automation
Owner
Trigger
Schedule
Status
Last Run
Next Run
Success Rate
```

Status:

```text
Active
Paused
Failed
Disabled
```

Detail:

```text
execution history
error
duration
jobs created
integration dependency
```

Actions:

```text
Pause
Resume
Run Once
```

Không chạy lại task có side effect nguy hiểm nếu không có protection.

---

# 20. MODULE 10 — INTEGRATIONS

Route:

```text
/admin/integrations
```

Theo dõi:

```text
Google Sheets
Google Drive
OAuth
Email
Storage
Payment Provider
AI Provider
```

Không hiển thị:

```text
API key
refresh token
access token
client secret
```

Chỉ hiển thị:

```text
Connected
Disconnected
Expired
Error
```

Ví dụ:

```text
Google Sheets

Status: Connected
Connected users: 58
Errors 24h: 2
Last provider error: 12 minutes ago
```

---

# 21. MODULE 11 — BILLING & PLANS

Route:

```text
/admin/billing
/admin/billing/plans
/admin/payments
```

Trước tiên audit Billing hiện tại.

Có dấu hiệu hệ thống sử dụng:

```text
plan
```

nhưng chỗ khác lại đọc:

```text
plan_tier
```

Phải thống nhất.

Một field phải là source of truth.

Ví dụ:

```text
FREE
STARTER
PRO
BUSINESS
```

Không để frontend tự quyết định quyền lợi.

Backend entitlement service phải xác định:

```text
plan
→ features
→ quota
→ limits
```

---

# 22. PAYMENT SECURITY

Đặc biệt audit:

```text
confirm-payment
```

Không được nâng plan chỉ dựa trên `session_id` do frontend gửi.

Phải verify payment với provider/server-side record.

Flow:

```text
Create Checkout
↓
Payment Provider
↓
Payment Completed
↓
Webhook / Server Verification
↓
Verify amount
Verify currency
Verify user/customer
Verify product/plan
Verify transaction status
↓
Create/Update Payment
↓
Activate Subscription
↓
Apply Plan
↓
Apply Quota
↓
Audit
```

Phải chống:

```text
fake session_id
duplicate webhook
replay
double upgrade
wrong user
wrong amount
```

Sử dụng idempotency.

---

# 23. PLANS MANAGEMENT

Admin có thể xem:

```text
Plan
Price
Features
Limits
Active Users
Status
```

Nếu cho sửa Plan:

chỉ SUPER_ADMIN.

Thay đổi ảnh hưởng user hiện tại phải rõ ràng.

Không để thay đổi quota âm thầm.

---

# 24. PAYMENT MANAGEMENT

Table:

```text
Transaction ID
User
Plan
Amount
Currency
Provider
Status
Created
Paid At
```

Status:

```text
Pending
Paid
Failed
Refunded
Cancelled
```

Detail phải chứa:

```text
provider transaction id
metadata
verification state
webhook events
```

Không hiển thị dữ liệu nhạy cảm.

---

# 25. MODULE 12 — AUDIT LOG

Route:

```text
/admin/audit-logs
```

Đây là chức năng bắt buộc.

Các action phải log:

```text
USER_LOCK
USER_UNLOCK
ROLE_CHANGE
PLAN_CHANGE
QUOTA_CHANGE
JOB_CANCEL
JOB_RETRY
TEMPLATE_PUBLISH
AUTOMATION_PAUSE
SYSTEM_SETTING_CHANGE
AI_MODEL_CHANGE
```

Schema nên chứa:

```text
id
actor_user_id
action
target_type
target_id
before
after
reason
metadata
ip_address
user_agent
created_at
```

Không lưu:

```text
password
token
API key
secret
```

Audit Logs là append-only.

Không cho Admin thường sửa/xóa.

---

# 26. AUDIT UI

Table:

```text
Time
Admin
Action
Target
Reason
IP
```

Filter:

```text
Admin
Action
Target
Date
```

Detail:

```text
Before
After
Reason
Metadata
```

Có diff viewer cho before/after nếu phù hợp.

---

# 27. MODULE 13 — SYSTEM HEALTH

Route:

```text
/admin/system
```

Hiển thị tình trạng thực:

```text
API
Database
Redis
Worker
Queue
Storage
AI Providers
Payment Provider
```

Statuses:

```text
Healthy
Degraded
Down
Unknown
```

Không hard-code `"Healthy"`.

Phải dựa trên health check thật.

Nếu chưa có health check:

xây endpoint thích hợp.

Không chạy health check quá nặng.

---

# 28. SYSTEM HEALTH CHARTS

Charts:

```text
API latency
Request volume
Error rate
Job queue length
Job processing time
Provider latency
Provider error rate
```

Theo thời gian.

Có range:

```text
1h
6h
24h
7d
```

Nếu hệ thống chưa lưu historical telemetry thì:

* tạo cấu trúc phù hợp;
* hoặc chỉ hiển thị current status;
* không giả historical chart.

---

# 29. MODULE 14 — AI MODEL CONFIG

Route:

```text
/admin/ai-config
```

Chỉ SUPER_ADMIN.

Hiển thị:

```text
Feature
Primary Model
Fallback Model
Timeout
Retry
Enabled
```

Ví dụ:

```text
Report Generation
Primary: Gemini ...
Fallback: ...
```

Feature mapping:

```text
report_generation
data_analysis
spreadsheet_analysis
ocr
research
chat
```

Không expose API keys.

---

# 30. PROVIDER MANAGEMENT

Route:

```text
/admin/providers
```

Hiển thị:

```text
Provider
Status
Models
Requests
Error Rate
Latency
Last Error
```

API key:

```text
Configured
Not configured
```

KHÔNG hiển thị key thật.

Không gửi key xuống frontend.

---

# 31. GLOBAL SEARCH

Admin Header nên có global search:

Search:

```text
User email
User name
Project
Document
Job ID
Payment ID
```

Kết quả chia category:

```text
Users
Projects
Jobs
Payments
```

Có debounce.

Không query database ở từng ký tự thiếu kiểm soát.

---

# 32. ADMIN NOTIFICATION CENTER

Có thể bổ sung notification cho:

```text
AI failure spike
Provider outage
High error rate
Quota anomalies
Payment failures
Storage threshold
Worker offline
```

Chỉ cảnh báo khi có dữ liệu đủ tin cậy.

Không tạo fake notifications.

---

# 33. FILTER SYSTEM DÙNG CHUNG

Tạo reusable filter components:

```text
DateRangeFilter
UserFilter
StatusFilter
ProviderFilter
ModelFilter
FeatureFilter
PlanFilter
```

Filter có thể đồng bộ URL query:

```text
/admin/usage?from=...&to=...&model=...
```

Để refresh/share URL không mất trạng thái.

---

# 34. TABLE COMPONENT CHUẨN ADMIN

Tạo reusable DataTable:

* pagination server-side;
* sorting;
* filtering;
* empty state;
* loading;
* error;
* retry;
* responsive;
* column visibility nếu hợp lý.

Không tải toàn bộ database về frontend rồi filter.

---

# 35. STATES BẮT BUỘC

Mọi màn phải xử lý:

```text
Loading
Empty
Error
Unauthorized
Forbidden
Success
Partial data
```

Ví dụ lỗi API:

Không chỉ:

```text
Something went wrong
```

mà nên:

```text
Unable to load AI usage

The usage service returned an error.

Retry
```

---

# 36. DỮ LIỆU THẬT

Quy tắc bắt buộc:

### TUYỆT ĐỐI KHÔNG:

```text
const totalUsers = 1250
const aiCost = 39.99
const providerHealth = 98
```

Nếu API chưa có:

1. kiểm tra DB;
2. thiết kế query/service;
3. tạo endpoint;
4. frontend gọi endpoint;
5. xử lý lỗi.

---

# 37. TIME RANGE

Tất cả metrics phụ thuộc thời gian phải hỗ trợ range.

Ví dụ API:

```text
GET /admin/overview?from=&to=
GET /admin/usage?from=&to=
```

Backend phải query đúng khoảng thời gian.

Không hiển thị "This month" nhưng cộng toàn bộ lịch sử.

---

# 38. TIMEZONE

Chuẩn hóa timezone.

Database ưu tiên UTC.

Frontend format theo timezone người dùng/admin.

Tránh lỗi chart lệch ngày.

---

# 39. DATABASE INDEXING

Kiểm tra các query Admin.

Nếu cần thêm index cho:

```text
created_at
user_id
status
job_type
provider
model
payment_status
```

hãy tạo migration hợp lý.

Không tạo index vô tội vạ.

---

# 40. PERFORMANCE

Admin dashboard không được chạy hàng chục query lặp.

Có thể sử dụng:

* aggregation;
* grouped query;
* cache ngắn hạn;
* pagination;
* lazy load;
* parallel requests hợp lý.

Overview ưu tiên endpoint tổng hợp thay vì 12 request độc lập nếu backend phù hợp.

---

# 41. SECURITY

Kiểm tra:

```text
Authentication
Authorization
RBAC
IDOR
Mass assignment
Rate limiting
Input validation
Sensitive logs
Secret leakage
XSS
CSRF nếu cần
```

Đặc biệt Admin API phải chống IDOR.

Ví dụ:

```text
/admin/users/{id}
```

phải check permission.

---

# 42. ADMIN ACTION CONFIRMATION

Các action nguy hiểm:

```text
Lock user
Change plan
Change quota
Grant admin
Cancel job
Retry job
Delete resource
Change AI model
Change system config
```

phải có confirmation.

Với action quan trọng yêu cầu:

```text
Reason
```

Audit log reason.

---

# 43. UI/UX

Thiết kế giống sản phẩm SaaS thực tế.

Không dùng quá nhiều gradient.

Không dùng quá nhiều màu neon.

Không biến tất cả thành card.

Ưu tiên:

```text
white space
hierarchy
readable typography
data density
professional charts
clear filters
clear status badges
```

Cards chỉ sử dụng cho KPI/highlights.

Tables dùng cho management.

Charts dùng cho trend/comparison.

---

# 44. CHART TOOLTIP

Tooltip chart phải có:

```text
Date
Metric
Value
```

Ví dụ:

```text
05 Sep 2026

AI Requests    1,248
Tokens         3.8M
Cost           $12.48
```

Nếu nhiều metric khác đơn vị không nên nhét chung một axis.

---

# 45. DRILL DOWN

Các chart nên cho phép drill-down khi hợp lý.

Ví dụ:

click:

```text
Failed Jobs: 42
```

→

```text
/admin/ai-jobs?status=failed
```

Click user:

→ user detail.

Click provider:

→ filtered Usage.

---

# 46. RESPONSIVE

Admin chủ yếu desktop nhưng phải usable trên:

```text
1440px
1280px
1024px
tablet
```

Mobile không cần ép bảng thành hàng chục cột.

Có thể dùng:

* horizontal scroll;
* card detail;
* hide secondary columns.

---

# 47. ACCESSIBILITY

Phải:

* keyboard navigation;
* semantic HTML;
* aria-label hợp lý;
* focus states;
* sufficient contrast;
* chart không chỉ dựa vào màu.

---

# 48. BACKEND API DESIGN

Có thể tổ chức:

```text
/api/v1/admin/overview
/api/v1/admin/users
/api/v1/admin/users/{id}
/api/v1/admin/jobs
/api/v1/admin/jobs/{id}
/api/v1/admin/usage
/api/v1/admin/quotas
/api/v1/admin/projects
/api/v1/admin/documents
/api/v1/admin/templates
/api/v1/admin/automations
/api/v1/admin/integrations
/api/v1/admin/plans
/api/v1/admin/payments
/api/v1/admin/audit-logs
/api/v1/admin/system/health
/api/v1/admin/ai-config
```

Không nhất thiết giữ đúng tên này nếu codebase có convention khác.

Tuân theo convention hiện tại.

---

# 49. SERVICE LAYER

Không nhồi SQL/query trực tiếp vào API route nếu dự án đang sử dụng service pattern.

Có thể:

```text
AdminOverviewService
AdminUserService
AdminJobService
AdminUsageService
AdminBillingService
AuditService
SystemHealthService
```

Tái sử dụng domain service hiện có.

---

# 50. AUDIT SERVICE

Tạo service dùng chung:

```text
audit.log(
 actor,
 action,
 target,
 before,
 after,
 reason
)
```

Mọi administrative mutation phải gọi service này.

Nếu transaction thất bại:

không tạo audit event sai trạng thái.

---

# 51. PLAN + QUOTA DOMAIN SERVICE

Không để controller tự sửa:

```text
user.plan = "pro"
```

Hãy xây service:

```text
change_user_plan()
```

Service chịu trách nhiệm:

```text
validate plan
update subscription
apply entitlements
apply quota
audit
transaction
```

---

# 52. ADMIN FRONTEND API CLIENT

Không gọi fetch rải rác.

Tạo module có cấu trúc:

```text
adminApi
adminUserApi
adminJobApi
adminUsageApi
adminBillingApi
```

Hoặc tuân theo API architecture hiện có.

TypeScript types phải rõ ràng.

Không dùng `any` vô tội vạ.

---

# 53. URL & NAVIGATION

Admin phải duy trì state thông qua URL khi hợp lý.

Ví dụ:

```text
/admin/users?page=2&plan=pro&status=active
```

Back/forward browser phải hoạt động đúng.

---

# 54. LOADING

Dùng skeleton cho:

* KPI;
* table;
* chart.

Không dùng spinner toàn màn hình cho mọi trang.

---

# 55. EMPTY STATE

Ví dụ:

```text
No failed AI jobs

No failed jobs were recorded for the selected period.
```

Không hiển thị chart trống kỳ quặc.

---

# 56. ERROR OBSERVABILITY

Frontend error không được nuốt.

Backend phải log lỗi phù hợp.

Không log:

```text
API key
JWT
password
document sensitive content
```

---

# 57. ADMIN HOME QUICK ACTIONS

Có thể thêm:

```text
Review Failed Jobs
Users Near Quota
Payment Issues
System Health
```

Nhưng chỉ hiển thị số liệu thật.

---

# 58. SECURITY PRIVACY

Admin không đồng nghĩa với quyền đọc mọi nội dung user.

Phân biệt:

```text
Operational Metadata
```

và:

```text
User Content
```

Admin thông thường có thể xem metadata.

Quyền xem nội dung phải riêng.

---

# 59. TESTING

Sau implementation, kiểm thử:

## Authentication

```text
Unauthenticated → /admin blocked
User → /admin blocked
Admin → allowed
Super Admin → allowed
```

## Backend

```text
User gọi /api/admin/users → 403
Admin → 200
```

## User management

```text
Lock
Unlock
Plan
Quota
```

## Jobs

```text
filter
pagination
retry
cancel
```

## Billing

```text
invalid session
unpaid transaction
duplicate confirmation
```

## Audit

Mutation phải tạo audit record.

---

# 60. TEST ROLE MATRIX

Kiểm thử:

| Action          | User |      Admin | Super Admin |
| --------------- | ---: | ---------: | ----------: |
| View Admin      |    ❌ |          ✅ |           ✅ |
| View Users      |    ❌ |          ✅ |           ✅ |
| Lock User       |    ❌ |          ✅ |           ✅ |
| Adjust Quota    |    ❌ |          ✅ |           ✅ |
| Grant Admin     |    ❌ | ❌/optional |           ✅ |
| AI Config       |    ❌ |          ❌ |           ✅ |
| Provider Config |    ❌ |          ❌ |           ✅ |

Điều chỉnh theo business rule thực tế.

---

# 61. KHÔNG LÀM HỎNG USER APPLICATION

Sau khi nâng Admin:

kiểm tra lại:

```text
register
login
logout
user dashboard
projects
reports
analysis
research
templates
automation
billing
```

Admin implementation không được làm hỏng flow người dùng.

---

# 62. ƯU TIÊN TRIỂN KHAI

Không xây tất cả một lúc thiếu kiểm soát.

## PHASE 0 — AUDIT & FIX

Làm trước:

```text
Admin authorization
Role consistency
Usage metrics
Plan/plan_tier
Billing verification
Hard-coded admin metrics
```

## PHASE 1 — ADMIN CORE

Xây:

```text
Admin Layout
Overview
Users
User Detail
AI Jobs
AI Job Detail
Usage
Quota
Audit Logs
```

## PHASE 2 — OPERATIONS

Xây:

```text
Projects
Documents
Storage
Templates
Automation
Integrations
System Health
```

## PHASE 3 — COMMERCIAL

Xây:

```text
Plans
Payments
Subscriptions
Billing monitoring
```

## PHASE 4 — PLATFORM CONFIG

Xây:

```text
AI models
Provider
System settings
advanced monitoring
```

---

# 63. CÁCH LÀM VIỆC

Không hỏi tôi những câu hỏi có thể tự xác định bằng cách đọc source code.

Nếu có implementation hiện tại, hãy ưu tiên nâng cấp nó.

Không tự xóa tính năng đang hoạt động.

Không rewrite cả project nếu không cần.

Không thay stack công nghệ.

Không thêm dependency lớn nếu framework hiện tại đã giải quyết được.

---

# 64. TRƯỚC MỖI THAY ĐỔI LỚN

Xác định:

```text
Existing implementation
Problem
Required change
Files affected
Potential regression
```

Sau đó mới sửa.

---

# 65. SAU MỖI MODULE

Kiểm tra:

```text
TypeScript
Lint
Backend tests
Frontend build
API contract
Authorization
```

Không tuyên bố hoàn thành khi build đang lỗi.

---

# 66. ACCEPTANCE CRITERIA TỔNG

Admin được xem là đạt khi:

1. `/admin` có layout riêng.

2. User bình thường không truy cập được.

3. Admin dùng chung login/session hiện tại.

4. Overview dùng dữ liệu thật.

5. User management có thao tác thật.

6. User detail xem được usage/jobs/projects.

7. AI Jobs theo dõi job thật.

8. Usage lấy token/request/cost thật.

9. Quota đồng bộ với Plan.

10. Mọi Admin mutation ghi Audit Log.

11. Billing không thể fake nâng plan bằng client input.

12. System Health không hard-code.

13. Không expose secret.

14. Search/filter/pagination hoạt động server-side khi cần.

15. Các chart có range thời gian.

16. Loading/error/empty states đầy đủ.

17. Responsive.

18. Không phá User Dashboard.

19. Build/test thành công.

20. Không tồn tại dữ liệu giả được trình bày như dữ liệu thật.

---

# 67. KẾT QUẢ CUỐI CÙNG TÔI MUỐN

Sau khi hoàn thành, dự án phải có cảm giác như một SaaS thật:

```text
USER SIDE
Register
Login
Projects
Documents
AI Analysis
Reports
Research
Automation
Templates
Billing

           │
           │ data + usage
           ▼

ADMIN CONSOLE
Overview
Users
AI Jobs
Usage
Quota
Projects
Documents
Templates
Automation
Integrations
Billing
Payments
Audit
System
AI Config
```

Admin phải giúp trả lời được:

```text
Ai đang sử dụng hệ thống?

Họ đang sử dụng chức năng gì?

Có bao nhiêu user đang hoạt động?

AI đang xử lý những job nào?

Job nào thất bại?

Lỗi do đâu?

Provider nào đang có vấn đề?

Model nào được sử dụng nhiều nhất?

Bao nhiêu token đã tiêu thụ?

Chi phí AI bao nhiêu?

User nào tiêu thụ nhiều nhất?

Feature nào tốn nhiều nhất?

User nào sắp hết quota?

Hệ thống đang lưu bao nhiêu dữ liệu?

Thanh toán nào thành công/thất bại?

Admin nào đã thay đổi tài khoản?

Cấu hình hệ thống hiện đang như thế nào?
```

---

# 68. YÊU CẦU CUỐI CÙNG

Hãy bắt đầu bằng việc **audit source code hiện tại**.

Sau đó lập mapping:

```text
Existing
Partially implemented
Missing
Incorrect
Hard-coded
Security issue
```

Ưu tiên sửa những phần `Incorrect`, `Hard-coded` và `Security issue` trước.

Tiếp theo triển khai Admin theo từng phase ở trên.

Không tạo UI giả để che backend chưa hoàn thiện.

Không báo `"done"` chỉ vì giao diện đã render.

Một module chỉ được coi là hoàn thành khi:

```text
UI
+
API
+
Database
+
Authorization
+
Validation
+
Audit
+
Error handling
+
Real data
+
Testing
```

đều hoạt động tương ứng.

Cuối quá trình hãy báo cáo:

```text
1. Các file đã sửa
2. Các file đã tạo
3. Database/migration thay đổi
4. API mới/thay đổi
5. Các route Admin mới
6. Các vấn đề bảo mật đã sửa
7. Các metrics hiện lấy từ đâu
8. Module nào hoàn thành
9. Module nào còn thiếu
10. Test/build đã chạy
11. Những vấn đề còn tồn tại
```

Không được che giấu lỗi hoặc nói hoàn thành khi chưa kiểm chứng.

Mục tiêu cuối cùng là xây dựng **Admin Console có thể dùng để vận hành dự án thật**, không phải một dashboard trang trí.
