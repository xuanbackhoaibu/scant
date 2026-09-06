"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, AlertCircle } from "lucide-react";
import { useAuthStore } from "@/stores/useAuthStore";
import { API_BASE } from "@/lib/api";
import { useTranslation } from "@/i18n/I18nContext";

function decodeUserParam(value: string) {
  try {
    const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    const decoded = new TextDecoder("utf-8").decode(bytes);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

async function fetchCurrentUserWithTimeout(token: string) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error("Failed to load current user");
    }
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setSession = useAuthStore((state) => state.setSession);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    const connection = searchParams?.get("google_connection");
    if (connection) {
      if (window.opener) {
        window.opener.postMessage({type:"google-sheets-connection",ok:connection==="success",error:searchParams?.get("connection_error")}, window.location.origin);
        window.close();
      } else {
        router.replace(`/settings?google_connection=${encodeURIComponent(connection)}`);
      }
      return;
    }
    const token = searchParams?.get("token");
    const encodedUser = searchParams?.get("user");
    const err = searchParams?.get("error");
    const from = searchParams?.get("from");
    const redirectTarget = from && from.startsWith("/") && !from.startsWith("//") && !from.includes("\\") ? from : "/";

    if (err) {
      setError(decodeURIComponent(err));
      setTimeout(() => router.push("/login"), 3000);
      return;
    }

    if (!token) {
      // Try checking if cookie was set or fallback to login
      const localToken = localStorage.getItem("auth_token");
      if (localToken) {
        router.push(redirectTarget);
      } else {
        router.push("/login");
      }
      return;
    }

    async function hydrateUser() {
      try {
        localStorage.setItem("auth_token", token!);
        const user = encodedUser ? decodeUserParam(encodedUser) : await fetchCurrentUserWithTimeout(token!);
        if (!user) {
          throw new Error(t("auth.sessionRestoreFailed"));
        }
        setSession(token!, user);
        router.replace(redirectTarget);
      } catch (err: any) {
        setError(err.message || t("auth.sessionRestoreFailed"));
        setTimeout(() => router.push("/login"), 3000);
      }
    }

    hydrateUser();
  }, [searchParams, router, setSession, t]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm bg-white rounded-3xl border border-slate-200 shadow-sm p-8 text-center space-y-4">
        {error ? (
          <div className="space-y-3">
            <div className="h-12 w-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <AlertCircle className="h-6 w-6" />
            </div>
            <h2 className="text-sm font-bold text-slate-900">{t("auth.callbackFailedTitle")}</h2>
            <p className="text-xs text-slate-500">{error}</p>
            <p className="text-[11px] text-slate-400">{t("auth.callbackRedirecting")}</p>
          </div>
        ) : (
          <div className="space-y-3">
            <Loader2 className="h-8 w-8 text-indigo-600 animate-spin mx-auto" />
            <h2 className="text-sm font-bold text-slate-900">{t("auth.callbackCompleting")}</h2>
            <p className="text-xs text-slate-500">{t("auth.callbackSyncing")}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
          <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
