// Mirrors platform/backend/app/schemas.py — kept in sync by hand (no
// generated client yet; see README.md "Not done").

export interface ScenarioSummary {
  id: string;
  description: string;
  technique_ids: string[];
}

export interface FindingResponse {
  technique_id: string;
  attack_id: string;
  attack_url: string;
  target_host_id: string;
  target_ip: string;
  tool: string;
  command: string[];
  status: string;
  summary: string;
  raw_output: unknown;
}

export interface RunResponse {
  id: string;
  scenario: string;
  mode: "dry_run" | "live";
  triggered_by: string;
  created_at: string;
  findings: FindingResponse[];
}

export interface RunSummaryResponse {
  id: string;
  scenario: string;
  mode: "dry_run" | "live";
  triggered_by: string;
  created_at: string;
  finding_count: number;
}

export interface TechniqueCoverageEntry {
  technique_id: string;
  attack_id: string;
  sigma_rule: string | null;
  rule_title: string | null;
  fixture_tests: {
    matching_passed: number;
    matching_total: number;
    non_matching_passed: number;
    non_matching_total: number;
  };
  covered: boolean;
}

export interface CoverageMatrix {
  generated_at: string;
  techniques: TechniqueCoverageEntry[];
  summary: {
    total_techniques: number;
    covered: number;
    coverage_pct: number;
  };
}
