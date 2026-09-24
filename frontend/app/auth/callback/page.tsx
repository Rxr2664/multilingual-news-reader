"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useEffect } from "react";
import { setToken, api } from "@/lib/api";

function Inner() {
  const params = useSearchParams();
  const router = useRouter();
  useEffect(() => {
    const token = params.get("token");
    if (!token) return;
    setToken(token);
    api<{ onboarded: boolean }>("/auth/me").then((me) => {
      router.replace(me.onboarded ? "/feed" : "/onboarding");
    });
  }, [params, router]);
  return <p className="muted">Signing you in…</p>;
}

export default function Callback() {
  return (
    <Suspense>
      <Inner />
    </Suspense>
  );
}
