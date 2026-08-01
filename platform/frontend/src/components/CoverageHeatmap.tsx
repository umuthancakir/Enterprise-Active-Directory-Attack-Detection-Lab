"use client";

import type { CoverageMatrix } from "@/lib/types";

export function CoverageHeatmap({ matrix }: { matrix: CoverageMatrix }) {
  return (
    <div>
      <p className="text-sm text-neutral-500">
        {matrix.summary.covered}/{matrix.summary.total_techniques} techniques covered (
        {matrix.summary.coverage_pct}%) — generated{" "}
        {new Date(matrix.generated_at).toLocaleString()}
      </p>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {matrix.techniques.map((t) => (
          <div
            key={t.technique_id}
            className={
              "rounded p-3 text-sm " +
              (t.covered
                ? "bg-emerald-100 dark:bg-emerald-950"
                : "bg-neutral-100 dark:bg-neutral-900")
            }
          >
            <div className="font-mono text-xs">{t.attack_id}</div>
            <div className="mt-1 font-medium">{t.technique_id}</div>
            <div className="mt-1 text-xs text-neutral-500">
              {t.rule_title ?? "no rule"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
