import { create } from "zustand";
import { api } from "@/lib/api";

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  avatar_url?: string;
  google_sub?: string;
  preferred_locale?: string;
  theme?: string;
  document_language?: string;
  plan: string;
  role?: string;
  is_superuser?: boolean;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("auth_token") : null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const res = await api.auth.login({ email, password });
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_token", res.access_token);
      }
      set({
        user: res.user,
        token: res.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (name, email, password) => {
    set({ isLoading: true });
    try {
      const res = await api.auth.register({ name, email, password });
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_token", res.access_token);
      }
      set({
        user: res.user,
        token: res.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  checkAuth: async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (!token) {
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
      return;
    }
    try {
      const user = await api.auth.me();
      set({ user, token, isAuthenticated: true, isLoading: false });
    } catch {
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
      }
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
