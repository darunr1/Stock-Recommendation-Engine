import { Suspense } from "react";
import AppShell from "@/components/AppShell";
import Screener from "@/components/workspace/Screener";
export const metadata = { title: "Screener" };
export default function Page() {
  return (
    <AppShell>
      <Suspense>
        <Screener />
      </Suspense>
    </AppShell>
  );
}
