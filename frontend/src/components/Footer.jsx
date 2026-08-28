import { Link } from "react-router-dom";
import { APP_NAME, MEDICAL_DISCLAIMER, ROUTES } from "../constants/appContent";

const quickLinks = [
  { label: "Home", to: ROUTES.home },
  { label: "Start Analysis", to: ROUTES.skinProfile },
  { label: "Previous Reports", to: ROUTES.reports },
  { label: "Login", to: ROUTES.login },
];

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-slate-200 bg-slate-950 text-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.3fr_0.7fr_1fr] lg:px-8">
        <div>
          <p className="text-lg font-bold">{APP_NAME}</p>
          <p className="mt-3 max-w-md text-sm leading-6 text-slate-300">
            College mini-project frontend for AI-assisted skincare guidance.
          </p>
          <p className="mt-4 text-sm text-slate-400">
            Current year: {currentYear}
          </p>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
            Quick links
          </h2>
          <ul className="mt-4 space-y-3">
            {quickLinks.map((link) => (
              <li key={link.label}>
                <Link
                  to={link.to}
                  className="text-sm text-slate-300 transition hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-100"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
            Privacy and safety notice
          </h2>
          <p className="mt-4 text-sm leading-6 text-slate-300">
            Account and skin-profile data are sent to the configured backend API.
            Consented images are sanitized and kept in non-public temporary storage.
          </p>
          <p className="mt-4 text-sm leading-6 text-slate-300">
            {MEDICAL_DISCLAIMER}
          </p>
        </div>
      </div>
    </footer>
  );
}
