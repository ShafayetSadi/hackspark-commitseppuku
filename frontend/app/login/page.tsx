import { cookies } from "next/headers";

import { AUTH_TOKEN_COOKIE, getGatewayUrl } from "@/lib/auth-service";

import AuthScreen from "./auth-screen";
import "./auth.css";

// /login route — RentPi sign-in / sign-up page.
//
// This is a faithful port of the design handoff (hackathon/project/Auth.html):
// dark brand panel on the left, tabbed Sign in / Create account form on the
// right. The interactive form lives in `auth-screen.tsx` (Client Component),
// while this Server Component pre-fetches the current user (if any) using the
// HTTP-only `hackspark_auth_token` cookie so authenticated visitors land on
// the session card instead of an empty form.

type AuthUser = {
  id: number;
  email: string;
  full_name: string;
};

async function getInitialUser(): Promise<AuthUser | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_TOKEN_COOKIE)?.value;

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${getGatewayUrl()}/users/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as {
      id: number;
      email: string;
      name?: string;
      full_name?: string;
    };
    return {
      id: payload.id,
      email: payload.email,
      full_name: payload.name ?? payload.full_name ?? "",
    };
  } catch {
    return null;
  }
}

export default async function LoginPage() {
  const initialUser = await getInitialUser();

  return <AuthScreen initialUser={initialUser} />;
}
