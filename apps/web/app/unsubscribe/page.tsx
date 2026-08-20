import { Suspense } from "react";
import AuthFlow from "@/components/AuthFlow";
export const metadata = { title: "Unsubscribe" };
export default function Unsubscribe() {
  return (
    <Suspense>
      <AuthFlow mode="unsubscribe" />
    </Suspense>
  );
}
