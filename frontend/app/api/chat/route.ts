import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  getGatewayUrl,
  readErrorDetail,
} from "@/lib/auth-service";

type ChatPayload = {
  query?: string;
  top_k?: number;
  session_id?: string | null;
  sessionId?: string;
  message?: string;
};

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as ChatPayload;
  const message = (payload.query ?? payload.message ?? "").trim();
  if (!message) {
    return NextResponse.json({ detail: "query must be at least 1 character." }, { status: 422 });
  }

  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  try {
    const upstream = await fetch(`${getGatewayUrl()}/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        query: message,
        top_k: payload.top_k ?? 3,
        session_id: payload.session_id ?? payload.sessionId ?? null,
      }),
      cache: "no-store",
    });
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: await readErrorDetail(upstream) },
        { status: upstream.status },
      );
    }

    const data = (await upstream.json()) as {
      session_id?: string;
      answer?: string;
      sources?: string[];
      confidence?: number;
    };
    return NextResponse.json({
      sessionId: data.session_id ?? payload.sessionId ?? "",
      session_id: data.session_id ?? payload.sessionId ?? "",
      reply: data.answer ?? "",
      answer: data.answer ?? "",
      sources: data.sources ?? [],
      confidence: typeof data.confidence === "number" ? data.confidence : 0,
    });
  } catch {
    return NextResponse.json(
      { detail: "RentPi Assistant is unavailable right now." },
      { status: 503 },
    );
  }
}
