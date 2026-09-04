import { DashboardShell } from "@/components/DashboardShell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardShell contentClassName="mx-auto w-full max-w-7xl p-8">
      {children}
    </DashboardShell>
  );
}
