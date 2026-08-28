import { LogOut, Menu, ScanFace, UserCircle, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { APP_NAME, ROUTES } from "../constants/appContent";
import { useAuth } from "../context/AuthContext";
import { useSkinProfile } from "../context/SkinProfileContext";

const baseLinks = [
  { label: "Home", to: ROUTES.home },
  { label: "How It Works", to: "/#how-it-works", anchor: true },
  { label: "Catalogue", to: ROUTES.products },
];

export default function Navbar() {
  const navigate = useNavigate();
  const { isAuthenticated, logout, user } = useAuth();
  const { hasProfile } = useSkinProfile();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const linkClasses = ({ isActive }) =>
    `rounded-lg px-3 py-2 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${
      isActive
        ? "bg-brand-50 text-brand-700"
        : "text-slate-700 hover:bg-slate-100 hover:text-brand-700"
    }`;

  const closeMenu = () => setIsMenuOpen(false);

  const handleLogout = async () => {
    await logout();
    closeMenu();
    navigate(ROUTES.home);
  };

  const renderLink = (link) => {
    if (link.anchor) {
      return (
        <a
          key={link.label}
          href={link.to}
          onClick={closeMenu}
          className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
        >
          {link.label}
        </a>
      );
    }

    return (
      <NavLink
        key={link.label}
        to={link.to}
        onClick={closeMenu}
        className={linkClasses}
      >
        {link.label}
      </NavLink>
    );
  };

  const authLinks = isAuthenticated
    ? [
        { label: "Start Analysis", to: ROUTES.faceScan },
        {
          label: hasProfile ? "Edit Profile" : "Skin Profile",
          to: ROUTES.skinProfile,
        },
        { label: "Reports", to: ROUTES.reports },
        { label: "Feedback", to: ROUTES.feedbackHistory },
      ]
    : [
        { label: "Start Analysis", to: ROUTES.skinProfile },
        { label: "Login", to: ROUTES.login },
        { label: "Register", to: ROUTES.register },
      ];

  const navLinks = [...baseLinks, ...authLinks];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-brand-700 focus:shadow-soft"
      >
        Skip to main content
      </a>
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8"
        aria-label="Main navigation"
      >
        <Link
          to="/"
          className="flex items-center gap-3 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
          onClick={closeMenu}
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 text-white">
            <ScanFace aria-hidden="true" className="h-5 w-5" />
          </span>
          <span className="text-lg font-bold text-slate-950">{APP_NAME}</span>
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          {navLinks.map(renderLink)}
          {isAuthenticated ? (
            <>
              <span className="ml-2 inline-flex items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 text-sm font-semibold text-brand-700">
                <UserCircle aria-hidden="true" className="h-4 w-4" />
                {user?.full_name || "Account"}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
              >
                <LogOut aria-hidden="true" className="h-4 w-4" />
                Logout
              </button>
            </>
          ) : null}
        </div>

        <button
          type="button"
          aria-label="Toggle navigation menu"
          aria-expanded={isMenuOpen}
          onClick={() => setIsMenuOpen((current) => !current)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-300 text-slate-700 transition hover:border-brand-500 hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 lg:hidden"
        >
          {isMenuOpen ? (
            <X aria-hidden="true" className="h-5 w-5" />
          ) : (
            <Menu aria-hidden="true" className="h-5 w-5" />
          )}
        </button>
      </nav>

      {isMenuOpen ? (
        <div className="border-t border-slate-200 bg-white px-4 py-4 shadow-sm lg:hidden">
          <div className="mx-auto flex max-w-7xl flex-col gap-2">
            {navLinks.map(renderLink)}
            {isAuthenticated ? (
              <>
                <div className="flex items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 text-sm font-semibold text-brand-700">
                  <UserCircle aria-hidden="true" className="h-4 w-4" />
                  {user?.full_name || "Account"}
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
                >
                  <LogOut aria-hidden="true" className="h-4 w-4" />
                  Logout
                </button>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </header>
  );
}
