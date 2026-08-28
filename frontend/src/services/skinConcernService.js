import api from "./api";

export async function analyzeSkinConcerns(uploadId) {
  const response = await api.post(`/skin-concerns/${uploadId}/analyze`);
  return response.data;
}

export async function getSkinConcernReport(uploadId) {
  const response = await api.get(`/skin-concerns/${uploadId}`);
  return response.data;
}

export async function getSkinConcernModelStatus() {
  const response = await api.get("/models/skin-concerns/status");
  return response.data;
}

export function getSkinConcernErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) {
    return "Unable to reach the visible skin-concern service. Check the backend connection and try again.";
  }
  return "We could not complete the visible skin-concern analysis. No medical diagnosis was performed.";
}
