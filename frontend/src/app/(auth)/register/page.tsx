"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { useAuth } from "@/providers/AuthProvider";
import { authService } from "@/services/api";
import { ParticlesBackground } from "@/components/3d/Particles";
import { Brain, Eye, EyeOff, Loader2, User as UserIcon, GraduationCap } from "lucide-react";
import toast from "react-hot-toast";

const registerSchema = zod.object({
  full_name: zod.string().min(2, "Full name must be at least 2 characters long"),
  email: zod.string().email("Please enter a valid email address"),
  password: zod
    .string()
    .min(8, "Password must be at least 8 characters long")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[0-9]/, "Password must contain at least one number")
    .regex(/[^a-zA-Z0-9]/, "Password must contain at least one special character"),
  role: zod.enum(["student", "teacher"]),
});

type RegisterForm = zod.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { login: handleLoginState } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    control,
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      role: "student",
    },
  });

  const selectedRole = useWatch({ control, name: "role", defaultValue: "student" });

  const onSubmit = async (data: RegisterForm) => {
    setIsSubmitting(true);
    try {
      // Register
      await authService.register(data);
      toast.success("Account created successfully!");
      
      // Auto Login
      const loginRes = await authService.login({
        email: data.email,
        password: data.password,
      });
      await handleLoginState(loginRes.access_token, loginRes.refresh_token);
    } catch (err: any) {

      const msg = err.response?.data?.message || "Registration failed. Try a different email.";
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
        <Link href="/" className="flex items-center justify-center gap-2 mb-6 group">
          <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-2.5 rounded-2xl flex items-center justify-center transition group-hover:scale-105">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <span className="bg-gradient-to-r from-white to-purple-400 bg-clip-text text-transparent font-extrabold text-xl tracking-wider">
            AI-LMS
          </span>
        </Link>

        <div className="glass-card rounded-3xl p-8 border border-zinc-800/80">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">Create Account</h2>
            <p className="text-sm text-zinc-400">Join our advanced learning platform</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            
            {/* Role Selection */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">I want to learn / teach</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setValue("role", "student")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border text-sm font-semibold transition ${
                    selectedRole === "student"
                      ? "bg-purple-950/30 text-purple-300 border-purple-500/35"
                      : "bg-zinc-950/45 text-zinc-400 border-zinc-800 hover:border-zinc-700"
                  }`}
                >
                  <GraduationCap className="w-4 h-4" />
                  Student
                </button>
                <button
                  type="button"
                  onClick={() => setValue("role", "teacher")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border text-sm font-semibold transition ${
                    selectedRole === "teacher"
                      ? "bg-purple-950/30 text-purple-300 border-purple-500/35"
                      : "bg-zinc-950/45 text-zinc-400 border-zinc-800 hover:border-zinc-700"
                  }`}
                >
                  <UserIcon className="w-4 h-4" />
                  Teacher
                </button>
              </div>
            </div>

            {/* Full Name */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Full Name</label>
              <input
                type="text"
                placeholder="Jane Doe"
                {...register("full_name")}
                className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 hover:border-zinc-700/80 text-white rounded-xl px-4 py-3 text-sm focus:outline-none transition-colors"
              />
              {errors.full_name && (
                <span className="text-xs text-red-400 font-semibold">{errors.full_name.message}</span>
              )}
            </div>

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
              <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Password</label>
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
                <span className="text-xs text-red-400 font-semibold leading-relaxed block max-w-sm">
                  {errors.password.message}
                </span>
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
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          <div className="h-px bg-zinc-900 my-6" />

          <p className="text-center text-sm text-zinc-500">
            Already have an account?{" "}
            <Link href="/login" className="text-purple-400 hover:text-purple-300 font-bold transition">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
