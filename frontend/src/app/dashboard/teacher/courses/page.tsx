"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { courseService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  BookOpen,
  Plus,
  Edit3,
  Trash2,
  Users,
  Eye,
  EyeOff,
  Loader2,
  FileText,
  Trophy,
  ChevronRight,
  GraduationCap,
  Copy,
  Archive,
} from "lucide-react";
import toast from "react-hot-toast";
import { CourseSummary } from "@/types";

export default function ManageCoursesPage() {
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | "published" | "draft" | "archived">("all");

  const { data: courses, isLoading } = useQuery({
    queryKey: ["teacherCourses"],
    queryFn: courseService.listTaught,
  });

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ["teacherCourses"] });
    queryClient.invalidateQueries({ queryKey: ["teacherDashboard"] });
    queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
  };

  const publishMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "published" | "draft" | "archived" }) =>
      courseService.update(id, { status }),
    onSuccess: (_, vars) => {
      toast.success(`Course status updated to "${vars.status}".`);
      setPublishingId(null);
      invalidateAll();
    },
    onError: () => {
      toast.error("Failed to update course status.");
      setPublishingId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => courseService.delete(id),
    onSuccess: () => {
      toast.success("Course deleted.");
      setDeletingId(null);
      invalidateAll();
    },
    onError: () => {
      toast.error("Failed to delete course.");
      setDeletingId(null);
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: string) => courseService.duplicate(id),
    onSuccess: () => {
      toast.success("Course duplicated successfully!");
      setDuplicatingId(null);
      invalidateAll();
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.message || "Failed to duplicate course.");
      setDuplicatingId(null);
    },
  });

  const handleDelete = (course: CourseSummary) => {
    if (!confirm(`Delete "${course.title}"? This cannot be undone.`)) return;
    setDeletingId(course.id);
    deleteMutation.mutate(course.id);
  };

  const handleTogglePublish = (course: CourseSummary) => {
    const newStatus = course.status === "published" ? "draft" : "published";
    setPublishingId(course.id);
    publishMutation.mutate({ id: course.id, status: newStatus });
  };

  const handleArchive = (course: CourseSummary) => {
    const newStatus = course.status === "archived" ? "draft" : "archived";
    setPublishingId(course.id);
    publishMutation.mutate({ id: course.id, status: newStatus });
  };

  const handleDuplicate = (course: CourseSummary) => {
    setDuplicatingId(course.id);
    duplicateMutation.mutate(course.id);
  };

  const publishedCount = courses?.filter((c) => c.status === "published").length ?? 0;
  const draftCount = courses?.filter((c) => c.status === "draft").length ?? 0;
  const archivedCount = courses?.filter((c) => c.status === "archived").length ?? 0;

  const filteredCourses = courses?.filter((c) => {
    if (statusFilter === "all") return true;
    return c.status === statusFilter;
  }) ?? [];

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">

          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold text-white">Manage Courses</h1>
              <p className="text-zinc-400 text-sm mt-1">
                Publish, edit, or remove your learning tracks.
              </p>
            </div>
            <Link
              href="/dashboard/teacher/courses/new"
              className="glow-btn flex items-center justify-center gap-2 py-3 px-5 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-md transition w-fit"
            >
              <Plus className="w-4 h-4" />
              Create New Course
            </Link>
          </div>

          {/* Summary Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-purple-950/40 border border-purple-500/10">
                <BookOpen className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{courses?.length ?? 0}</p>
                <p className="text-xs text-zinc-500">Total Courses</p>
              </div>
            </div>
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
              <div className="p-2 rounded-xl bg-zinc-800/60 border border-zinc-700/20">
                <Archive className="w-5 h-5 text-zinc-400" />
              </div>
              <div>
                <p className="text-xl font-black text-white">{archivedCount}</p>
                <p className="text-xs text-zinc-500">Archived</p>
              </div>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-2 flex-wrap">
            {(["all", "published", "draft", "archived"] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setStatusFilter(filter)}
                className={`py-1.5 px-4 rounded-xl text-xs font-semibold border transition cursor-pointer ${
                  statusFilter === filter
                    ? "bg-purple-950/30 border-purple-500/40 text-purple-300"
                    : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700"
                }`}
              >
                {filter.charAt(0).toUpperCase() + filter.slice(1)}
                {filter === "all" && ` (${courses?.length ?? 0})`}
                {filter === "published" && ` (${publishedCount})`}
                {filter === "draft" && ` (${draftCount})`}
                {filter === "archived" && ` (${archivedCount})`}
              </button>
            ))}
          </div>

          {/* Course Table */}
          {isLoading ? (
            <TableSkeleton />
          ) : filteredCourses.length > 0 ? (
            <div className="glass-card rounded-3xl p-6 overflow-hidden">
              <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800/80 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                      <th className="py-3.5 px-3">Course</th>
                      <th className="py-3.5 px-3 text-center">Status</th>
                      <th className="py-3.5 px-3 text-center">Students</th>
                      <th className="py-3.5 px-3 text-center">Lessons</th>
                      <th className="py-3.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCourses.map((course) => (
                      <tr
                        key={course.id}
                        className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-950/20"
                      >
                        {/* Course Name */}
                        <td className="py-4 px-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-purple-950/30 border border-purple-500/10 flex items-center justify-center shrink-0">
                              <BookOpen className="w-4 h-4 text-purple-400" />
                            </div>
                            <div>
                              <p className="text-sm font-bold text-white leading-snug">{course.title}</p>
                              <p className="text-[10px] text-zinc-500 mt-0.5 font-semibold uppercase">
                                {course.category} • {course.level}
                              </p>
                            </div>
                          </div>
                        </td>

                        {/* Status Badge */}
                        <td className="py-4 px-3 text-center">
                          <span
                            className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${
                              course.status === "published"
                                ? "bg-green-950/30 text-green-400 border-green-500/20"
                                : "bg-yellow-950/30 text-yellow-400 border-yellow-500/20"
                            }`}
                          >
                            {course.status === "published" ? (
                              <Eye className="w-3 h-3" />
                            ) : (
                              <EyeOff className="w-3 h-3" />
                            )}
                            {course.status}
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

                        <td className="py-4 px-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {/* Publish / Unpublish */}
                            <button
                              onClick={() => handleTogglePublish(course)}
                              disabled={publishingId === course.id || course.status === "archived"}
                              title={course.status === "published" ? "Revert to Draft" : "Publish Course"}
                              className={`p-2 rounded-xl border text-xs font-bold transition flex items-center justify-center cursor-pointer disabled:opacity-40 ${
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

                            {/* Archive / Unarchive */}
                            <button
                              onClick={() => handleArchive(course)}
                              disabled={publishingId === course.id}
                              title={course.status === "archived" ? "Restore from Archive" : "Archive Course"}
                              className="p-2 rounded-xl border bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-white transition flex items-center justify-center cursor-pointer disabled:opacity-40"
                            >
                              <Archive className="w-4 h-4" />
                            </button>

                            {/* Duplicate */}
                            <button
                              onClick={() => handleDuplicate(course)}
                              disabled={duplicatingId === course.id}
                              title="Duplicate Course"
                              className="p-2 bg-blue-950/20 border border-blue-900/30 text-blue-400 hover:text-blue-300 rounded-xl transition flex items-center justify-center cursor-pointer disabled:opacity-40"
                            >
                              {duplicatingId === course.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </button>

                            {/* Manage / Edit */}
                            <Link
                              href={`/dashboard/teacher/courses/${course.id}`}
                              className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-400 hover:text-white flex items-center justify-center cursor-pointer"
                              title="Manage Course"
                            >
                              <Edit3 className="w-4 h-4" />
                            </Link>

                            {/* Delete */}
                            <button
                              onClick={() => handleDelete(course)}
                              disabled={deletingId === course.id}
                              title="Delete Course"
                              className="p-2 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 rounded-xl transition flex items-center justify-center cursor-pointer disabled:opacity-40"
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
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="py-24 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center gap-4">
              <div className="p-4 bg-purple-950/20 rounded-2xl border border-purple-500/10">
                <BookOpen className="w-8 h-8 text-purple-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">No Courses Yet</h3>
                <p className="text-sm text-zinc-500 mt-1">Create your first course to get started.</p>
              </div>
              <Link
                href="/dashboard/teacher/courses/new"
                className="flex items-center gap-2 py-3 px-6 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-sm font-bold text-white rounded-xl shadow-md transition"
              >
                <Plus className="w-4 h-4" />
                Create Your First Course
              </Link>
            </div>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
