import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050/api/v1";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get("code");
  const error = searchParams.get("error");
  const state = searchParams.get("state");

  const loginUrl = new URL("/login", request.url);

  if (error) {
    loginUrl.searchParams.set("error", error);
    return NextResponse.redirect(loginUrl);
  }

  if (!code) {
    loginUrl.searchParams.set("error", "missing_code");
    return NextResponse.redirect(loginUrl);
  }

  const redirectUri = process.env.GOOGLE_REDIRECT_URI || "http://localhost:3050/api/auth/callback/google";

  try {
    // Forward code to FastAPI backend for secure verification, user upsert, and token generation
    const response = await fetch(`${API_BASE}/auth/google/code`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        code,
        redirect_uri: redirectUri,
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || "Google authentication failed";
      loginUrl.searchParams.set("error", encodeURIComponent(detail));
      return NextResponse.redirect(loginUrl);
    }

    const authData = await response.json();
    const token = authData.access_token;

    // Redirect to client callback page which hydrates Zustand store and sets localStorage
    const callbackUrl = new URL("/auth/callback", request.url);
    callbackUrl.searchParams.set("token", token);

    const res = NextResponse.redirect(callbackUrl);

    // Set cookie for session persistence & middleware
    res.cookies.set("auth_token", token, {
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
    });

    return res;
  } catch (err: any) {
    loginUrl.searchParams.set("error", encodeURIComponent(err.message || "Network error during Google auth"));
    return NextResponse.redirect(loginUrl);
  }
}
