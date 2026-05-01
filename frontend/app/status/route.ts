import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({ service: "frontend", status: "OK" });
}
