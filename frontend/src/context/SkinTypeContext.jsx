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
  analyzeSkinType,
  getSkinTypeErrorMessage,
  getSkinTypeModelStatus,
  getSkinTypeReport,
} from "../services/skinTypeService";

const SkinTypeContext = createContext(null);

export function SkinTypeProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [skinTypeReport, setSkinTypeReport] = useState(null);
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

  const clearSkinTypeState = useCallback(() => {
    stopProgress();
    setSkinTypeReport(null);
    setModelStatus(null);
    setIsCheckingModel(false);
    setIsAnalyzing(false);
    setIsLoadingReport(false);
    setAnalysisProgress(0);
    setError("");
  }, [stopProgress]);

  useEffect(() => clearSkinTypeState(), [uploadId, clearSkinTypeState]);
  useEffect(() => {
    if (!isAuthenticated) clearSkinTypeState();
  }, [isAuthenticated, clearSkinTypeState]);
  useEffect(() => stopProgress, [stopProgress]);

  const checkModelReadiness = useCallback(async () => {
    setIsCheckingModel(true);
    setError("");
    try {
      const response = await getSkinTypeModelStatus();
      setModelStatus(response);
      return response;
    } catch (requestError) {
      setError(getSkinTypeErrorMessage(requestError));
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
      setAnalysisProgress((current) => Math.min(current + 9, 94));
    }, 420);
    try {
      const response = await analyzeSkinType(uploadId);
      stopProgress();
      setAnalysisProgress(100);
      setSkinTypeReport(response);
      setCurrentUploadStatus(
        response.result_status === "estimated"
          ? "skin_type_estimated"
          : "skin_type_uncertain",
      );
      return response;
    } catch (requestError) {
      stopProgress();
      setAnalysisProgress(0);
      setError(getSkinTypeErrorMessage(requestError));
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
      const response = await getSkinTypeReport(uploadId);
      setSkinTypeReport(response);
      return response;
    } catch (requestError) {
      setError(getSkinTypeErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingReport(false);
    }
  }, [uploadId, isLoadingReport]);

  const value = useMemo(
    () => ({
      skinTypeReport,
      modelStatus,
      isCheckingModel,
      isAnalyzing,
      isLoadingReport,
      analysisProgress,
      error,
      canContinue: Boolean(skinTypeReport?.can_continue),
      checkModelReadiness,
      analyzeCurrentImage,
      loadReport,
      clearSkinTypeState,
    }),
    [
      skinTypeReport,
      modelStatus,
      isCheckingModel,
      isAnalyzing,
      isLoadingReport,
      analysisProgress,
      error,
      checkModelReadiness,
      analyzeCurrentImage,
      loadReport,
      clearSkinTypeState,
    ],
  );

  return <SkinTypeContext.Provider value={value}>{children}</SkinTypeContext.Provider>;
}

export function useSkinType() {
  const context = useContext(SkinTypeContext);
  if (!context) throw new Error("useSkinType must be used inside SkinTypeProvider");
  return context;
}
