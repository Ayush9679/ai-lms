"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User, UserRole } from "@/types";
import { authService } from "@/services/api";
import { clearTokens, getAccessToken } from "@/lib/api-client";
import toast from "react-hot-toast";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const redirectUser = useCallback((role: UserRole) => {
    if (role === "student") {
      router.push("/dashboard/student");
    } else if (role === "teacher") {
      router.push("/dashboard/teacher");
    } else if (role === "admin") {
      router.push("/dashboard/admin");
    }
  }, [router]);

  const fetchUser = async () => {
    try {
      const u = await authService.getMe();
      setUser(u);
    } catch (err) {
      console.error("Failed to fetch user profile:", err);
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = getAccessToken();
    const timer = setTimeout(() => {
      if (token) {
        fetchUser();
      } else {
        setIsLoading(false);
        setUser(null);
      }
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  // Protected route checking
  useEffect(() => {
    if (isLoading) return;

    const token = getAccessToken();
    const isAuthRoute = ["/login", "/register", "/forgot-password"].includes(pathname);
    const isDashboardRoute = pathname.startsWith("/dashboard") || pathname.startsWith("/ai") || pathname.includes("/lessons/");

    if (!token && isDashboardRoute) {
      toast.error("Please login to access this area.");
      router.push("/login");
    } else if (token && isAuthRoute) {
      // Redirect authenticated users away from auth pages to their dashboard
      if (user) {
        redirectUser(user.role);
      }
    }
  }, [pathname, user, isLoading, redirectUser, router]);

  const login = async (accessToken: string, refreshToken: string) => {
    setIsLoading(true);
    try {
      const u = await authService.getMe();
      setUser(u);
      toast.success(`Welcome back, ${u.full_name}!`);
      redirectUser(u.role);
    } catch (err) {
      toast.error("Login failed. Please try again.");
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    toast.success("Logged out successfully.");
    router.push("/");
  };

  const refreshUser = async () => {
    try {
      const u = await authService.getMe();
      setUser(u);
    } catch (err) {
      console.error("Error refreshing user:", err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
        refreshUser,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
