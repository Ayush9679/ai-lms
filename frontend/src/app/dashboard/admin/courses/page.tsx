"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminCourseService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  BookOpen,
  Search,
  Eye,
  EyeOff,
  Trash2,
  Loader2,
  Users,
  RefreshCcw,
  Archive,
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";
import { CourseSummary } from "@/types";

const STATUS_CONFIG: Record<string, { label: string; color: string; Icon: any }> = {
  published: { label: "Published", color: "text-green-400 border-green-500/20 bg-green-950/20", Icon: Eye },
  draft: { label: "Draft", color: "text-yellow-400 border-yellow-500/20 bg-yellow-950/20", Icon: EyeOff },
  archived: { label: "Archived", color: "text-zinc-400 border-zinc-700 bg-zinc-900/30", Icon: Archive },
};

export default function AdminCoursesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [publishingId, setPublishingId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["adminCourses"],
    queryFn: () => adminCourseService.listAll({ page_size: 100 }),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["adminCourses"] });
    queryClient.invalidateQueries({ queryKey: ["adminDashboard"] });
    queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
    queryClient.invalidateQueries({ queryKey: ["teacherCourses"] });
  };

  const publishMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "published" | "draft" | "archived" }) =>
      adminCourseService.forcePublish(id, status),
    onSuccess: (_, vars) => {
      toast.success(`Course set to "${vars.status}".`);
      setPublishingId(null);
      invalidate();
    },
    onError: () => {
      toast.error("Failed to update course status.");
      setPublishingId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminCourseService.forceDelete(id),
    onSuccess: () => {
      toast.success("Course deleted.");
      setDeletingId(null);
      invalidate();
    },
    onError: () => {
      toast.error("Failed to delete course.");
      setDeletingId(null);
    },
  });

  const handleDelete = (course: CourseSummary) => {
    if (!confirm(`Permanently delete "${course.title}"? This cannot be undone.`)) return;
    setDeletingId(course.id);
    deleteMutation.mutate(course.id);
  };

  const handleTogglePublish = (course: CourseSummary) => {
    const newStatus: "published" | "draft" = course.status === "published" ? "draft" : "published";
    setPublishingId(course.id);
    publishMutation.mutate({ id: course.id, status: newStatus });
  };

  const filtered = data?.items.filter((c) =>
    !search ||
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    (c.instructor_name ?? "").toLowerCase().includes(search.toLowerCase())
  ) ?? [];

  const publishedCount = data?.items.filter((c) => c.status === "published").length ?? 0;
  const draftCount = data?.items.filter((c) => c.status === "draft").length ?? 0;
  const archivedCount = data?.items.filter((c) => c.status === "archived").length ?? 0;

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold text-white">Courses Manager</h1>
              <p className="text-zinc-400 text-sm mt-1">Platform-wide view of all courses. Force publish, archive, or remove any course.</p>
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
              <div className="p-2 rounded-xl bg-green-950/40 border border-green-500/10">
                <Eye className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{publishedCount}</p>
                <p className="text-xs text-zinc-500">Published</p>
              </div>
            </div>
            <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-yellow-950/40 border border-yellow-500/10">
                <EyeOff className="w-5 h-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{draftCount}</p>
                <p className="text-xs text-zinc-500">Drafts</p>
              </div>
            </div>
            <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-zinc-800/40 border border-zinc-700/20">
                <Archive className="w-5 h-5 text-zinc-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{archivedCount}</p>
                <p className="text-xs text-zinc-500">Archived</p>
              </div>
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search by title or instructor name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl pl-11 pr-4 py-3 text-sm focus:outline-none transition"
            />
          </div>

          {/* Courses Table */}
          {isLoading ? (
            <TableSkeleton />
          ) : filtered.length > 0 ? (
            <div className="glass-card rounded-3xl p-6 overflow-hidden">
              <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800/80 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                      <th className="py-3.5 px-3">Course</th>
                      <th className="py-3.5 px-3">Instructor</th>
                      <th className="py-3.5 px-3 text-center">Status</th>
                      <th className="py-3.5 px-3 text-center">Students</th>
                      <th className="py-3.5 px-3 text-center">Lessons</th>
                      <th className="py-3.5 px-3 text-center">Price</th>
                      <th className="py-3.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((course) => {
                      const statusMeta = STATUS_CONFIG[course.status] ?? STATUS_CONFIG.draft;
                      const StatusIcon = statusMeta.Icon;
                      return (
                        <tr
                          key={course.id}
                          className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-950/20"
                        >
                          {/* Course */}
                          <td className="py-4 px-3">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-purple-950/30 border border-purple-500/10 flex items-center justify-center shrink-0">
                                <BookOpen className="w-4 h-4 text-purple-400" />
                              </div>
                              <div>
                                <p className="text-sm font-bold text-white max-w-[160px] truncate">{course.title}</p>
                                <p className="text-[10px] text-zinc-500 font-semibold uppercase mt-0.5">
                                  {course.category} • {course.level}
                                </p>
                              </div>
                            </div>
                          </td>

                          {/* Instructor */}
                          <td className="py-4 px-3">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center text-white text-[9px] font-extrabold uppercase shrink-0">
                                {(course.instructor_name ?? "?")?.[0]}
                              </div>
                              <span className="text-xs text-zinc-300 font-semibold truncate max-w-[100px]">
                                {course.instructor_name ?? "Unknown"}
                              </span>
                            </div>
                          </td>

                          {/* Status */}
                          <td className="py-4 px-3 text-center">
                            <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${statusMeta.color}`}>
                              <StatusIcon className="w-3 h-3" />
                              {statusMeta.label}
                            </span>
                          </td>

                          {/* Students */}
                          <td className="py-4 px-3 text-center">
                            <div className="flex items-center justify-center gap-1 text-sm font-semibold text-zinc-300">
                              <Users className="w-3.5 h-3.5 text-zinc-500" />
                              {course.total_students}
                            </div>
                          </td>

                          {/* Lessons */}
                          <td className="py-4 px-3 text-center">
                            <span className="text-sm font-semibold text-zinc-300">{course.total_lessons}</span>
                          </td>

                          {/* Price */}
                          <td className="py-4 px-3 text-center">
                            <span className="text-sm font-semibold text-white">
                              {course.price === 0 ? "Free" : `$${course.price}`}
                            </span>
                          </td>

                          {/* Actions */}
                          <td className="py-4 px-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              {/* Publish / Unpublish toggle */}
                              <button
                                onClick={() => handleTogglePublish(course)}
                                disabled={publishingId === course.id}
                                title={course.status === "published" ? "Revert to Draft" : "Force Publish"}
                                className={`p-2 rounded-xl border text-xs font-bold transition flex items-center justify-center ${
                                  course.status === "published"
                                    ? "bg-yellow-950/20 border-yellow-900/30 text-yellow-400 hover:text-yellow-300"
                                    : "bg-green-950/20 border-green-900/30 text-green-400 hover:text-green-300"
                                }`}
                              >
                                {publishingId === course.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : course.status === "published" ? (
                                  <EyeOff className="w-4 h-4" />
                                ) : (
                                  <Eye className="w-4 h-4" />
                                )}
                              </button>

                              {/* Delete */}
                              <button
                                onClick={() => handleDelete(course)}
                                disabled={deletingId === course.id}
                                title="Delete course"
                                className="p-2 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 rounded-xl transition flex items-center justify-center"
                              >
                                {deletingId === course.id ? (
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
              <BookOpen className="w-10 h-10 text-zinc-600" />
              <p className="text-base font-bold text-white">No Courses Found</p>
              <p className="text-sm text-zinc-500">No courses match your search query.</p>
            </div>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
