import { request } from './api';

export type AdminRecord = Record<string, unknown>;
export interface AdminSession { id: string; email: string; name: string; role: string; is_superuser: boolean; permissions: string[] }
export interface AdminPage<T = AdminRecord> { items: T[]; total: number; page: number; page_size: number; [key: string]: unknown }
export interface AdminMetric { key: string; label: string; value: number | null; previous: number | null; change_pct: number | null; unit: string; definition: string; href: string }
export interface AdminOverview { period: AdminRecord; metrics: AdminMetric[]; trends: { users: AdminRecord[]; tokens: AdminRecord[]; cost: AdminRecord[] }; breakdowns: Record<string, AdminRecord[]>; unavailable: unknown[] }
export const adminApi = {
  session: () => request<AdminSession>('/admin/session'),
  get: <T = AdminRecord>(path: string, query = '') => request<T>(`/admin/${path}${query ? `?${query}` : ''}`),
  list: (path: string, query = '') => request<AdminPage>(`/admin/${path}${query ? `?${query}` : ''}`),
  mutate: (path: string, body: AdminRecord, method: 'PATCH' | 'POST' = 'POST') => request<AdminRecord>(`/admin/${path}`, { method, body: JSON.stringify(body) }),
};
