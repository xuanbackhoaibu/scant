"use client";

import { useState, useEffect, useRef } from "react";
import { ExternalLink, RefreshCw, CreditCard } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/useAuthStore";

interface VietQRPaymentModalProps {
  planTier: "pro" | "enterprise";
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}
interface Checkout {
  session_id: string;
  target_plan: string;
  amount_vnd: number;
  currency: string;
  checkout_url: string;
}

export function VietQRPaymentModal({ planTier, isOpen, onClose, onSuccess }: VietQRPaymentModalProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const checkAuth = useAuthStore(state => state.checkAuth);
  const [checkout, setCheckout] = useState<Checkout | null>(null);
  const [loading, setLoading] = useState(false);
  const [activating, setActivating] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const pendingCheckout = useRef<{key:string;promise:Promise<Checkout>} | null>(null);

  useEffect(() => {
    if (isOpen) dialog.current?.showModal(); else dialog.current?.close();
  }, [isOpen]);
  useEffect(() => {
    if (!isOpen) { pendingCheckout.current = null; return; }
    let active = true;
    const key = `${planTier}:${attempt}`;
    setCheckout(null); setLoading(true); setError("");
    if (pendingCheckout.current?.key !== key) {
      pendingCheckout.current = {key,promise:api.billing.checkout({plan_tier:planTier,success_url:`${location.origin}/settings?billing=success`,cancel_url:`${location.origin}/settings?billing=cancelled`})};
    }
    pendingCheckout.current.promise.then(result => {if(active)setCheckout(result);})
      .catch(error => {if(active)setError(error instanceof Error ? error.message : "Không tạo được phiên thanh toán.");})
      .finally(() => {if(active)setLoading(false);});
    return () => {active=false;};
  }, [isOpen,planTier,attempt]);

  async function confirm() {
    if (!checkout || activating) return;
    setActivating(true); setError("");
    try {
      const result = await api.billing.confirmPayment({session_id:checkout.session_id,target_plan:checkout.target_plan});
      if (!result.success) throw new Error("Nhà cung cấp chưa xác nhận thanh toán.");
      await checkAuth();
      onSuccess?.(); onClose();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Chưa xác nhận được thanh toán. Vui lòng thử lại.");
    } finally {setActivating(false);}
  }

  return <dialog ref={dialog} onCancel={event => {if(activating)event.preventDefault();else onClose();}} aria-labelledby="payment-title" className="m-auto w-[calc(100%-2rem)] max-w-lg rounded-xl border border-border bg-card p-6 text-foreground shadow-xl backdrop:bg-black/50">
    <div className="flex items-start justify-between gap-4"><div><CreditCard className="mb-3 h-6 w-6 text-primary"/><h2 id="payment-title" className="text-lg font-semibold">Nâng cấp gói {planTier.toUpperCase()}</h2><p className="mt-1 text-sm text-muted-foreground">Thanh toán qua trang PayOS và kiểm tra kết quả tại đây.</p></div><button aria-label="Đóng thanh toán" disabled={activating} onClick={onClose} className="rounded p-2">×</button></div>
    {loading ? <p role="status" className="flex items-center gap-2 py-8"><RefreshCw className="h-4 w-4 animate-spin"/>Đang tạo phiên thanh toán…</p> : checkout ? <div className="my-6 space-y-4"><p className="text-2xl font-semibold">{new Intl.NumberFormat('vi-VN',{style:'currency',currency:checkout.currency}).format(checkout.amount_vnd)}</p><p className="text-sm text-muted-foreground">Trang thanh toán cung cấp mã QR, ngân hàng thụ hưởng và thời hạn của phiên.</p><a href={checkout.checkout_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-primary-foreground">Mở trang thanh toán<ExternalLink className="h-4 w-4"/></a></div> : null}
    {error && <p role="alert" className="my-4 rounded-md border border-destructive/30 p-3 text-sm text-destructive">{error}</p>}
    <div className="mt-6 flex flex-wrap justify-end gap-3"><button disabled={activating} onClick={onClose} className="rounded-md border px-4 py-2">Để sau</button>{!loading && !checkout ? <button onClick={()=>setAttempt(value=>value+1)} className="rounded-md border px-4 py-2">Thử lại</button> : <button disabled={!checkout || loading || activating} onClick={confirm} className="rounded-md bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">{activating ? "Đang xác minh…" : "Kiểm tra thanh toán"}</button>}</div>
  </dialog>;
}
