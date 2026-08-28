import api from "./api";

export async function analyzeSkinType(uploadId) {
  const response = await api.post(`/skin-type/${uploadId}/analyze`);
  return response.data;
}

export async function getSkinTypeReport(uploadId) {
  const response = await api.get(`/skin-type/${uploadId}`);
  return response.data;
}

export async function getSkinTypeModelStatus() {
  const response = await api.get("/models/skin-type/status");
  return response.data;
}

export function getSkinTypeErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) {
    return "Unable to reach the skin-type analysis service. Check the backend connection and try again.";
  }
  return "We could not complete the skin-type estimate. No medical diagnosis or skin-concern analysis was performed.";
}
