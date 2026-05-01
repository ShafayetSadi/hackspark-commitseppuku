import { cookies } from "next/headers";

import AuthPanel from "@/app/components/auth-panel";
import { AUTH_TOKEN_COOKIE, getGatewayUrl } from "@/lib/auth-service";

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

    const payload = (await response.json()) as AuthUser;
    return payload;
  } catch {
    return null;
  }
}

export default async function Home() {
  const initialUser = await getInitialUser();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl flex-col justify-center px-6 py-12 sm:px-8">
      <AuthPanel initialUser={initialUser} />
    </main>
  );
}
