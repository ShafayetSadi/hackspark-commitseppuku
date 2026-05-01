"use client";

// Client-side auth screen for /login.
// Faithful port of hackathon/project/Auth.html (the design handoff bundle):
//   - split-screen layout: dark brand panel (left) + form panel (right)
//   - tabbed Sign in / Create account toggle with sliding indicator
//   - live email regex + password length + confirm-match validation
//   - live password strength meter (0..4)
//   - show/hide password toggle
//   - toast on success / error, mirroring the design's bottom-center toast
//   - deep link support: ?mode=register lands on the create-account tab
//
// Submissions wire up to the existing same-origin Next route handlers under
// /api/auth/* (login + register), which proxy to the gateway and set the
// HTTP-only auth cookie. We never call the gateway directly from the browser.

import Link from "next/link";

import { CompanyLogoMark } from "../components/company-logo";
import { useRouter, useSearchParams } from "next/navigation";
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

type AuthUser = {
  id: number;
  email: string;
  full_name: string;
};

type Mode = "login" | "register";

type AuthScreenProps = {
  initialUser: AuthUser | null;
};

type ToastTone = "success" | "error";

type ToastState = {
  message: string;
  tone: ToastTone;
} | null;

const APP_HREF = "/products";
const HOME_HREF = "/";

const isEmail = (value: string): boolean =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);

const passwordScore = (value: string): number => {
  let score = 0;
  if (value.length >= 8) score += 1;
  if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score += 1;
  if (/\d/.test(value)) score += 1;
  if (/[^A-Za-z0-9]/.test(value)) score += 1;
  return score;
};

const STRENGTH_LABELS = [
  "Use 8+ characters with letters, numbers, and a symbol.",
  "Weak — add length and variety.",
  "Fair — getting there.",
  "Strong password.",
  "Excellent — very strong password.",
];

async function readErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.length > 0) {
      return payload.detail;
    }
  } catch {
    // Ignore JSON parse failures and fall back below.
  }
  return fallback;
}

/* ===== Inline SVG icons (kept tiny so the file stays single-purpose) ===== */

function MailIcon() {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 7l9 6 9-6" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="4" y="11" width="16" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      width={12}
      height={12}
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M5 12l5 5L20 7" />
    </svg>
  );
}


function FeatureIconShield() {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 8L12 3 3 8v8l9 5 9-5V8z" />
      <path d="M3 8l9 5 9-5" />
    </svg>
  );
}

function FeatureIconCalendar() {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </svg>
  );
}

function FeatureIconChat() {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12a8 8 0 1 1-3.5-6.6L21 4l-1 4.5A7.95 7.95 0 0 1 21 12z" />
    </svg>
  );
}

/* ===== Brand panel (left half) ===== */

