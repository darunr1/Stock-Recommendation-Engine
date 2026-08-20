import { Suspense } from "react";
import AuthFlow from "@/components/AuthFlow";
export const metadata = { title: "Sign in" };
export default function Login() {
  return (
    <Suspense>
      <AuthFlow mode="login" />
    </Suspense>
  );
}
