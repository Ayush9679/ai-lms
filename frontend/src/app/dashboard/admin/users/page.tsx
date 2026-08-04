"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { userService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  Users,
  GraduationCap,
  BookOpen,
  ShieldCheck,
  Search,
  Trash2,
  Loader2,
  CheckCircle2,
  XCircle,
  RefreshCcw,
} from "lucide-react";
import toast from "react-hot-toast";
import { User } from "@/types";

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  student: { label: "Student", color: "text-blue-400 border-blue-500/20 bg-blue-950/20" },
  teacher: { label: "Teacher", color: "text-purple-400 border-purple-500/20 bg-purple-950/20" },
  admin: { label: "Admin", color: "text-red-400 border-red-500/20 bg-red-950/20" },
};

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["adminUsers", roleFilter],
    queryFn: () => userService.listAll({ role: roleFilter !== "all" ? roleFilter : undefined, page_size: 100 }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => userService.adminDelete(id),
    onSuccess: () => {
      toast.success("User deleted.");
      setDeletingId(null);
      queryClient.invalidateQueries({ queryKey: ["adminUsers"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
    },
    onError: () => {
      toast.error("Failed to delete user.");
      setDeletingId(null);
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      userService.adminUpdate(id, { is_active }),
    onSuccess: (updated) => {
      toast.success(`User ${updated.is_active ? "activated" : "deactivated"}.`);
      queryClient.invalidateQueries({ queryKey: ["adminUsers"] });
    },
    onError: () => toast.error("Failed to update user status."),
  });

  const handleDelete = (user: User) => {
    if (!confirm(`Permanently delete ${user.full_name}? This cannot be undone.`)) return;
    setDeletingId(user.id);
    deleteMutation.mutate(user.id);
  };

  const filtered = data?.items.filter((u) =>
    !search ||
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  ) ?? [];

  const totalStudents = data?.items.filter((u) => u.role === "student").length ?? 0;
  const totalTeachers = data?.items.filter((u) => u.role === "teacher").length ?? 0;
  const totalAdmins = data?.items.filter((u) => u.role === "admin").length ?? 0;

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold text-white">Users Directory</h1>
              <p className="text-zinc-400 text-sm mt-1">Manage all platform accounts, roles, and permissions.</p>
            </div>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-2 py-2.5 px-4 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-sm font-semibold text-zinc-300 hover:text-white rounded-xl transition w-fit"
            >
              <RefreshCcw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-blue-950/40 border border-blue-500/10">
                <GraduationCap className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{totalStudents}</p>
                <p className="text-xs text-zinc-500">Students</p>
              </div>
            </div>
            <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-purple-950/40 border border-purple-500/10">
                <BookOpen className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{totalTeachers}</p>
                <p className="text-xs text-zinc-500">Teachers</p>
              </div>
            </div>
            <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-red-950/40 border border-red-500/10">
                <ShieldCheck className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{totalAdmins}</p>
                <p className="text-xs text-zinc-500">Admins</p>
              </div>
            </div>
          </div>

          {/* Search + Filter Controls */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="text"
                placeholder="Search by name or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl pl-11 pr-4 py-3 text-sm focus:outline-none transition"
              />
            </div>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none transition shrink-0"
            >
              <option value="all">All Roles</option>
              <option value="student">Students</option>
              <option value="teacher">Teachers</option>
              <option value="admin">Admins</option>
            </select>
          </div>

          {/* Users Table */}
          {isLoading ? (
            <TableSkeleton />
          ) : filtered.length > 0 ? (
            <div className="glass-card rounded-3xl p-6 overflow-hidden">
              <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800/80 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                      <th className="py-3.5 px-3">User</th>
                      <th className="py-3.5 px-3 text-center">Role</th>
                      <th className="py-3.5 px-3 text-center">Status</th>
                      <th className="py-3.5 px-3 text-center">Verified</th>
                      <th className="py-3.5 px-3 text-center">Joined</th>
                      <th className="py-3.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((user) => {
                      const roleMeta = ROLE_LABELS[user.role] ?? { label: user.role, color: "text-zinc-400 border-zinc-700 bg-zinc-900" };
                      return (
                        <tr
                          key={user.id}
                          className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-950/20"
                        >
                          {/* User Info */}
                          <td className="py-4 px-3">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center text-white text-xs font-extrabold uppercase shrink-0">
                                {user.full_name?.[0] ?? "?"}
                              </div>
                              <div>
                                <p className="text-sm font-bold text-white">{user.full_name}</p>
                                <p className="text-[11px] text-zinc-500">{user.email}</p>
                              </div>
                            </div>
                          </td>

                          {/* Role */}
                          <td className="py-4 px-3 text-center">
                            <span className={`inline-flex items-center text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${roleMeta.color}`}>
                              {roleMeta.label}
                            </span>
                          </td>

                          {/* Active Status */}
                          <td className="py-4 px-3 text-center">
                            <span
                              className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${
                                user.is_active
                                  ? "text-green-400 border-green-500/20 bg-green-950/20"
                                  : "text-red-400 border-red-500/20 bg-red-950/20"
                              }`}
                            >
                              {user.is_active ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                              {user.is_active ? "Active" : "Inactive"}
                            </span>
                          </td>

                          {/* Verified */}
                          <td className="py-4 px-3 text-center">
                            {user.is_verified ? (
                              <CheckCircle2 className="w-4 h-4 text-green-400 mx-auto" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-400 mx-auto" />
                            )}
                          </td>

                          {/* Join Date */}
                          <td className="py-4 px-3 text-center">
                            <span className="text-xs text-zinc-400">
                              {new Date(user.created_at).toLocaleDateString()}
                            </span>
                          </td>

                          {/* Actions */}
                          <td className="py-4 px-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              {/* Toggle Active */}
                              <button
                                onClick={() => toggleActiveMutation.mutate({ id: user.id, is_active: !user.is_active })}
                                title={user.is_active ? "Deactivate account" : "Activate account"}
                                className={`p-2 rounded-xl border text-xs font-bold transition flex items-center justify-center ${
                                  user.is_active
                                    ? "bg-yellow-950/20 border-yellow-900/30 text-yellow-400 hover:text-yellow-300"
                                    : "bg-green-950/20 border-green-900/30 text-green-400 hover:text-green-300"
                                }`}
                              >
                                {user.is_active ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                              </button>

                              {/* Delete */}
                              <button
                                onClick={() => handleDelete(user)}
                                disabled={deletingId === user.id}
                                title="Delete user"
                                className="p-2 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 rounded-xl transition flex items-center justify-center"
                              >
                                {deletingId === user.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Trash2 className="w-4 h-4" />
                                )}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center gap-3">
              <Users className="w-10 h-10 text-zinc-600" />
              <p className="text-base font-bold text-white">No Users Found</p>
              <p className="text-sm text-zinc-500">Try changing your role filter or search query.</p>
            </div>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
