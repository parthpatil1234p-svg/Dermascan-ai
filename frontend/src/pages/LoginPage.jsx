import { Eye, EyeOff, LogIn } from "lucide-react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import FormCheckbox from "../components/FormCheckbox";
import FormInput from "../components/FormInput";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import { ROUTES } from "../constants/appContent";
import { useAuth } from "../context/AuthContext";
import { getFormErrorsFromApiError } from "../services/authService";
import { getSkinProfileStatus } from "../services/skinProfileService";
import { validateLogin } from "../utils/validation";

const initialValues = {
  email: "",
  password: "",
  rememberMe: false,
};

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState("");
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

    const nextErrors = validateLogin(values);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length === 0) {
      setIsSubmitting(true);

      try {
        await login(values);
        setMessage("Login successful.");
        let destination = ROUTES.skinProfile;
        try {
          const profileStatus = await getSkinProfileStatus();
          const intendedRoute = location.state?.from;
          const profileRequiredRoutes = [
            ROUTES.faceScan,
            ROUTES.analysisLoading,
            ROUTES.results,
          ];
          const canUseIntendedRoute =
            intendedRoute &&
            (!profileRequiredRoutes.includes(intendedRoute) ||
              profileStatus.is_complete);
          destination = canUseIntendedRoute
            ? intendedRoute
            : profileStatus.next_route;
        } catch {
          destination = ROUTES.skinProfile;
        }
        navigate(destination, { replace: true });
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
        eyebrow="Account access"
        title="Login to DermaScan AI"
        description="Access your DermaScan AI account to continue to protected project pages."
      />

      <form
        onSubmit={handleSubmit}
        className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-soft"
        noValidate
      >
        <ErrorMessage id="login-form-error" message={errors.form} />

        <div className="space-y-5">
          <FormInput
            id="login-email"
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
              htmlFor="login-password"
              className="block text-sm font-semibold text-slate-800"
            >
              Password
            </label>
            <div className="mt-2 flex rounded-lg border border-slate-300 bg-white shadow-sm focus-within:border-brand-600 focus-within:ring-4 focus-within:ring-brand-100">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={values.password}
                onChange={(event) => updateField("password", event.target.value)}
                className="min-w-0 flex-1 rounded-l-lg border-0 px-3 py-3 text-sm text-slate-950 outline-none placeholder:text-slate-400"
                disabled={isSubmitting}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                className="flex w-12 items-center justify-center rounded-r-lg text-slate-600 transition hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff aria-hidden="true" className="h-5 w-5" />
                ) : (
                  <Eye aria-hidden="true" className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <FormCheckbox
              id="remember-me"
              label="Keep me signed in on this browser"
              checked={values.rememberMe}
              disabled={isSubmitting}
              onChange={(event) =>
                updateField("rememberMe", event.target.checked)
              }
            />
            <a
              href="#forgot-password"
              className="text-sm font-semibold text-brand-700 hover:text-brand-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
            >
              Forgot password?
            </a>
          </div>
        </div>

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
          icon={LogIn}
          className="mt-6 w-full"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Logging in..." : "Login"}
        </PrimaryButton>

        <p className="mt-5 text-center text-sm text-slate-600">
          New to DermaScan AI?{" "}
          <Link
            to={ROUTES.register}
            className="font-semibold text-brand-700 hover:text-brand-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
          >
            Create an account
          </Link>
        </p>
      </form>
    </section>
  );
}
