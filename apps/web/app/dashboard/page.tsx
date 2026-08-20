import AppShell from "@/components/AppShell";
import Dashboard from "@/components/workspace/Dashboard";
export const metadata = { title: "Dashboard" };
export default function Page() {
  return (
    <AppShell>
      <Dashboard />
    </AppShell>
  );
}
