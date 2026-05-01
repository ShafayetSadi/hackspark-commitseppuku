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

  let upstreamResponse: Response;

  try {
    upstreamResponse = await fetch(`${getGatewayUrl()}/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });
  } catch {
    const response = NextResponse.json(
      {
        detail:
          "Auth backend is unreachable. Start backend services (e.g. `make up`) and try again.",
      },
      { status: 503 },
    );

    response.cookies.set(AUTH_TOKEN_COOKIE, "", {
      ...authCookieOptions(),
      maxAge: 0,
    });

    return response;
  }

  if (!upstreamResponse.ok) {
    const response = NextResponse.json(
      { detail: await readErrorDetail(upstreamResponse) },
      { status: upstreamResponse.status },
    );

    if (upstreamResponse.status === 401) {
      response.cookies.set(AUTH_TOKEN_COOKIE, "", {
        ...authCookieOptions(),
        maxAge: 0,
      });
    }

    return response;
  }

  const userPayload = (await upstreamResponse.json()) as {
    id: number;
    email: string;
    full_name: string;
  };

  return NextResponse.json(userPayload);
}
