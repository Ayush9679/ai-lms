"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { useAuth } from "@/providers/AuthProvider";
import { authService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PageTransition } from "@/components/shared/PageTransitions";
import { User, Eye, EyeOff, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

// Schema for profile details
const profileSchema = zod.object({
  full_name: zod.string().min(2, "Full name must be at least 2 characters long"),
  bio: zod.string().max(300, "Bio cannot exceed 300 characters").nullable().optional(),
});

type ProfileForm = zod.infer<typeof profileSchema>;

// Schema for password changes
const passwordSchema = zod
  .object({
    current_password: zod.string().min(6, "Current password is required"),
    new_password: zod
      .string()
      .min(8, "New password must be at least 8 characters long")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirm_password: zod.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type PasswordForm = zod.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [isSavingDetails, setIsSavingDetails] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  const {
    register: registerDetails,
    handleSubmit: handleSubmitDetails,
    formState: { errors: detailsErrors },
  } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name || "",
      bio: user?.bio || "",
    },
  });

  const {
    register: registerPassword,
    handleSubmit: handleSubmitPassword,
    reset: resetPasswordForm,
    formState: { errors: passwordErrors },
  } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  });

  const onSubmitDetails = async (data: ProfileForm) => {
    setIsSavingDetails(true);
    try {
      // Assuming a generic patch endpoint, or we can use custom axios updates
      const { apiClient } = await import("@/lib/api-client");
      await apiClient.patch(`/users/me`, data);
      await refreshUser();
      toast.success("Profile details updated successfully!");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to update profile details.");
    } finally {
      setIsSavingDetails(false);
    }
  };

  const onSubmitPassword = async (data: PasswordForm) => {
    setIsChangingPassword(true);
    try {
      await authService.changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      });
      toast.success("Password changed successfully!");
      resetPasswordForm();
    } catch (err: any) {
      console.error(err);
      const msg = err.response?.data?.message || "Incorrect current password.";
      toast.error(msg);
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (!user) return null;

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="max-w-4xl mx-auto flex flex-col gap-8 text-left">
          <div>
            <h1 className="text-3xl font-extrabold text-white">Profile Workspace</h1>
            <p className="text-zinc-400 text-sm mt-1">Manage your public bio, credentials, and password security.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            
            {/* Left profile image card */}
            <div className="glass-card rounded-3xl p-6 flex flex-col items-center gap-4 text-center">
              {user.profile_image ? (
                <img
                  src={user.profile_image}
                  alt={user.full_name}
                  className="w-24 h-24 rounded-full object-cover border-2 border-purple-500/20"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-purple-600 flex items-center justify-center text-3xl font-bold text-white border-2 border-purple-500/20">
                  {user.full_name[0].toUpperCase()}
                </div>
              )}
              <div>
                <h3 className="text-lg font-bold text-white leading-snug">{user.full_name}</h3>
                <p className="text-xs text-zinc-500 capitalize mt-1 font-semibold">{user.role}</p>
              </div>
              <p className="text-xs text-zinc-400 italic">
                {user.bio || "No biography added yet."}
              </p>
            </div>

            {/* Right profile forms */}
            <div className="md:col-span-2 flex flex-col gap-6">
              
              {/* Profile Details Form */}
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                <h3 className="text-base font-bold text-white">Public Bio</h3>
                <form onSubmit={handleSubmitDetails(onSubmitDetails)} className="flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Full Name</label>
                    <input
                      type="text"
                      {...registerDetails("full_name")}
                      className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                    />
                    {detailsErrors.full_name && (
                      <span className="text-xs text-red-400 font-semibold">{detailsErrors.full_name.message}</span>
                    )}
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Biography</label>
                    <textarea
                      rows={3}
                      placeholder="Share a little bit about your learning journey..."
                      {...registerDetails("bio")}
                      className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
                    />
                    {detailsErrors.bio && (
                      <span className="text-xs text-red-400 font-semibold">{detailsErrors.bio.message}</span>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={isSavingDetails}
                    className="glow-btn py-3 px-5 text-sm font-semibold bg-zinc-900 border border-zinc-850 hover:border-zinc-700 text-white rounded-xl shadow-md transition w-fit flex items-center gap-2 cursor-pointer"
                  >
                    {isSavingDetails && <Loader2 className="w-4 h-4 animate-spin" />}
                    Save Changes
                  </button>
                </form>
              </div>

              {/* Password Form */}
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                <h3 className="text-base font-bold text-white">Security Settings</h3>
                <form onSubmit={handleSubmitPassword(onSubmitPassword)} className="flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Current Password</label>
                    <div className="relative">
                      <input
                        type={showCurrentPassword ? "text" : "password"}
                        placeholder="••••••••"
                        {...registerPassword("current_password")}
                        className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-xl pl-4 pr-11 py-3 text-sm focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition"
                      >
                        {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {passwordErrors.current_password && (
                      <span className="text-xs text-red-400 font-semibold">{passwordErrors.current_password.message}</span>
                    )}
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">New Password</label>
                    <div className="relative">
                      <input
                        type={showNewPassword ? "text" : "password"}
                        placeholder="••••••••"
                        {...registerPassword("new_password")}
                        className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-xl pl-4 pr-11 py-3 text-sm focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition"
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {passwordErrors.new_password && (
                      <span className="text-xs text-red-400 font-semibold leading-normal block max-w-sm">
                        {passwordErrors.new_password.message}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Confirm New Password</label>
                    <input
                      type="password"
                      placeholder="••••••••"
                      {...registerPassword("confirm_password")}
                      className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                    />
                    {passwordErrors.confirm_password && (
                      <span className="text-xs text-red-400 font-semibold">{passwordErrors.confirm_password.message}</span>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={isChangingPassword}
                    className="glow-btn py-3 px-5 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-md transition w-fit flex items-center gap-2 cursor-pointer"
                  >
                    {isChangingPassword && <Loader2 className="w-4 h-4 animate-spin" />}
                    Update Password
                  </button>
                </form>
              </div>

            </div>

          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
