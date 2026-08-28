import { useRef, useState } from "react";
import { ImagePlus, UploadCloud } from "lucide-react";
import ErrorMessage from "./ErrorMessage";
import SecondaryButton from "./SecondaryButton";

export default function UploadArea({ error, onCameraClick, onFileSelect }) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const errorId = "image-upload-error";

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const handleFiles = (files) => {
    const [file] = files;
    if (file) {
      onFileSelect(file);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openFileDialog();
    }
  };

  return (
    <div>
      <div
        role="button"
        tabIndex="0"
        aria-describedby={error ? errorId : undefined}
        onClick={openFileDialog}
        onKeyDown={handleKeyDown}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
        className={`flex min-h-72 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed bg-white p-8 text-center shadow-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${
          isDragging
            ? "border-brand-600 bg-brand-50"
            : "border-slate-300 hover:border-brand-500"
        }`}
      >
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-lg bg-clinic-100 text-clinic-700">
          <UploadCloud aria-hidden="true" className="h-8 w-8" />
        </div>
        <h2 className="text-xl font-semibold text-slate-950">
          Drag and drop a facial image
        </h2>
        <p className="mt-3 max-w-md text-sm leading-6 text-slate-600">
          Upload one clear image for the interface demo. Real face
          detection and image analysis will be implemented later.
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <SecondaryButton
            type="button"
            icon={ImagePlus}
            onClick={(event) => {
              event.stopPropagation();
              openFileDialog();
            }}
          >
            Select Image
          </SecondaryButton>
          <SecondaryButton
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onCameraClick();
            }}
          >
            Camera Capture
          </SecondaryButton>
        </div>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
        className="sr-only"
        onChange={(event) => handleFiles(event.target.files)}
      />
      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}
