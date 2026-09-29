import { useNavigate } from 'react-router-dom';
import { Sparkles, FileImage, FileText, Layers, ArrowRight, ShieldCheck, Zap, Activity } from 'lucide-react';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans selection:bg-amber-500/30">
      {/* Subtle Background Glow */}
      <div className="absolute inset-0 z-0 flex items-center justify-center pointer-events-none">
        <div className="w-[800px] h-[800px] bg-amber-500/10 rounded-full blur-[120px] animate-pulse"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-20 lg:py-32 flex flex-col items-center text-center">
        {/* Hero Icon */}
        <div className="mb-8 relative">
          <div className="absolute inset-0 bg-amber-500 blur-xl opacity-20 rounded-full"></div>
          <Sparkles className="w-20 h-20 text-amber-500 relative z-10 animate-bounce" style={{ animationDuration: '3s' }} />
        </div>

        {/* Hero Title */}
        <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-6">
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-amber-400 via-orange-500 to-amber-600">
            Lucen AI
          </span>
        </h1>

        {/* Tagline */}
        <p className="text-2xl md:text-3xl text-slate-400 italic font-medium mb-12 max-w-3xl">
          Illuminate the Claim. Eliminate the Fraud.
        </p>

        {/* Stats Bar */}
        <div className="flex flex-wrap justify-center gap-6 mb-16">
          <div className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-sm border border-slate-800 px-6 py-3 rounded-full shadow-lg">
            <Layers className="w-5 h-5 text-amber-500" />
            <span className="font-semibold text-slate-200">3 Pipelines</span>
          </div>
          <div className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-sm border border-slate-800 px-6 py-3 rounded-full shadow-lg">
            <ShieldCheck className="w-5 h-5 text-amber-500" />
            <span className="font-semibold text-slate-200">12+ Detectors</span>
          </div>
          <div className="flex items-center gap-2 bg-slate-900/80 backdrop-blur-sm border border-slate-800 px-6 py-3 rounded-full shadow-lg">
            <Zap className="w-5 h-5 text-amber-500" />
            <span className="font-semibold text-slate-200">&lt;10s Analysis</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-24">
          <button
            onClick={() => navigate('/analyze')}
            className="group relative px-8 py-4 bg-gradient-to-r from-amber-600 to-orange-600 text-white font-bold rounded-xl shadow-[0_0_40px_-10px_rgba(245,158,11,0.5)] hover:shadow-[0_0_60px_-15px_rgba(245,158,11,0.7)] transition-all duration-300 hover:-translate-y-1 overflow-hidden"
          >
            <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-in-out"></div>
            <span className="relative flex items-center gap-2">
              Start Analysis <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </span>
          </button>
          <button className="px-8 py-4 bg-slate-900 border border-slate-700 hover:border-slate-500 hover:bg-slate-800 text-slate-300 font-bold rounded-xl transition-all duration-300">
            View Documentation
          </button>
        </div>

        {/* Feature Cards */}
        <div className="grid md:grid-cols-3 gap-8 w-full max-w-5xl text-left">
          {/* Card 1 */}
          <div className="group relative p-1 rounded-2xl bg-gradient-to-b from-slate-800 to-slate-900 hover:from-amber-500/50 hover:to-orange-600/50 transition-all duration-500 hover:-translate-y-2">
            <div className="bg-slate-950 p-8 rounded-xl h-full border border-slate-800/50 flex flex-col">
              <div className="w-14 h-14 bg-amber-500/10 rounded-lg flex items-center justify-center mb-6 border border-amber-500/20 group-hover:border-amber-500/50 transition-colors">
                <FileImage className="w-7 h-7 text-amber-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-200 mb-3">Image Forgery</h3>
              <p className="text-slate-400 leading-relaxed">
                Detect metadata anomalies, ELA compression artifacts, and AI-generated manipulations in claim images.
              </p>
            </div>
          </div>

          {/* Card 2 */}
          <div className="group relative p-1 rounded-2xl bg-gradient-to-b from-slate-800 to-slate-900 hover:from-amber-500/50 hover:to-orange-600/50 transition-all duration-500 hover:-translate-y-2">
            <div className="bg-slate-950 p-8 rounded-xl h-full border border-slate-800/50 flex flex-col">
              <div className="w-14 h-14 bg-amber-500/10 rounded-lg flex items-center justify-center mb-6 border border-amber-500/20 group-hover:border-amber-500/50 transition-colors">
                <FileText className="w-7 h-7 text-amber-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-200 mb-3">Document Fraud</h3>
              <p className="text-slate-400 leading-relaxed">
                Identify edited PDFs, mismatched fonts, and altered timestamps in invoices and police reports.
              </p>
            </div>
          </div>

          {/* Card 3 */}
          <div className="group relative p-1 rounded-2xl bg-gradient-to-b from-slate-800 to-slate-900 hover:from-amber-500/50 hover:to-orange-600/50 transition-all duration-500 hover:-translate-y-2">
            <div className="bg-slate-950 p-8 rounded-xl h-full border border-slate-800/50 flex flex-col">
              <div className="w-14 h-14 bg-amber-500/10 rounded-lg flex items-center justify-center mb-6 border border-amber-500/20 group-hover:border-amber-500/50 transition-colors">
                <Activity className="w-7 h-7 text-amber-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-200 mb-3">Behavioral Scrape</h3>
              <p className="text-slate-400 leading-relaxed">
                Cross-reference claim details against social graphs and historical records for deeper context.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
