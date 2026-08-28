import api from "./api";

const fieldMap = {
  age_group: "ageGroup",
  oiliness_level: "oilinessLevel",
  dryness_level: "drynessLevel",
  is_sensitive: "sensitivity",
  known_allergies: "knownAllergies",
  current_products: "currentProducts",
  budget_min: "budgetMin",
  budget_max: "budgetMax",
  preferred_brands: "preferredBrands",
  ingredients_to_avoid: "ingredientsToAvoid",
  fragrance_preference: "fragrancePreference",
  experience_level: "experienceLevel",
  additional_notes: "additionalNotes",
};

function cleanMessage(message) {
  return String(message || "Unable to save your changes. Please try again.").replace(
    /^Value error,\s*/i,
    "",
  );
}

export function getSkinProfileErrors(error) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return { form: detail };
  }

  if (Array.isArray(detail)) {
    return detail.reduce((errors, item) => {
      const rawField = item.loc?.[item.loc.length - 1] || "form";
      const field = fieldMap[rawField] || rawField;
      const message = cleanMessage(item.msg);
      errors[field === "body" ? "form" : field] = message;
      return errors;
    }, {});
  }

  return { form: "Unable to save your changes. Please try again." };
}

export function mapSkinProfilePayload(values) {
  const sensitivityMap = { Yes: true, No: false, "Not sure": null };
  const hasBudget = !values.noSpecificBudget;

  return {
    age_group: values.ageGroup,
    oiliness_level: values.oilinessLevel,
    dryness_level: values.drynessLevel,
    is_sensitive: sensitivityMap[values.sensitivity],
    known_allergies: values.knownAllergies,
    current_products: values.currentProducts,
    budget_min: hasBudget ? Number(values.budgetMin) : null,
    budget_max: hasBudget ? Number(values.budgetMax) : null,
    preferred_brands: values.preferredBrands,
    ingredients_to_avoid: values.ingredientsToAvoid,
    fragrance_preference: values.fragrancePreference,
    country: values.country,
    experience_level: values.experienceLevel,
    additional_notes: values.additionalNotes || null,
  };
}

export async function createSkinProfile(values) {
  const response = await api.post("/skin-profile", mapSkinProfilePayload(values));
  return response.data;
}

export async function getSkinProfile() {
  try {
    const response = await api.get("/skin-profile");
    return response.data;
  } catch (error) {
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function updateSkinProfile(values) {
  const response = await api.put("/skin-profile", mapSkinProfilePayload(values));
  return response.data;
}

export async function getSkinProfileStatus() {
  const response = await api.get("/skin-profile/status");
  return response.data;
}

export async function deleteSkinProfile() {
  const response = await api.delete("/skin-profile");
  return response.data;
}
