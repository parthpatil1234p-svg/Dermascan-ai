import api from "./api";


export async function submitFeedback(payload) {
  const response = await api.post("/feedback", payload);
  return response.data;
}


export async function getFeedback(filters = {}) {
  const response = await api.get("/feedback", { params: filters });
  return response.data;
}


export async function getFeedbackById(feedbackId) {
  const response = await api.get(`/feedback/${encodeURIComponent(feedbackId)}`);
  return response.data;
}


export async function updateFeedback(feedbackId, payload) {
  const response = await api.put(`/feedback/${encodeURIComponent(feedbackId)}`, payload);
  return response.data;
}


export async function withdrawFeedback(feedbackId) {
  const response = await api.delete(`/feedback/${encodeURIComponent(feedbackId)}`);
  return response.data;
}


export async function getFeedbackOptions() {
  const response = await api.get("/feedback/options");
  return response.data;
}


export async function getProductAvoidances() {
  const response = await api.get("/feedback/product-avoidance");
  return response.data;
}


export async function removeProductAvoidance(productId) {
  const response = await api.delete(`/feedback/product-avoidance/${encodeURIComponent(productId)}`);
  return response.data;
}


export function getFeedbackErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg.replace(/^Value error,\s*/i, "");
  }
  if (!error?.response) {
    return "Unable to reach the feedback service. Check the backend connection and try again.";
  }
  return "We could not save your feedback. Review the form and try again.";
}
