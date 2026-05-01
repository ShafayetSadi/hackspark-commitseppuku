import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  authCookieOptions,
  getGatewayUrl,
  readErrorDetail,
} from "@/lib/auth-service";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  try {
    const upstream = await fetch(`${getGatewayUrl()}/users/me`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });

    if (!upstream.ok) {
      const response = NextResponse.json(
        { detail: await readErrorDetail(upstream) },
        { status: upstream.status },
      );
      if (upstream.status === 401) {
        response.cookies.set(AUTH_TOKEN_COOKIE, "", {
          ...authCookieOptions(),
          maxAge: 0,
        });
      }
      return response;
    }

    return NextResponse.json(await upstream.json());
  } catch {
    return NextResponse.json(
      { detail: "User service is unreachable right now." },
      { status: 503 },
    );
  }
}
