import AppShell from "@/components/AppShell";
import Watchlist from "@/components/workspace/Watchlist";
export const metadata = { title: "Watchlist" };
export default function Page() {
  return (
    <AppShell>
      <Watchlist />
    </AppShell>
  );
}
