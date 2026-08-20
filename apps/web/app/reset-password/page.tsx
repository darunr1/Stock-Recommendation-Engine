import { Suspense } from "react";
import AuthFlow from "@/components/AuthFlow";
export const metadata = { title: "Reset password" };
export default function Reset() {
  return (
    <Suspense>
      <AuthFlow mode="reset" />
    </Suspense>
  );
}
