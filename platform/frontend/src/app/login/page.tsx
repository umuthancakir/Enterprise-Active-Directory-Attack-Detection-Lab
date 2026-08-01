"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-sm space-y-4">
      <h1 className="text-xl font-semibold">Sign in</h1>
      <div>
        <label htmlFor="username" className="block text-sm font-medium">
          Username
        </label>
        <input
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
          required
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
          required
        />
      </div>
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded bg-neutral-900 px-3 py-2 text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
      >
        {submitting ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
