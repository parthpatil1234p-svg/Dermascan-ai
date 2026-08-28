import api from "./api";

export async function getIngredients(filters = {}) {
  const response = await api.get("/ingredients", { params: filters });
  return response.data;
}

export async function getIngredientById(ingredientId) {
  const response = await api.get(`/ingredients/${encodeURIComponent(ingredientId)}`);
  return response.data;
}

