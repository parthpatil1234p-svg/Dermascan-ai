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
  getPreprocessingErrorMessage,
  getPreprocessingReport,
  processImage,
  reprocessImage,
} from "../services/imagePreprocessingService";

const ImagePreprocessingContext = createContext(null);

export function ImagePreprocessingProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [preprocessingReport, setPreprocessingReport] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [error, setError] = useState("");
  const progressTimerRef = useRef(null);

  const stopProgressTimer = useCallback(() => {
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const clearPreprocessingState = useCallback(() => {
    stopProgressTimer();
    setPreprocessingReport(null);
    setIsProcessing(false);
    setIsLoadingReport(false);
    setProcessingProgress(0);
    setError("");
  }, [stopProgressTimer]);

  useEffect(() => {
    clearPreprocessingState();
  }, [uploadId, clearPreprocessingState]);

  useEffect(() => {
    if (!isAuthenticated) clearPreprocessingState();
  }, [isAuthenticated, clearPreprocessingState]);

  useEffect(() => stopProgressTimer, [stopProgressTimer]);

  const runProcessRequest = useCallback(
    async (requestFunction) => {
      if (!uploadId || isProcessing) return null;
      setIsProcessing(true);
      setError("");
      setProcessingProgress(7);
      stopProgressTimer();
      progressTimerRef.current = window.setInterval(() => {
        setProcessingProgress((current) => Math.min(current + 8, 93));
      }, 350);
      try {
        const response = await requestFunction(uploadId);
        stopProgressTimer();
        setProcessingProgress(100);
        setPreprocessingReport(response);
        setCurrentUploadStatus(
          response.preprocessing_status === "completed"
            ? "skin_type_analysis_pending"
            : response.preprocessing_status === "warning"
              ? "preprocessing_warning"
              : "preprocessing_failed",
        );
        return response;
      } catch (requestError) {
        stopProgressTimer();
        setProcessingProgress(0);
        setError(getPreprocessingErrorMessage(requestError));
        throw requestError;
      } finally {
        setIsProcessing(false);
      }
    },
    [uploadId, isProcessing, setCurrentUploadStatus, stopProgressTimer],
  );

  const processCurrentImage = useCallback(
    () => runProcessRequest(processImage),
    [runProcessRequest],
  );

  const reprocessCurrentImage = useCallback(
    () => runProcessRequest(reprocessImage),
    [runProcessRequest],
  );

  const loadReport = useCallback(async () => {
    if (!uploadId || isLoadingReport) return null;
    setIsLoadingReport(true);
    setError("");
    try {
      const response = await getPreprocessingReport(uploadId);
      setPreprocessingReport(response);
      return response;
    } catch (requestError) {
      setError(getPreprocessingErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingReport(false);
    }
  }, [uploadId, isLoadingReport]);

  const value = useMemo(
    () => ({
      preprocessingReport,
      preprocessingStatus: preprocessingReport?.preprocessing_status || "",
      isProcessing,
      isLoadingReport,
      processingProgress,
      error,
      canContinue: Boolean(preprocessingReport?.can_continue),
      processCurrentImage,
      reprocessCurrentImage,
      loadReport,
      clearPreprocessingState,
    }),
    [
      preprocessingReport,
      isProcessing,
      isLoadingReport,
      processingProgress,
      error,
      processCurrentImage,
      reprocessCurrentImage,
      loadReport,
      clearPreprocessingState,
    ],
  );

  return (
    <ImagePreprocessingContext.Provider value={value}>
      {children}
    </ImagePreprocessingContext.Provider>
  );
}

export function useImagePreprocessing() {
  const context = useContext(ImagePreprocessingContext);
  if (!context) {
    throw new Error(
      "useImagePreprocessing must be used inside ImagePreprocessingProvider",
    );
  }
  return context;
}
