"use client";

import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();

  async function demo() {
    const res = await api<{ access_token: string }>("/auth/demo", { method: "POST" });
    setToken(res.access_token);
    const me = await api<{ onboarded: boolean }>("/auth/me");
    router.push(me.onboarded ? "/feed" : "/onboarding");
  }

  async function google() {
    try {
      const { url } = await api<{ url: string }>("/auth/google/url");
      window.location.href = url;
    } catch {
      alert("Google OAuth is not configured. Use demo login locally.");
    }
  }

  return (
    <div className="auth">
      <div className="card">
        <p className="eyebrow">Multilingual News Reader</p>
        <h1>Read real news at the edge of what you know.</h1>
        <p className="lead">
          Articles scored against your vocabulary. Unknown words highlighted. One tap to mark
          a lemma known — everywhere.
        </p>
        <button onClick={google}>Continue with Google</button>
        <button className="ghost" onClick={demo}>
          Demo login
        </button>
      </div>
    </div>
  );
}
