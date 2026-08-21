"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileText, ArrowRight, Lock, Mail, User, AlertCircle, Languages } from "lucide-react";
import { useAuthStore } from "@/stores/useAuthStore";
import { useTranslation, Locale } from "@/i18n/I18nContext";

export default function RegisterPage() {
  const { t, locale, setLocale } = useTranslation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const register = useAuthStore((state) => state.register);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await register(name, email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || t("auth.registerFailed"));
    } finally {
      setLoading(false);
    }
  };

  const toggleLanguage = () => {
    const next: Locale = locale === "vi" ? "en" : "vi";
    setLocale(next);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4 relative">
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:text-indigo-600 rounded-lg shadow-2xs transition-colors"
        >
          <Languages className="h-3.5 w-3.5" />
          <span className="uppercase">{locale}</span>
        </button>
      </div>

      <div className="w-full max-w-md bg-white rounded-3xl border border-slate-200 shadow-sm p-8 space-y-6">
        <div className="flex flex-col items-center text-center">
          <div className="h-12 w-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-md mb-3">
            <FileText className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-bold text-slate-900">{t("auth.createAccount")}</h1>
          <p className="text-xs text-slate-500 mt-1">{t("auth.registerSubtitle")}</p>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">{t("auth.nameLabel")}</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("auth.namePlaceholder")}
                className="w-full h-10 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-500 outline-none transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">{t("auth.emailLabel")}</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t("auth.emailPlaceholder")}
                className="w-full h-10 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-500 outline-none transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">{t("auth.passwordLabel")}</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("auth.passwordPlaceholder")}
                className="w-full h-10 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-indigo-500 outline-none transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full h-10 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
          >
            {loading ? t("auth.signingUp") : t("auth.signUp")}
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </form>

        <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
          {t("auth.alreadyHaveAccount")}{" "}
          <Link href="/login" className="font-bold text-indigo-600 hover:text-indigo-700">
            {t("auth.signIn")}
          </Link>
        </div>
      </div>
    </div>
  );
}
