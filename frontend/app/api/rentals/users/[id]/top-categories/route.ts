import { NextRequest, NextResponse } from "next/server";

import { getGatewayUrl, readErrorDetail } from "@/lib/auth-service";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const query = request.nextUrl.searchParams.toString();
  const suffix = query ? `?${query}` : "";
  try {
    const upstream = await fetch(
      `${getGatewayUrl()}/rentals/users/${id}/top-categories${suffix}`,
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
      { detail: "Top categories are unavailable right now." },
      { status: 503 },
    );
  }
}
