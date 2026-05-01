import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_TOKEN_COOKIE,
  getGatewayUrl,
  readErrorDetail,
} from "@/lib/auth-service";

type ChatMessage = { role: "user" | "assistant"; content: string };

type ChatRequestPayload = {
  messages: ChatMessage[];
  question?: string;
};

// Proxy the RentPi assistant chat through the gateway so the frontend never
// holds a JWT. The downstream AI service exposes POST /ai/chat. Different
// implementations may shape the response differently — we try a few common
// fields so the UI keeps working as the backend evolves.
export async function POST(request: NextRequest) {
  const payload = (await request.json()) as ChatRequestPayload;
  const lastUser = [...(payload.messages || [])]
    .reverse()
    .find((m) => m.role === "user");
  const question = payload.question ?? lastUser?.content ?? "";

  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_TOKEN_COOKIE)?.value;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${getGatewayUrl()}/ai/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        question,
        messages: payload.messages,
      }),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      {
        detail:
          "AI backend is unreachable. Start backend services (e.g. `make up`) and try again.",
      },
      { status: 503 },
    );
  }

  if (!upstream.ok) {
    return NextResponse.json(
      { detail: await readErrorDetail(upstream) },
      { status: upstream.status },
    );
  }

  // Normalize the response so the client always sees `reply`.
  const raw = (await upstream.json()) as Record<string, unknown>;
  const reply =
    (typeof raw.reply === "string" && raw.reply) ||
    (typeof raw.answer === "string" && raw.answer) ||
    (typeof raw.message === "string" && raw.message) ||
    (typeof raw.content === "string" && raw.content) ||
    "";

  return NextResponse.json({ reply, raw });
}
