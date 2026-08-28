import { VALIDATION_MESSAGES } from "../constants/validationMessages.js";
import { IMAGE_UPLOAD_RULES } from "../constants/appContent.js";

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const MAX_IMAGE_SIZE_BYTES = IMAGE_UPLOAD_RULES.maxSizeMb * 1024 * 1024;

export function isValidEmail(email) {
  return emailPattern.test(String(email).trim());
}

export function validateLogin(values) {
  const errors = {};

  if (!values.email || !values.password) {
    errors.form = VALIDATION_MESSAGES.required;
  }

  if (values.email && !isValidEmail(values.email)) {
    errors.email = VALIDATION_MESSAGES.email;
  }

  return errors;
}

export function validateRegistration(values) {
  const errors = {};

  if (
    !values.fullName ||
    !values.email ||
    !values.password ||
    !values.confirmPassword ||
    !values.ageGroup ||
    !values.location
  ) {
    errors.form = VALIDATION_MESSAGES.required;
  }

  if (values.email && !isValidEmail(values.email)) {
    errors.email = VALIDATION_MESSAGES.email;
  }

  if (values.password && values.password.length < 8) {
    errors.password = VALIDATION_MESSAGES.passwordLength;
  }

  if (
    values.confirmPassword &&
    values.password &&
    values.confirmPassword !== values.password
  ) {
    errors.confirmPassword = VALIDATION_MESSAGES.passwordMatch;
  }

  if (!values.acceptTerms) {
    errors.acceptTerms = VALIDATION_MESSAGES.terms;
  }

  return errors;
}

export function validateSkinProfile(values) {
  const errors = {};

  if (!values.ageGroup) errors.ageGroup = "Please select an age group.";
  if (!values.country?.trim()) errors.country = "Please enter a country or location.";
  if (!values.experienceLevel) {
    errors.experienceLevel = "Please select your skincare experience level.";
  }
  if (!values.oilinessLevel) {
    errors.oilinessLevel = "Please select an oiliness level.";
  }
  if (!values.drynessLevel) {
    errors.drynessLevel = "Please select a dryness level.";
  }
  if (!values.sensitivity) {
    errors.sensitivity = "Please select a sensitivity option.";
  }
  if (!values.fragrancePreference) {
    errors.fragrancePreference = "Please select a fragrance preference.";
  }

  if (!values.noSpecificBudget) {
    const minimumBudget = Number(values.budgetMin);
    const maximumBudget = Number(values.budgetMax);

    if (values.budgetMin === "" || !Number.isFinite(minimumBudget)) {
      errors.budgetMin = "Please enter a minimum budget or select no specific budget.";
    } else if (minimumBudget < 0 || minimumBudget > 1000000) {
      errors.budgetMin = "Minimum budget must be between INR 0 and INR 1,000,000.";
    }

    if (values.budgetMax === "" || !Number.isFinite(maximumBudget)) {
      errors.budgetMax = "Please enter a maximum budget or select no specific budget.";
    } else if (maximumBudget < 0 || maximumBudget > 1000000) {
      errors.budgetMax = "Maximum budget must be between INR 0 and INR 1,000,000.";
    } else if (!errors.budgetMin && maximumBudget < minimumBudget) {
      errors.budgetMax = VALIDATION_MESSAGES.budgetRange;
    }
  }

  if (values.additionalNotes?.length > 1000) {
    errors.additionalNotes = "Additional notes must be 1,000 characters or fewer.";
  }

  return errors;
}

export function validateSkinProfileStep(values, stepIndex) {
  const allErrors = validateSkinProfile(values);
  const fieldsByStep = [
    ["ageGroup", "country", "experienceLevel"],
    ["oilinessLevel", "drynessLevel", "sensitivity"],
    ["fragrancePreference"],
    ["budgetMin", "budgetMax"],
    ["additionalNotes"],
  ];

  return fieldsByStep[stepIndex].reduce((stepErrors, field) => {
    if (allErrors[field]) stepErrors[field] = allErrors[field];
    return stepErrors;
  }, {});
}

export function validateImageFile(file) {
  if (!file) {
    return VALIDATION_MESSAGES.imageRequired;
  }

  const lowerName = file.name.toLowerCase();
  const hasValidExtension = IMAGE_UPLOAD_RULES.allowedExtensions.some((extension) =>
    lowerName.endsWith(extension),
  );
  const hasValidType = IMAGE_UPLOAD_RULES.allowedMimeTypes.includes(file.type);

  if (!hasValidExtension || !hasValidType) {
    return VALIDATION_MESSAGES.imageType;
  }

  if (file.size > MAX_IMAGE_SIZE_BYTES) {
    return VALIDATION_MESSAGES.imageSize;
  }

  return "";
}

export function validateImageFiles(files) {
  const selectedFiles = Array.from(files || []);
  if (selectedFiles.length === 0) return VALIDATION_MESSAGES.imageRequired;
  if (selectedFiles.length !== 1) return VALIDATION_MESSAGES.imageCount;
  return validateImageFile(selectedFiles[0]);
}

export function formatBytes(bytes) {
  if (!bytes) {
    return "0 KB";
  }

  return `${(bytes / 1024).toFixed(1)} KB`;
}
