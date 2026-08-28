import {
  AlertTriangle,
  ArrowLeft,
  FileImage,
  LockKeyhole,
  ScanFace,
  UploadCloud,
} from "lucide-react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import DisclaimerBox from "../components/DisclaimerBox";
import ErrorMessage from "../components/ErrorMessage";
import FaceImageUploader from "../components/FaceImageUploader";
import FormCheckbox from "../components/FormCheckbox";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import {
  IMAGE_GUIDELINES,
  IMAGE_UPLOAD_RULES,
  ROUTES,
} from "../constants/appContent";
import { VALIDATION_MESSAGES } from "../constants/validationMessages";
import { useUpload } from "../context/UploadContext";

export default function FaceScanPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    selectedFile,
    previewUrl,
    uploadProgress,
    isUploading,
    validationError,
    serverError,
    selectFiles,
    clearSelectedFile,
    uploadSelectedFile,
  } = useUpload();
  const [consentGiven, setConsentGiven] = useState(false);
  const [consentError, setConsentError] = useState("");

  const handleFiles = (files) => {
    if (selectFiles(files)) {
      setConsentGiven(false);
      setConsentError("");
    }
  };

  const handleRemove = () => {
    clearSelectedFile();
    setConsentGiven(false);
    setConsentError("");
  };

  const handleUpload = async () => {
    if (isUploading) return;
    if (!selectedFile) {
      selectFiles([]);
      return;
    }
    if (!consentGiven) {
      setConsentError(VALIDATION_MESSAGES.imageConsent);
      return;
    }

    setConsentError("");
    try {
      const response = await uploadSelectedFile(consentGiven);
      navigate(response.next_route || ROUTES.imageQualityCheck);
    } catch {
      // The context exposes a safe validation or server message.
    }
  };

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Secure image upload"
        title="Upload a Clear Facial Image"
        description="Upload one clear, front-facing facial image. The image will be temporarily processed to prepare it for AI-assisted skincare analysis."
      />

      {location.state?.profileSaved ? (
        <p
          className="mx-auto mb-6 max-w-6xl rounded-lg border border-leaf-100 bg-leaf-50 px-4 py-3 text-sm font-semibold text-leaf-700"
          role="status"
        >
          Your skin profile has been saved successfully.
        </p>
      ) : null}
      {location.state?.uploadDeleted ? (
        <p
          className="mx-auto mb-6 max-w-6xl rounded-lg border border-clinic-100 bg-clinic-50 px-4 py-3 text-sm font-semibold text-clinic-700"
          role="status"
        >
          The temporary image was deleted successfully.
        </p>
      ) : null}
      {location.state?.uploadError ? (
        <p
          className="mx-auto mb-6 max-w-6xl rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900"
          role="alert"
        >
          {location.state.uploadError}
        </p>
      ) : null}

      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[minmax(0,1.25fr)_22rem]">
        <div className="space-y-6">
          <FaceImageUploader
            selectedFile={selectedFile}
            previewUrl={previewUrl}
            error={validationError}
            onFiles={handleFiles}
            onRemove={handleRemove}
            disabled={isUploading}
          />

          <div className="grid gap-4 border-y border-slate-200 py-5 sm:grid-cols-3">
            <div className="flex items-start gap-3">
              <FileImage className="mt-0.5 h-5 w-5 text-brand-700" aria-hidden="true" />
              <div><h2 className="text-sm font-semibold text-slate-950">Supported formats</h2><p className="mt-1 text-sm text-slate-600">JPG, JPEG, PNG</p></div>
            </div>
            <div className="flex items-start gap-3">
              <UploadCloud className="mt-0.5 h-5 w-5 text-clinic-700" aria-hidden="true" />
              <div><h2 className="text-sm font-semibold text-slate-950">Maximum size</h2><p className="mt-1 text-sm text-slate-600">{IMAGE_UPLOAD_RULES.maxSizeMb} MB</p></div>
            </div>
            <div className="flex items-start gap-3">
              <ScanFace className="mt-0.5 h-5 w-5 text-leaf-700" aria-hidden="true" />
              <div><h2 className="text-sm font-semibold text-slate-950">Minimum resolution</h2><p className="mt-1 text-sm text-slate-600">{IMAGE_UPLOAD_RULES.minWidth} x {IMAGE_UPLOAD_RULES.minHeight} pixels</p></div>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <h2 className="text-lg font-semibold text-slate-950">
                  Processing consent
                </h2>
                <FormCheckbox
                  id="image-processing-consent"
                  className="mt-4"
                  label="I consent to this facial image being temporarily processed for general skincare analysis. I understand that DermaScan AI is not a medical diagnostic system."
                  checked={consentGiven}
                  error={consentError}
                  disabled={isUploading}
                  onChange={(event) => {
                    setConsentGiven(event.target.checked);
                    setConsentError("");
                  }}
                />
              </div>
            </div>
          </div>

          {isUploading ? (
            <div className="rounded-lg border border-brand-100 bg-brand-50 p-5" role="status">
              <div className="flex items-center justify-between gap-4 text-sm font-semibold text-brand-700">
                <span>Securely uploading and validating your image...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div
                className="mt-3 h-2 overflow-hidden rounded-full bg-white"
                role="progressbar"
                aria-label="Image upload progress"
                aria-valuemin="0"
                aria-valuemax="100"
                aria-valuenow={uploadProgress}
              >
                <div
                  className="h-full rounded-full bg-brand-600 transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : null}

          <ErrorMessage id="face-upload-server-error" message={serverError} />

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
            <SecondaryButton
              type="button"
              icon={ArrowLeft}
              onClick={() => navigate(ROUTES.skinProfile)}
              disabled={isUploading}
            >
              Edit Skin Profile
            </SecondaryButton>
            <PrimaryButton
              type="button"
              icon={UploadCloud}
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading ? "Uploading and Validating..." : "Upload and Continue"}
            </PrimaryButton>
          </div>
        </div>

        <aside className="space-y-6">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">Capture instructions</h2>
            <ul className="mt-4 grid gap-3">
              {IMAGE_GUIDELINES.map((guideline) => (
                <li key={guideline} className="flex gap-3 text-sm text-slate-700">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-600" />
                  <span>{guideline}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" aria-hidden="true" />
              <p className="text-sm leading-6 text-amber-950">
                Your image will be stored temporarily for processing and will not be used as a medical diagnosis. Avoid uploading an image containing other people. Do not upload an image unless you have the right to use it.
              </p>
            </div>
          </div>

          <DisclaimerBox title="Not a medical diagnostic system" />
        </aside>
      </div>
    </section>
  );
}
