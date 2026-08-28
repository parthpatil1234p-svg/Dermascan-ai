import api from "./api";

export async function analyzeImageQuality(uploadId) {
  const response = await api.post(`/image-quality/${uploadId}/analyze`);
  return response.data;
}

export async function getImageQualityReport(uploadId) {
  const response = await api.get(`/image-quality/${uploadId}`);
  return response.data;
}

export async function acceptQualityWarning(uploadId) {
  const response = await api.post(
    `/image-quality/${uploadId}/accept-warning`,
  );
  return response.data;
}

export function getImageQualityErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) {
    return "Unable to reach the image-quality service. Check the backend connection and try again.";
  }
  return "We could not complete the image-quality check. Your image has not been analyzed for skin concerns. Please try again.";
}
