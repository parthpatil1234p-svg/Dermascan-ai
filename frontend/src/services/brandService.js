import api from "./api";

export async function getBrands(filters = {}) {
  const response = await api.get("/brands", { params: filters });
  return response.data;
}

