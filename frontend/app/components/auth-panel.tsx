"use client";

import { FormEvent, useState } from "react";

type AuthUser = {
  id: number;
  email: string;
  full_name: string;
};

type AuthPanelProps = {
  initialUser: AuthUser | null;
};

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

async function getResponseDetail(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.length > 0) {
      return payload.detail;
    }
  } catch {
    // Ignore parse failures and use fallback.
  }

  return `Request failed with status ${response.status}`;
}

export default function AuthPanel({ initialUser }: AuthPanelProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [user, setUser] = useState<AuthUser | null>(initialUser);
  const [isCheckingSession, setIsCheckingSession] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const refreshCurrentUser = async (showLoadingState = true) => {
    if (showLoadingState) {
      setIsCheckingSession(true);
    }

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
        throw new Error(await getResponseDetail(response));
      }

      const payload = (await response.json()) as AuthUser;
      setUser(payload);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "Unable to load current user"));
    } finally {
      setIsCheckingSession(false);
    }
  };

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    const formData = new FormData(event.currentTarget);
    const payload = {
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
    };

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(await getResponseDetail(response));
      }

      await refreshCurrentUser(true);
      setSuccessMessage("Login successful.");
      event.currentTarget.reset();
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "Login failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegister = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    const formData = new FormData(event.currentTarget);
    const payload = {
      full_name: String(formData.get("full_name") ?? ""),
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
    };

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(await getResponseDetail(response));
      }

      await refreshCurrentUser(true);
      setSuccessMessage("Registration successful. You are now logged in.");
      event.currentTarget.reset();
      setMode("login");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "Registration failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(await getResponseDetail(response));
      }

      setUser(null);
      setSuccessMessage("Logged out successfully.");
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "Logout failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="space-y-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Hackspark Auth UI</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Register, log in, and inspect your current authenticated user via the
          gateway-backed auth service.
        </p>
      </header>

      {errorMessage ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-950 dark:bg-red-950/40 dark:text-red-200">
          {errorMessage}
        </p>
      ) : null}

      {successMessage ? (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-950 dark:bg-emerald-950/40 dark:text-emerald-200">
          {successMessage}
        </p>
      ) : null}

      <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="mb-2 text-base font-medium">Session</h2>

        {isCheckingSession ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">Checking session...</p>
        ) : user ? (
          <div className="space-y-3">
            <div className="space-y-1 text-sm">
              <p>
                <span className="font-medium">ID:</span> {user.id}
              </p>
              <p>
                <span className="font-medium">Name:</span> {user.full_name}
              </p>
              <p>
                <span className="font-medium">Email:</span> {user.email}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => void refreshCurrentUser(true)}
                disabled={isSubmitting}
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm font-medium hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:hover:bg-zinc-900"
              >
                Refresh profile
              </button>
              <button
                type="button"
                onClick={() => void handleLogout()}
                disabled={isSubmitting}
                className="rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                Logout
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">Not authenticated.</p>
        )}
      </div>

      {!user ? (
        <div className="space-y-4">
          <div className="inline-flex rounded-md border border-zinc-200 p-1 dark:border-zinc-800">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`rounded px-3 py-1 text-sm font-medium ${
                mode === "login"
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
              }`}
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`rounded px-3 py-1 text-sm font-medium ${
                mode === "register"
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
              }`}
            >
              Register
            </button>
          </div>

          {mode === "login" ? (
            <form className="space-y-3" onSubmit={handleLogin}>
              <label className="block space-y-1 text-sm">
                <span>Email</span>
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  required
                  className="w-full rounded-md border border-zinc-300 px-3 py-2 outline-none ring-zinc-400 focus:ring dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>

              <label className="block space-y-1 text-sm">
                <span>Password</span>
                <input
                  type="password"
                  name="password"
                  autoComplete="current-password"
                  required
                  minLength={8}
                  className="w-full rounded-md border border-zinc-300 px-3 py-2 outline-none ring-zinc-400 focus:ring dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>

              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                {isSubmitting ? "Logging in..." : "Login"}
              </button>
            </form>
          ) : (
            <form className="space-y-3" onSubmit={handleRegister}>
              <label className="block space-y-1 text-sm">
                <span>Full name</span>
                <input
                  type="text"
                  name="full_name"
                  autoComplete="name"
                  required
                  minLength={2}
                  className="w-full rounded-md border border-zinc-300 px-3 py-2 outline-none ring-zinc-400 focus:ring dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>

              <label className="block space-y-1 text-sm">
                <span>Email</span>
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  required
                  className="w-full rounded-md border border-zinc-300 px-3 py-2 outline-none ring-zinc-400 focus:ring dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>

              <label className="block space-y-1 text-sm">
                <span>Password</span>
                <input
                  type="password"
                  name="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  className="w-full rounded-md border border-zinc-300 px-3 py-2 outline-none ring-zinc-400 focus:ring dark:border-zinc-700 dark:bg-zinc-950"
                />
              </label>

              <button
                type="submit"
                disabled={isSubmitting}
                className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
              >
                {isSubmitting ? "Registering..." : "Register"}
              </button>
            </form>
          )}
        </div>
      ) : null}
    </section>
  );
}
