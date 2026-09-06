import { Suspense } from 'react';
import { AdminShell } from '@/components/admin/AdminShell';
import './admin.css';
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<p className="p-8">Đang kiểm tra phiên quản trị…</p>}><AdminShell>{children}</AdminShell></Suspense>;
}
