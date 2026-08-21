"use client";

import { useState, useEffect } from "react";
import { Settings, Cpu, ShieldCheck, Key, Save, Check, User, Globe, Moon, Sun, Monitor, AlertCircle } from "lucide-react";
import { useTranslation, Locale } from "@/i18n/I18nContext";
import { useAuthStore } from "@/stores/useAuthStore";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const { t, locale, setLocale } = useTranslation();
  const { user } = useAuthStore();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState("profile");

  // Profile Form
  const [fullName, setFullName] = useState(user?.name || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar || "");
  const [docLang, setDocLang] = useState("vi");
  const [themeMode, setThemeMode] = useState("system");

  // AI Form
  const [provider, setProvider] = useState("gemini");
  const [model, setModel] = useState("gemini-2.5-flash");

  // Password Form
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [changingPass, setChangingPass] = useState(false);

  // Linked accounts
  const [linkedAccounts, setLinkedAccounts] = useState<any[]>([]);

  useEffect(() => {
    if (user) {
      setFullName(user.name);
      setAvatarUrl(user.avatar || "");
    }

    async function loadAccounts() {
      try {
        const token = localStorage.getItem("auth_token");
        if (token) {
          const accs = await fetch("http://localhost:8050/api/v1/auth/accounts", {
            headers: { Authorization: `Bearer ${token}` }
          }).then((r) => r.json());
          if (Array.isArray(accs)) setLinkedAccounts(accs);
        }
      } catch {}
    }
    loadAccounts();
  }, [user]);

  const handleSaveProfile = async () => {
    try {
      const token = localStorage.getItem("auth_token");
      const res = await fetch("http://localhost:8050/api/v1/auth/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: fullName,
          avatar_url: avatarUrl,
          preferred_locale: locale,
          theme: themeMode,
          document_language: docLang,
        })
      });

      if (!res.ok) throw new Error("Update failed");
      toast.success(t("common.saved"));
    } catch {
      toast.error(t("common.errorOccurred"));
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setChangingPass(true);
    try {
      const token = localStorage.getItem("auth_token");
      const res = await fetch("http://localhost:8050/api/v1/auth/change-password", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Password change failed");
      }
      toast.success("Mật khẩu đã được thay đổi thành công");
      setOldPassword("");
      setNewPassword("");
    } catch (err: any) {
      toast.error(err.message || t("common.errorOccurred"));
    } finally {
      setChangingPass(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl py-2">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{t("settings.title")}</h1>
        <p className="text-xs text-slate-500">{t("settings.subtitle")}</p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-200 pb-2 text-xs font-semibold">
        {[
          { key: "profile", label: t("settings.profileTab"), icon: User },
          { key: "language", label: t("settings.languageTab"), icon: Globe },
          { key: "ai", label: t("settings.aiTab"), icon: Cpu },
          { key: "security", label: t("settings.securityTab"), icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
                activeTab === tab.key
                  ? "bg-indigo-50 text-indigo-700 font-bold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Profile & Appearance Tab */}
      {activeTab === "profile" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-5 text-xs">
          <h3 className="font-bold text-slate-900 text-sm">{t("settings.profileTab")}</h3>
          <div className="space-y-4 max-w-md">
            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.fullName")}</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none focus:bg-white focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.avatarUrl")}</label>
              <input
                type="text"
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://example.com/avatar.png"
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none focus:bg-white focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.theme")}</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: "light", label: t("settings.themeLight"), icon: Sun },
                  { key: "dark", label: t("settings.themeDark"), icon: Moon },
                  { key: "system", label: t("settings.themeSystem"), icon: Monitor },
                ].map((th) => {
                  const Icon = th.icon;
                  return (
                    <button
                      key={th.key}
                      type="button"
                      onClick={() => setThemeMode(th.key)}
                      className={`flex items-center justify-center gap-1.5 p-2 rounded-lg border text-xs font-semibold transition-all ${
                        themeMode === th.key
                          ? "border-indigo-600 bg-indigo-50/50 text-indigo-700 shadow-2xs"
                          : "border-slate-200 text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      <span>{th.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <button
              onClick={handleSaveProfile}
              className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-xs transition-colors"
            >
              <Save className="h-3.5 w-3.5" />
              <span>{t("common.save")}</span>
            </button>
          </div>
        </div>
      )}

      {/* Language Tab */}
      {activeTab === "language" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-5 text-xs">
          <h3 className="font-bold text-slate-900 text-sm">{t("settings.languageTab")}</h3>
          <div className="space-y-4 max-w-md">
            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.uiLanguage")}</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setLocale("vi")}
                  className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                    locale === "vi"
                      ? "border-indigo-600 bg-indigo-50/50 text-indigo-700 shadow-2xs"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <span className="block font-bold">🇻🇳 Tiếng Việt</span>
                  <span className="text-[10px] text-slate-400 font-normal">Vietnamese Interface</span>
                </button>
                <button
                  type="button"
                  onClick={() => setLocale("en")}
                  className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                    locale === "en"
                      ? "border-indigo-600 bg-indigo-50/50 text-indigo-700 shadow-2xs"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <span className="block font-bold">🇬🇧 English</span>
                  <span className="text-[10px] text-slate-400 font-normal">English Interface</span>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.documentLanguage")}</label>
              <select
                value={docLang}
                onChange={(e) => setDocLang(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
              >
                <option value="vi">Tiếng Việt (Mặc định)</option>
                <option value="en">English (US/UK Standard)</option>
                <option value="auto">Tự động nhận diện (Auto Detect)</option>
              </select>
            </div>

            <button
              onClick={handleSaveProfile}
              className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-xs transition-colors"
            >
              <Save className="h-3.5 w-3.5" />
              <span>{t("common.save")}</span>
            </button>
          </div>
        </div>
      )}

      {/* AI Tab */}
      {activeTab === "ai" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-5 text-xs">
          <h3 className="font-bold text-slate-900 text-sm">{t("settings.aiTab")}</h3>
          <div className="space-y-4 max-w-md">
            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.aiProvider")}</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
              >
                <option value="gemini">Google Gemini 2.5 (Khuyên dùng)</option>
                <option value="openai">OpenAI (GPT-4o / O3-Mini)</option>
                <option value="anthropic">Anthropic Claude (Sonnet 3.7)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.aiModel")}</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
              />
            </div>

            <button
              onClick={() => toast.success(t("common.saved"))}
              className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-xs transition-colors"
            >
              <Save className="h-3.5 w-3.5" />
              <span>{t("common.save")}</span>
            </button>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === "security" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-6 text-xs">
          <h3 className="font-bold text-slate-900 text-sm">{t("settings.securityTab")}</h3>

          {/* Linked Accounts */}
          <div className="space-y-2">
            <h4 className="font-semibold text-slate-800">{t("settings.linkedAccounts")}</h4>
            <div className="p-3 rounded-xl border border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold">Google</span>
                <span className="text-slate-500">{user?.google_sub ? user.email : t("settings.googleNotLinked")}</span>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${user?.google_sub ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                {user?.google_sub ? t("settings.googleLinked") : t("settings.googleNotLinked")}
              </span>
            </div>
          </div>

          {/* Change Password */}
          <form onSubmit={handleChangePassword} className="space-y-3 max-w-md pt-2 border-t border-slate-100">
            <h4 className="font-semibold text-slate-800">{t("settings.changePassword")}</h4>
            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.currentPassword")}</label>
              <input
                type="password"
                required
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-medium mb-1">{t("settings.newPassword")}</label>
              <input
                type="password"
                required
                minLength={6}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full h-9 px-3 bg-slate-50 border border-slate-200 rounded-lg outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={changingPass}
              className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold shadow-xs transition-colors"
            >
              <Key className="h-3.5 w-3.5" />
              <span>{changingPass ? "Đang xử lý..." : t("settings.changePassword")}</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
