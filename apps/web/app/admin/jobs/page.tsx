import AppShell from "@/components/AppShell";
import AdminPanels from "@/components/workspace/AdminPanels";
export const metadata = { title: "Admin jobs" };
export default function Page() {
  return (
    <AppShell>
      <AdminPanels kind="jobs" />
    </AppShell>
  );
}
