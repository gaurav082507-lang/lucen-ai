import type { AnalysisResult, ClaimMetadata, DemoSample, JobStatus } from "./types";

const API_BASE = "/api/v1";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || err?.error?.message || `HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const claimGuardApi = {
  async analyzeImage(file: File): Promise<{ job_id: string }> {
    const fd = new FormData();
    fd.append("file", file);
    return request(`${API_BASE}/analyze/image`, { method: "POST", body: fd });
  },

  async analyzeDocument(file: File): Promise<{ job_id: string }> {
    const fd = new FormData();
    fd.append("file", file);
    return request(`${API_BASE}/analyze/document`, { method: "POST", body: fd });
  },

  async analyzeClaim(image: File, document: File, metadata?: ClaimMetadata): Promise<{ job_id: string }> {
    const fd = new FormData();
    fd.append("image", image);
    fd.append("document", document);
    if (metadata) fd.append("metadata", JSON.stringify(metadata));
    return request(`${API_BASE}/analyze/claim`, { method: "POST", body: fd });
  },

  async getJob(jobId: string): Promise<JobStatus> {
    return request(`${API_BASE}/jobs/${jobId}`);
  },

  async getResult(resultId: string): Promise<AnalysisResult> {
    return request(`${API_BASE}/results/${resultId}`);
  },

  async listResults(): Promise<AnalysisResult[]> {
    try {
      return await request(`${API_BASE}/results/history`);
    } catch {
      return [];
    }
  },

  async getSamples(): Promise<DemoSample[]> {
    return request(`${API_BASE}/health/samples`);
  },

  async downloadReport(resultId: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/results/${resultId}/report.pdf`);
    if (!res.ok) throw new Error("Failed to download report");
    return res.blob();
  },
};
