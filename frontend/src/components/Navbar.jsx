import { Activity, FlaskConical, LogOut, Menu, ScanFace, Sparkles, UserCircle, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { APP_NAME, ROUTES } from "../constants/appContent";
import { useAuth } from "../context/AuthContext";
import { useSkinProfile } from "../context/SkinProfileContext";

const baseLinks = [
  { label: "Home", to: ROUTES.home },
  { label: "AI Ingredients", to: ROUTES.ingredientChecker, icon: FlaskConical },
  { label: "Catalogue", to: ROUTES.products },
  { label: "How It Works", to: "/#how-it-works", anchor: true },
];

export default function Navbar() {
  const navigate = useNavigate();
  const { isAuthenticated, logout, user } = useAuth();
  const { hasProfile } = useSkinProfile();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const linkClasses = ({ isActive }) =>
    `relative flex items-center gap-1.5 whitespace-nowrap rounded-xl px-2.5 py-1.5 text-[11px] font-bold uppercase tracking-wider transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 ${
      isActive
        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
        : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
    }`;

  const closeMenu = () => setIsMenuOpen(false);

  const handleLogout = async () => {
    await logout();
    closeMenu();
    navigate(ROUTES.home);
  };

  const renderLink = (link) => {
    const Icon = link.icon;
    if (link.anchor) {
      return (
        <a
          key={link.label}
          href={link.to}
          onClick={closeMenu}
          className="flex items-center gap-1.5 whitespace-nowrap rounded-xl px-2.5 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-300 transition-all duration-200 hover:bg-slate-800/60 hover:text-white"
        >
          {Icon ? <Icon className="h-3.5 w-3.5 text-emerald-400 shrink-0" /> : null}
          <span>{link.label}</span>
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
        {Icon ? <Icon className="h-3.5 w-3.5 text-emerald-400 shrink-0" /> : null}
        <span>{link.label}</span>
      </NavLink>
    );
  };

  const authLinks = isAuthenticated
    ? [
        { label: "Start Scan", to: ROUTES.faceScan },
        {
          label: hasProfile ? "Skin Profile" : "Profile",
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
    <header className="sticky top-0 z-50 px-2 py-2.5 sm:px-6 sm:py-3">
      <div className="mx-auto max-w-7xl rounded-2xl border border-white/10 bg-slate-900/85 backdrop-blur-xl shadow-2xl shadow-slate-950/60 transition-all">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-emerald-500 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-slate-950 focus:shadow-lg"
        >
          Skip to main content
        </a>
        <nav
          className="flex items-center justify-between px-3.5 py-2 sm:px-5"
          aria-label="Main navigation"
        >
          {/* Logo with 3D Holographic Glow */}
          <Link
            to="/"
            className="group flex items-center gap-2.5 shrink-0 whitespace-nowrap focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500"
            onClick={closeMenu}
          >
            <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-400 text-slate-950 shadow-lg shadow-emerald-500/30 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3 shrink-0">
              <ScanFace aria-hidden="true" className="h-5 w-5" />
              <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div className="flex flex-col whitespace-nowrap">
              <span className="text-sm sm:text-base font-black tracking-tight text-white group-hover:text-emerald-400 transition leading-tight">
                {APP_NAME}
              </span>
              <span className="flex items-center gap-1 text-[8.5px] font-bold uppercase tracking-widest text-emerald-400 whitespace-nowrap leading-none mt-0.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                Gemini 3D Vision AI
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden items-center gap-0.5 lg:flex xl:gap-1">
            {navLinks.map(renderLink)}

            {isAuthenticated ? (
              <div className="ml-2 flex items-center gap-1.5 border-l border-slate-700/60 pl-2.5">
                <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-xl bg-slate-800/80 px-2.5 py-1.5 text-[11px] font-bold text-slate-200 border border-slate-700">
                  <UserCircle aria-hidden="true" className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                  <span className="max-w-[100px] truncate">{user?.full_name || "Account"}</span>
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="inline-flex items-center gap-1 rounded-xl p-1.5 text-xs font-semibold text-rose-400 hover:bg-rose-500/10 transition shrink-0"
                  title="Logout"
                >
                  <LogOut aria-hidden="true" className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <Link
                to={ROUTES.skinProfile}
                className="ml-2 inline-flex items-center gap-1.5 whitespace-nowrap rounded-xl bg-gradient-to-r from-emerald-500 to-teal-400 px-3.5 py-1.5 text-xs font-extrabold text-slate-950 shadow-md shadow-emerald-500/20 hover:scale-105 hover:shadow-emerald-500/40 transition-all duration-200 shrink-0"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Launch Scan</span>
              </Link>
            )}
          </div>

          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            aria-label="Toggle navigation menu"
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen((current) => !current)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-slate-800/80 text-slate-300 shadow-xs transition hover:border-emerald-500/50 hover:text-white lg:hidden"
          >
            {isMenuOpen ? (
              <X aria-hidden="true" className="h-5 w-5" />
            ) : (
              <Menu aria-hidden="true" className="h-5 w-5" />
            )}
          </button>
        </nav>

        {/* Mobile Dropdown Menu */}
        {isMenuOpen ? (
          <div className="border-t border-white/10 bg-slate-900/95 px-4 py-4 backdrop-blur-2xl rounded-b-2xl lg:hidden">
            <div className="flex flex-col gap-1.5">
              {navLinks.map(renderLink)}
              {isAuthenticated ? (
                <div className="mt-3 flex items-center justify-between border-t border-slate-800 pt-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                    <UserCircle aria-hidden="true" className="h-4 w-4 text-emerald-400" />
                    {user?.full_name || "Account"}
                  </div>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="inline-flex items-center gap-1 rounded-lg bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-400"
                  >
                    <LogOut aria-hidden="true" className="h-3.5 w-3.5" />
                    Logout
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    </header>
  );
}


