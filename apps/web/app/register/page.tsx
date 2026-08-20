import { Suspense } from "react";
import AuthFlow from "@/components/AuthFlow";
export const metadata = { title: "Create account" };
export default function Register() {
  return (
    <Suspense>
      <AuthFlow mode="register" />
    </Suspense>
  );
}
