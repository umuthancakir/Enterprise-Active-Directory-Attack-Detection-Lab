"use client";

import Link from "next/link";

export function Nav() {
  return (
    <nav className="border-b border-neutral-200 dark:border-neutral-800">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
        <span className="font-semibold">EADADL</span>
        <Link href="/" className="text-sm hover:underline">
          Dashboard
        </Link>
        <Link href="/coverage" className="text-sm hover:underline">
          Coverage
        </Link>
        <Link href="/login" className="ml-auto text-sm hover:underline">
          Login
        </Link>
      </div>
    </nav>
  );
}
