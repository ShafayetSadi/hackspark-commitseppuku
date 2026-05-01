import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  authCookieOptions,
  getGatewayUrl,
  readErrorDetail,
  TokenResponse,
} from "@/lib/auth-service";

export async function POST(request: NextRequest) {
  const payload = await request.json();

  let upstreamResponse: Response;

  try {
    upstreamResponse = await fetch(`${getGatewayUrl()}/users/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
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
  const response = NextResponse.json({ success: true });

  response.cookies.set(
    AUTH_TOKEN_COOKIE,
    tokenPayload.access_token,
    authCookieOptions(),
  );

  return response;
}
