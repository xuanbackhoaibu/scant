"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import viMessages from "./messages/vi.json";
import enMessages from "./messages/en.json";

export type Locale = "vi" | "en";

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, variables?: Record<string, string | number>) => string;
}

const dictionaries: Record<Locale, any> = {
  vi: viMessages,
  en: enMessages,
};

const I18nContext = createContext<I18nContextType>({
  locale: "vi",
  setLocale: () => {},
  t: (key: string) => key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("vi");

  useEffect(() => {
    // Read from localStorage on mount
    const saved = localStorage.getItem("app_locale") as Locale | null;
    if (saved && (saved === "vi" || saved === "en")) {
      setLocaleState(saved);
      document.documentElement.lang = saved;
    } else {
      // Check navigator language
      const navLang = navigator.language.startsWith("vi") ? "vi" : "en";
      setLocaleState(navLang);
      document.documentElement.lang = navLang;
    }
  }, []);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem("app_locale", newLocale);
    document.documentElement.lang = newLocale;
  };

  const t = (path: string, variables?: Record<string, string | number>): string => {
    const keys = path.split(".");
    let current: any = dictionaries[locale] || dictionaries["vi"];

    for (const k of keys) {
      if (current && typeof current === "object" && k in current) {
        current = current[k];
      } else {
        // Fallback to English dictionary if key missing in current locale
        let fallback: any = dictionaries["en"];
        for (const fk of keys) {
          if (fallback && typeof fallback === "object" && fk in fallback) {
            fallback = fallback[fk];
          } else {
            return path; // return key as fallback
          }
        }
        current = fallback;
        break;
      }
    }

    if (typeof current !== "string") {
      return path;
    }

    let text = current;
    if (variables) {
      for (const [vKey, vVal] of Object.entries(variables)) {
        text = text.replace(new RegExp(`\\{${vKey}\\}`, "g"), String(vVal));
      }
    }
    return text;
  };

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslation() {
  return useContext(I18nContext);
}
