import api from "./api";

export async function generateProductRecommendations(uploadId) {
  const response = await api.post(
    `/product-recommendations/${encodeURIComponent(uploadId)}/generate`,
  );
  return response.data;
}

export async function getProductRecommendationReport(uploadId, filters = {}) {
  const response = await api.get(
    `/product-recommendations/${encodeURIComponent(uploadId)}`,
    { params: filters },
  );
  return response.data;
}

export async function getProductRecommendationDetail(uploadId, productId) {
  const response = await api.get(
    `/product-recommendations/${encodeURIComponent(uploadId)}/products/${encodeURIComponent(productId)}`,
  );
  return response.data;
}

export function getProductRecommendationErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) {
    return "Unable to reach the recommendation service. Check the backend connection and try again.";
  }
  return "We could not safely generate product recommendations. Your eligibility exclusions were not changed.";
}
