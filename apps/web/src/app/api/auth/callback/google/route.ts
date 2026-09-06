import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050/api/v1";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get("code");
  const error = searchParams.get("error");
  const state = searchParams.get("state");

  const connecting = request.cookies.get("oauth_intent")?.value === "sheets";
  const loginUrl = new URL("/login", request.url);
  const finish = (response: NextResponse) => {
    response.cookies.delete("oauth_state");
    response.cookies.delete("oauth_intent");
    response.cookies.delete("oauth_connection_user");
    response.cookies.delete("oauth_from");
    response.headers.set("Cache-Control", "no-store");
    return response;
  };
  const connectionResult = (message?: string) => {
    const destination = new URL("/callback", request.url);
    destination.searchParams.set("google_connection", message ? "error" : "success");
    if (message) destination.searchParams.set("connection_error", message);
    return finish(NextResponse.redirect(destination));
  };
  const expectedState = request.cookies.get("oauth_state")?.value;
  if (!state || !expectedState || state !== expectedState) {
    if (connecting) return connectionResult("Phiên kết nối đã hết hạn. Vui lòng thử lại.");
    loginUrl.searchParams.set("error", "invalid_state");
    return finish(NextResponse.redirect(loginUrl));
  }

  if (error) {
    if (connecting) return connectionResult("Bạn chưa cấp quyền Google Sheets. Phiên đăng nhập vẫn được giữ nguyên.");
    loginUrl.searchParams.set("error", error);
    return finish(NextResponse.redirect(loginUrl));
  }

  if (!code) {
    if (connecting) return connectionResult("Google chưa trả về mã cấp quyền. Vui lòng thử lại.");
    loginUrl.searchParams.set("error", "missing_code");
    return finish(NextResponse.redirect(loginUrl));
  }

  const redirectUri = process.env.GOOGLE_REDIRECT_URI || "http://localhost:3050/api/auth/callback/google";

  try {
    if (connecting) {
      const token = request.cookies.get("auth_token")?.value;
      const owner = request.cookies.get("oauth_connection_user")?.value;
      if (!token || !owner) return connectionResult("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      const result = await fetch(`${API_BASE}/auth/google/connect`, {
        method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${token}`},
        body:JSON.stringify({code,redirect_uri:redirectUri,expected_user_id:owner}),
        signal:AbortSignal.timeout(25000),
      });
      if (!result.ok) return connectionResult("Không kết nối được Google Sheets. Kiểm tra tài khoản và quyền đã cấp rồi thử lại.");
      return connectionResult();
    }
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
      return finish(NextResponse.redirect(loginUrl));
    }

    const authData = await response.json();
    const token = authData.access_token;

    // Redirect to client callback page which hydrates Zustand store and sets localStorage
    const callbackUrl = new URL("/callback", request.url);
    callbackUrl.searchParams.set("token", token);
    if (authData.user) {
      callbackUrl.searchParams.set(
        "user",
        Buffer.from(JSON.stringify(authData.user), "utf8").toString("base64url")
      );
    }
    const from = request.cookies.get("oauth_from")?.value;
    if (from && from.startsWith("/") && !from.startsWith("//") && !from.includes("\\")) {
      callbackUrl.searchParams.set("from", from);
    }

    const res = NextResponse.redirect(callbackUrl);

    // Set cookie for session persistence & middleware
    res.cookies.set("auth_token", token, {
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
    });
    res.cookies.delete("oauth_from");

    return finish(res);
  } catch (err: unknown) {
    if (connecting) return connectionResult("Kết nối Google tạm thời thất bại. Vui lòng thử lại.");
    loginUrl.searchParams.set("error", encodeURIComponent(err instanceof Error ? err.message : "Network error during Google auth"));
    return finish(NextResponse.redirect(loginUrl));
  }
}
