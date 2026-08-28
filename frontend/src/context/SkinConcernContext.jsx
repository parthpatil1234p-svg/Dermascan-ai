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
  analyzeSkinConcerns,
  getSkinConcernErrorMessage,
  getSkinConcernModelStatus,
  getSkinConcernReport,
} from "../services/skinConcernService";

const SkinConcernContext = createContext(null);

export function SkinConcernProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [concernReport, setConcernReport] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [isCheckingModel, setIsCheckingModel] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [error, setError] = useState("");
  const progressTimerRef = useRef(null);

  const stopProgress = useCallback(() => {
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const clearConcernState = useCallback(() => {
    stopProgress();
    setConcernReport(null);
    setModelStatus(null);
    setIsCheckingModel(false);
    setIsAnalyzing(false);
    setIsLoadingReport(false);
    setAnalysisProgress(0);
    setError("");
  }, [stopProgress]);

  useEffect(() => clearConcernState(), [uploadId, clearConcernState]);
  useEffect(() => {
    if (!isAuthenticated) clearConcernState();
  }, [isAuthenticated, clearConcernState]);
  useEffect(() => stopProgress, [stopProgress]);

  const checkModelReadiness = useCallback(async () => {
    setIsCheckingModel(true);
    setError("");
    try {
      const response = await getSkinConcernModelStatus();
      setModelStatus(response);
      return response;
    } catch (requestError) {
      setError(getSkinConcernErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsCheckingModel(false);
    }
  }, []);

  const analyzeCurrentImage = useCallback(async () => {
    if (!uploadId || isAnalyzing) return null;
    setIsAnalyzing(true);
    setError("");
    setAnalysisProgress(8);
    stopProgress();
    progressTimerRef.current = window.setInterval(() => {
      setAnalysisProgress((current) => Math.min(current + 8, 94));
    }, 430);
    try {
      const response = await analyzeSkinConcerns(uploadId);
      stopProgress();
      setAnalysisProgress(100);
      setConcernReport(response);
      setCurrentUploadStatus(
        response.overall_status === "completed"
          ? "skin_concern_analysis_completed"
          : "skin_concern_analysis_uncertain",
      );
      return response;
    } catch (requestError) {
      stopProgress();
      setAnalysisProgress(0);
      setError(getSkinConcernErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsAnalyzing(false);
    }
  }, [uploadId, isAnalyzing, setCurrentUploadStatus, stopProgress]);

  const loadReport = useCallback(async () => {
    if (!uploadId || isLoadingReport) return null;
    setIsLoadingReport(true);
    setError("");
    try {
      const response = await getSkinConcernReport(uploadId);
      setConcernReport(response);
      return response;
    } catch (requestError) {
      setError(getSkinConcernErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingReport(false);
    }
  }, [uploadId, isLoadingReport]);

  const value = useMemo(
    () => ({
      concernReport,
      modelStatus,
      isCheckingModel,
      isAnalyzing,
      isLoadingReport,
      analysisProgress,
      error,
      canContinue: Boolean(concernReport?.can_continue),
      checkModelReadiness,
      analyzeCurrentImage,
      loadReport,
      clearConcernState,
    }),
    [
      concernReport,
      modelStatus,
      isCheckingModel,
      isAnalyzing,
      isLoadingReport,
      analysisProgress,
      error,
      checkModelReadiness,
      analyzeCurrentImage,
      loadReport,
      clearConcernState,
    ],
  );

  return <SkinConcernContext.Provider value={value}>{children}</SkinConcernContext.Provider>;
}

export function useSkinConcern() {
  const context = useContext(SkinConcernContext);
  if (!context) throw new Error("useSkinConcern must be used inside SkinConcernProvider");
  return context;
}
