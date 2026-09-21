import { ArrowLeft, CheckCircle2, Eye, EyeOff, KeyRound, Mail, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import FormInput from "../components/FormInput";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import { ROUTES } from "../constants/appContent";
import { getFormErrorsFromApiError, requestPasswordReset, resetPassword } from "../services/authService";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();

  // Step 1: "request", Step 2: "verify", Step 3: "success"
  const [step, setStep] = useState("request");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [errors, setErrors] = useState({});
  const [infoMessage, setInfoMessage] = useState("");
  const [demoOtp, setDemoOtp] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Step 1 handler: Request OTP
  const handleRequestOtp = async (event) => {
    event.preventDefault();
    if (isSubmitting) return;

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setErrors({ email: "Email address is required." });
      return;
    }
    if (!/\S+@\S+\.\S+/.test(trimmedEmail)) {
      setErrors({ email: "Please enter a valid email address." });
      return;
    }

    setIsSubmitting(true);
    setErrors({});
    setInfoMessage("");

    try {
      const response = await requestPasswordReset(trimmedEmail);
      setInfoMessage(response.message || "A verification code has been sent.");
      if (response.dev_otp) {
        setDemoOtp(response.dev_otp);
        setOtp(response.dev_otp); // auto-fill in demo mode for convenience
      }
      setStep("verify");
    } catch (error) {
      setErrors(getFormErrorsFromApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 2 handler: Verify OTP & Reset Password
  const handleResetPassword = async (event) => {
    event.preventDefault();
    if (isSubmitting) return;

    const validationErrors = {};
    const trimmedOtp = otp.trim();
    if (!trimmedOtp) {
      validationErrors.otp = "Verification code is required.";
    } else if (trimmedOtp.length !== 6) {
      validationErrors.otp = "Verification code must be exactly 6 digits.";
    }

    if (!newPassword) {
      validationErrors.newPassword = "New password is required.";
    } else if (newPassword.length < 8) {
      validationErrors.newPassword = "Password must be at least 8 characters long.";
    }

    if (newPassword !== confirmPassword) {
      validationErrors.confirmPassword = "Passwords do not match.";
    }

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});
    setInfoMessage("");

    try {
      await resetPassword({
        email: email.trim(),
        otp: trimmedOtp,
        newPassword,
        confirmPassword,
      });
      setStep("success");
    } catch (error) {
      setErrors(getFormErrorsFromApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="px-4 py-14 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Account Security"
        title="Reset Your Password"
        description="Follow the steps below to securely reset your DermaScan AI account password."
      />

      <div className="mx-auto max-w-md rounded-xl border border-slate-200 bg-white p-6 sm:p-8 shadow-soft">
        <ErrorMessage id="forgot-password-error" message={errors.form} />

        {/* Step 1: Request verification code */}
        {step === "request" && (
          <form onSubmit={handleRequestOtp} noValidate className="space-y-5">
            <div className="flex items-center gap-3 rounded-lg bg-sky-50 border border-sky-100 p-3.5 text-xs text-sky-800">
              <Mail className="h-5 w-5 text-sky-600 flex-shrink-0" />
              <span>
                Enter your registered email address and we'll send you a 6-digit code to reset your password.
              </span>
            </div>

            <FormInput
              id="reset-email"
              label="Registered Email Address"
              type="email"
              autoComplete="email"
              value={email}
              error={errors.email}
              onChange={(event) => {
                setEmail(event.target.value);
                setErrors((prev) => ({ ...prev, email: "", form: "" }));
              }}
              placeholder="name@example.com"
              disabled={isSubmitting}
              required
            />

            <PrimaryButton
              type="submit"
              icon={KeyRound}
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Sending Code..." : "Send Verification Code"}
            </PrimaryButton>

            <div className="pt-2 text-center">
              <Link
                to={ROUTES.login}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-brand-700 transition"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Login
              </Link>
            </div>
          </form>
        )}

        {/* Step 2: Verify Code and Set New Password */}
        {step === "verify" && (
          <form onSubmit={handleResetPassword} noValidate className="space-y-5">
            {demoOtp ? (
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-3.5 text-xs text-amber-900">
                <span className="font-semibold">Demo / Testing Code:</span> Your verification code is{" "}
                <span className="font-mono font-bold text-sm bg-amber-100 px-2 py-0.5 rounded text-amber-950">
                  {demoOtp}
                </span>
              </div>
            ) : null}

            {infoMessage ? (
              <div className="rounded-lg bg-emerald-50 border border-emerald-100 p-3.5 text-xs text-emerald-800 flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>{infoMessage}</span>
              </div>
            ) : null}

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="reset-otp" className="block text-sm font-semibold text-slate-800">
                  6-Digit Verification Code
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setStep("request");
                    setErrors({});
                  }}
                  className="text-xs text-brand-700 hover:underline"
                >
                  Change email ({email})
                </button>
              </div>
              <input
                id="reset-otp"
                type="text"
                maxLength={6}
                value={otp}
                onChange={(event) => {
                  setOtp(event.target.value.replace(/\D/g, ""));
                  setErrors((prev) => ({ ...prev, otp: "", form: "" }));
                }}
                placeholder="123456"
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-center font-mono text-lg tracking-widest text-slate-900 shadow-sm focus:border-brand-600 focus:outline-none focus:ring-4 focus:ring-brand-100"
                disabled={isSubmitting}
                required
              />
              {errors.otp ? (
                <p className="mt-1 text-xs text-rose-600">{errors.otp}</p>
              ) : null}
            </div>

            <div>
              <label htmlFor="new-password" className="block text-sm font-semibold text-slate-800">
                New Password
              </label>
              <div className="mt-2 flex rounded-lg border border-slate-300 bg-white shadow-sm focus-within:border-brand-600 focus-within:ring-4 focus-within:ring-brand-100">
                <input
                  id="new-password"
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(event) => {
                    setNewPassword(event.target.value);
                    setErrors((prev) => ({ ...prev, newPassword: "", form: "" }));
                  }}
                  placeholder="At least 8 characters"
                  className="min-w-0 flex-1 rounded-l-lg border-0 px-3 py-2.5 text-sm text-slate-950 outline-none placeholder:text-slate-400"
                  disabled={isSubmitting}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="flex w-12 items-center justify-center rounded-r-lg text-slate-500 hover:text-brand-700"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.newPassword ? (
                <p className="mt-1 text-xs text-rose-600">{errors.newPassword}</p>
              ) : null}
            </div>

            <div>
              <label htmlFor="confirm-new-password" className="block text-sm font-semibold text-slate-800">
                Confirm New Password
              </label>
              <div className="mt-2 flex rounded-lg border border-slate-300 bg-white shadow-sm focus-within:border-brand-600 focus-within:ring-4 focus-within:ring-brand-100">
                <input
                  id="confirm-new-password"
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(event) => {
                    setConfirmPassword(event.target.value);
                    setErrors((prev) => ({ ...prev, confirmPassword: "", form: "" }));
                  }}
                  placeholder="Re-enter your new password"
                  className="min-w-0 flex-1 rounded-l-lg border-0 px-3 py-2.5 text-sm text-slate-950 outline-none placeholder:text-slate-400"
                  disabled={isSubmitting}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  className="flex w-12 items-center justify-center rounded-r-lg text-slate-500 hover:text-brand-700"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.confirmPassword ? (
                <p className="mt-1 text-xs text-rose-600">{errors.confirmPassword}</p>
              ) : null}
            </div>

            <PrimaryButton
              type="submit"
              icon={ShieldCheck}
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Resetting Password..." : "Update Password"}
            </PrimaryButton>

            <div className="flex items-center justify-between pt-2 text-xs">
              <button
                type="button"
                onClick={handleRequestOtp}
                className="text-brand-700 hover:underline font-semibold"
                disabled={isSubmitting}
              >
                Resend code
              </button>
              <Link
                to={ROUTES.login}
                className="text-slate-600 hover:text-brand-700 transition"
              >
                Cancel and Login
              </Link>
            </div>
          </form>
        )}

        {/* Step 3: Success Screen */}
        {step === "success" && (
          <div className="text-center py-4 space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">
              Password Reset Successfully!
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Your account password has been updated. You can now log in using your new credentials.
            </p>
            <PrimaryButton
              type="button"
              className="w-full mt-4"
              onClick={() => navigate(ROUTES.login, { replace: true })}
            >
              Proceed to Login
            </PrimaryButton>
          </div>
        )}
      </div>
    </section>
  );
}
