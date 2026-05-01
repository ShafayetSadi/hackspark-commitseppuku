import { NextResponse } from "next/server";

import { getGatewayUrl, readErrorDetail } from "@/lib/auth-service";

export async function GET() {
  try {
    const upstream = await fetch(`${getGatewayUrl()}/chat/sessions`, {
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
      { detail: "Chat sessions are unavailable right now." },
      { status: 503 },
    );
  }
}
