export interface BBox {
  page: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

export type PipelineType = "image" | "document" | "identity" | "claim";
export type EvidenceKind = "risk" | "info" | "warning";
export type SeverityLevel = "low" | "medium" | "high";
export type RiskBand = "LOW" | "MEDIUM" | "HIGH";
export type ConfidenceLevel = "high" | "medium" | "low";
export type StepStatus = "pending" | "running" | "done" | "skipped" | "failed";
export type JobStatusType = "queued" | "running" | "done" | "failed";

export interface Evidence {
  id: string;
  pipeline: PipelineType;
  source: string;
  kind: EvidenceKind;
  raw_score: number;
  calibrated_score: number;
  weight: number;
  effective_weight: number;
  severity: SeverityLevel;
  title: string;
  reason: string;
  field?: string | null;
  bbox?: BBox | null;
  details: Record<string, unknown>;
  artifact?: string | null;
}

export interface DetectorStatus {
  detector: string;
  status: "ok" | "skipped" | "failed";
  duration_ms?: number | null;
  error?: string | null;
}

export interface PipelineScore {
  pipeline: string;
  risk: number;      // 0.0–1.0
  authenticity: number;
  band: RiskBand;
  confidence: ConfidenceLevel;
  evidence_ids: string[];
}

export interface QualityWarning {
  code: string;
  message: string;
}

export interface OverallScore {
  risk: number;      // 0.0–1.0
  band: RiskBand;
  confidence: ConfidenceLevel;
  summary: string;
}

export interface AnalysisResult {
  id: string;
  mode: "image" | "document" | "claim";
  created_at: string;
  image?: PipelineScore | null;
  document?: PipelineScore | null;
  identity?: PipelineScore | null;
  overall: OverallScore;
  evidence: Evidence[];
  detector_status: DetectorStatus[];
  quality_warnings: QualityWarning[];
  artifacts: Record<string, unknown>;
  versions: Record<string, string>;
}

export interface StepProgress {
  name: string;
  label?: string;    // alias for compatibility
  status: StepStatus;
  duration_ms?: number | null;
  detail?: string | null;
}

export interface JobStatus {
  job_id: string;
  status: JobStatusType;
  mode: "image" | "document" | "claim";
  steps: StepProgress[];
  result_id?: string | null;
  error?: string | null;
}

export interface ClaimMetadata {
  claim_date?: string;
  incident_date?: string;
  claimed_amount?: number;
  currency?: string;
  claimant_name?: string;
}

export interface DemoSample {
  id: string;
  title: string;
  type: "image" | "document" | "claim";
  description: string;
  file?: string;
  expected_band: RiskBand;
}
