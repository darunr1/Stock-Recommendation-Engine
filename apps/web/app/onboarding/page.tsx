import AppShell from "@/components/AppShell";
import Onboarding from "@/components/workspace/Onboarding";
export const metadata = { title: "Onboarding" };
export default function Page() {
  return (
    <AppShell>
      <Onboarding />
    </AppShell>
  );
}
