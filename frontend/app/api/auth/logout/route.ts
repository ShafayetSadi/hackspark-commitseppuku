import { NextResponse } from "next/server";

import { AUTH_TOKEN_COOKIE, authCookieOptions } from "@/lib/auth-service";

export async function POST() {
  const response = NextResponse.json({ success: true });
  response.cookies.set(AUTH_TOKEN_COOKIE, "", {
    ...authCookieOptions(),
    maxAge: 0,
  });
  return response;
}
