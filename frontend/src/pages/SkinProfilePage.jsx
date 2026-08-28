import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  Info,
  Save,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ErrorMessage from "../components/ErrorMessage";
import FormCheckbox from "../components/FormCheckbox";
import FormInput from "../components/FormInput";
import FormRadioGroup from "../components/FormRadioGroup";
import FormSelect from "../components/FormSelect";
import PageHeader from "../components/PageHeader";
import PrimaryButton from "../components/PrimaryButton";
import SecondaryButton from "../components/SecondaryButton";
import TagInput from "../components/TagInput";
import {
  AGE_GROUPS,
  CURRENT_PRODUCT_OPTIONS,
  EXPERIENCE_LEVELS,
  FRAGRANCE_OPTIONS,
  ROUTES,
  SENSITIVITY_OPTIONS,
  SKIN_BEHAVIOUR_LEVELS,
} from "../constants/appContent";
import { useAuth } from "../context/AuthContext";
import { useSkinProfile } from "../context/SkinProfileContext";
import { getSkinProfileErrors } from "../services/skinProfileService";
import {
  validateSkinProfile,
  validateSkinProfileStep,
} from "../utils/validation";

const STEPS = [
  "Basic information",
  "Skin behaviour",
  "Allergies and preferences",
  "Budget and routine",
  "Review and save",
];

const FIELD_STEPS = {
  ageGroup: 0,
  country: 0,
  experienceLevel: 0,
  oilinessLevel: 1,
  drynessLevel: 1,
  sensitivity: 1,
  knownAllergies: 2,
  ingredientsToAvoid: 2,
  fragrancePreference: 2,
  currentProducts: 3,
  budgetMin: 3,
  budgetMax: 3,
  preferredBrands: 3,
  additionalNotes: 4,
};

function createEmptyProfile(user) {
  return {
    ageGroup: user?.age_group || "",
    country: user?.location || "India",
    experienceLevel: "",
    oilinessLevel: "",
    drynessLevel: "",
    sensitivity: "",
    knownAllergies: [],
    ingredientsToAvoid: [],
    fragrancePreference: "",
    currentProducts: [],
    noSpecificBudget: false,
    budgetMin: "",
    budgetMax: "",
    preferredBrands: [],
    additionalNotes: "",
  };
}

function mapProfileToForm(profile) {
  const sensitivity =
    profile.is_sensitive === null
      ? "Not sure"
      : profile.is_sensitive
        ? "Yes"
        : "No";
  const noSpecificBudget =
    profile.budget_min === null && profile.budget_max === null;

  return {
    ageGroup: profile.age_group,
    country: profile.country,
    experienceLevel: profile.experience_level,
    oilinessLevel: profile.oiliness_level,
    drynessLevel: profile.dryness_level,
    sensitivity,
    knownAllergies: profile.known_allergies,
    ingredientsToAvoid: profile.ingredients_to_avoid,
    fragrancePreference: profile.fragrance_preference,
    currentProducts: profile.current_products,
    noSpecificBudget,
    budgetMin: noSpecificBudget ? "" : String(profile.budget_min),
    budgetMax: noSpecificBudget ? "" : String(profile.budget_max),
    preferredBrands: profile.preferred_brands,
    additionalNotes: profile.additional_notes || "",
  };
}

