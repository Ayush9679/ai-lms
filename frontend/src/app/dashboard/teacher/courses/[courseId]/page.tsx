"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { courseService, getApiErrorMessage, lessonService, quizService, assignmentService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { formatCoursePrice } from "@/lib/course-price";
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
  Edit3,
  Copy,
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function CourseDetailsManager() {
  const { courseId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"lessons" | "quizzes" | "assignments">("lessons");
  const [publishError, setPublishError] = useState<string | null>(null);
  const [priceDraft, setPriceDraft] = useState<string | null>(null);

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

  const effectivePrice = Number(priceDraft ?? course?.price ?? 0);
  const priceValid = Number.isFinite(effectivePrice) && effectivePrice >= 0 && Math.round(effectivePrice * 100) === effectivePrice * 100;

  // Mutations
  const deleteCourseMutation = useMutation({
    mutationFn: () => courseService.delete(courseId as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacherCourses"] });
      queryClient.invalidateQueries({ queryKey: ["teacherDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
      toast.success("Course deleted successfully!");
      router.push("/dashboard/teacher/courses");
    },
  });

  const publishCourseMutation = useMutation({
    mutationFn: (status: "published" | "draft") => courseService.update(courseId as string, { status, ...(status === "published" ? { price: effectivePrice, currency: "INR" } : {}) }),
    onMutate: () => setPublishError(null),
    onSuccess: (_, newStatus) => {
      queryClient.invalidateQueries({ queryKey: ["teacherCourse", courseId] });
      queryClient.invalidateQueries({ queryKey: ["teacherCourses"] });
      queryClient.invalidateQueries({ queryKey: ["teacherDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
      toast.success(newStatus === "published" ? "Course published! Students can now see it." : "Course reverted to draft.");
    },
    onError: (error: unknown) => {
      const message = getApiErrorMessage(error, "Could not publish course. Check the requirements and try again.");
      setPublishError(message);
      toast.error(message);
    },
  });

  const handleDeleteCourse = () => {
    if (confirm("Are you sure you want to delete this course? This action is permanent.")) {
      deleteCourseMutation.mutate();
    }
  };

  const [uploadingThumbnail, setUploadingThumbnail] = useState(false);

  const handleThumbnailUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Thumbnail must be 10 MB or smaller.");
      return;
    }

    setUploadingThumbnail(true);
    try {
      const updatedCourse = await courseService.uploadThumbnail(courseId as string, file);
      queryClient.setQueryData(["teacherCourse", courseId], updatedCourse);
      queryClient.invalidateQueries({ queryKey: ["teacherCourse", courseId] });
      queryClient.invalidateQueries({ queryKey: ["teacherCourses"] });
      queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
      toast.success("Thumbnail uploaded successfully!");
    } catch (err: unknown) {
      console.error(err);
      toast.error(getApiErrorMessage(err, "Thumbnail upload failed. Check storage CORS and retry."));
    } finally {
      setUploadingThumbnail(false);
    }
  };

  const handleDeleteThumbnail = async () => {
    if (!confirm("Are you sure you want to delete the course cover image?")) return;
    try {
      await courseService.update(courseId as string, { thumbnail: null });
      queryClient.invalidateQueries({ queryKey: ["teacherCourse", courseId] });
      queryClient.invalidateQueries({ queryKey: ["teacherCourses"] });
      queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
      toast.success("Thumbnail deleted.");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to delete thumbnail.");
    }
  };

  const deleteQuizMutation = useMutation({
    mutationFn: (quizId: string) => quizService.delete(quizId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courseQuizzes", courseId] });
      toast.success("Quiz deleted successfully!");
    },
    onError: () => {
      toast.error("Failed to delete quiz.");
    },
  });

  const handleDeleteQuiz = (quizId: string) => {
    if (confirm("Are you sure you want to delete this quiz permanently? This cannot be undone.")) {
      deleteQuizMutation.mutate(quizId);
    }
  };

  const deleteAssignmentMutation = useMutation({
    mutationFn: (asgId: string) => assignmentService.delete(asgId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courseAssignments", courseId] });
      toast.success("Assignment deleted successfully!");
    },
    onError: () => {
      toast.error("Failed to delete assignment.");
    },
  });

  const handleDeleteAssignment = (asgId: string) => {
    if (confirm("Are you sure you want to delete this assignment permanently? This cannot be undone.")) {
      deleteAssignmentMutation.mutate(asgId);
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

  const publishRequirements = [
    { label: "Course title is valid", complete: course.title.trim().length >= 3 },
    { label: "Course cover thumbnail is uploaded", complete: Boolean(course.thumbnail) },
    { label: "At least one lesson video is ready", complete: Boolean(lessons?.some((lesson) => lesson.video_status === "ready")) },
    { label: "INR price is valid (up to two decimal places)", complete: priceValid && (course.currency ?? "INR") === "INR" },
    { label: "Paid checkout is enabled", complete: effectivePrice === 0 },
  ];
  const canPublish = publishRequirements.every((requirement) => requirement.complete);

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
                <p className="mt-1 text-sm font-semibold text-purple-300">{formatCoursePrice(course.price)}</p>
                <p className="text-zinc-400 text-xs mt-0.5">Category: {course.category} • {course.level}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
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
                  disabled={publishCourseMutation.isPending || !canPublish}
                  aria-describedby="publish-requirements"
                  title={canPublish ? "Publish this course" : "Complete the listed requirements to publish"}
                  className="px-5 py-3 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-md transition disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Publish Course
                </button>
              ) : (
                <button
                  onClick={() => publishCourseMutation.mutate("draft")}
                  disabled={publishCourseMutation.isPending}
                  className="px-5 py-3 text-sm font-semibold bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white rounded-xl transition cursor-pointer"
                >
                  Revert to Draft
                </button>
              )}
            </div>
          </div>

          {course.status === "draft" && (
            <div id="publish-requirements" aria-live="polite" className="rounded-2xl border border-zinc-800 bg-zinc-950/40 p-4 text-xs text-zinc-400" title="Course publishing requirements">
              <p className="mb-2 font-semibold text-zinc-300">Before publishing, complete all requirements:</p>
              <ul className="flex flex-col gap-1">
                {publishRequirements.map((requirement) => (
                  <li key={requirement.label} aria-label={`${requirement.complete ? "Complete" : "Incomplete"}: ${requirement.label}`}>
                    <span aria-hidden="true" className={requirement.complete ? "text-emerald-400" : "text-amber-400"}>{requirement.complete ? "✓" : "•"}</span>{" "}{requirement.label}
                  </li>
                ))}
              </ul>
              {publishError && <p role="alert" className="mt-2 text-red-400">{publishError}</p>}
            </div>
          )}

          {/* Cover Thumbnail Management */}
          <div className="glass-card rounded-3xl p-5 flex flex-col sm:flex-row items-center gap-5 border border-zinc-850 bg-zinc-950/20">
            <div className="w-40 aspect-video bg-zinc-950 rounded-2xl border border-zinc-900 overflow-hidden relative shrink-0">
              {course.thumbnail ? (
                <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-zinc-650 font-bold text-[10px] uppercase">
                  No Thumbnail
                </div>
              )}
            </div>
            <div className="flex-grow flex flex-col gap-2 text-center sm:text-left">
              <h3 className="text-sm font-bold text-white">Course Cover Image</h3>
              <p className="text-zinc-555 text-xs">PNG, JPEG, WEBP or GIF. Max 10 MB.</p>
              <div className="flex flex-wrap items-center gap-2 mt-1 justify-center sm:justify-start">
                <label className="py-2 px-4 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-bold rounded-xl text-zinc-300 hover:text-white transition cursor-pointer select-none">
                  {uploadingThumbnail ? "Uploading..." : course.thumbnail ? "Replace Image" : "Upload Image"}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleThumbnailUpload}
                    disabled={uploadingThumbnail}
                    className="hidden"
                  />
                </label>
                {course.thumbnail && (
                  <button
                    onClick={handleDeleteThumbnail}
                    className="py-2 px-4 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 text-xs font-bold rounded-xl transition cursor-pointer"
                  >
                    Delete Image
                  </button>
                )}
              </div>
            </div>
          </div>

          <section className="glass-card rounded-2xl p-5 flex flex-col gap-3" aria-label="Course pricing">
            <h2 className="text-base font-bold text-white">Course pricing</h2>
            <div className="flex flex-wrap items-end gap-3">
              <label className="flex min-w-40 flex-col gap-1 text-xs font-semibold text-zinc-400">Pricing model
                <select value={effectivePrice > 0 ? "paid" : "free"} onChange={(event) => setPriceDraft(event.target.value === "free" ? "0" : "1")} className="rounded-xl border border-zinc-800 bg-zinc-950/60 px-3 py-2.5 text-sm text-white"><option value="free">Free</option><option value="paid">Paid</option></select>
              </label>
              {effectivePrice > 0 && <label className="flex min-w-40 flex-col gap-1 text-xs font-semibold text-zinc-400">Price (INR)
                <input aria-label="Price in Indian rupees" type="number" min="0.01" step="0.01" value={priceDraft ?? String(course.price)} onChange={(event) => setPriceDraft(event.target.value)} className="rounded-xl border border-zinc-800 bg-zinc-950/60 px-3 py-2.5 text-sm text-white" />
              </label>}
              <button onClick={async () => {
                if (!priceValid) { toast.error("Enter a valid INR price with up to two decimal places."); return; }
                try {
                  const updatedCourse = await courseService.update(courseId as string, { price: effectivePrice, currency: "INR" });
                  queryClient.setQueryData(["teacherCourse", courseId], updatedCourse);
                  setPriceDraft(null);
                  await queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
                  toast.success("Course price saved.");
                } catch (error) { toast.error(getApiErrorMessage(error, "Could not save the course price.")); }
              }} disabled={!priceValid} className="rounded-xl border border-zinc-700 px-4 py-2.5 text-sm text-white disabled:opacity-50">Save price</button>
            </div>
            {effectivePrice > 0 && <p className="text-xs text-amber-300">Paid checkout is unavailable. Paid courses cannot be published until checkout is enabled.</p>}
          </section>

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
                        
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/dashboard/teacher/courses/${courseId}/quizzes/${quiz.id}`}
                            className="py-2 px-3.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white rounded-xl transition cursor-pointer"
                          >
                            Edit Questions
                          </Link>
                          <button
                            onClick={() => handleDeleteQuiz(quiz.id)}
                            disabled={deleteQuizMutation.isPending}
                            className="p-2 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 rounded-xl transition flex items-center justify-center cursor-pointer"
                            title="Delete Quiz"
                          >
                            <Trash className="w-4 h-4" />
                          </button>
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
                        
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/dashboard/teacher/submissions?assignment_id=${asg.id}`}
                            className="py-2 px-3.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white rounded-xl transition cursor-pointer"
                          >
                            Grade Submissions
                          </Link>
                          <Link
                            href={`/dashboard/teacher/courses/${courseId}/assignments/${asg.id}`}
                            className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-400 hover:text-white flex items-center justify-center cursor-pointer"
                            title="Edit Assignment"
                          >
                            <Edit3 className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() => handleDeleteAssignment(asg.id)}
                            disabled={deleteAssignmentMutation.isPending}
                            className="p-2 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 rounded-xl transition flex items-center justify-center cursor-pointer"
                            title="Delete Assignment"
                          >
                            <Trash className="w-4 h-4" />
                          </button>
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
