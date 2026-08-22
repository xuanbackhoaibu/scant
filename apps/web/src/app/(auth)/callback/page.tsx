"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, AlertCircle } from "lucide-react";
import { useAuthStore } from "@/stores/useAuthStore";
import { api } from "@/lib/api";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setSession = useAuthStore((state) => state.setSession);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get("token");
    const err = searchParams.get("error");

    if (err) {
      setError(decodeURIComponent(err));
      setTimeout(() => router.push("/login"), 3000);
      return;
    }

    if (!token) {
      // Try checking if cookie was set or fallback to login
      const localToken = localStorage.getItem("auth_token");
      if (localToken) {
        router.push("/");
      } else {
        router.push("/login");
      }
      return;
    }

    async function hydrateUser() {
      try {
        localStorage.setItem("auth_token", token!);
        const user = await api.auth.me();
        setSession(token!, user);
        router.push("/");
      } catch (err: any) {
        setError(err.message || "Failed to restore authenticated session");
        setTimeout(() => router.push("/login"), 3000);
      }
    }

    hydrateUser();
  }, [searchParams, router, setSession]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm bg-white rounded-3xl border border-slate-200 shadow-sm p-8 text-center space-y-4">
        {error ? (
          <div className="space-y-3">
            <div className="h-12 w-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <AlertCircle className="h-6 w-6" />
            </div>
            <h2 className="text-sm font-bold text-slate-900">Xác thực không thành công</h2>
            <p className="text-xs text-slate-500">{error}</p>
            <p className="text-[11px] text-slate-400">Đang chuyển hướng về trang đăng nhập...</p>
          </div>
        ) : (
          <div className="space-y-3">
            <Loader2 className="h-8 w-8 text-indigo-600 animate-spin mx-auto" />
            <h2 className="text-sm font-bold text-slate-900">Đang hoàn tất đăng nhập...</h2>
            <p className="text-xs text-slate-500">Hệ thống đang đồng bộ tài khoản Google và không gian làm việc của bạn.</p>
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
