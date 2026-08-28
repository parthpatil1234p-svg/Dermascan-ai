import {
  FileImage,
  ImagePlus,
  RefreshCw,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { formatBytes } from "../utils/validation";
import ErrorMessage from "./ErrorMessage";
import SecondaryButton from "./SecondaryButton";

function formatName(file) {
  if (file.type === "image/png") return "PNG";
  return file.name.toLowerCase().endsWith(".jpeg") ? "JPEG" : "JPG";
}

export default function FaceImageUploader({
  selectedFile,
  previewUrl,
  error,
  onFiles,
  onRemove,
  disabled = false,
}) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const errorId = "face-image-upload-error";

  useEffect(() => {
    if (!selectedFile && fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [selectedFile]);

  const openFileDialog = () => {
    if (!disabled) fileInputRef.current?.click();
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openFileDialog();
    }
  };

  const handleFiles = (files) => {
    onFiles(files);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
        className="sr-only"
        aria-label="Select facial image"
        disabled={disabled}
        onChange={(event) => handleFiles(event.target.files)}
      />

      {selectedFile && previewUrl ? (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="grid gap-0 md:grid-cols-[minmax(0,1fr)_18rem]">
            <div className="bg-slate-100">
              <img
                src={previewUrl}
                alt="Preview of the selected facial image"
                className="aspect-square h-full w-full object-contain"
              />
            </div>
            <div className="flex flex-col justify-between p-5">
              <div>
                <div className="flex items-center gap-3">
                  <FileImage className="h-5 w-5 text-brand-700" aria-hidden="true" />
                  <h2 className="text-lg font-semibold text-slate-950">Selected image</h2>
                </div>
                <dl className="mt-5 space-y-4 text-sm">
                  <div>
                    <dt className="font-semibold text-slate-800">Filename</dt>
                    <dd className="mt-1 break-all text-slate-600">{selectedFile.name}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-slate-800">Format</dt>
                    <dd className="mt-1 text-slate-600">{formatName(selectedFile)}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-slate-800">File size</dt>
                    <dd className="mt-1 text-slate-600">{formatBytes(selectedFile.size)}</dd>
                  </div>
                </dl>
              </div>
              <div className="mt-6 grid gap-3">
                <SecondaryButton
                  type="button"
                  icon={RefreshCw}
                  onClick={openFileDialog}
                  disabled={disabled}
                  className="w-full"
                >
                  Replace Image
                </SecondaryButton>
                <SecondaryButton
                  type="button"
                  icon={Trash2}
                  onClick={onRemove}
                  disabled={disabled}
                  className="w-full"
                >
                  Remove Image
                </SecondaryButton>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-disabled={disabled}
          aria-describedby={error ? errorId : undefined}
          onClick={openFileDialog}
          onKeyDown={handleKeyDown}
          onDragOver={(event) => {
            event.preventDefault();
            if (!disabled) setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            if (!disabled) handleFiles(event.dataTransfer.files);
          }}
          className={`flex min-h-80 flex-col items-center justify-center rounded-lg border-2 border-dashed bg-white p-8 text-center shadow-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${
            disabled
              ? "cursor-not-allowed border-slate-200 opacity-70"
              : isDragging
                ? "cursor-copy border-brand-600 bg-brand-50"
                : "cursor-pointer border-slate-300 hover:border-brand-500"
          }`}
        >
          <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-clinic-100 text-clinic-700">
            <UploadCloud aria-hidden="true" className="h-8 w-8" />
          </div>
          <h2 className="mt-5 text-xl font-semibold text-slate-950">
            Drag and drop one facial image
          </h2>
          <p className="mt-3 max-w-md text-sm leading-6 text-slate-600">
            Choose a clear JPG, JPEG, or PNG image. It will not upload until you review the preview and provide consent.
          </p>
          <SecondaryButton
            type="button"
            icon={ImagePlus}
            className="mt-6"
            disabled={disabled}
            onClick={(event) => {
              event.stopPropagation();
              openFileDialog();
            }}
          >
            Select Image
          </SecondaryButton>
        </div>
      )}

      <ErrorMessage id={errorId} message={error} />
    </div>
  );
}
