import { cookies } from "next/headers";
import type { Metadata } from "next";

import { AUTH_TOKEN_COOKIE, getGatewayUrl } from "@/lib/auth-service";

import AppShell from "./app-shell";
import "./app.css";

// RentPi marketplace app shell — implementation of RentPi.html.
// Server Component: fetches the current user (if any), then hands off to
// the interactive shell that handles page switching, filters, and chat.

type AppUser = {
  id: number;
  email: string;
  full_name: string;
};

export const metadata: Metadata = {
  title: "RentPi — Rental Marketplace",
  description:
    "Browse rental products, check availability, discover trends, and chat with the RentPi assistant.",
};

async function getInitialUser(): Promise<AppUser | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_TOKEN_COOKIE)?.value;

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${getGatewayUrl()}/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as AppUser;
  } catch {
    return null;
  }
}

export default async function RentPiAppPage() {
  const initialUser = await getInitialUser();
  return <AppShell initialUser={initialUser} />;
}
