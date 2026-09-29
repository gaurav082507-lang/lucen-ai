import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { claimGuardApi } from '../api/client'
import type { AnalysisResult, JobStatus, PipelineScore } from '../api/types'
import { RiskBadge } from '../components/RiskBadge'
import { ScoreGauge } from '../components/ScoreGauge'
import { EvidenceCard } from '../components/EvidenceCard'
import { Download, ChevronLeft, RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react'

export default function ResultPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [job, setJob] = useState<JobStatus | null>(null)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const retryCountRef = useRef(0)
  const MAX_RETRIES = 6

  const fetchJob = async () => {
    if (!id) return
    try {
      const j = await claimGuardApi.getJob(id)
      retryCountRef.current = 0
      setJob(j)
      if (j.status === 'done') {
        if (pollRef.current) clearInterval(pollRef.current)
        const resultId = j.result_id || id
        try {
          const r = await claimGuardApi.getResult(resultId)
          setResult(r)
        } catch (e) {
          setError('Could not load result: ' + (e instanceof Error ? e.message : String(e)))
        }
      } else if (j.status === 'failed') {
        if (pollRef.current) clearInterval(pollRef.current)
        setError('Analysis failed: ' + (j.error || 'Unknown error'))
      }
    } catch (e) {
      retryCountRef.current += 1
      if (retryCountRef.current >= MAX_RETRIES) {
        setError('Could not reach backend: ' + (e instanceof Error ? e.message : String(e)))
        if (pollRef.current) clearInterval(pollRef.current)
      }
    }
  }

  useEffect(() => {
    fetchJob()
    pollRef.current = setInterval(fetchJob, 1500)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [id])

  const downloadReport = async () => {
    if (!id) return
    try {
      const resultId = result?.id || id
      const blob = await claimGuardApi.downloadReport(resultId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `lucen_ai_report_${resultId}.pdf`; a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('Could not download report: ' + (e instanceof Error ? e.message : String(e)))
    }
  }

  if (error) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="flex items-start gap-3 bg-red-950/50 border border-red-800 rounded-xl p-6">
          <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-300 mb-1">Error</p>
            <p className="text-sm text-red-400">{error}</p>
          </div>
        </div>
        <button onClick={() => navigate('/analyze')} className="mt-6 flex items-center gap-2 text-blue-400 hover:underline text-sm">
          <ChevronLeft className="w-4 h-4" /> Back to Analyze
        </button>
      </main>
    )
  }

  // Loading / polling state
  if (!result) {
    const steps = job?.steps || []
    return (
      <main className="max-w-2xl mx-auto px-4 py-12">
        <button onClick={() => navigate('/analyze')} className="flex items-center gap-2 text-gray-400 hover:text-gray-200 text-sm mb-8">
          <ChevronLeft className="w-4 h-4" /> Back
        </button>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            {job?.status === 'done'
              ? <CheckCircle className="w-5 h-5 text-green-400" />
              : job?.status === 'failed'
              ? <AlertCircle className="w-5 h-5 text-red-400" />
              : <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />}
            <h2 className="text-xl font-semibold">
              {job?.status === 'done' ? 'Loading results…' : job?.status === 'failed' ? 'Analysis failed' : 'Running analysis…'}
            </h2>
          </div>
          {steps.length > 0 ? (
            <div className="space-y-3">
              {steps.map((step, i) => (
                <div key={i} className="flex items-center gap-3">
                  {step.status === 'done'
                    ? <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    : step.status === 'running'
                    ? <RefreshCw className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />
                    : <Clock className="w-4 h-4 text-gray-600 flex-shrink-0" />}
                  <span className={`text-sm ${step.status === 'done' ? 'text-gray-300' : step.status === 'running' ? 'text-blue-300' : 'text-gray-600'}`}>
                    {step.name || step.label}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-3 text-gray-400">
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>{job ? 'Processing…' : 'Connecting…'}</span>
            </div>
          )}
        </div>
      </main>
    )
  }

  // Build pipeline list
  const pipelines: (PipelineScore & { label: string })[] = [
    result.image && { ...result.image, label: 'Image' },
    result.document && { ...result.document, label: 'Document' },
    result.identity && { ...result.identity, label: 'Identity' },
  ].filter(Boolean) as (PipelineScore & { label: string })[]

  const topEvidence = [...(result.evidence || [])]
    .sort((a, b) => (b.calibrated_score ?? 0) - (a.calibrated_score ?? 0))
    .slice(0, 8)

  const overall = result.overall

  return (
    <main className="max-w-5xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <button onClick={() => navigate('/analyze')} className="flex items-center gap-2 text-gray-400 hover:text-gray-200 text-sm">
          <ChevronLeft className="w-4 h-4" /> New Analysis
        </button>
        <button
          onClick={downloadReport}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm font-medium transition-all"
        >
          <Download className="w-4 h-4" /> Download PDF Report
        </button>
      </div>

      {/* Overall Score */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 mb-6">
        <div className="flex flex-col md:flex-row items-center gap-8">
          <ScoreGauge value={overall.risk} band={overall.band} label="Fraud Risk" size={180} />
          <div className="flex-1 text-center md:text-left">
            <div className="flex items-center gap-3 justify-center md:justify-start mb-2">
              <h1 className="text-3xl font-bold">Overall Risk Score</h1>
              <RiskBadge band={overall.band} />
            </div>
            <p className="text-gray-400 text-sm mb-4">
              Confidence: <span className="font-medium text-gray-200">{overall.confidence}</span>
            </p>
            {overall.summary && (
              <p className="text-gray-300 leading-relaxed">{overall.summary}</p>
            )}
          </div>
        </div>
      </div>

      {/* Per-Pipeline Scores */}
      {pipelines.length > 0 && (
        <div className={`grid grid-cols-1 gap-4 mb-6 ${pipelines.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'}`}>
          {pipelines.map(p => (
            <div key={p.pipeline} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-300">{p.label} Pipeline</span>
                <RiskBadge band={p.band} size="sm" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold">{(p.risk * 100).toFixed(0)}</span>
                <span className="text-gray-500 text-sm">/ 100</span>
              </div>
              <div className="mt-2 h-1.5 bg-gray-800 rounded-full">
                <div
                  className={`h-full rounded-full ${p.band === 'HIGH' ? 'bg-red-500' : p.band === 'MEDIUM' ? 'bg-amber-500' : 'bg-green-500'}`}
                  style={{ width: `${p.risk * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Evidence */}
      {topEvidence.length > 0 && (
        <div>
          <h2 className="text-xl font-bold mb-4">Forensic Evidence ({topEvidence.length} signals)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topEvidence.map((ev, i) => (
              <EvidenceCard key={i} evidence={ev} />
            ))}
          </div>
        </div>
      )}

      {/* Footer meta */}
      <div className="mt-8 text-xs text-gray-600 text-center">
        Result ID: {result.id} · Mode: {result.mode} · {result.created_at ? new Date(result.created_at).toLocaleString() : ''}
      </div>
    </main>
  )
}
