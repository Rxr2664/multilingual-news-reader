export type User = {
  id: number;
  email: string;
  name: string;
  target_language: string;
  target_country: string;
  vocab_version: number;
  onboarded: boolean;
};

export type ArticleListItem = {
  id: number;
  title: string;
  url: string;
  source_name: string;
  country: string;
  language: string;
  published_at: string;
  unknown_pct: number;
  unknown_count: number;
  content_lemma_count: number;
};

export type TokenSpan = {
  text: string;
  lemma: string;
  is_entity: boolean;
  is_punct: boolean;
  unknown: boolean;
};

export type ArticleDetail = {
  id: number;
  title: string;
  url: string;
  source_name: string;
  country: string;
  language: string;
  published_at: string;
  body: string;
  tokens: TokenSpan[];
  unknown_pct: number;
};

export type FrequencyWord = {
  lemma: string;
  rank: number;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mnr_token");
}

export function setToken(token: string) {
  localStorage.setItem("mnr_token", token);
}

export function clearToken() {
  localStorage.removeItem("mnr_token");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API}${path}`, { ...init, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json() as Promise<T>;
}

export const COUNTRIES = [
  { code: "FR", language: "fr", label: "France" },
  { code: "ES", language: "es", label: "Spain" },
  { code: "DE", language: "de", label: "Germany" },
  { code: "IT", language: "it", label: "Italy" },
];
