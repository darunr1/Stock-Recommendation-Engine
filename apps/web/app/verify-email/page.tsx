import { Suspense } from "react";
import AuthFlow from "@/components/AuthFlow";
export const metadata = { title: "Verify email" };
export default function Verify() {
  return (
    <Suspense>
      <AuthFlow mode="verify" />
    </Suspense>
  );
}
