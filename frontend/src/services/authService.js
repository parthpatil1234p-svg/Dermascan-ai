import api, { clearStoredToken, storeToken } from "./api";

const fieldMap = {
  full_name: "fullName",
  confirm_password: "confirmPassword",
  age_group: "ageGroup",
  accept_terms: "acceptTerms",
};

function cleanBackendMessage(message) {
  return String(message || "Something went wrong. Please try again.").replace(
    /^Value error,\s*/i,
    "",
  );
}

export function getFormErrorsFromApiError(error) {
  const detail = error.response?.data?.detail;

  if (typeof detail === "string") {
    return { form: detail };
  }

  if (Array.isArray(detail)) {
    return detail.reduce((errors, item) => {
      const rawField = item.loc?.[item.loc.length - 1] || "form";
      const field = fieldMap[rawField] || rawField;
      const message = cleanBackendMessage(item.msg);

      if (field === "body" || field === "form") {
        errors.form = message;
      } else {
        errors[field] = message;
      }

      return errors;
    }, {});
  }

  if (error.response?.data?.message) {
    return { form: error.response.data.message };
  }

  if (error.message) {
    return { form: `${error.message}. Please check connection.` };
  }

  return { form: "Unable to complete the request. Please try again." };
}

function mapRegistrationPayload(values) {
  return {
    full_name: values.fullName,
    email: values.email,
    password: values.password,
    confirm_password: values.confirmPassword,
    age_group: values.ageGroup,
    location: values.location,
    accept_terms: values.acceptTerms,
  };
}

export async function registerUser(values) {
  const response = await api.post("/auth/register", mapRegistrationPayload(values));
  storeToken(response.data.access_token);
  return response.data;
}

export async function loginUser(values) {
  const response = await api.post("/auth/login", {
    email: values.email,
    password: values.password,
  });
  storeToken(response.data.access_token);
  return response.data;
}

export async function getCurrentUser() {
  const response = await api.get("/users/me");
  return response.data;
}

export async function logoutUser() {
  try {
    await api.post("/auth/logout");
  } finally {
    clearStoredToken();
  }
}

