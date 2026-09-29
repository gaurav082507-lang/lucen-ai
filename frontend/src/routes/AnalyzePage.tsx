import { useState, useCallback, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileImage, FileText, Layers, X, AlertCircle } from 'lucide-react'
import { claimGuardApi } from '../api/client'

type Tab = 'image' | 'document' | 'claim'

interface UploadedFile {
  file: File
  preview?: string
}

export default function AnalyzePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>('image')
  const [imageFile, setImageFile] = useState<UploadedFile | null>(null)
  const [documentFile, setDocumentFile] = useState<UploadedFile | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Handle demo query param
  useEffect(() => {
    const demo = searchParams.get('demo')
    if (demo === 'document') setTab('document')
    else if (demo === 'image') setTab('image')
  }, [searchParams])

  const onDropImage = useCallback((accepted: File[]) => {
    const f = accepted[0]
    if (f) setImageFile({ file: f, preview: URL.createObjectURL(f) })
  }, [])

  const onDropDoc = useCallback((accepted: File[]) => {
    const f = accepted[0]
    if (f) setDocumentFile({ file: f })
  }, [])

  const { getRootProps: getImgRootProps, getInputProps: getImgInputProps, isDragActive: imgDrag } = useDropzone({
    onDrop: onDropImage, accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.bmp'] }, maxFiles: 1
  })
  const { getRootProps: getDocRootProps, getInputProps: getDocInputProps, isDragActive: docDrag } = useDropzone({
    onDrop: onDropDoc, accept: { 'application/pdf': ['.pdf'] }, maxFiles: 1
  })

  const handleSubmit = async () => {
    setError(null)
    setLoading(true)
    try {
      if (tab === 'image') {
        if (!imageFile) { setError('Please select an image file.'); setLoading(false); return }
        const res = await claimGuardApi.analyzeImage(imageFile.file)
        navigate(`/results/${res.job_id}`)
      } else if (tab === 'document') {
        if (!documentFile) { setError('Please select a PDF document.'); setLoading(false); return }
        const res = await claimGuardApi.analyzeDocument(documentFile.file)
        navigate(`/results/${res.job_id}`)
      } else {
        if (!imageFile || !documentFile) { setError('Full claim requires both an image and a document.'); setLoading(false); return }
        const res = await claimGuardApi.analyzeClaim(imageFile.file, documentFile.file)
        navigate(`/results/${res.job_id}`)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Analysis failed. Is the backend running on port 8000?')
      setLoading(false)
    }
  }

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'image', label: 'Image', icon: FileImage },
    { id: 'document', label: 'Document', icon: FileText },
    { id: 'claim', label: 'Full Claim', icon: Layers },
  ]

  return (
    <main className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">New Analysis</h1>
      <p className="text-gray-400 mb-8">Upload files for Lucen AI forensic detection.</p>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 p-1 rounded-xl mb-8 border border-gray-800">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
              tab === id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Image Drop */}
      {(tab === 'image' || tab === 'claim') && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {tab === 'claim' ? 'Claim Image' : 'Image File'}
          </label>
          {imageFile ? (
            <div className="relative border border-gray-700 rounded-xl overflow-hidden">
              <img src={imageFile.preview} alt="preview" className="w-full max-h-64 object-contain bg-gray-900" />
              <button
                onClick={() => setImageFile(null)}
                className="absolute top-2 right-2 p-1 bg-gray-900/80 rounded-full hover:bg-gray-800"
              >
                <X className="w-4 h-4" />
              </button>
              <div className="absolute bottom-0 left-0 right-0 bg-gray-900/80 px-3 py-1.5 text-xs text-gray-300">
                {imageFile.file.name} ({(imageFile.file.size / 1024).toFixed(0)} KB)
              </div>
            </div>
          ) : (
            <div
              {...getImgRootProps()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                imgDrag ? 'border-blue-500 bg-blue-950/30' : 'border-gray-700 hover:border-gray-500'
              }`}
            >
              <input {...getImgInputProps()} />
              <Upload className="w-8 h-8 text-gray-500 mx-auto mb-3" />
              <p className="text-sm text-gray-400">Drop image here, or <span className="text-blue-400">click to browse</span></p>
              <p className="text-xs text-gray-600 mt-1">JPG, PNG, WebP, BMP</p>
            </div>
          )}
        </div>
      )}

      {/* Document Drop */}
      {(tab === 'document' || tab === 'claim') && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {tab === 'claim' ? 'Claim Document' : 'PDF Document'}
          </label>
          {documentFile ? (
            <div className="flex items-center gap-3 border border-gray-700 rounded-xl p-4 bg-gray-900">
              <FileText className="w-8 h-8 text-purple-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{documentFile.file.name}</p>
                <p className="text-xs text-gray-500">{(documentFile.file.size / 1024).toFixed(0)} KB</p>
              </div>
              <button onClick={() => setDocumentFile(null)} className="p-1 hover:bg-gray-800 rounded-full">
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          ) : (
            <div
              {...getDocRootProps()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                docDrag ? 'border-purple-500 bg-purple-950/30' : 'border-gray-700 hover:border-gray-500'
              }`}
            >
              <input {...getDocInputProps()} />
              <Upload className="w-8 h-8 text-gray-500 mx-auto mb-3" />
              <p className="text-sm text-gray-400">Drop PDF here, or <span className="text-purple-400">click to browse</span></p>
              <p className="text-xs text-gray-600 mt-1">PDF only</p>
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 bg-red-950/50 border border-red-800 rounded-xl p-4 mb-6">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-4 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all text-lg"
      >
        {loading ? '⏳ Submitting…' : 'Run Forensic Analysis →'}
      </button>
    </main>
  )
}
