import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  getGatewayUrl,
  readErrorDetail,
} from "@/lib/auth-service";

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> },
) {
  const { sessionId } = await params;
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const headers: HeadersInit = token
    ? { Authorization: `Bearer ${token}` }
    : {};
  try {
    const upstream = await fetch(`${getGatewayUrl()}/chat/${sessionId}`, {
      method: "DELETE",
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
      { detail: "Could not delete this chat session right now." },
      { status: 503 },
    );
  }
}
