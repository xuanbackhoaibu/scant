"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect, useState } from "react";
import { useAuthStore } from "@/stores/useAuthStore";
import { I18nProvider } from "@/i18n/I18nContext";
import { ToastProvider } from "@/components/Toast";
import { MotionWrapper } from "@/components/MotionWrapper";
import { ThemeProvider, useTheme } from "next-themes";

function ThemePreferenceBridge() {
  const userTheme = useAuthStore((state) => state.user?.theme);
  const { setTheme } = useTheme();

  useEffect(() => {
    const storedTheme = localStorage.getItem("theme_mode");
    if (!storedTheme && userTheme) setTheme(userTheme);
  }, [setTheme, userTheme]);

  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: false,
      },
    },
  }));

  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem storageKey="theme_mode" disableTransitionOnChange>
      <ThemePreferenceBridge />
      <I18nProvider>
        <ToastProvider>
          <QueryClientProvider client={queryClient}>
            <MotionWrapper>{children}</MotionWrapper>
          </QueryClientProvider>
        </ToastProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}
