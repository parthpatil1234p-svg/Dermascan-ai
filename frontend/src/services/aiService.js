import api from "./api";

export async function sendAIChatMessage(message, history = [], userContext = null) {
  const response = await api.post("/ai/chat", {
    message,
    history,
    user_context: userContext,
  });
  return response.data;
}

export async function checkIngredients(ingredientsText, skinType = null) {
  const response = await api.post("/ai/ingredient-check", {
    ingredients_text: ingredientsText,
    skin_type: skinType,
  });
  return response.data;
}
