import AppShell from "@/components/AppShell";
import AdminPanels from "@/components/workspace/AdminPanels";
export const metadata = { title: "Admin feedback" };
export default function Page() {
  return (
    <AppShell>
      <AdminPanels kind="feedback" />
    </AppShell>
  );
}
