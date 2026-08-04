"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { authService } from "@/services/api";
import { ParticlesBackground } from "@/components/3d/Particles";
import { Brain, ArrowLeft, Loader2, CheckCircle2 } from "lucide-react";
import toast from "react-hot-toast";

const forgotSchema = zod.object({
  email: zod.string().email("Please enter a valid email address"),
});

type ForgotForm = zod.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotForm>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (data: ForgotForm) => {
    setIsSubmitting(true);
    try {
      await authService.forgotPassword(data.email);
      setIsSuccess(true);
      toast.success("Reset email sent if the account exists!");
    } catch (err: any) {
      console.error(err);
      toast.error("An error occurred. Please try again.");
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
          {isSuccess ? (
            <div className="text-center flex flex-col items-center gap-4">
              <CheckCircle2 className="w-12 h-12 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">Check Your Email</h2>
              <p className="text-sm text-zinc-400 leading-relaxed max-w-xs">
                We have sent password reset instructions to your email address if it is registered on our platform.
              </p>
              <Link
                href="/login"
                className="w-full mt-4 flex items-center justify-center gap-2 text-sm bg-zinc-900 border border-zinc-800 text-white font-semibold py-3 rounded-xl hover:bg-zinc-800 hover:border-zinc-700 transition cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-white mb-2">Forgot Password</h2>
                <p className="text-sm text-zinc-400">Enter email to receive instructions</p>
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

                {/* Submit */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="glow-btn mt-2 w-full bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-semibold py-3.5 rounded-xl flex items-center justify-center gap-2 shadow-lg hover:shadow-purple-500/10 transition-all cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Sending instructions...
                    </>
                  ) : (
                    "Send Reset Link"
                  )}
                </button>
              </form>

              <div className="h-px bg-zinc-900 my-6" />

              <Link
                href="/login"
                className="flex items-center justify-center gap-2 text-sm text-zinc-400 hover:text-white transition font-medium"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
