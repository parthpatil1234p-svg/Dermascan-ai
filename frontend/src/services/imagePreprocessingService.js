import api from "./api";

export async function processImage(uploadId) {
  const response = await api.post(`/image-preprocessing/${uploadId}/process`);
  return response.data;
}

export async function getPreprocessingReport(uploadId) {
  const response = await api.get(`/image-preprocessing/${uploadId}`);
  return response.data;
}

export async function reprocessImage(uploadId) {
  return processImage(uploadId);
}

export function getPreprocessingErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) {
    return "Unable to reach the image-preprocessing service. Check the backend connection and try again.";
  }
  return "We could not prepare the facial image. No skin type, skin concern, identity, or medical analysis was performed.";
}
