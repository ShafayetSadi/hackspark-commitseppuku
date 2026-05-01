import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  getGatewayUrl,
  readErrorDetail,
} from "@/lib/auth-service";

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const limit = params.get("limit") ?? "5";
  const category = params.get("category") ?? "";
  const query = new URLSearchParams({ limit });
  if (category) query.set("category", category);
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const headers: HeadersInit = token
    ? { Authorization: `Bearer ${token}` }
    : {};

  try {
    const upstream = await fetch(
      `${getGatewayUrl()}/analytics/recommendations?${query.toString()}`,
      {
        method: "GET",
        cache: "no-store",
        headers,
      },
    );
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: await readErrorDetail(upstream) },
        { status: upstream.status },
      );
    }
    return NextResponse.json(await upstream.json());
  } catch {
    return NextResponse.json(
      { detail: "Recommendations are unavailable right now." },
      { status: 503 },
    );
  }
}
