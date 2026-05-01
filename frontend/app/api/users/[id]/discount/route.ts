import { NextResponse } from "next/server";

import { getGatewayUrl, readErrorDetail } from "@/lib/auth-service";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } },
) {
  try {
    const upstream = await fetch(`${getGatewayUrl()}/users/${params.id}/discount`, {
      method: "GET",
      cache: "no-store",
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
      { detail: "Discount data is unavailable right now." },
      { status: 503 },
    );
  }
}
