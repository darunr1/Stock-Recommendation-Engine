import AppShell from "@/components/AppShell";
import PaperPortfolio from "@/components/workspace/PaperPortfolio";
export const metadata = { title: "Paper portfolio" };
export default function Page() {
  return (
    <AppShell>
      <PaperPortfolio />
    </AppShell>
  );
}
