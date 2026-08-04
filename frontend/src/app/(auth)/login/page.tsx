"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { useAuth } from "@/providers/AuthProvider";
import { authService } from "@/services/api";
import { ParticlesBackground } from "@/components/3d/Particles";
import { Brain, Eye, EyeOff, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

const loginSchema = zod.object({
  email: zod.string().email("Please enter a valid email address"),
  password: zod.string().min(6, "Password must be at least 6 characters long"),
});

type LoginForm = zod.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login: handleLoginState } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setIsSubmitting(true);
    try {
      const res = await authService.login(data);
      await handleLoginState(res.access_token, res.refresh_token);
    } catch (err: any) {
      console.error(err);
      const msg = err.response?.data?.message || "Invalid email or password.";
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative px-4 py-12">
      {/* 3D background */}
      <ParticlesBackground />

      <div className="w-full max-w-md relative z-10">
        <Link href="/" className="flex items-center justify-center gap-2 mb-8 group">
          <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-2.5 rounded-2xl flex items-center justify-center transition group-hover:scale-105">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <span className="bg-gradient-to-r from-white to-purple-400 bg-clip-text text-transparent font-extrabold text-xl tracking-wider">
            AI-LMS
          </span>
        </Link>

        <div className="glass-card rounded-3xl p-8 border border-zinc-800/80">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">Welcome Back</h2>
            <p className="text-sm text-zinc-400">Sign in to your learning dashboard</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            {/* Email */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Email Address</label>
              <input
                type="email"
                placeholder="you@example.com"
                {...register("email")}
                className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 hover:border-zinc-700/80 text-white rounded-xl px-4 py-3 text-sm focus:outline-none transition-colors"
              />
              {errors.email && (
                <span className="text-xs text-red-400 font-semibold">{errors.email.message}</span>
              )}
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Password</label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-purple-400 hover:text-purple-300 font-semibold transition"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  {...register("password")}
                  className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 hover:border-zinc-700/80 text-white rounded-xl pl-4 pr-11 py-3 text-sm focus:outline-none transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <span className="text-xs text-red-400 font-semibold">{errors.password.message}</span>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="glow-btn mt-2 w-full bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-semibold py-3.5 rounded-xl flex items-center justify-center gap-2 shadow-lg hover:shadow-purple-500/10 transition-all cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Logging in...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="h-px bg-zinc-900 my-6" />

          <p className="text-center text-sm text-zinc-500">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-purple-400 hover:text-purple-300 font-bold transition">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
