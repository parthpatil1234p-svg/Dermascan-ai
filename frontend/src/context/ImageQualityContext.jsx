import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useAuth } from "./AuthContext";
import { useUpload } from "./UploadContext";
import {
  acceptQualityWarning,
  analyzeImageQuality,
  getImageQualityErrorMessage,
  getImageQualityReport,
} from "../services/imageQualityService";

const ImageQualityContext = createContext(null);

export function ImageQualityProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [qualityReport, setQualityReport] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [isAcceptingWarning, setIsAcceptingWarning] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [error, setError] = useState("");
  const progressTimerRef = useRef(null);

  const stopProgressTimer = useCallback(() => {
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const clearQualityState = useCallback(() => {
    stopProgressTimer();
    setQualityReport(null);
    setIsAnalyzing(false);
    setIsLoadingReport(false);
    setIsAcceptingWarning(false);
    setAnalysisProgress(0);
    setError("");
  }, [stopProgressTimer]);

  useEffect(() => {
    clearQualityState();
  }, [uploadId, clearQualityState]);

  useEffect(() => {
    if (!isAuthenticated) clearQualityState();
  }, [isAuthenticated, clearQualityState]);

  useEffect(() => stopProgressTimer, [stopProgressTimer]);

  const analyze = useCallback(async () => {
    if (!uploadId || isAnalyzing) return null;
    setIsAnalyzing(true);
    setError("");
    setAnalysisProgress(6);
    stopProgressTimer();
    progressTimerRef.current = window.setInterval(() => {
      setAnalysisProgress((current) => Math.min(current + 8, 92));
    }, 350);

    try {
      const response = await analyzeImageQuality(uploadId);
      stopProgressTimer();
      setAnalysisProgress(100);
      setQualityReport(response);
      setCurrentUploadStatus(`quality_${response.quality_status}`);
      return response;
    } catch (requestError) {
      stopProgressTimer();
      setAnalysisProgress(0);
      setError(getImageQualityErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsAnalyzing(false);
    }
  }, [
    uploadId,
    isAnalyzing,
    setCurrentUploadStatus,
    stopProgressTimer,
  ]);

  const loadReport = useCallback(async () => {
    if (!uploadId || isLoadingReport) return null;
    setIsLoadingReport(true);
    setError("");
    try {
      const response = await getImageQualityReport(uploadId);
      setQualityReport(response);
      return response;
    } catch (requestError) {
      setError(getImageQualityErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingReport(false);
    }
  }, [uploadId, isLoadingReport]);

  const acceptWarning = useCallback(async () => {
    if (!uploadId || isAcceptingWarning) return null;
    setIsAcceptingWarning(true);
    setError("");
    try {
      const response = await acceptQualityWarning(uploadId);
      setQualityReport((current) => ({ ...current, ...response }));
      setCurrentUploadStatus("face_detection_pending");
      return response;
    } catch (requestError) {
      setError(getImageQualityErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsAcceptingWarning(false);
    }
  }, [uploadId, isAcceptingWarning, setCurrentUploadStatus]);

  const value = useMemo(
    () => ({
      qualityReport,
      qualityStatus: qualityReport?.quality_status || "",
      isAnalyzing,
      isLoadingReport,
      isAcceptingWarning,
      analysisProgress,
      error,
      canContinue: Boolean(qualityReport?.can_continue),
      warningAccepted: Boolean(qualityReport?.warning_accepted),
      analyze,
      loadReport,
      acceptWarning,
      clearQualityState,
    }),
    [
      qualityReport,
      isAnalyzing,
      isLoadingReport,
      isAcceptingWarning,
      analysisProgress,
      error,
      analyze,
      loadReport,
      acceptWarning,
      clearQualityState,
    ],
  );

  return (
    <ImageQualityContext.Provider value={value}>
      {children}
    </ImageQualityContext.Provider>
  );
}

export function useImageQuality() {
  const context = useContext(ImageQualityContext);
  if (!context) {
    throw new Error("useImageQuality must be used inside ImageQualityProvider");
  }
  return context;
}
