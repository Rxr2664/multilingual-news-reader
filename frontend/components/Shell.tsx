"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { COUNTRIES, User, api, clearToken } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function Shell({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function switchCountry(code: string, language: string) {
    const next = await api<User>("/auth/me", {
      method: "PATCH",
      body: JSON.stringify({ target_country: code, target_language: language }),
    });
    setUser(next);
    router.push("/feed");
    router.refresh();
  }

  return (
    <div className="page">
      <header className="top">
        <Link href="/feed" className="brand">
          Lemma
        </Link>
        <nav>
          {COUNTRIES.map((c) => (
            <button
              key={c.code}
              className={user?.target_country === c.code ? "chip on" : "chip"}
              onClick={() => switchCountry(c.code, c.language)}
            >
              {c.label}
            </button>
          ))}
        </nav>
        <div className="who">
          {user ? <span>{user.email}</span> : null}
          <button
            className="ghost"
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
          >
            Sign out
          </button>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
