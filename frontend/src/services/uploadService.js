import api from "./api";

export function getUploadErrorMessage(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "Unable to upload and validate the image. Please try again.";
}

export async function uploadFaceImage(file, consentGiven, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("consent_given", String(consentGiven));

  const response = await api.post("/uploads/face-image", formData, {
    timeout: 60000,
    onUploadProgress: (event) => {
      if (!event.total) return;
      onProgress?.(Math.min(100, Math.round((event.loaded / event.total) * 100)));
    },
  });
  return response.data;
}

export async function getUploadStatus(uploadId) {
  const response = await api.get(`/uploads/${uploadId}`);
  return response.data;
}

export async function deleteUpload(uploadId) {
  const response = await api.delete(`/uploads/${uploadId}`);
  return response.data;
}
