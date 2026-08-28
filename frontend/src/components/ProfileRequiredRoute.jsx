import { Navigate } from "react-router-dom";
import { ROUTES } from "../constants/appContent";
import { useSkinProfile } from "../context/SkinProfileContext";

export default function ProfileRequiredRoute({ children }) {
  const { error, isComplete, isInitialized, isLoading, loadProfile } =
    useSkinProfile();

  if (!isInitialized || isLoading) {
    return (
      <div className="flex min-h-[55vh] items-center justify-center px-4">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="mt-4 text-sm font-semibold text-slate-700">
            Checking your skin profile...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <section className="mx-auto max-w-lg px-4 py-20 text-center">
        <h1 className="text-2xl font-bold text-slate-950">Profile check unavailable</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">{error}</p>
        <button
          type="button"
          onClick={loadProfile}
          className="mt-6 rounded-lg bg-brand-600 px-5 py-3 text-sm font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
        >
          Try again
        </button>
      </section>
    );
  }

  if (!isComplete) {
    return <Navigate to={ROUTES.skinProfile} replace />;
  }

  return children;
}
