import { AdminScreen } from '@/components/admin/AdminScreen';
export default async function AdminPage({ params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await params;
  return <AdminScreen path={path} />;
}
