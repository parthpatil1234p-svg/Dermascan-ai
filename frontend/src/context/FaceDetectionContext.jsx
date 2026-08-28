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
  acceptFaceDetectionWarning,
  analyzeFace,
  getFaceDetectionErrorMessage,
  getFaceDetectionReport,
} from "../services/faceDetectionService";

const FaceDetectionContext = createContext(null);

export function FaceDetectionProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [faceReport, setFaceReport] = useState(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [isAcceptingWarning, setIsAcceptingWarning] = useState(false);
  const [detectionProgress, setDetectionProgress] = useState(0);
  const [error, setError] = useState("");
  const progressTimerRef = useRef(null);

  const stopProgressTimer = useCallback(() => {
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const clearFaceDetectionState = useCallback(() => {
    stopProgressTimer();
    setFaceReport(null);
    setIsDetecting(false);
    setIsLoadingReport(false);
    setIsAcceptingWarning(false);
    setDetectionProgress(0);
    setError("");
  }, [stopProgressTimer]);

  useEffect(() => {
    clearFaceDetectionState();
  }, [uploadId, clearFaceDetectionState]);

  useEffect(() => {
    if (!isAuthenticated) clearFaceDetectionState();
  }, [isAuthenticated, clearFaceDetectionState]);

  useEffect(() => stopProgressTimer, [stopProgressTimer]);

  const analyze = useCallback(async () => {
    if (!uploadId || isDetecting) return null;
    setIsDetecting(true);
    setError("");
    setDetectionProgress(8);
    stopProgressTimer();
    progressTimerRef.current = window.setInterval(() => {
      setDetectionProgress((current) => Math.min(current + 9, 92));
    }, 350);

    try {
      const response = await analyzeFace(uploadId);
      stopProgressTimer();
      setDetectionProgress(100);
      setFaceReport(response);
      setCurrentUploadStatus(
        response.detection_status === "passed"
          ? "face_detected"
          : response.detection_status === "warning"
            ? "face_detection_warning"
            : "face_detection_failed",
      );
      return response;
    } catch (requestError) {
      stopProgressTimer();
      setDetectionProgress(0);
      setError(getFaceDetectionErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsDetecting(false);
    }
  }, [uploadId, isDetecting, setCurrentUploadStatus, stopProgressTimer]);

  const loadReport = useCallback(async () => {
    if (!uploadId || isLoadingReport) return null;
    setIsLoadingReport(true);
    setError("");
    try {
      const response = await getFaceDetectionReport(uploadId);
      setFaceReport(response);
      return response;
    } catch (requestError) {
      setError(getFaceDetectionErrorMessage(requestError));
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
      const response = await acceptFaceDetectionWarning(uploadId);
      setFaceReport((current) => ({ ...current, ...response }));
      setCurrentUploadStatus("preprocessing_pending");
      return response;
    } catch (requestError) {
      setError(getFaceDetectionErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsAcceptingWarning(false);
    }
  }, [uploadId, isAcceptingWarning, setCurrentUploadStatus]);

  const value = useMemo(
    () => ({
      faceReport,
      detectionStatus: faceReport?.detection_status || "",
      isDetecting,
      isLoadingReport,
      isAcceptingWarning,
      detectionProgress,
      error,
      canContinue: Boolean(faceReport?.can_continue),
      warningAccepted: Boolean(faceReport?.warning_accepted),
      analyze,
      loadReport,
      acceptWarning,
      clearFaceDetectionState,
    }),
    [
      faceReport,
      isDetecting,
      isLoadingReport,
      isAcceptingWarning,
      detectionProgress,
      error,
      analyze,
      loadReport,
      acceptWarning,
      clearFaceDetectionState,
    ],
  );

  return (
    <FaceDetectionContext.Provider value={value}>
      {children}
    </FaceDetectionContext.Provider>
  );
}

export function useFaceDetection() {
  const context = useContext(FaceDetectionContext);
  if (!context) {
    throw new Error("useFaceDetection must be used inside FaceDetectionProvider");
  }
  return context;
}
