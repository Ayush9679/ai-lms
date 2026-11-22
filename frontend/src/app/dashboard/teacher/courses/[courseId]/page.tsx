"use client";

import React, { useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { courseService, lessonService, quizService, assignmentService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  ArrowLeft,
  BookOpen,
  Trophy,
  FileText,
  Plus,
  Loader2,
  Trash,
  Sparkles,
  Play,
  Upload,
  Image as ImageIcon,
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function CourseDetailsManager() {
  const { courseId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"lessons" | "quizzes" | "assignments">("lessons");
  const thumbnailAbort = useRef<AbortController | null>(null);

  // Fetch Course details
  const { data: course, isLoading: courseLoading } = useQuery({
    queryKey: ["teacherCourse", courseId],
    queryFn: () => courseService.getDetails(courseId as string),
  });

  // Fetch lessons
  const { data: lessons, isLoading: lessonsLoading } = useQuery({
    queryKey: ["courseLessons", courseId],
    queryFn: () => lessonService.listByCourse(courseId as string),
  });

  // Fetch quizzes
  const { data: quizzes, isLoading: quizzesLoading } = useQuery({
    queryKey: ["courseQuizzes", courseId],
    queryFn: () => quizService.listByCourse(courseId as string),
  });

  // Fetch assignments
  const { data: assignments, isLoading: assignmentsLoading } = useQuery({
    queryKey: ["courseAssignments", courseId],
    queryFn: () => assignmentService.listByCourse(courseId as string),
  });

  // Mutations
  const deleteCourseMutation = useMutation({
    mutationFn: () => courseService.delete(courseId as string),
    onSuccess: () => {
      toast.success("Course deleted successfully!");
      router.push("/dashboard/teacher");
    },
  });

  const publishCourseMutation = useMutation({
    mutationFn: (status: "published" | "draft") => courseService.update(courseId as string, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacherCourse", courseId] });
      toast.success("Course status updated!");
    },
    onError: (error: any) => toast.error(error?.response?.data?.message ?? "Could not publish course."),
  });

  const thumbnailMutation = useMutation({
    mutationFn: ({ file, signal }: { file: File; signal: AbortSignal }) =>
      courseService.uploadThumbnail(courseId as string, file, signal),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["teacherCourse", courseId] });
      await queryClient.invalidateQueries({ queryKey: ["course"] });
      toast.success("Course thumbnail updated.");
    },
    onError: (error: any) => {
      if (error?.name !== "AbortError") {
        toast.error(error?.response?.data?.message ?? error?.message ?? "Could not upload the thumbnail.");
      }
    },
  });

  const handleDeleteCourse = () => {
    if (confirm("Are you sure you want to delete this course? This action is permanent.")) {
      deleteCourseMutation.mutate();
    }
  };

  if (courseLoading) {
    return (
      <DashboardLayout>
        <TableSkeleton />
      </DashboardLayout>
    );
  }

  if (!course) return null;

  const publishRequirements: string[] = [];
  if (!course.title?.trim()) publishRequirements.push("Add a nonempty course title.");
  if (!course.thumbnail?.trim()) publishRequirements.push("Upload a course thumbnail.");
  if (!lessons?.some((lesson) => lesson.video_status === "ready")) {
    publishRequirements.push("Upload and verify video for at least one lesson.");
  }
  const publishDisabled = lessonsLoading || publishRequirements.length > 0;

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">
          
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard/teacher"
                className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <div>
                <h1 className="text-2xl font-extrabold text-white">{course.title}</h1>
                <p className="text-zinc-400 text-xs mt-0.5">Category: {course.category} • {course.level}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm font-semibold text-zinc-300 hover:text-white">
                <ImageIcon className="h-4 w-4" />
                {thumbnailMutation.isPending ? "Uploading…" : "Course thumbnail"}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  className="sr-only"
                  disabled={thumbnailMutation.isPending}
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      thumbnailAbort.current = new AbortController();
                      thumbnailMutation.mutate({ file, signal: thumbnailAbort.current.signal });
                    }
                    event.currentTarget.value = "";
                  }}
                />
              </label>
              {thumbnailMutation.isPending && (
                <button type="button" onClick={() => thumbnailAbort.current?.abort()} className="rounded-xl border border-zinc-800 px-3 py-2 text-xs text-zinc-300">
                  Cancel upload
                </button>
              )}
              <button
                onClick={handleDeleteCourse}
                disabled={deleteCourseMutation.isPending}
                className="p-3 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 rounded-xl transition flex items-center justify-center"
                title="Delete Course"
              >
                <Trash className="w-4 h-4" />
              </button>

              {course.status === "draft" ? (
                <button
                  onClick={() => publishCourseMutation.mutate("published")}
                  disabled={publishCourseMutation.isPending || publishDisabled}
                  aria-describedby="course-publish-help"
                  title={publishRequirements.join(" ") || "Course meets the publishing requirements."}
                  className="px-5 py-3 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-md transition"
                >
                  Publish Course
                </button>
              ) : (
                <button
                  onClick={() => publishCourseMutation.mutate("draft")}
                  disabled={publishCourseMutation.isPending}
                  className="px-5 py-3 text-sm font-semibold bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white rounded-xl transition"
                >
                  Revert to Draft
                </button>
              )}
            </div>
            {course.status === "draft" && (
              <div id="course-publish-help" aria-live="polite" className="text-right text-xs text-zinc-400">
                {lessonsLoading ? "Checking publishing requirements…" : publishRequirements.length
                  ? <span>To publish: {publishRequirements.join(" ")}</span>
                  : "Ready to publish: title, thumbnail, and a verified lesson video are complete."}
              </div>
            )}
          </div>

          {/* TABS SELECTOR */}
          <div className="flex border-b border-zinc-800/80 mt-4">
            {(["lessons", "quizzes", "assignments"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-6 text-sm font-bold border-b-2 capitalize transition ${
                  activeTab === tab
                    ? "border-purple-500 text-purple-400"
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* TAB CONTENTS */}
          <div className="mt-2">
            {activeTab === "lessons" && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white">Syllabus Curriculum</h3>
                  <Link
                    href={`/dashboard/teacher/courses/${courseId}/lessons/new`}
                    className="flex items-center gap-1.5 py-2 px-4 bg-zinc-900 border border-zinc-850 hover:border-zinc-700 text-sm font-semibold rounded-xl text-zinc-300 hover:text-white transition"
                  >
                    <Plus className="w-4 h-4" />
                    Add Lesson
                  </Link>
                </div>

                {lessonsLoading ? (
                  <TableSkeleton />
                ) : lessons && lessons.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    {lessons.map((lesson) => (
                      <div key={lesson.id} className="glass-card rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-purple-950/30 rounded-xl text-purple-400 mt-0.5">
                            <Play className="w-4 h-4 fill-purple-400" />
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-white">{lesson.title}</h4>
                            <p className="text-xs text-zinc-500 mt-1">Duration: {lesson.duration_minutes || 0} mins</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <Link
                            href={`/dashboard/teacher/courses/${courseId}/lessons/${lesson.id}/upload`}
                            className="flex items-center gap-1.5 py-2 px-3 bg-zinc-950/45 border border-zinc-900 hover:border-zinc-800 text-xs font-semibold text-zinc-400 hover:text-zinc-300 rounded-xl transition"
                          >
                            <Upload className="w-3.5 h-3.5" />
                            Upload Video/PDF
                          </Link>
                          <Link
                            href={`/dashboard/teacher/courses/${courseId}/lessons/${lesson.id}`}
                            className="py-2 px-3.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white rounded-xl transition"
                          >
                            Edit
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 border border-dashed border-zinc-800/80 rounded-2xl flex flex-col items-center justify-center">
                    <p className="text-sm text-zinc-500">No lessons created yet.</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === "quizzes" && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white">Course Quizzes</h3>
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/dashboard/teacher/courses/${courseId}/quizzes/generate`}
                      className="flex items-center gap-1.5 py-2 px-4 bg-purple-950/20 border border-purple-500/25 hover:bg-purple-900/10 text-sm font-semibold rounded-xl text-purple-300 transition"
                    >
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      AI Quiz Wizard
                    </Link>
                    <Link
                      href={`/dashboard/teacher/courses/${courseId}/quizzes/new`}
                      className="flex items-center gap-1.5 py-2 px-4 bg-zinc-900 border border-zinc-850 hover:border-zinc-700 text-sm font-semibold rounded-xl text-zinc-300 hover:text-white transition"
                    >
                      <Plus className="w-4 h-4" />
                      Add Manual Quiz
                    </Link>
                  </div>
                </div>

                {quizzesLoading ? (
                  <TableSkeleton />
                ) : quizzes && quizzes.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    {quizzes.map((quiz) => (
                      <div key={quiz.id} className="glass-card rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-pink-950/30 rounded-xl text-pink-400 mt-0.5">
                            <Trophy className="w-4 h-4" />
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-white">{quiz.title}</h4>
                            <p className="text-xs text-zinc-500 mt-1 uppercase font-semibold">
                              Passing: {quiz.passing_score}% • Max Attempts: {quiz.max_attempts || "Unlimited"}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <Link
                            href={`/dashboard/teacher/courses/${courseId}/quizzes/${quiz.id}`}
                            className="py-2 px-3.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white rounded-xl transition"
                          >
                            Edit Questions
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 border border-dashed border-zinc-800/80 rounded-2xl flex flex-col items-center justify-center">
                    <p className="text-sm text-zinc-500">No quizzes created yet.</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === "assignments" && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white">Course Assignments</h3>
                  <Link
                    href={`/dashboard/teacher/courses/${courseId}/assignments/new`}
                    className="flex items-center gap-1.5 py-2 px-4 bg-zinc-900 border border-zinc-850 hover:border-zinc-700 text-sm font-semibold rounded-xl text-zinc-300 hover:text-white transition"
                  >
                    <Plus className="w-4 h-4" />
                    Add Assignment
                  </Link>
                </div>

                {assignmentsLoading ? (
                  <TableSkeleton />
                ) : assignments && assignments.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    {assignments.map((asg) => (
                      <div key={asg.id} className="glass-card rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-blue-950/30 rounded-xl text-blue-400 mt-0.5">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-white">{asg.title}</h4>
                            <p className="text-xs text-zinc-500 mt-1">
                              Max Marks: {asg.max_marks} • Due: {asg.due_date ? new Date(asg.due_date).toLocaleDateString() : "No deadline"}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <Link
                            href={`/dashboard/teacher/submissions?assignment_id=${asg.id}`}
                            className="py-2 px-3.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white rounded-xl transition"
                          >
                            Grade Submissions
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 border border-dashed border-zinc-800/80 rounded-2xl flex flex-col items-center justify-center">
                    <p className="text-sm text-zinc-500">No assignments created yet.</p>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
