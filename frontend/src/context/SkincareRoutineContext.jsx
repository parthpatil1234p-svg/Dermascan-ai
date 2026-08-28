import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { useUpload } from "./UploadContext";
import { generateSkincareRoutine, getRoutineErrorMessage, getSkincareRoutine } from "../services/skincareRoutineService";


const SkincareRoutineContext = createContext(null);


export function SkincareRoutineProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [routineReport, setRoutineReport] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const requestRef = useRef(null);
  const timerRef = useRef(null);

  const stopTimer = useCallback(() => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = null;
  }, []);
  const clearRoutine = useCallback(() => {
    stopTimer();
    requestRef.current = null;
    setRoutineReport(null);
    setIsGenerating(false);
    setProgress(0);
    setError("");
  }, [stopTimer]);
  useEffect(() => clearRoutine(), [uploadId, clearRoutine]);
  useEffect(() => { if (!isAuthenticated) clearRoutine(); }, [isAuthenticated, clearRoutine]);
  useEffect(() => stopTimer, [stopTimer]);

  const generateCurrentRoutine = useCallback(async () => {
    if (!uploadId) return null;
    if (requestRef.current) return requestRef.current;
    setIsGenerating(true);
    setError("");
    setProgress(8);
    timerRef.current = window.setInterval(() => setProgress((value) => Math.min(94, value + 11)), 420);
    const request = generateSkincareRoutine(uploadId)
      .then((result) => {
        stopTimer();
        setProgress(100);
        setRoutineReport(result);
        setCurrentUploadStatus("final_report_pending");
        return result;
      })
      .catch((requestError) => {
        stopTimer();
        setProgress(0);
        setError(getRoutineErrorMessage(requestError));
        throw requestError;
      })
      .finally(() => { setIsGenerating(false); requestRef.current = null; });
    requestRef.current = request;
    return request;
  }, [uploadId, setCurrentUploadStatus, stopTimer]);

  const loadRoutine = useCallback(async () => {
    if (!uploadId) return null;
    try {
      const result = await getSkincareRoutine(uploadId);
      setRoutineReport(result);
      return result;
    } catch (requestError) {
      setError(getRoutineErrorMessage(requestError));
      throw requestError;
    }
  }, [uploadId]);

  const value = useMemo(() => ({ routineReport, isGenerating, generationProgress: progress, error, generateCurrentRoutine, loadRoutine, clearRoutine }), [routineReport, isGenerating, progress, error, generateCurrentRoutine, loadRoutine, clearRoutine]);
  return <SkincareRoutineContext.Provider value={value}>{children}</SkincareRoutineContext.Provider>;
}


export function useSkincareRoutine() {
  const value = useContext(SkincareRoutineContext);
  if (!value) throw new Error("useSkincareRoutine must be used inside SkincareRoutineProvider");
  return value;
}
