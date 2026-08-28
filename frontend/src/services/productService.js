import api from "./api";

export async function getProducts(filters = {}) {
  const response = await api.get("/products", { params: filters });
  return response.data;
}

export async function getProductById(productId) {
  const response = await api.get(`/products/${encodeURIComponent(productId)}`);
  return response.data;
}

export function getCatalogueErrorMessage(error, fallback = "Product information could not be loaded.") {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

