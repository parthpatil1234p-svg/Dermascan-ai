export const PRODUCT_CATEGORIES = [
  ["cleanser", "Cleanser"], ["toner", "Toner"], ["serum", "Serum"],
  ["moisturizer", "Moisturizer"], ["sunscreen", "Sunscreen"],
  ["exfoliant", "Exfoliant"], ["spot_care", "Spot care"],
  ["under_eye_product", "Under-eye product"], ["face_mask", "Face mask"],
  ["night_cream", "Night cream"], ["lip_care", "Lip care"],
];

export const CATALOGUE_SKIN_TYPES = [
  ["normal", "Normal"], ["oily", "Oily"], ["dry", "Dry"],
  ["combination", "Combination"],
  ["sensitive_self_reported", "Self-reported sensitive"],
  ["all_skin_types", "All skin types"],
];

export const VISIBLE_CONCERNS = [
  ["visible_oiliness", "Visible oiliness"], ["dry_looking_areas", "Dry-looking areas"],
  ["visible_pores", "Visible pores"], ["visible_redness", "Visible redness"],
  ["uneven_looking_tone", "Uneven-looking tone"], ["dark_spots", "Dark spots"],
  ["acne_like_spots", "Acne-like spots"], ["under_eye_darkness", "Under-eye darkness"],
  ["dull_looking_appearance", "Dull-looking appearance"],
  ["fine_line_visibility", "Fine-line visibility"],
];

export const FRAGRANCE_STATUSES = [
  ["fragrance_free", "Fragrance free"],
  ["contains_added_fragrance", "Contains added fragrance"],
  ["contains_fragrant_ingredients", "Contains fragrant ingredients"],
  ["unknown", "Unknown"],
];

export const SORT_OPTIONS = [
  ["name_asc", "Name A-Z"], ["name_desc", "Name Z-A"],
  ["price_low_to_high", "Price: low to high"],
  ["price_high_to_low", "Price: high to low"], ["newest", "Newest records"],
];

export function displayCode(value) {
  return value?.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Not specified";
}

