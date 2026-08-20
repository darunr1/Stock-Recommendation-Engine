import AppShell from "@/components/AppShell";
import Backtests from "@/components/workspace/Backtests";
export const metadata = { title: "Backtests" };
export default function Page() {
  return (
    <AppShell>
      <Backtests />
    </AppShell>
  );
}
