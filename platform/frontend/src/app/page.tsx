"use client";

import { useEffect, useState } from "react";
import { ApiError, createRun, listRuns, listScenarios } from "@/lib/api";
import { RunList } from "@/components/RunList";
import type { RunSummaryResponse, ScenarioSummary } from "@/lib/types";

export default function DashboardPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [runs, setRuns] = useState<RunSummaryResponse[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  async function refresh() {
    try {
      const [scenarioList, runList] = await Promise.all([listScenarios(), listRuns()]);
      setScenarios(scenarioList);
      setRuns(runList);
      setSelectedScenario((current) => current || scenarioList[0]?.id || "");
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load — are you signed in?");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleRun() {
    if (!selectedScenario) return;
    setRunning(true);
    setError(null);
    try {
      // Always dry_run from the UI — see attack/runner.py's module
      // docstring for why "live" is a deliberate opt-in path, not
      // something exposed as a casual button click.
      await createRun(selectedScenario, "dry_run");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Run failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-xl font-semibold">Run a scenario</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Dry-run only — resolves targets through the scope guard and prints what would run.
          See attack/runner.py.
        </p>
        <div className="mt-4 flex items-center gap-3">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="rounded border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
          >
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.id} ({s.technique_ids.length} techniques)
              </option>
            ))}
          </select>
          <button
            onClick={handleRun}
            disabled={running || !selectedScenario}
            className="rounded bg-neutral-900 px-4 py-2 text-white disabled:opacity-50 dark:bg-neutral-100 dark:text-neutral-900"
          >
            {running ? "Running..." : "Run"}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>}
      </section>

      <section>
        <h2 className="text-lg font-semibold">Run history</h2>
        <div className="mt-4">
          <RunList runs={runs} />
        </div>
      </section>
    </div>
  );
}
