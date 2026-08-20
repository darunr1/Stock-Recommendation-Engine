import AppShell from "@/components/AppShell";
import DataHealth from "@/components/workspace/DataHealth";
export const metadata = { title: "Data health" };
export default function Page() {
  return (
    <AppShell>
      <DataHealth />
    </AppShell>
  );
}
