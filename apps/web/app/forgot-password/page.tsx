import { Suspense } from "react";
import AuthFlow from "@/components/AuthFlow";
export const metadata = { title: "Forgot password" };
export default function Forgot() {
  return (
    <Suspense>
      <AuthFlow mode="forgot" />
    </Suspense>
  );
}
