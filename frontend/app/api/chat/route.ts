import { NextResponse } from "next/server";

import { getGatewayUrl, readErrorDetail } from "@/lib/auth-service";

type ChatPayload = {
  sessionId?: string;
  message?: string;
};

export async function POST(request: Request) {
  const payload = (await request.json()) as ChatPayload;
  const message = (payload.message ?? "").trim();
  if (!message) {
    return NextResponse.json({ detail: "Message is required." }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${getGatewayUrl()}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: message,
        top_k: 3,
        session_id: payload.sessionId ?? null,
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
    };
    return NextResponse.json({
      sessionId: data.session_id ?? payload.sessionId ?? "",
      reply: data.answer ?? "",
    });
  } catch {
    return NextResponse.json(
      { detail: "RentPi Assistant is unavailable right now." },
      { status: 503 },
    );
  }
}
