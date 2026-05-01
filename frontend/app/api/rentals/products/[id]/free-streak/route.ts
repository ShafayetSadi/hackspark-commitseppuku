import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  getGatewayUrl,
  readErrorDetail,
} from "@/lib/auth-service";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const query = request.nextUrl.searchParams.toString();
  const suffix = query ? `?${query}` : "";
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const headers: HeadersInit = token
    ? { Authorization: `Bearer ${token}` }
    : {};
  try {
    const upstream = await fetch(
      `${getGatewayUrl()}/rentals/products/${id}/free-streak${suffix}`,
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
      { detail: "Free streak data is unavailable right now." },
      { status: 503 },
    );
  }
}
