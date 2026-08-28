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
  generateProductRecommendations,
  getProductRecommendationDetail,
  getProductRecommendationErrorMessage,
  getProductRecommendationReport,
} from "../services/productRecommendationService";

const ProductRecommendationContext = createContext(null);

export function ProductRecommendationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { uploadId, setCurrentUploadStatus } = useUpload();
  const [recommendationReport, setRecommendationReport] = useState(null);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [isLoadingProduct, setIsLoadingProduct] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [error, setError] = useState("");
  const timerRef = useRef(null);
  const requestRef = useRef(null);

  const stopProgress = useCallback(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const clearRecommendationState = useCallback(() => {
    stopProgress();
    requestRef.current = null;
    setRecommendationReport(null);
    setSelectedRecommendation(null);
    setIsGenerating(false);
    setIsLoadingReport(false);
    setIsLoadingProduct(false);
    setGenerationProgress(0);
    setError("");
  }, [stopProgress]);

  useEffect(() => clearRecommendationState(), [uploadId, clearRecommendationState]);
  useEffect(() => {
    if (!isAuthenticated) clearRecommendationState();
  }, [isAuthenticated, clearRecommendationState]);
  useEffect(() => stopProgress, [stopProgress]);

  const generateCurrentRecommendations = useCallback(async () => {
    if (!uploadId) return null;
    if (requestRef.current) return requestRef.current;
    setIsGenerating(true);
    setError("");
    setGenerationProgress(7);
    stopProgress();
    timerRef.current = window.setInterval(() => {
      setGenerationProgress((current) => Math.min(current + 8, 94));
    }, 380);

    const request = generateProductRecommendations(uploadId)
      .then((response) => {
        stopProgress();
        setGenerationProgress(100);
        setRecommendationReport(response);
        setCurrentUploadStatus("routine_generation_pending");
        return response;
      })
      .catch((requestError) => {
        stopProgress();
        setGenerationProgress(0);
        setError(getProductRecommendationErrorMessage(requestError));
        throw requestError;
      })
      .finally(() => {
        setIsGenerating(false);
        requestRef.current = null;
      });
    requestRef.current = request;
    return request;
  }, [uploadId, setCurrentUploadStatus, stopProgress]);

  const loadReport = useCallback(async (filters = {}) => {
    if (!uploadId || isLoadingReport) return null;
    setIsLoadingReport(true);
    setError("");
    try {
      const response = await getProductRecommendationReport(uploadId, filters);
      setRecommendationReport(response);
      return response;
    } catch (requestError) {
      setError(getProductRecommendationErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingReport(false);
    }
  }, [uploadId, isLoadingReport]);

  const loadRecommendationDetail = useCallback(async (productId) => {
    if (!uploadId || isLoadingProduct) return null;
    setIsLoadingProduct(true);
    setError("");
    try {
      const response = await getProductRecommendationDetail(uploadId, productId);
      setSelectedRecommendation(response);
      return response;
    } catch (requestError) {
      setError(getProductRecommendationErrorMessage(requestError));
      throw requestError;
    } finally {
      setIsLoadingProduct(false);
    }
  }, [uploadId, isLoadingProduct]);

  const closeRecommendationDetail = useCallback(() => setSelectedRecommendation(null), []);
  const value = useMemo(() => ({
    recommendationReport,
    selectedRecommendation,
    isGenerating,
    isLoadingReport,
    isLoadingProduct,
    generationProgress,
    error,
    generateCurrentRecommendations,
    loadReport,
    loadRecommendationDetail,
    closeRecommendationDetail,
    clearRecommendationState,
  }), [
    recommendationReport,
    selectedRecommendation,
    isGenerating,
    isLoadingReport,
    isLoadingProduct,
    generationProgress,
    error,
    generateCurrentRecommendations,
    loadReport,
    loadRecommendationDetail,
    closeRecommendationDetail,
    clearRecommendationState,
  ]);

  return (
    <ProductRecommendationContext.Provider value={value}>
      {children}
    </ProductRecommendationContext.Provider>
  );
}

export function useProductRecommendation() {
  const context = useContext(ProductRecommendationContext);
  if (!context) {
    throw new Error("useProductRecommendation must be used inside ProductRecommendationProvider");
  }
  return context;
}
