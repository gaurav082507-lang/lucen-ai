import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { claimGuardApi } from '../api/client'
import type { AnalysisResult } from '../api/types'
import { RiskBadge } from '../components/RiskBadge'
import { Clock, ChevronRight } from 'lucide-react'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<AnalysisResult[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    claimGuardApi.listResults().then(r => {
      setHistory(r)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-gray-500 text-center py-20">Loading history…</div>
      </main>
    )
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">Analysis History</h1>
      <p className="text-gray-400 mb-8">All past claim analyses with their risk scores.</p>

      {history.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center">
          <p className="text-gray-500">No analyses yet.</p>
          <button
            onClick={() => navigate('/analyze')}
            className="mt-4 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all"
          >
            Start First Analysis
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((r) => (
            <div
              key={r.id}
              onClick={() => navigate(`/results/${r.id}`)}
              className="flex items-center gap-4 bg-gray-900 border border-gray-800 rounded-xl p-5 cursor-pointer hover:border-gray-600 transition-all"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-mono text-gray-400 truncate">{r.id}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  {r.created_at ? new Date(r.created_at).toLocaleString() : 'Unknown time'}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-2xl font-bold">
                    {r.overall ? (r.overall.risk * 100).toFixed(0) : '—'}
                  </div>
                  <div className="text-xs text-gray-500">risk score</div>
                </div>
                {r.overall && <RiskBadge band={r.overall.band} />}
                <ChevronRight className="w-5 h-5 text-gray-600" />
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
