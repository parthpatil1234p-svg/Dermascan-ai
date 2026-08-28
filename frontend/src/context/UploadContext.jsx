import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useAuth } from "./AuthContext";
import { VALIDATION_MESSAGES } from "../constants/validationMessages";
import {
  deleteUpload,
  getUploadErrorMessage,
  getUploadStatus,
  uploadFaceImage,
} from "../services/uploadService";
import { validateImageFile, validateImageFiles } from "../utils/validation";

const UploadContext = createContext(null);
const ACTIVE_UPLOAD_KEY = "dermascan_active_upload_id";

function getStoredUploadId() {
  return typeof window === "undefined"
    ? ""
    : window.sessionStorage.getItem(ACTIVE_UPLOAD_KEY) || "";
}

export function UploadProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [uploadResponse, setUploadResponse] = useState(null);
  const [uploadId, setUploadId] = useState(getStoredUploadId);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [validationError, setValidationError] = useState("");
  const [serverError, setServerError] = useState("");
  const [verificationError, setVerificationError] = useState("");

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const clearSelectedFile = useCallback(() => {
    setSelectedFile(null);
    setPreviewUrl("");
    setValidationError("");
    setServerError("");
    setUploadProgress(0);
  }, []);

  const clearUploadReference = useCallback(() => {
    window.sessionStorage.removeItem(ACTIVE_UPLOAD_KEY);
    setUploadResponse(null);
    setUploadId("");
    setUploadStatus("");
    setIsVerified(false);
    setVerificationError("");
  }, []);

  const setCurrentUploadStatus = useCallback((status) => {
    setUploadStatus(status);
    setUploadResponse((current) =>
      current ? { ...current, status } : current,
    );
  }, []);

  const resetUploadWorkflow = useCallback(() => {
    clearSelectedFile();
    clearUploadReference();
  }, [clearSelectedFile, clearUploadReference]);

  useEffect(() => {
    if (!isAuthenticated) resetUploadWorkflow();
  }, [isAuthenticated, resetUploadWorkflow]);

  const selectFiles = useCallback((files) => {
    const nextError = validateImageFiles(files);
    if (nextError) {
      setValidationError(nextError);
      return false;
    }

    const file = Array.from(files)[0];
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setValidationError("");
    setServerError("");
    setUploadProgress(0);
    return true;
  }, []);

  const uploadSelectedFile = useCallback(async (consentGiven) => {
    const fileError = validateImageFile(selectedFile);
    if (fileError) {
      setValidationError(fileError);
      throw new Error(fileError);
    }
    if (!consentGiven) {
      throw new Error(VALIDATION_MESSAGES.imageConsent);
    }
    if (isUploading) return uploadResponse;

    setIsUploading(true);
    setUploadProgress(0);
    setServerError("");
    try {
      const response = await uploadFaceImage(
        selectedFile,
        consentGiven,
        setUploadProgress,
      );
      setUploadResponse(response);
      setUploadId(response.upload_id);
      window.sessionStorage.setItem(ACTIVE_UPLOAD_KEY, response.upload_id);
      setUploadStatus(response.status);
      setIsVerified(false);
      clearSelectedFile();
      return response;
    } catch (error) {
      const message = getUploadErrorMessage(error);
      setServerError(message);
      throw error;
    } finally {
      setIsUploading(false);
    }
  }, [clearSelectedFile, isUploading, selectedFile, uploadResponse]);

  const verifyCurrentUpload = useCallback(async () => {
    if (!uploadId) return null;
    setIsVerifying(true);
    setVerificationError("");
    try {
      const response = await getUploadStatus(uploadId);
      setUploadResponse((current) => ({ ...current, ...response }));
      setUploadStatus(response.status);
      setIsVerified(true);
      return response;
    } catch (error) {
      window.sessionStorage.removeItem(ACTIVE_UPLOAD_KEY);
      setUploadId("");
      setUploadStatus("");
      setVerificationError(getUploadErrorMessage(error));
      setIsVerified(false);
      throw error;
    } finally {
      setIsVerifying(false);
    }
  }, [uploadId]);

  const deleteCurrentUpload = useCallback(async () => {
    if (!uploadId) return null;
    setIsDeleting(true);
    setServerError("");
    try {
      return await deleteUpload(uploadId);
    } catch (error) {
      setServerError(getUploadErrorMessage(error));
      throw error;
    } finally {
      setIsDeleting(false);
    }
  }, [uploadId]);

  const value = useMemo(
    () => ({
      selectedFile,
      previewUrl,
      uploadResponse,
      uploadId,
      uploadStatus,
      uploadProgress,
      isUploading,
      isVerifying,
      isDeleting,
      isVerified,
      validationError,
      serverError,
      verificationError,
      selectFiles,
      clearSelectedFile,
      clearUploadReference,
      setCurrentUploadStatus,
      resetUploadWorkflow,
      uploadSelectedFile,
      verifyCurrentUpload,
      deleteCurrentUpload,
    }),
    [
      selectedFile,
      previewUrl,
      uploadResponse,
      uploadId,
      uploadStatus,
      uploadProgress,
      isUploading,
      isVerifying,
      isDeleting,
      isVerified,
      validationError,
      serverError,
      verificationError,
      selectFiles,
      clearSelectedFile,
      clearUploadReference,
      setCurrentUploadStatus,
      resetUploadWorkflow,
      uploadSelectedFile,
      verifyCurrentUpload,
      deleteCurrentUpload,
    ],
  );

  return <UploadContext.Provider value={value}>{children}</UploadContext.Provider>;
}

export function useUpload() {
  const context = useContext(UploadContext);
  if (!context) throw new Error("useUpload must be used inside UploadProvider");
  return context;
}