function formatDate(value) {
  if (!value) return "Not saved yet";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function ReviewItem({ label, value }) {
  const displayValue = Array.isArray(value)
    ? value.length
      ? value.join(", ")
      : "None entered"
    : value || "Not provided";

  return (
    <div className="border-b border-slate-100 py-3 last:border-0">
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </dt>
      <dd className="mt-1 break-words text-sm font-medium text-slate-800">
        {displayValue}
      </dd>
    </div>
  );
}

export default function SkinProfilePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const {
    profile,
    isLoading,
    isSaving,
    error: loadError,
    hasProfile,
    loadProfile,
    saveProfile,
  } = useSkinProfile();
  const [values, setValues] = useState(() => createEmptyProfile(user));
  const [currentStep, setCurrentStep] = useState(0);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (!isLoading && !isInitialized) {
      setValues(profile ? mapProfileToForm(profile) : createEmptyProfile(user));
      setIsInitialized(true);
    }
  }, [isLoading, isInitialized, profile, user]);

  const updateField = (field, value) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: "", form: "" }));
    setMessage("");
  };

  const focusFirstError = () => {
    window.setTimeout(() => {
      document.querySelector('[aria-invalid="true"]')?.focus();
    }, 0);
  };

  const handleNext = () => {
    const nextErrors = validateSkinProfileStep(values, currentStep);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      focusFirstError();
      return;
    }
    setCurrentStep((step) => Math.min(step + 1, STEPS.length - 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handlePrevious = () => {
    if (currentStep === 0) {
      navigate(ROUTES.home);
      return;
    }
    setErrors({});
    setCurrentStep((step) => step - 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (currentStep < STEPS.length - 1) {
      handleNext();
      return;
    }
    if (isSaving) return;

    const nextErrors = validateSkinProfile(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      const firstField = Object.keys(nextErrors)[0];
      setCurrentStep(FIELD_STEPS[firstField] ?? 0);
      focusFirstError();
      return;
    }

    const wasEditing = hasProfile;
    try {
      await saveProfile(values);
      if (wasEditing) {
        setMessage("Your skin profile has been updated successfully.");
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        navigate(ROUTES.faceScan, {
          replace: true,
          state: { profileSaved: true },
        });
      }
    } catch (error) {
      const apiErrors = getSkinProfileErrors(error);
      setErrors(apiErrors);
      const firstField = Object.keys(apiErrors).find((field) => field !== "form");
      if (firstField) setCurrentStep(FIELD_STEPS[firstField] ?? 0);
      focusFirstError();
    }
  };

  const handleRetryLoad = async () => {
    setIsInitialized(false);
    await loadProfile();
  };

  if (isLoading || !isInitialized) {
    return (
      <section className="flex min-h-[55vh] items-center justify-center px-4">
        <div className="text-center">
          <div className="mx-auto h-11 w-11 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Loading your skin profile...
          </p>
        </div>
      </section>
    );
  }

  if (loadError) {
    return (
      <section className="mx-auto max-w-lg px-4 py-20 text-center">
        <h1 className="text-2xl font-bold text-slate-950">
          Unable to load your skin profile
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{loadError}</p>
        <PrimaryButton className="mt-6" onClick={handleRetryLoad}>
          Try again
        </PrimaryButton>
      </section>
    );
  }

  const budgetSummary = values.noSpecificBudget
    ? "No specific budget"
    : values.budgetMin !== "" && values.budgetMax !== ""
      ? `INR ${values.budgetMin} to INR ${values.budgetMax}`
      : "Not provided";

  return (
    <section className="px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow={hasProfile ? "Edit profile" : "Skin profile"}
        title={hasProfile ? "Update your skin profile" : "Tell us about your skin preferences"}
        description="Share self-reported preferences that cannot be reliably determined from a facial image."
      />

      <div className="mx-auto mb-7 grid max-w-6xl gap-3 border-y border-slate-200 py-4 text-sm sm:grid-cols-3">
        <p>
          <span className="font-semibold text-slate-950">User:</span>{" "}
          <span className="text-slate-600">{user?.full_name}</span>
        </p>
        <p>
          <span className="font-semibold text-slate-950">Status:</span>{" "}
          <span className={hasProfile ? "text-leaf-700" : "text-amber-700"}>
            {hasProfile ? "Complete" : "Not saved"}
          </span>
        </p>
        <p className="sm:text-right">
          <span className="font-semibold text-slate-950">Last updated:</span>{" "}
          <span className="text-slate-600">{formatDate(profile?.updated_at)}</span>
        </p>
      </div>

      {!hasProfile ? (
        <p className="mx-auto mb-6 max-w-6xl rounded-lg border border-clinic-100 bg-clinic-50 px-4 py-3 text-sm text-clinic-700">
          No saved profile was found. Complete all five steps to continue to face scan.
        </p>
      ) : null}

      {message ? (
        <p
          className="mx-auto mb-6 max-w-6xl rounded-lg border border-leaf-100 bg-leaf-50 px-4 py-3 text-sm font-semibold text-leaf-700"
          role="status"
        >
          {message}
        </p>
      ) : null}

      <div className="mx-auto mb-6 max-w-6xl rounded-lg border border-brand-100 bg-brand-50 p-5">
        <div className="flex items-start gap-3">
          <Info aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" />
          <div className="text-sm leading-6 text-slate-700">
            <p className="font-semibold text-slate-950">General guidance only</p>
            <p className="mt-1">
              Your answers help DermaScan AI personalize general skincare guidance.
              They are not used to diagnose medical conditions. Facial-image analysis
              and product recommendations will be handled in later steps.
            </p>
          </div>
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="mx-auto max-w-6xl rounded-lg border border-slate-200 bg-white shadow-soft"
        noValidate
      >
        <div className="border-b border-slate-200 px-5 py-5 sm:px-7">
          <div className="flex items-center justify-between text-sm font-semibold text-slate-700">
            <span>Step {currentStep + 1} of {STEPS.length}</span>
            <span>{Math.round(((currentStep + 1) / STEPS.length) * 100)}%</span>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-brand-600 transition-all"
              style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
            />
          </div>
          <ol className="mt-5 grid grid-cols-5 gap-2" aria-label="Questionnaire progress">
            {STEPS.map((step, index) => (
              <li key={step}>
                <button
                  type="button"
                  onClick={() => index <= currentStep && setCurrentStep(index)}
                  disabled={index > currentStep || isSaving}
                  aria-current={index === currentStep ? "step" : undefined}
                  className={`flex w-full flex-col items-center gap-2 text-center text-xs font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${
                    index === currentStep
                      ? "text-brand-700"
                      : index < currentStep
                        ? "text-leaf-700"
                        : "text-slate-400"
                  }`}
                >
                  <span
                    className={`flex h-8 w-8 items-center justify-center rounded-full ${
                      index === currentStep
                        ? "bg-brand-600 text-white"
                        : index < currentStep
                          ? "bg-leaf-500 text-white"
                          : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {index < currentStep ? <Check className="h-4 w-4" /> : index + 1}
                  </span>
                  <span className="hidden leading-4 sm:block">{step}</span>
                </button>
              </li>
            ))}
          </ol>
        </div>

        <div className="p-5 sm:p-7">
          <ErrorMessage id="skin-profile-form-error" message={errors.form} />

          {currentStep === 0 ? (
            <fieldset>
              <legend className="text-xl font-bold text-slate-950">Basic information</legend>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                This information helps later product-availability and routine guidance.
              </p>
              <div className="mt-6 grid gap-6 md:grid-cols-2">
                <FormSelect
                  id="ageGroup"
                  label="Age group"
                  options={AGE_GROUPS}
                  value={values.ageGroup}
                  error={errors.ageGroup}
                  onChange={(event) => updateField("ageGroup", event.target.value)}
                  disabled={isSaving}
                  required
                />
                <FormInput
                  id="country"
                  label="Country or location"
                  value={values.country}
                  error={errors.country}
                  onChange={(event) => updateField("country", event.target.value)}
                  placeholder="Example: India"
                  maxLength={120}
                  disabled={isSaving}
                  required
                />
                <FormSelect
                  id="experienceLevel"
                  label="Skincare experience level"
                  options={EXPERIENCE_LEVELS}
                  value={values.experienceLevel}
                  error={errors.experienceLevel}
                  onChange={(event) => updateField("experienceLevel", event.target.value)}
                  disabled={isSaving}
                  required
                />
              </div>
            </fieldset>
          ) : null}

          {currentStep === 1 ? (
            <fieldset>
              <legend className="text-xl font-bold text-slate-950">Skin behaviour</legend>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Select the option that best describes how your skin usually feels during a normal day.
              </p>
              <div className="mt-6 space-y-7">
                <FormRadioGroup
                  legend="Self-reported oiliness"
                  name="oilinessLevel"
                  options={SKIN_BEHAVIOUR_LEVELS}
                  value={values.oilinessLevel}
                  error={errors.oilinessLevel}
                  onChange={(value) => updateField("oilinessLevel", value)}
                />
                <FormRadioGroup
                  legend="Self-reported dryness or tightness"
                  name="drynessLevel"
                  options={SKIN_BEHAVIOUR_LEVELS}
                  value={values.drynessLevel}
                  error={errors.drynessLevel}
                  onChange={(value) => updateField("drynessLevel", value)}
                />
                <FormRadioGroup
                  legend="Does your skin seem sensitive?"
                  name="sensitivity"
                  options={SENSITIVITY_OPTIONS}
                  value={values.sensitivity}
                  error={errors.sensitivity}
                  onChange={(value) => updateField("sensitivity", value)}
                />
              </div>
            </fieldset>
          ) : null}

          {currentStep === 2 ? (
            <fieldset>
              <legend className="text-xl font-bold text-slate-950">
                Allergies and preferences
              </legend>
              <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950">
                <div className="flex gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
                  <p>
                    DermaScan AI cannot verify medical allergies. Enter only allergies or
                    sensitivities that you already know about.
                  </p>
                </div>
              </div>
              <div className="mt-6 space-y-7">
                <TagInput
                  id="knownAllergies"
                  label="Known allergies or sensitivities"
                  value={values.knownAllergies}
                  onChange={(value) => updateField("knownAllergies", value)}
                  placeholder="Type an item, then press Enter"
                  description="Leave empty if you do not know of any."
                  error={errors.knownAllergies}
                  disabled={isSaving}
                />
                <TagInput
                  id="ingredientsToAvoid"
                  label="Ingredients to avoid"
                  value={values.ingredientsToAvoid}
                  onChange={(value) => updateField("ingredientsToAvoid", value)}
                  placeholder="Example: Added fragrance"
                  suggestions={["Added fragrance", "Drying alcohol", "Essential oils"]}
                  error={errors.ingredientsToAvoid}
                  disabled={isSaving}
                />
                <FormSelect
                  id="fragrancePreference"
                  label="Fragrance preference"
                  options={FRAGRANCE_OPTIONS}
                  value={values.fragrancePreference}
                  error={errors.fragrancePreference}
                  onChange={(event) =>
                    updateField("fragrancePreference", event.target.value)
                  }
                  disabled={isSaving}
                  required
                />
              </div>
            </fieldset>
          ) : null}

          {currentStep === 3 ? (
            <fieldset>
              <legend className="text-xl font-bold text-slate-950">
                Budget and current routine
              </legend>
              <div className="mt-6 space-y-7">
                <TagInput
                  id="currentProducts"
                  label="Current skincare products"
                  value={values.currentProducts}
                  onChange={(value) => updateField("currentProducts", value)}
                  placeholder="Add another product category"
                  suggestions={CURRENT_PRODUCT_OPTIONS}
                  description="Choose common categories or enter your own."
                  error={errors.currentProducts}
                  disabled={isSaving}
                />
                <div className="border-y border-slate-200 py-6">
                  <p className="text-sm font-semibold text-slate-950">
                    Product budget
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    Currency: Indian Rupees (INR)
                  </p>
                  <FormCheckbox
                    id="noSpecificBudget"
                    label="No specific budget"
                    className="mt-4"
                    checked={values.noSpecificBudget}
                    onChange={(event) =>
                      updateField("noSpecificBudget", event.target.checked)
                    }
                    disabled={isSaving}
                  />
                  <div className="mt-5 grid gap-5 sm:grid-cols-2">
                    <FormInput
                      id="budgetMin"
                      label="Minimum budget (INR)"
                      type="number"
                      min="0"
                      max="1000000"
                      step="1"
                      value={values.budgetMin}
                      error={errors.budgetMin}
                      onChange={(event) => updateField("budgetMin", event.target.value)}
                      disabled={isSaving || values.noSpecificBudget}
                      placeholder="Example: 200"
                    />
                    <FormInput
                      id="budgetMax"
                      label="Maximum budget (INR)"
                      type="number"
                      min="0"
                      max="1000000"
                      step="1"
                      value={values.budgetMax}
                      error={errors.budgetMax}
                      onChange={(event) => updateField("budgetMax", event.target.value)}
                      disabled={isSaving || values.noSpecificBudget}
                      placeholder="Example: 1000"
                    />
                  </div>
                </div>
                <TagInput
                  id="preferredBrands"
                  label="Preferred brands"
                  value={values.preferredBrands}
                  onChange={(value) => updateField("preferredBrands", value)}
                  placeholder="Example: Minimalist"
                  suggestions={["Minimalist", "Cetaphil"]}
                  description="Optional. Availability filtering will be added in a later step."
                  error={errors.preferredBrands}
                  disabled={isSaving}
                />
              </div>
            </fieldset>
          ) : null}

          {currentStep === 4 ? (
            <fieldset>
              <legend className="text-xl font-bold text-slate-950">Review and save</legend>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Review your self-reported answers. You can return to any completed step before saving.
              </p>
              <FormInput
                id="additionalNotes"
                label="Additional notes"
                as="textarea"
                rows="4"
                maxLength={1000}
                className="mt-6"
                value={values.additionalNotes}
                error={errors.additionalNotes}
                onChange={(event) => updateField("additionalNotes", event.target.value)}
                placeholder="Optional non-medical details about your routine or product preferences"
                disabled={isSaving}
              />
              <p className="mt-2 text-right text-xs text-slate-500">
                {values.additionalNotes.length}/1000 characters
              </p>

              <div className="mt-7 grid gap-x-8 border-y border-slate-200 py-3 md:grid-cols-2">
                <dl>
                  <ReviewItem label="Age group" value={values.ageGroup} />
                  <ReviewItem label="Country" value={values.country} />
                  <ReviewItem label="Experience" value={values.experienceLevel} />
                  <ReviewItem label="Oiliness" value={values.oilinessLevel} />
                  <ReviewItem label="Dryness" value={values.drynessLevel} />
                  <ReviewItem label="Sensitivity" value={values.sensitivity} />
                  <ReviewItem label="Fragrance" value={values.fragrancePreference} />
                </dl>
                <dl>
                  <ReviewItem label="Known allergies" value={values.knownAllergies} />
                  <ReviewItem label="Ingredients to avoid" value={values.ingredientsToAvoid} />
                  <ReviewItem label="Current products" value={values.currentProducts} />
                  <ReviewItem label="Budget" value={budgetSummary} />
                  <ReviewItem label="Preferred brands" value={values.preferredBrands} />
                </dl>
              </div>
            </fieldset>
          ) : null}

          <div className="mt-8 flex flex-col-reverse gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:justify-between">
            <SecondaryButton
              type="button"
              icon={ArrowLeft}
              onClick={handlePrevious}
              disabled={isSaving}
            >
              {currentStep === 0 ? "Back to Home" : "Previous"}
            </SecondaryButton>
            {currentStep < STEPS.length - 1 ? (
              <PrimaryButton type="button" icon={ArrowRight} onClick={handleNext}>
                Next
              </PrimaryButton>
            ) : (
              <PrimaryButton type="submit" icon={Save} disabled={isSaving}>
                {isSaving
                  ? "Saving..."
                  : hasProfile
                    ? "Update Skin Profile"
                    : "Save and Continue"}
              </PrimaryButton>
            )}
          </div>
        </div>
      </form>

      <div className="mx-auto mt-6 max-w-6xl rounded-lg border border-amber-200 bg-amber-50 p-5">
        <div className="flex items-start gap-3 text-sm leading-6 text-amber-950">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
          <p>
            For severe, painful, persistent, infected, or unusual skin concerns,
            consult a qualified dermatologist.
          </p>
        </div>
      </div>
    </section>
  );
}
