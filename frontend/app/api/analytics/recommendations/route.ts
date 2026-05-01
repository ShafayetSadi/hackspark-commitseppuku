import { NextRequest, NextResponse } from "next/server";

import { getGatewayUrl, readErrorDetail } from "@/lib/auth-service";

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const date = params.get("date") ?? new Date().toISOString().slice(0, 10);
  const limit = params.get("limit") ?? "6";
  const query = new URLSearchParams({ date, limit });

  try {
    const upstream = await fetch(
      `${getGatewayUrl()}/analytics/recommendations?${query.toString()}`,
      {
        method: "GET",
        cache: "no-store",
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
