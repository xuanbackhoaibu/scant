const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050/api/v1";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const errorMsg = data?.detail || (typeof data === "string" ? data : "An error occurred");
    throw new ApiError(errorMsg, response.status, data);
  }

  return data as T;
}

export const api = {
  // Auth
  auth: {
    register: (data: any) => request<any>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
    login: (data: any) => request<any>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
    me: () => request<any>("/auth/me"),
  },

  // Projects
  projects: {
    list: () => request<any[]>("/projects"),
    get: (id: string) => request<any>(`/projects/${id}`),
    create: (data: any) => request<any>("/projects", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: any) => request<any>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: string) => request<any>(`/projects/${id}`, { method: "DELETE" }),
  },

  // Files
  files: {
    upload: (formData: FormData) => request<any>("/files/upload", { method: "POST", body: formData }),
    listByProject: (projectId: string) => request<any[]>(`/files/project/${projectId}`),
  },

  // Templates
  templates: {
    list: () => request<any[]>("/templates"),
    uploadDocx: (formData: FormData) => request<any>("/templates/upload-docx", { method: "POST", body: formData }),
  },

  // AI Generation, Drafting & Review
  ai: {
    analyzeIntent: (data: any) => request<any>("/ai/analyze-intent", { method: "POST", body: JSON.stringify(data) }),
    generateOutline: (data: any) => request<any>("/ai/generate-outline", { method: "POST", body: JSON.stringify(data) }),
    draftSection: (data: any) => request<any>("/ai/draft-section", { method: "POST", body: JSON.stringify(data) }),
    editSelection: (data: any) => request<any>("/ai/edit-selection", { method: "POST", body: JSON.stringify(data) }),
    checkReport: (reportId: string) => request<any>(`/ai/check-report/${reportId}`, { method: "POST" }),
  },

  // Research
  research: {
    search: (projectId: string, query: string, mode: string = "standard") =>
      request<any>(`/research/search?project_id=${projectId}&query=${encodeURIComponent(query)}&mode=${mode}`, { method: "POST" }),
    listSources: (projectId: string) => request<any[]>(`/research/sources/project/${projectId}`),
    addSource: (data: any) => request<any>("/research/sources", { method: "POST", body: JSON.stringify(data) }),
    traceCitation: (citationId: string) => request<any>(`/research/citations/trace/${citationId}`),
  },

  // Reports
  reports: {
    create: (data: any) => request<any>("/reports", { method: "POST", body: JSON.stringify(data) }),
    get: (id: string) => request<any>(`/reports/${id}`),
    updateSection: (sectionId: string, data: any) => request<any>(`/reports/sections/${sectionId}`, { method: "PUT", body: JSON.stringify(data) }),
  },

  // Exports
  exports: {
    exportDocx: (data: any) => request<any>("/exports/docx", { method: "POST", body: JSON.stringify(data) }),
    exportPdf: (data: any) => request<any>("/exports/pdf", { method: "POST", body: JSON.stringify(data) }),
    getDownloadUrl: (filename: string) => `${API_BASE}/exports/download/${filename}`,
  },

  // Health
  health: () => request<any>("/health"),
};