function BrandPanel() {
  return (
    <aside className="auth-brand" aria-hidden="false">
      <div className="auth-logo">
        <span className="logo-mark">
          <CompanyLogoMark width={30} height={30} />
        </span>
        <span>RentPi</span>
      </div>

      <div className="auth-brand-content">
        <div className="auth-eyebrow">
          <span className="dot" />
          Trusted by 47,000+ renters in Dhaka
        </div>
        <h1 className="auth-h1">
          Rent smarter with <em>real-time availability</em> and AI-powered help.
        </h1>
        <p className="auth-sub">
          Join RentPi to browse half a million products, lock in dates with
          confidence, and get grounded answers from an assistant that knows the
          catalog.
        </p>

        <div className="auth-features">
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <FeatureIconShield />
            </div>
            <div className="auth-feature-text">
              <strong>Browse 487K+ rental products</strong>
              <span>
                Across 9 categories — cameras, vehicles, tools, outdoor gear,
                more.
              </span>
            </div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <FeatureIconCalendar />
            </div>
            <div className="auth-feature-text">
              <strong>Check availability before booking</strong>
              <span>
                See free windows, busy periods, and conflicts on a clean
                timeline.
              </span>
            </div>
          </div>
          <div className="auth-feature">
            <div className="auth-feature-icon">
              <FeatureIconChat />
            </div>
            <div className="auth-feature-text">
              <strong>Ask the RentPi Assistant anything</strong>
              <span>
                Trends, prices, owner details — grounded in real rental data.
              </span>
            </div>
          </div>
        </div>

        <div className="auth-preview" aria-hidden="true">
          <div className="auth-preview-card c1">
            <div
              className="preview-thumb"
              style={{
                background:
                  "linear-gradient(135deg, oklch(0.78 0.08 200), oklch(0.65 0.1 200))",
              }}
            />
            <div className="preview-info">
              <div className="preview-title">Premium Camera Kit</div>
              <div className="preview-meta">৳450/day · #1042</div>
            </div>
            <span className="preview-badge">Free</span>
          </div>
          <div className="auth-preview-card c2">
            <div
              className="preview-thumb"
              style={{
                background:
                  "linear-gradient(135deg, oklch(0.78 0.08 145), oklch(0.65 0.1 145))",
              }}
            />
            <div className="preview-info">
              <div className="preview-title">Outdoor Camping Tent</div>
              <div className="preview-meta">৳300/day · #1088</div>
            </div>
            <span className="preview-badge">Trending</span>
          </div>
          <div className="auth-preview-card c3">
            <div
              className="preview-thumb"
              style={{
                background:
                  "linear-gradient(135deg, oklch(0.78 0.08 25), oklch(0.65 0.1 25))",
              }}
            />
            <div className="preview-info">
              <div className="preview-title">Mountain Bike — Trail</div>
              <div className="preview-meta">৳540/day · #1233</div>
            </div>
            <span className="preview-badge">New</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

/* ===== Authenticated session card (replaces the form when logged in) ===== */

function SessionCard({
  user,
  onRefresh,
  onLogout,
  isBusy,
}: {
  user: AuthUser;
  onRefresh: () => void;
  onLogout: () => void;
  isBusy: boolean;
}) {
  return (
    <div className="session-card">
      <div className="session-eyebrow">
        <span className="dot" />
        Authenticated session
      </div>
      <div>
        <h2>Welcome back, {user.full_name || user.email}.</h2>
        <p className="auth-form-sub" style={{ marginTop: 6, marginBottom: 0 }}>
          You&apos;re signed in via the Hackspark gateway. Jump back into the
          marketplace or refresh your profile to confirm the session.
        </p>
      </div>
      <div className="session-meta">
        <span className="k">ID</span>
        <span>{user.id}</span>
        <span className="k">Email</span>
        <span>{user.email}</span>
        <span className="k">Name</span>
        <span>{user.full_name}</span>
      </div>
      <div className="session-actions">
        <Link href={APP_HREF} className="btn btn-primary btn-lg">
          Open RentPi
        </Link>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onRefresh}
          disabled={isBusy}
        >
          Refresh profile
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onLogout}
          disabled={isBusy}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}

/* ===== Main screen ===== */

export default function AuthScreen({ initialUser }: AuthScreenProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialMode: Mode =
    searchParams?.get("mode") === "register" ? "register" : "login";

  const [mode, setMode] = useState<Mode>(initialMode);
  const [user, setUser] = useState<AuthUser | null>(initialUser);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(false);

  // Login form state.
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginEmailError, setLoginEmailError] = useState<string | null>(null);
  const [loginPasswordError, setLoginPasswordError] = useState<string | null>(
    null,
  );
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Register form state.
  const [regFirst, setRegFirst] = useState("");
  const [regLast, setRegLast] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirm, setRegConfirm] = useState("");
  const [regTerms, setRegTerms] = useState(false);
  const [regEmailError, setRegEmailError] = useState<string | null>(null);
  const [regPasswordError, setRegPasswordError] = useState<string | null>(null);
  const [regConfirmError, setRegConfirmError] = useState<string | null>(null);
  const [showRegPassword, setShowRegPassword] = useState(false);

  // Toast.
  const [toast, setToast] = useState<ToastState>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((message: string, tone: ToastTone = "success") => {
    setToast({ message, tone });
    if (toastTimer.current) {
      clearTimeout(toastTimer.current);
    }
    toastTimer.current = setTimeout(() => setToast(null), 2400);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimer.current) {
        clearTimeout(toastTimer.current);
      }
    };
  }, []);

  // Sync mode changes back to the URL so deep-link `?mode=register` survives
  // tab switches without forcing a navigation. (Replace, don't push.)
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (mode === "register") {
      url.searchParams.set("mode", "register");
    } else {
      url.searchParams.delete("mode");
    }
    const next = `${url.pathname}${url.search}${url.hash}`;
    if (`${window.location.pathname}${window.location.search}${window.location.hash}` !== next) {
      window.history.replaceState({}, "", next);
    }
  }, [mode]);

  const strengthScore = useMemo(() => passwordScore(regPassword), [regPassword]);
  const strengthLabel =
    regPassword.length === 0
      ? STRENGTH_LABELS[0]
      : STRENGTH_LABELS[Math.max(1, strengthScore)];

  const refreshCurrentUser = useCallback(async () => {
    setIsCheckingSession(true);
    try {
      const response = await fetch("/api/auth/me", {
        method: "GET",
        cache: "no-store",
      });
      if (response.status === 401) {
        setUser(null);
        return;
      }
      if (!response.ok) {
        const message = await readErrorMessage(
          response,
          "Unable to load current user.",
        );
        showToast(message, "error");
        return;
      }
      const payload = (await response.json()) as AuthUser;
      setUser(payload);
    } catch {
      showToast("Unable to reach the auth backend.", "error");
    } finally {
      setIsCheckingSession(false);
    }
  }, [showToast]);

  const handleLogout = useCallback(async () => {
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok) {
        const message = await readErrorMessage(response, "Logout failed.");
        showToast(message, "error");
        return;
      }
      setUser(null);
      showToast("Signed out.");
    } catch {
      showToast("Unable to reach the auth backend.", "error");
    } finally {
      setIsSubmitting(false);
    }
  }, [showToast]);

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const emailBad = !isEmail(loginEmail);
    const passwordBad = loginPassword.length === 0;
    setLoginEmailError(emailBad ? "Please enter a valid email." : null);
    setLoginPasswordError(passwordBad ? "Password is required." : null);
    if (emailBad || passwordBad) return;

    setIsSubmitting(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });

      if (!response.ok) {
        if (response.status === 422) {
          showToast("Please enter your email and password correctly.", "error");
          return;
        }
        if (response.status === 401) {
          showToast("Invalid email or password. Please try again.", "error");
          return;
        }
        const message = await readErrorMessage(
          response,
          "Sign in failed. Check your credentials and try again.",
        );
        showToast(message, "error");
        return;
      }

      showToast("Welcome back! Opening RentPi…");
      // Pull the freshly-authenticated profile into local state so the
      // session card renders immediately, then move them into the app.
      await refreshCurrentUser();
      setTimeout(() => {
        router.push(APP_HREF);
      }, 700);
    } catch {
      showToast("Unable to reach the auth backend.", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegister = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const emailBad = !isEmail(regEmail);
    const passwordBad = regPassword.length < 8;
    const confirmBad =
      regConfirm.length === 0 || regConfirm !== regPassword;
    setRegEmailError(emailBad ? "Please enter a valid email." : null);
    setRegPasswordError(
      passwordBad ? "Password must be at least 8 characters." : null,
    );
    setRegConfirmError(confirmBad ? "Passwords don't match." : null);

    if (emailBad || passwordBad || confirmBad) return;
    if (!regTerms) {
      showToast("Please accept the terms to continue.", "error");
      return;
    }

    const fullName = [regFirst.trim(), regLast.trim()].filter(Boolean).join(" ");
    if (fullName.length < 2) {
      showToast("Please enter your name to continue.", "error");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: fullName,
          email: regEmail,
          password: regPassword,
        }),
      });

      if (!response.ok) {
        if (response.status === 422) {
          showToast("Please fill in all required fields correctly.", "error");
          return;
        }
        if (response.status === 409) {
          showToast(
            "An account with this email already exists. Try signing in instead.",
            "error",
          );
          return;
        }
        const message = await readErrorMessage(
          response,
          "Could not create your account. Please try again.",
        );
        showToast(message, "error");
        return;
      }

      showToast("Account created! Opening RentPi…");
      await refreshCurrentUser();
      setTimeout(() => {
        router.push(APP_HREF);
      }, 700);
    } catch {
      showToast("Unable to reach the auth backend.", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchMode = (next: Mode) => setMode(next);

  return (
    <div className="rentpi-auth">
      <div className="auth">
        <BrandPanel />

        {/* RIGHT: form panel */}
        <section className="auth-form-wrap">
          <div className="auth-form-top">
            <Link href={HOME_HREF} className="auth-home-link">
              ← Back to home
            </Link>
            <div className="auth-form-top-actions">
              {user ? (
                <>
                  <span>Signed in as {user.email}</span>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => void handleLogout()}
                    disabled={isSubmitting || isCheckingSession}
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <>
                  <span>
                    {mode === "login"
                      ? "New to RentPi?"
                      : "Already have an account?"}
                  </span>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() =>
                      switchMode(mode === "login" ? "register" : "login")
                    }
                  >
                    {mode === "login" ? "Create account" : "Sign in"}
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="auth-form-center">
            <div className="auth-form">
              {user ? (
                <SessionCard
                  user={user}
                  onRefresh={() => void refreshCurrentUser()}
                  onLogout={() => void handleLogout()}
                  isBusy={isSubmitting || isCheckingSession}
                />
              ) : (
                <>
                  <div
                    className="auth-tabs"
                    data-mode={mode}
                    role="tablist"
                    aria-label="Authentication mode"
                  >
                    <span className="auth-tab-indicator" aria-hidden="true" />
                    <button
                      type="button"
                      role="tab"
                      aria-selected={mode === "login"}
                      className={`auth-tab ${mode === "login" ? "active" : ""}`}
                      onClick={() => switchMode("login")}
                    >
                      Sign in
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={mode === "register"}
                      className={`auth-tab ${
                        mode === "register" ? "active" : ""
                      }`}
                      onClick={() => switchMode("register")}
                    >
                      Create account
                    </button>
                  </div>

                  {mode === "login" ? (
                    <form onSubmit={handleLogin} noValidate autoComplete="on">
                      <h2 className="auth-form-title">Welcome back</h2>
                      <p className="auth-form-sub">
                        Sign in to continue browsing rentals and saved trips.
                      </p>

                      <div className="auth-fields">
                        <div className="field">
                          <label
                            className="field-label"
                            htmlFor="loginEmail"
                          >
                            Email address
                          </label>
                          <div className="input-wrap">
                            <span className="icon-l">
                              <MailIcon />
                            </span>
                            <input
                              id="loginEmail"
                              name="username"
                              className={`input ${loginEmailError ? "invalid" : ""}`}
                              type="email"
                              placeholder="you@example.com"
                              autoComplete="section-login username"
                              autoCapitalize="none"
                              autoCorrect="off"
                              spellCheck={false}
                              value={loginEmail}
                              onChange={(e) => {
                                setLoginEmail(e.target.value);
                                if (loginEmailError) setLoginEmailError(null);
                              }}
                            />
                          </div>
                          {loginEmailError ? (
                            <div className="field-error">{loginEmailError}</div>
                          ) : null}
                        </div>

                        <div className="field">
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                            }}
                          >
                            <label
                              className="field-label"
                              htmlFor="loginPassword"
                            >
                              Password
                            </label>
                            <a href="#" className="link">
                              Forgot password?
                            </a>
                          </div>
                          <div className="input-wrap">
                            <span className="icon-l">
                              <LockIcon />
                            </span>
                            <input
                              id="loginPassword"
                              name="password"
                              className={`input ${loginPasswordError ? "invalid" : ""}`}
                              type={showLoginPassword ? "text" : "password"}
                              placeholder="••••••••"
                              autoComplete="section-login current-password"
                              value={loginPassword}
                              onChange={(e) => {
                                setLoginPassword(e.target.value);
                                if (loginPasswordError)
                                  setLoginPasswordError(null);
                              }}
                            />
                            <button
                              type="button"
                              className="icon-r"
                              aria-label={
                                showLoginPassword
                                  ? "Hide password"
                                  : "Show password"
                              }
                              onClick={() =>
                                setShowLoginPassword((v) => !v)
                              }
                            >
                              <EyeIcon />
                            </button>
                          </div>
                          {loginPasswordError ? (
                            <div className="field-error">
                              {loginPasswordError}
                            </div>
                          ) : null}
                        </div>

                        <div className="row-between">
                          <label className="checkbox">
                            <input type="checkbox" /> Remember me for 30 days
                          </label>
                        </div>

                        <button
                          type="submit"
                          className="btn btn-primary btn-lg"
                          style={{ width: "100%", marginTop: 6 }}
                          disabled={isSubmitting}
                        >
                          {isSubmitting ? "Signing in…" : "Sign in"}
                        </button>
                      </div>

                    </form>
                  ) : (
                    <form onSubmit={handleRegister} noValidate autoComplete="off">
                      <h2 className="auth-form-title">Create your account</h2>
                      <p className="auth-form-sub">
                        Browse products, check availability, and save your
                        rental preferences.
                      </p>

                      <div className="auth-fields">
                        <div className="auth-field-row">
                          <div className="field">
                            <label className="field-label" htmlFor="regFirst">
                              First name
                            </label>
                            <input
                              id="regFirst"
                              name="givenName"
                              className="input"
                              placeholder="Ayesha"
                              autoComplete="given-name"
                              value={regFirst}
                              onChange={(e) => setRegFirst(e.target.value)}
                            />
                          </div>
                          <div className="field">
                            <label className="field-label" htmlFor="regLast">
                              Last name
                            </label>
                            <input
                              id="regLast"
                              name="familyName"
                              className="input"
                              placeholder="Rahman"
                              autoComplete="family-name"
                              value={regLast}
                              onChange={(e) => setRegLast(e.target.value)}
                            />
                          </div>
                        </div>

                        <div className="field">
                          <label className="field-label" htmlFor="regEmail">
                            Email address
                          </label>
                          <div className="input-wrap">
                            <span className="icon-l">
                              <MailIcon />
                            </span>
                            <input
                              id="regEmail"
                              name="email"
                              className={`input ${regEmailError ? "invalid" : ""}`}
                              type="email"
                              placeholder="you@example.com"
                              autoComplete="section-register email"
                              autoCapitalize="none"
                              autoCorrect="off"
                              spellCheck={false}
                              value={regEmail}
                              onChange={(e) => {
                                setRegEmail(e.target.value);
                                if (regEmailError) setRegEmailError(null);
                              }}
                            />
                          </div>
                          {regEmailError ? (
                            <div className="field-error">{regEmailError}</div>
                          ) : null}
                        </div>

                        <div className="field">
                          <label className="field-label" htmlFor="regPassword">
                            Password
                          </label>
                          <div className="input-wrap">
                            <span className="icon-l">
                              <LockIcon />
                            </span>
                            <input
                              id="regPassword"
                              name="password"
                              className={`input ${regPasswordError ? "invalid" : ""}`}
                              type={showRegPassword ? "text" : "password"}
                              placeholder="At least 8 characters"
                              autoComplete="section-register new-password"
                              value={regPassword}
                              onChange={(e) => {
                                setRegPassword(e.target.value);
                                if (regPasswordError)
                                  setRegPasswordError(null);
                              }}
                            />
                            <button
                              type="button"
                              className="icon-r"
                              aria-label={
                                showRegPassword
                                  ? "Hide password"
                                  : "Show password"
                              }
                              onClick={() => setShowRegPassword((v) => !v)}
                            >
                              <EyeIcon />
                            </button>
                          </div>
                          <div
                            className={`password-strength s${strengthScore}`}
                            aria-hidden="true"
                          >
                            <div className="bar" />
                            <div className="bar" />
                            <div className="bar" />
                            <div className="bar" />
                          </div>
                          <div className="strength-label">{strengthLabel}</div>
                          {regPasswordError ? (
                            <div className="field-error">
                              {regPasswordError}
                            </div>
                          ) : null}
                        </div>

                        <div className="field">
                          <label className="field-label" htmlFor="regConfirm">
                            Confirm password
                          </label>
                          <div className="input-wrap">
                            <span className="icon-l">
                              <LockIcon />
                            </span>
                            <input
                              id="regConfirm"
                              name="confirmPassword"
                              className={`input ${regConfirmError ? "invalid" : ""}`}
                              type="password"
                              placeholder="Re-type password"
                              autoComplete="section-register new-password"
                              value={regConfirm}
                              onChange={(e) => {
                                setRegConfirm(e.target.value);
                                if (regConfirmError) setRegConfirmError(null);
                              }}
                            />
                          </div>
                          {regConfirmError ? (
                            <div className="field-error">{regConfirmError}</div>
                          ) : null}
                        </div>

                        <label
                          className="checkbox"
                          style={{ marginTop: 6, alignItems: "flex-start" }}
                        >
                          <input
                            type="checkbox"
                            checked={regTerms}
                            onChange={(e) => setRegTerms(e.target.checked)}
                          />
                          <span
                            className="terms-text"
                            style={{ margin: 0 }}
                          >
                            I agree to the <a href="#">Terms of Service</a> and{" "}
                            <a href="#">Privacy Policy</a>.
                          </span>
                        </label>

                        <button
                          type="submit"
                          className="btn btn-primary btn-lg"
                          style={{ width: "100%", marginTop: 6 }}
                          disabled={isSubmitting}
                        >
                          {isSubmitting ? "Creating account…" : "Create account"}
                        </button>
                      </div>

                    </form>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="auth-foot">
            <span>© 2026 RentPi · Dhaka</span>
          </div>
        </section>
      </div>

      {/* Toast */}
      <div
        className={`toast ${toast ? "show" : ""} ${
          toast?.tone === "error" ? "toast-error" : ""
        }`}
        role="status"
        aria-live="polite"
      >
        <div className="toast-icon">
          <CheckIcon />
        </div>
        <span>{toast?.message ?? ""}</span>
      </div>
    </div>
  );
}
