import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  authCookieOptions,
  extractToken,
  getGatewayUrl,
  readErrorDetail,
  TokenResponse,
} from "@/lib/auth-service";

export async function POST(request: NextRequest) {
  const rawPayload = (await request.json()) as {
    name?: unknown;
    full_name?: unknown;
    email?: unknown;
    password?: unknown;
  };

  const normalizedPayload = {
    name:
      typeof rawPayload.name === "string" && rawPayload.name.trim().length > 0
        ? rawPayload.name.trim()
        : typeof rawPayload.full_name === "string"
          ? rawPayload.full_name
          : "",
    email: typeof rawPayload.email === "string" ? rawPayload.email : "",
    password: typeof rawPayload.password === "string" ? rawPayload.password : "",
  };

  let upstreamResponse: Response;

  try {
    upstreamResponse = await fetch(`${getGatewayUrl()}/users/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(normalizedPayload),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      {
        detail:
          "Auth backend is unreachable. Start backend services (e.g. `make up`) and try again.",
      },
      { status: 503 },
    );
  }

  if (!upstreamResponse.ok) {
    return NextResponse.json(
      { detail: await readErrorDetail(upstreamResponse) },
      { status: upstreamResponse.status },
    );
  }

  const tokenPayload = (await upstreamResponse.json()) as TokenResponse;
  const token = extractToken(tokenPayload);
  if (!token) {
    return NextResponse.json(
      { detail: "Registration succeeded but no JWT token was returned." },
      { status: 502 },
    );
  }
  const response = NextResponse.json({ success: true });

  response.cookies.set(
    AUTH_TOKEN_COOKIE,
    token,
    authCookieOptions(),
  );

  return response;
}
