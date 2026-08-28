import { Eye, EyeOff, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import FormCheckbox from "../components/FormCheckbox";
import FormInput from "../components/FormInput";
import FormSelect from "../components/FormSelect";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import { AGE_GROUPS, ROUTES } from "../constants/appContent";
import { useAuth } from "../context/AuthContext";
import { getFormErrorsFromApiError } from "../services/authService";
import { validateRegistration } from "../utils/validation";

const initialValues = {
  fullName: "",
  email: "",
  password: "",
  confirmPassword: "",
  ageGroup: "",
  location: "",
  acceptTerms: false,
};

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = (field, value) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: "", form: "" }));
    setMessage("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const nextErrors = validateRegistration(values);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length === 0) {
      setIsSubmitting(true);

      try {
        await register(values);
        setMessage("Registration successful.");
        navigate(ROUTES.skinProfile, { replace: true });
      } catch (error) {
        setErrors(getFormErrorsFromApiError(error));
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Create profile"
        title="Register for DermaScan AI"
        description="Create a secure account for protected project pages. Passwords are hashed on the backend and never saved in browser storage."
      />

      <form
        onSubmit={handleSubmit}
        className="mx-auto max-w-2xl rounded-lg border border-slate-200 bg-white p-6 shadow-soft"
        noValidate
      >
        <ErrorMessage id="register-form-error" message={errors.form} />

        <div className="grid gap-5 sm:grid-cols-2">
          <FormInput
            id="register-full-name"
            label="Full name"
            value={values.fullName}
            onChange={(event) => updateField("fullName", event.target.value)}
            placeholder="Enter your full name"
            disabled={isSubmitting}
            required
          />
          <FormInput
            id="register-email"
            label="Email address"
            type="email"
            autoComplete="email"
            value={values.email}
            error={errors.email}
            onChange={(event) => updateField("email", event.target.value)}
            placeholder="name@example.com"
            disabled={isSubmitting}
            required
          />
          <div>
            <label
              htmlFor="register-password"
              className="block text-sm font-semibold text-slate-800"
            >
              Password
            </label>
            <div className="mt-2 flex rounded-lg border border-slate-300 bg-white shadow-sm focus-within:border-brand-600 focus-within:ring-4 focus-within:ring-brand-100">
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                value={values.password}
                onChange={(event) => updateField("password", event.target.value)}
                className="min-w-0 flex-1 rounded-l-lg border-0 px-3 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400"
                placeholder="Minimum 8 characters"
                disabled={isSubmitting}
                aria-invalid={errors.password ? "true" : "false"}
                aria-describedby={errors.password ? "register-password-error" : undefined}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                className="flex w-12 items-center justify-center rounded-r-lg text-slate-600 transition hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
                aria-label={showPassword ? "Hide password" : "Show password"}
                disabled={isSubmitting}
              >
                {showPassword ? (
                  <EyeOff aria-hidden="true" className="h-5 w-5" />
                ) : (
                  <Eye aria-hidden="true" className="h-5 w-5" />
                )}
              </button>
            </div>
            <ErrorMessage id="register-password-error" message={errors.password} />
          </div>
          <div>
            <label
              htmlFor="register-confirm-password"
              className="block text-sm font-semibold text-slate-800"
            >
              Confirm password
            </label>
            <div className="mt-2 flex rounded-lg border border-slate-300 bg-white shadow-sm focus-within:border-brand-600 focus-within:ring-4 focus-within:ring-brand-100">
              <input
                id="register-confirm-password"
                type={showConfirmPassword ? "text" : "password"}
                autoComplete="new-password"
                value={values.confirmPassword}
                onChange={(event) =>
                  updateField("confirmPassword", event.target.value)
                }
                className="min-w-0 flex-1 rounded-l-lg border-0 px-3 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400"
                placeholder="Re-enter password"
                disabled={isSubmitting}
                aria-invalid={errors.confirmPassword ? "true" : "false"}
                aria-describedby={
                  errors.confirmPassword
                    ? "register-confirm-password-error"
                    : undefined
                }
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword((current) => !current)}
                className="flex w-12 items-center justify-center rounded-r-lg text-slate-600 transition hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
                aria-label={
                  showConfirmPassword ? "Hide confirm password" : "Show confirm password"
                }
                disabled={isSubmitting}
              >
                {showConfirmPassword ? (
                  <EyeOff aria-hidden="true" className="h-5 w-5" />
                ) : (
                  <Eye aria-hidden="true" className="h-5 w-5" />
                )}
              </button>
            </div>
            <ErrorMessage
              id="register-confirm-password-error"
              message={errors.confirmPassword}
            />
          </div>
          <FormSelect
            id="register-age-group"
            label="Age group"
            options={AGE_GROUPS}
            value={values.ageGroup}
            onChange={(event) => updateField("ageGroup", event.target.value)}
            disabled={isSubmitting}
            required
          />
          <FormInput
            id="register-location"
            label="Location"
            value={values.location}
            onChange={(event) => updateField("location", event.target.value)}
            placeholder="City or country"
            disabled={isSubmitting}
            required
          />
        </div>

        <FormCheckbox
          id="register-terms"
          label="I agree to the terms and privacy notice"
          description="This creates a real project account for authentication. Do not use a password from another service."
          className="mt-6"
          checked={values.acceptTerms}
          error={errors.acceptTerms}
          disabled={isSubmitting}
          onChange={(event) => updateField("acceptTerms", event.target.checked)}
        />

        {message ? (
          <p
            className="mt-5 rounded-lg border border-clinic-100 bg-clinic-50 px-4 py-3 text-sm font-medium text-clinic-700"
            role="status"
          >
            {message}
          </p>
        ) : null}

        <PrimaryButton
          type="submit"
          icon={UserPlus}
          className="mt-6 w-full"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Creating account..." : "Register"}
        </PrimaryButton>

        <p className="mt-5 text-center text-sm text-slate-600">
          Already have an account?{" "}
          <Link
            to={ROUTES.login}
            className="font-semibold text-brand-700 hover:text-brand-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
          >
            Login
          </Link>
        </p>
      </form>
    </section>
  );
}
