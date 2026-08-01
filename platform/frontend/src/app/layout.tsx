import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "EADADL Platform",
  description: "Scenario runner, run history, and ATT&CK coverage for the EADADL lab.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
        <Nav />
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
