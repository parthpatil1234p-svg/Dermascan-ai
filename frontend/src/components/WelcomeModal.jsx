import { useEffect, useState } from "react";
import {
  Camera,
  CheckCircle2,
  GraduationCap,
  Info,
  Sparkles,
  User,
  X,
} from "lucide-react";
import PrimaryButton from "./PrimaryButton";

const STORAGE_KEY = "dermascan_welcome_shown";

export default function WelcomeModal() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    try {
      const alreadyShown = sessionStorage.getItem(STORAGE_KEY);
      if (!alreadyShown) {
        setIsOpen(true);
      }
    } catch {
      // Fallback if sessionStorage is disabled/inaccessible
      setIsOpen(true);
    }
  }, []);

  const handleClose = () => {
    try {
      sessionStorage.setItem(STORAGE_KEY, "true");
    } catch {
      // Ignore storage errors
    }
    setIsOpen(false);
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        handleClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-opacity duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-modal-title"
    >
      <div
        className="relative flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-100 bg-gradient-to-r from-brand-50/70 via-clinic-50/50 to-white px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-soft">
              <Sparkles className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h2
                id="welcome-modal-title"
                className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl"
              >
                Welcome to DermaScan AI! 👋
              </h2>
              <p className="text-xs font-medium text-brand-700 sm:text-sm">
                AI-Powered Skincare Analysis & Recommendations
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Close welcome message"
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-600"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="space-y-6 overflow-y-auto px-6 py-5 text-slate-700">
          {/* Welcome Intro */}
          <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-4 text-sm leading-relaxed text-slate-600 sm:text-base">
            <p>
              <strong className="font-semibold text-slate-800">DermaScan AI</strong> uses AI-based facial image analysis to provide general skincare guidance based on visible skin characteristics.
            </p>
          </div>

          {/* Instructions */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-900">
              <Camera className="h-4 w-4 text-brand-600" aria-hidden="true" />
              Important Instructions & Guidelines
            </h3>
            <ul className="mt-3 space-y-2.5 text-xs text-slate-600 sm:text-sm">
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                <span>Upload a clear, front-facing facial image.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                <span>Make sure the face is properly visible and well-lit.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                <span>Avoid sunglasses, masks, heavy filters, or extreme angles.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                <span>Use a recent image for better analysis.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                <span>Enter the required user information accurately.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-clinic-500" aria-hidden="true" />
                <span>The AI analysis provides general skincare guidance only.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
                <span>Results are not a medical diagnosis.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                <span>
                  Product recommendations are based on the detected skin type, visible concerns, preferences, and available product information.
                </span>
              </li>
            </ul>
          </div>

          {/* Developer / Student Information */}
          <div className="rounded-xl border border-brand-200 bg-gradient-to-br from-brand-50/60 to-clinic-50/60 p-4 text-xs sm:text-sm">
            <h4 className="flex items-center gap-2 font-semibold text-brand-900">
              <GraduationCap className="h-4 w-4 text-brand-700" aria-hidden="true" />
              Academic Project Information
            </h4>
            <div className="mt-2.5 grid grid-cols-1 gap-2 text-slate-700 sm:grid-cols-3">
              <div className="flex items-center gap-2">
                <User className="h-3.5 w-3.5 text-slate-500" aria-hidden="true" />
                <span>
                  <strong className="text-slate-900">Developed by:</strong> Parth Patil
                </span>
              </div>
              <div>
                <strong className="text-slate-900">Roll No.:</strong> 25110042
              </div>
              <div>
                <strong className="text-slate-900">Project:</strong> DermaScan AI
              </div>
            </div>
          </div>
        </div>

        {/* Footer with Action */}
        <div className="flex items-center justify-end border-t border-slate-100 bg-slate-50/70 px-6 py-4">
          <PrimaryButton onClick={handleClose} className="w-full sm:w-auto">
            Get Started
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
}