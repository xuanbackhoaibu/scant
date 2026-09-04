import { DashboardShell } from "@/components/DashboardShell";

export default function ProjectsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardShell>{children}</DashboardShell>;
}
