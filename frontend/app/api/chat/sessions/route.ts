import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  getGatewayUrl,
  readErrorDetail,
} from "@/lib/auth-service";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const headers: HeadersInit = token
    ? { Authorization: `Bearer ${token}` }
    : {};
  try {
    const upstream = await fetch(`${getGatewayUrl()}/chat/sessions`, {
      method: "GET",
      cache: "no-store",
      headers,
    });
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: await readErrorDetail(upstream) },
        { status: upstream.status },
      );
    }
    return NextResponse.json(await upstream.json());
  } catch {
    return NextResponse.json(
      { detail: "Chat sessions are unavailable right now." },
      { status: 503 },
    );
  }
}
