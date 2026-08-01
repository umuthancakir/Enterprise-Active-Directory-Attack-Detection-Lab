"use client";

import Link from "next/link";
import type { RunSummaryResponse } from "@/lib/types";

export function RunList({ runs }: { runs: RunSummaryResponse[] }) {
  if (runs.length === 0) {
    return <p className="text-sm text-neutral-500">No runs yet.</p>;
  }

  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b border-neutral-200 dark:border-neutral-800">
          <th className="py-2">Scenario</th>
          <th className="py-2">Mode</th>
          <th className="py-2">Triggered by</th>
          <th className="py-2">Findings</th>
          <th className="py-2">Created</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr key={run.id} className="border-b border-neutral-100 dark:border-neutral-900">
            <td className="py-2">
              <Link href={`/runs/${run.id}`} className="hover:underline">
                {run.scenario}
              </Link>
            </td>
            <td className="py-2">{run.mode}</td>
            <td className="py-2">{run.triggered_by}</td>
            <td className="py-2">{run.finding_count}</td>
            <td className="py-2">{new Date(run.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
