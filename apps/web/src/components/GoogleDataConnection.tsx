"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { request } from "@/lib/api";
import { useAuthStore } from "@/stores/useAuthStore";
import { useTranslation } from "@/i18n/I18nContext";

type Connection = { connected: boolean; email: string | null };

export function GoogleDataConnection() {
  const { locale } = useTranslation();
  const vi = locale === "vi";
  const userId = useAuthStore((s) => s.user?.id);
  const popup = useRef<Window | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const { data, refetch, isError } = useQuery({
    queryKey: ["google-data-connection", userId],
    queryFn: () => request<Connection>("/auth/google/connection"),
    enabled: !!userId,
    retry: false,
  });

  useEffect(() => {
    function receive(event: MessageEvent) {
      if (event.origin !== window.location.origin || !popup.current || event.source !== popup.current || event.data?.type !== "google-sheets-connection") return;
      setPending(false);
      if (event.data.ok) { setError(""); void refetch(); }
      else setError(typeof event.data.error === "string" ? event.data.error : (vi ? "Kết nối chưa hoàn tất. Hãy thử lại." : "Connection incomplete. Please try again."));
      popup.current = null;
    }
    window.addEventListener("message", receive);
    const timer = window.setInterval(() => {
      if (popup.current?.closed) { popup.current = null; setPending(false); }
    }, 1000);
    return () => { window.removeEventListener("message", receive); window.clearInterval(timer); };
  }, [refetch, vi]);

  function connect() {
    setError("");
    popup.current = window.open("/api/auth/google?intent=sheets", "google-sheets-consent", "popup,width=520,height=700");
    if (!popup.current) {
      setError(vi ? "Hãy cho phép cửa sổ bật lên rồi thử kết nối lại." : "Allow popups and try connecting again.");
      return;
    }
    setPending(true);
  }

  return (
    <div className="flex flex-col gap-2 py-2 text-xs sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0" aria-live="polite">
        <p className="font-medium text-slate-700 break-words">{data?.connected ? `${vi ? "Sheets đã kết nối" : "Sheets connected"}: ${data.email}` : (vi ? "Kết nối Google Sheets để đồng bộ chỉnh sửa" : "Connect Google Sheets to sync edits")}</p>
        <p className="mt-1 text-slate-500">{vi ? "Link công khai vẫn đọc được mà không cần kết nối." : "Public links can be read without connecting."}</p>
        {(error || isError) && <p role="alert" className="mt-1 text-red-600">{error || (vi ? "Chưa kiểm tra được kết nối. Bạn có thể thử kết nối lại." : "Unable to check connection. You can reconnect.")}</p>}
      </div>
      <button type="button" onClick={connect} disabled={pending || !userId} className="shrink-0 rounded-lg border border-slate-300 bg-white px-3 py-2 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
        {pending ? (vi ? "Đang kết nối…" : "Connecting…") : data?.connected ? (vi ? "Kết nối lại Sheets" : "Reconnect Sheets") : (vi ? "Kết nối Google Sheets" : "Connect Google Sheets")}
      </button>
    </div>
  );
}
