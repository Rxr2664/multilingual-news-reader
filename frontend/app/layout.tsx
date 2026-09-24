import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lemma — Multilingual News Reader",
  description: "Read real news at the edge of your vocabulary.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
