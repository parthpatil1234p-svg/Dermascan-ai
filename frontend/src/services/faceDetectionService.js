import api from "./api";

export async function analyzeFace(uploadId) {
  const response = await api.post(`/face-detection/${uploadId}/analyze`);
  return response.data;
}

export async function getFaceDetectionReport(uploadId) {
  const response = await api.get(`/face-detection/${uploadId}`);
  return response.data;
}

export async function acceptFaceDetectionWarning(uploadId) {
  const response = await api.post(`/face-detection/${uploadId}/accept-warning`);
  return response.data;
}

export function getFaceDetectionErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) {
    return "Unable to reach the face-detection service. Check the backend connection and try again.";
  }
  return "We could not complete face detection. No identity, skin, or medical analysis was performed. Please try again.";
}
