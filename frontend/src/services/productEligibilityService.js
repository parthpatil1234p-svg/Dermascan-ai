import api from "./api";

export async function evaluateProductEligibility(uploadId) {
  const response = await api.post(
    `/product-eligibility/${encodeURIComponent(uploadId)}/evaluate`,
  );
  return response.data;
}

export async function getProductEligibilityReport(uploadId, filters = {}) {
  const response = await api.get(
    `/product-eligibility/${encodeURIComponent(uploadId)}`,
    { params: filters },
  );
  return response.data;
}

export async function getProductEligibilityDetail(uploadId, productId) {
  const response = await api.get(
    `/product-eligibility/${encodeURIComponent(uploadId)}/products/${encodeURIComponent(productId)}`,
  );
  return response.data;
}

export function getProductEligibilityErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) {
    return "Unable to reach the product eligibility service. Check the backend connection and try again.";
  }
  return "We could not safely filter the product catalogue. No recommendation ranking was created.";
}
