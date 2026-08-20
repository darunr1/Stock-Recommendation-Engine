import AppShell from "@/components/AppShell";
import AdminPanels from "@/components/workspace/AdminPanels";
export const metadata = { title: "Product metrics" };
export default function Page() {
  return (
    <AppShell>
      <AdminPanels kind="metrics" />
    </AppShell>
  );
}
