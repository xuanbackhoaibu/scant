"use client";

import { useState, useEffect } from "react";
import { QrCode, Check, Copy, RefreshCw, ShieldCheck, Zap, ArrowRight, Building2, CreditCard } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/useAuthStore";

interface VietQRPaymentModalProps {
  planTier: "pro" | "enterprise";
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function VietQRPaymentModal({ planTier, isOpen, onClose, onSuccess }: VietQRPaymentModalProps) {
  const user = useAuthStore((state) => state.user);
  const setSession = useAuthStore((state) => state.setSession);
  const token = useAuthStore((state) => state.token);

  const [checkoutData, setCheckoutData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isActivating, setIsActivating] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState(900); // 15 mins

  useEffect(() => {
    if (!isOpen) return;

    async function initCheckout() {
      setIsLoading(true);
      try {
        const res = await api.billing.checkout({ plan_tier: planTier });
        setCheckoutData(res);
        setTimeLeft(res.expires_in_seconds || 900);
      } catch (err: any) {
        alert("Lỗi khởi tạo phiên thanh toán: " + err.message);
      } finally {
        setIsLoading(false);
      }
    }

    initCheckout();
  }, [isOpen, planTier]);

  useEffect(() => {
    if (!isOpen || timeLeft <= 0) return;
    const timer = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [isOpen, timeLeft]);

  if (!isOpen) return null;

  const handleCopy = (field: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleConfirm = async () => {
    if (!checkoutData) return;
    setIsActivating(true);
    try {
      const res = await api.billing.confirmPayment({
        session_id: checkoutData.session_id,
        target_plan: planTier,
      });
      if (res.success && user && token) {
        setSession(token, { ...user, plan: planTier });
      }
      alert(`🎉 Chúc mừng! Bạn đã nâng cấp thành công gói ${planTier.toUpperCase()}!`);
      onSuccess?.();
      onClose();
    } catch (err: any) {
      alert("Lỗi xác nhận thanh toán: " + err.message);
    } finally {
      setIsActivating(false);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl border border-slate-200 max-w-xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-emerald-50/50 via-white to-indigo-50/50 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="h-9 w-9 rounded-2xl bg-emerald-600 text-white flex items-center justify-center shadow-md shadow-emerald-100">
              <QrCode className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Thanh toán Nâng Cấp Gói qua VietQR</h3>
              <p className="text-xs text-slate-500">Quét mã QR qua ứng dụng ngân hàng hoặc MoMo/ViettelMoney</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-sm font-bold px-2 py-1 rounded-lg hover:bg-slate-100">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {isLoading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-3 text-emerald-600">
              <RefreshCw className="h-8 w-8 animate-spin" />
              <p className="text-xs font-semibold text-slate-600">Đang tạo mã VietQR động NAPAS 24/7...</p>
            </div>
          ) : checkoutData ? (
            <>
              {/* Plan Info Card */}
              <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white flex items-center justify-between shadow-lg shadow-emerald-200">
                <div>
                  <span className="text-[10px] font-extrabold uppercase tracking-wider bg-white/20 px-2 py-0.5 rounded-full">
                    {checkoutData.plan_name}
                  </span>
                  <div className="text-xl font-black mt-1">{checkoutData.formatted_amount}</div>
                  <p className="text-[11px] text-emerald-100 mt-0.5">{checkoutData.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-emerald-100 font-medium">Hết hạn sau</div>
                  <div className="text-base font-mono font-bold">{formatTime(timeLeft)}</div>
                </div>
              </div>

              {/* QR Image + Bank Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                {/* QR Code Container */}
                <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-2xl border border-slate-200">
                  <div className="bg-white p-2.5 rounded-xl shadow-sm border border-slate-200">
                    <img
                      src={checkoutData.qr_code_url}
                      alt="VietQR Payment Code"
                      className="w-48 h-48 object-contain rounded-lg"
                    />
                  </div>
                  <div className="flex items-center space-x-1 text-[11px] text-slate-500 mt-2 font-medium">
                    <Zap className="h-3.5 w-3.5 text-amber-500" />
                    <span>Tự động điền số tiền & nội dung</span>
                  </div>
                </div>

                {/* Transfer Info */}
                <div className="space-y-2.5 text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                    <div className="text-[10px] font-bold text-slate-400 uppercase">Ngân hàng thụ hưởng</div>
                    <div className="font-bold text-slate-800 mt-0.5">{checkoutData.bank_name}</div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase">Số tài khoản</div>
                      <div className="font-mono font-bold text-slate-900 text-sm mt-0.5">{checkoutData.account_number}</div>
                    </div>
                    <button
                      onClick={() => handleCopy("acc", checkoutData.account_number)}
                      className="p-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-600 transition"
                    >
                      {copiedField === "acc" ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] font-bold text-slate-400 uppercase">Nội dung chuyển khoản (bắt buộc)</div>
                      <div className="font-mono font-bold text-emerald-700 text-xs mt-0.5">{checkoutData.transfer_content}</div>
                    </div>
                    <button
                      onClick={() => handleCopy("content", checkoutData.transfer_content)}
                      className="p-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-100 text-slate-600 transition"
                    >
                      {copiedField === "content" ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <button onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 rounded-xl">
            Để sau
          </button>
          <button
            onClick={handleConfirm}
            disabled={isActivating}
            className="flex items-center space-x-1.5 px-5 py-2.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl shadow-md shadow-emerald-200 transition"
          >
            {isActivating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            <span>Tôi đã hoàn tất chuyển khoản</span>
          </button>
        </div>
      </div>
    </div>
  );
}
