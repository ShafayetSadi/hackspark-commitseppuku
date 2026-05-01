export const AUTH_TOKEN_COOKIE = "hackspark_auth_token";

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export function getGatewayUrl(): string {
  const configured = process.env.GATEWAY_URL;
  if (!configured) {
    return "http://localhost:8000";
  }

  return configured.replace(/\/+$/, "");
}

export function authCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
  };
}

export async function readErrorDetail(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.length > 0) {
      return payload.detail;
    }
  } catch {
    // Ignore parsing errors and use a fallback message.
  }

  return `Request failed with status ${response.status}`;
}
