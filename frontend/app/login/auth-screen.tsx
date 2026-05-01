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

const APP_HREF = "/app";
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

function GoogleIcon() {
  return (
    <svg width={15} height={15} viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.5 12.3c0-.8-.1-1.5-.2-2.2H12v4.2h5.9c-.3 1.4-1 2.5-2.2 3.3v2.7h3.5c2-1.9 3.3-4.6 3.3-8z"
      />
      <path
        fill="#34A853"
        d="M12 23c3 0 5.5-1 7.3-2.7l-3.5-2.7c-1 .7-2.3 1.1-3.8 1.1-2.9 0-5.4-2-6.3-4.6H2v2.8C3.8 20.5 7.6 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.7 14.1c-.2-.7-.4-1.4-.4-2.1s.1-1.4.4-2.1V7.1H2C1.4 8.6 1 10.2 1 12s.4 3.4 1 4.9l3.7-2.8z"
      />
      <path
        fill="#EA4335"
        d="M12 5.4c1.6 0 3.1.6 4.2 1.6l3.1-3.1C17.5 2.2 15 1 12 1 7.6 1 3.8 3.5 2 7.1l3.7 2.8C6.6 7.4 9.1 5.4 12 5.4z"
      />
    </svg>
  );
}

function AppleIcon() {
  return (
    <svg
      width={15}
      height={15}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
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
          full_name: fullName,
          email: regEmail,
          password: regPassword,
        }),
      });

      if (!response.ok) {
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
                    <form onSubmit={handleLogin} noValidate>
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
                              className={`input ${loginEmailError ? "invalid" : ""}`}
                              type="email"
                              placeholder="you@example.com"
                              autoComplete="email"
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
                              className={`input ${loginPasswordError ? "invalid" : ""}`}
                              type={showLoginPassword ? "text" : "password"}
                              placeholder="••••••••"
                              autoComplete="current-password"
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

                      <div className="auth-divider">or continue with</div>
                      <div className="auth-oauth">
                        <button type="button" className="btn-oauth" disabled>
                          <GoogleIcon />
                          Google
                        </button>
                        <button type="button" className="btn-oauth" disabled>
                          <AppleIcon />
                          Apple
                        </button>
                      </div>
                    </form>
                  ) : (
                    <form onSubmit={handleRegister} noValidate>
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
                              className={`input ${regEmailError ? "invalid" : ""}`}
                              type="email"
                              placeholder="you@example.com"
                              autoComplete="email"
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
                              className={`input ${regPasswordError ? "invalid" : ""}`}
                              type={showRegPassword ? "text" : "password"}
                              placeholder="At least 8 characters"
                              autoComplete="new-password"
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
                              className={`input ${regConfirmError ? "invalid" : ""}`}
                              type="password"
                              placeholder="Re-type password"
                              autoComplete="new-password"
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

                      <div className="auth-divider">or sign up with</div>
                      <div className="auth-oauth">
                        <button type="button" className="btn-oauth" disabled>
                          <GoogleIcon />
                          Google
                        </button>
                        <button type="button" className="btn-oauth" disabled>
                          <AppleIcon />
                          Apple
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
