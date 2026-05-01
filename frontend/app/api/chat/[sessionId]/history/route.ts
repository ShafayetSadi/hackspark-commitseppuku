import { NextResponse } from "next/server";

import { getGatewayUrl, readErrorDetail } from "@/lib/auth-service";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ sessionId: string }> },
) {
  const { sessionId } = await params;
  try {
    const upstream = await fetch(
      `${getGatewayUrl()}/chat/${sessionId}/history`,
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
      { detail: "Chat history is unavailable right now." },
      { status: 503 },
    );
  }
}
