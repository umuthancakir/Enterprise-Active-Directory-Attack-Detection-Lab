"use client";

import { use, useEffect, useState } from "react";
import { ApiError, getRun } from "@/lib/api";
import type { RunResponse } from "@/lib/types";

export default function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [run, setRun] = useState<RunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRun(id)
      .then(setRun)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load run"));
  }, [id]);

  if (error) return <p className="text-sm text-red-600 dark:text-red-400">{error}</p>;
  if (!run) return <p className="text-sm text-neutral-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{run.scenario}</h1>
        <p className="text-sm text-neutral-500">
          {run.mode} · triggered by {run.triggered_by} ·{" "}
          {new Date(run.created_at).toLocaleString()}
        </p>
      </div>

      <div className="space-y-4">
        {run.findings.map((finding, i) => (
          <div
            key={i}
            className="rounded border border-neutral-200 p-4 dark:border-neutral-800"
          >
            <div className="flex items-baseline justify-between">
              <a
                href={finding.attack_url}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-sm hover:underline"
              >
                {finding.technique_id} ({finding.attack_id})
              </a>
              <span className="text-xs uppercase text-neutral-500">{finding.status}</span>
            </div>
            <p className="mt-2 text-sm">{finding.summary}</p>
            <pre className="mt-2 overflow-x-auto rounded bg-neutral-100 p-2 text-xs dark:bg-neutral-900">
              {finding.command.join(" ")}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
