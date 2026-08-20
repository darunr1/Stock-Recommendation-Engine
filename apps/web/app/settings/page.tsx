import AppShell from "@/components/AppShell";
import SettingsPanel from "@/components/workspace/SettingsPanel";
export const metadata = { title: "Settings" };
export default function Page() {
  return (
    <AppShell>
      <SettingsPanel />
    </AppShell>
  );
}
