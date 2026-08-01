"use client";

import { useEffect, useState } from "react";
import { ApiError, getCoverage } from "@/lib/api";
import { CoverageHeatmap } from "@/components/CoverageHeatmap";
import type { CoverageMatrix } from "@/lib/types";

export default function CoveragePage() {
  const [matrix, setMatrix] = useState<CoverageMatrix | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCoverage()
      .then(setMatrix)
      .catch((err) =>
        setError(
          err instanceof ApiError
            ? err.message
            : "Failed to load coverage — has `make detections-test` run?",
        ),
      );
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold">ATT&amp;CK coverage</h1>
      {error && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>}
      {matrix && (
        <div className="mt-4">
          <CoverageHeatmap matrix={matrix} />
        </div>
      )}
    </div>
  );
}
