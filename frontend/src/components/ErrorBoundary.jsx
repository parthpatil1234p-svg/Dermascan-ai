import { Component } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an unhandled error:", error, errorInfo);
    // If it's a chunk cache mismatch due to a recent deployment, auto-reload once
    if (
      error?.message?.includes("dynamically imported module") ||
      error?.message?.includes("Failed to fetch dynamically imported module")
    ) {
      const hasReloaded = window.sessionStorage.getItem("chunk_error_reloaded");
      if (!hasReloaded) {
        window.sessionStorage.setItem("chunk_error_reloaded", "true");
        window.location.reload();
      }
    }
  }

  handleReset = () => {
    window.sessionStorage.removeItem("chunk_error_reloaded");
    this.setState({ hasError: false, error: null });
    window.location.href = "/";
  };

  handleReload = () => {
    window.sessionStorage.removeItem("chunk_error_reloaded");
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const isChunkError =
        this.state.error?.message?.includes("dynamically imported module") ||
        this.state.error?.message?.includes("Failed to fetch");

      return (
        <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-16 text-slate-100">
          <section className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-red-500/30 bg-slate-900/90 p-8 text-center shadow-[0_0_50px_rgba(239,68,68,0.2)] backdrop-blur-2xl">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 shadow-inner">
              {isChunkError ? (
                <RefreshCw className="h-8 w-8 animate-spin text-emerald-400" />
              ) : (
                <AlertTriangle className="h-8 w-8 animate-pulse text-red-400" />
              )}
            </div>
            
            <h1 className="mt-5 text-2xl font-black tracking-tight text-white">
              {isChunkError ? "New Version Deployed" : "Workflow State Notice"}
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-400">
              {isChunkError
                ? "A new update of DermaScan AI was deployed. Please refresh to load the latest modules."
                : "An unexpected render issue occurred while assembling the report telemetry. Your data has not been lost."}
            </p>

            {this.state.error?.message && !isChunkError && (
              <div className="mt-4 rounded-xl border border-white/5 bg-slate-950/60 p-3 text-left">
                <p className="font-mono text-[11px] text-red-300 break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={this.handleReload}
                className="inline-flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition hover:bg-emerald-500 hover:scale-105"
              >
                <RefreshCw className="h-4 w-4" />
                {isChunkError ? "Load Latest Version" : "Reload Page"}
              </button>
              <button
                type="button"
                onClick={this.handleReset}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition hover:scale-105"
              >
                <Home className="h-4 w-4" />
                Return to Dashboard
              </button>
            </div>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}


