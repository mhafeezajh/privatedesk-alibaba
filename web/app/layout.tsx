import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrivateDesk MemoryAgent",
  description: "Per-principal private memory — the glass box.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans text-slate-800 antialiased">{children}</body>
    </html>
  );
}
