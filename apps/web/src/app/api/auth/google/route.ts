import { NextRequest, NextResponse } from "next/server";
import { randomBytes } from "node:crypto";

export async function GET(request: NextRequest) {
  const clientId = process.env.GOOGLE_CLIENT_ID || process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  const redirectUri = process.env.GOOGLE_REDIRECT_URI || "http://localhost:3050/api/auth/callback/google";
  const from = request.nextUrl.searchParams.get("from");
  const connecting = request.nextUrl.searchParams.get("intent") === "sheets";

  if (!clientId) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("error", "google_not_configured");
    return NextResponse.redirect(loginUrl);
  }

  let connectionUser: string | undefined;
  if (connecting) {
    const token = request.cookies.get("auth_token")?.value;
    try {
      const me = token ? await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050/api/v1"}/auth/me`, {headers:{Authorization:`Bearer ${token}`},cache:"no-store",signal:AbortSignal.timeout(10000)}) : null;
      if (me?.ok) connectionUser = (await me.json()).id;
    } catch { /* Return a recoverable connection error in the popup. */ }
    if (!connectionUser) {
      const result = new URL("/callback", request.url);
      result.searchParams.set("google_connection", "error");
      result.searchParams.set("connection_error", "Vui lòng đăng nhập ứng dụng rồi kết nối Google Sheets.");
      return NextResponse.redirect(result);
    }
  }

  // Generate random state for CSRF defense
  const state = randomBytes(32).toString("hex");

  const googleAuthUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  googleAuthUrl.searchParams.set("client_id", clientId);
  googleAuthUrl.searchParams.set("response_type", "code");
  googleAuthUrl.searchParams.set("redirect_uri", redirectUri);
  googleAuthUrl.searchParams.set(
    "scope",
    connecting ? "openid email profile https://www.googleapis.com/auth/spreadsheets" : "openid email profile"
  );
  if (connecting) {
    googleAuthUrl.searchParams.set("access_type", "offline");
    googleAuthUrl.searchParams.set("include_granted_scopes", "true");
  }
  googleAuthUrl.searchParams.set("prompt", connecting ? "consent select_account" : "select_account");
  googleAuthUrl.searchParams.set("state", state);

  const response = NextResponse.redirect(googleAuthUrl);
  const cookieOptions = {httpOnly:true,secure:process.env.NODE_ENV === "production",sameSite:"lax" as const,path:"/",maxAge:600};
  response.cookies.set("oauth_intent", connecting ? "sheets" : "signin", cookieOptions);
  response.cookies.delete("oauth_connection_user");
  if (connectionUser) response.cookies.set("oauth_connection_user", connectionUser, cookieOptions);
  response.cookies.set("oauth_state", state, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 600, // 10 minutes
  });
  response.headers.set("Cache-Control", "no-store");
  response.cookies.delete("oauth_from");
  if (from && from.startsWith("/") && !from.startsWith("//") && !from.includes("\\")) {
    response.cookies.set("oauth_from", from, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 600,
    });
  }

  return response;
}
