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
  evaluateProductEligibility,
  getProductEligibilityDetail,
  getProductEligibilityErrorMessage,
  getProductEligibilityReport,
} from "../services/productEligibilityService";

const ProductEligibilityContext = createContext(null);

export function ProductEligibilityProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [eligibilityReport, setEligibilityReport] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [isLoadingProduct, setIsLoadingProduct] = useState(false);
  const [evaluationProgress, setEvaluationProgress] = useState(0);
  const [error, setError] = useState("");
  const progressTimerRef = useRef(null);
  const evaluationPromiseRef = useRef(null);

  const stopProgress = useCallback(() => {
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  const clearEligibilityState = useCallback(() => {
    stopProgress();
    evaluationPromiseRef.current = null;
    setEligibilityReport(null);
    setSelectedProduct(null);
    setIsEvaluating(false);
    setIsLoadingReport(false);
    setIsLoadingProduct(false);
    setEvaluationProgress(0);
    setError("");
  }, [stopProgress]);

  useEffect(() => clearEligibilityState(), [uploadId, clearEligibilityState]);
  useEffect(() => {
    if (!isAuthenticated) clearEligibilityState();
  }, [isAuthenticated, clearEligibilityState]);
  useEffect(() => stopProgress, [stopProgress]);

  const evaluateCurrentProducts = useCallback(async () => {
    if (!uploadId) return null;
    if (evaluationPromiseRef.current) return evaluationPromiseRef.current;

    setIsEvaluating(true);
    setError("");
    setEvaluationProgress(8);
    stopProgress();
    progressTimerRef.current = window.setInterval(() => {
      setEvaluationProgress((current) => Math.min(current + 9, 94));
    }, 360);

    const request = evaluateProductEligibility(uploadId)
      .then((response) => {
        stopProgress();
        setEvaluationProgress(100);
        setEligibilityReport(response);
        setCurrentUploadStatus("recommendation_scoring_pending");
        return response;
      })
      .catch((requestError) => {
        stopProgress();
        setEvaluationProgress(0);
        setError(getProductEligibilityErrorMessage(requestError));
        throw requestError;
      })
      .finally(() => {
        setIsEvaluating(false);
        evaluationPromiseRef.current = null;
      });

    evaluationPromiseRef.current = request;
    return request;
  }, [uploadId, setCurrentUploadStatus, stopProgress]);

  const loadReport = useCallback(async (filters = {}) => {
    if (!uploadId || isLoadingReport) return null;
    setIsLoadingReport(true);
    setError("");
    try {
      const response = await getProductEligibilityReport(uploadId, filters);
      setEligibilityReport(response);
      return response;
    } catch (requestError) {
      setError(getProductEligibilityErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingReport(false);
    }
  }, [uploadId, isLoadingReport]);

  const loadProductDetail = useCallback(async (productId) => {
    if (!uploadId || isLoadingProduct) return null;
    setIsLoadingProduct(true);
    setError("");
    try {
      const response = await getProductEligibilityDetail(uploadId, productId);
      setSelectedProduct(response);
      return response;
    } catch (requestError) {
      setError(getProductEligibilityErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingProduct(false);
    }
  }, [uploadId, isLoadingProduct]);

  const closeProductDetail = useCallback(() => setSelectedProduct(null), []);

  const value = useMemo(() => ({
    eligibilityReport,
    selectedProduct,
    isEvaluating,
    isLoadingReport,
    isLoadingProduct,
    evaluationProgress,
    error,
    evaluateCurrentProducts,
    loadReport,
    loadProductDetail,
    closeProductDetail,
    clearEligibilityState,
  }), [
    eligibilityReport,
    selectedProduct,
    isEvaluating,
    isLoadingReport,
    isLoadingProduct,
    evaluationProgress,
    error,
    evaluateCurrentProducts,
    loadReport,
    loadProductDetail,
    closeProductDetail,
    clearEligibilityState,
  ]);

  return (
    <ProductEligibilityContext.Provider value={value}>
      {children}
    </ProductEligibilityContext.Provider>
  );
}

export function useProductEligibility() {
  const context = useContext(ProductEligibilityContext);
  if (!context) {
    throw new Error("useProductEligibility must be used inside ProductEligibilityProvider");
  }
  return context;
}
