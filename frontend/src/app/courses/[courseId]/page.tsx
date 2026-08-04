"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { courseService, lessonService, enrollmentService } from "@/services/api";
import { useAuth } from "@/providers/AuthProvider";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { ParticlesBackground } from "@/components/3d/Particles";
import { PageTransition } from "@/components/shared/PageTransitions";
import { BookOpen, GraduationCap, ChevronRight, CheckCircle, HelpCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function CourseDetailsPage() {
  const { courseId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();

  // Fetch Course details
  const { data: course, isLoading: courseLoading } = useQuery({
    queryKey: ["courseDetails", courseId],
    queryFn: () => courseService.getDetails(courseId as string),
  });

  // Fetch lessons
  const { data: lessons, isLoading: lessonsLoading } = useQuery({
    queryKey: ["courseLessons", courseId],
    queryFn: () => lessonService.listByCourse(courseId as string),
  });

  // Fetch Enrollment status
  const { data: enrollmentStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["enrollmentStatus", courseId],
    queryFn: () => enrollmentService.getStatus(courseId as string),
    enabled: isAuthenticated,
  });

  // Enrollment mutation
  const enrollMutation = useMutation({
    mutationFn: () => enrollmentService.enroll(courseId as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enrollmentStatus", courseId] });
      toast.success("Successfully enrolled in course!");
    },
    onError: (err: any) => {
      console.error(err);
      toast.error("Failed to enroll in the course.");
    },
  });

  const handleEnrollment = () => {
    if (!isAuthenticated) {
      toast.error("Please login to enroll in this course.");
      router.push("/login");
      return;
    }
    enrollMutation.mutate();
  };

  const getSyllabusAction = () => {
    if (statusLoading) return null;
    
    const isEnrolled = enrollmentStatus?.is_enrolled;
    
    if (isEnrolled) {
      // Find first lesson to play
      const firstLessonId = lessons && lessons.length > 0 ? lessons[0].id : null;
      if (firstLessonId) {
        return (
          <Link
            href={`/courses/${courseId}/lessons/${firstLessonId}`}
            className="glow-btn w-full py-4 text-sm font-bold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-2xl flex items-center justify-center gap-1.5 shadow-lg shadow-purple-500/10 cursor-pointer"
          >
            Continue Learning
            <ChevronRight className="w-4 h-4" />
          </Link>
        );
      }
    }

    return (
      <button
        onClick={handleEnrollment}
        disabled={enrollMutation.isPending}
        className="glow-btn w-full py-4 text-sm font-bold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-2xl flex items-center justify-center gap-1.5 shadow-lg shadow-purple-500/10 cursor-pointer"
      >
        {enrollMutation.isPending ? "Processing..." : course?.price === 0 ? "Enroll Free" : `Enroll for $${course?.price}`}
        <ChevronRight className="w-4 h-4" />
      </button>
    );
  };

  if (courseLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (!course) return null;

  return (
    <div className="min-h-screen relative flex flex-col justify-between overflow-x-hidden">
      <ParticlesBackground />
      <Header />

      <main className="flex-grow pt-32 pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full z-10 text-left">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Course Info (Left 2 columns) */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            
            {/* Header info */}
            <div>
              <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest bg-purple-950/20 border border-purple-500/10 px-3 py-1 rounded-full">
                {course.category}
              </span>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white mt-4 leading-snug">{course.title}</h1>
              <p className="text-zinc-400 text-sm mt-3 leading-relaxed">{course.description}</p>
            </div>

            {/* Syllabus */}
            <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BookOpen className="w-4.5 h-4.5 text-purple-400" />
                Syllabus Curriculum
              </h3>
              
              {lessonsLoading ? (
                <TableSkeleton />
              ) : lessons && lessons.length > 0 ? (
                <div className="flex flex-col gap-3">
                  {lessons.map((lesson, idx) => (
                    <div
                      key={lesson.id}
                      className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60 flex items-center justify-between gap-4"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-black text-zinc-650 bg-zinc-900 border border-zinc-850 w-7 h-7 flex items-center justify-center rounded-lg">
                          {idx + 1}
                        </span>
                        <div>
                          <h4 className="text-sm font-semibold text-white leading-tight">{lesson.title}</h4>
                          <p className="text-[10px] text-zinc-500 mt-1">{lesson.duration_minutes || 0} mins</p>
                        </div>
                      </div>
                      
                      {enrollmentStatus?.is_enrolled && (
                        <Link
                          href={`/courses/${courseId}/lessons/${lesson.id}`}
                          className="p-1.5 bg-zinc-900 border border-zinc-800 hover:border-purple-500/20 text-zinc-400 hover:text-purple-400 rounded-lg transition"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-10 border border-dashed border-zinc-800/80 rounded-2xl flex items-center justify-center">
                  <p className="text-sm text-zinc-500">No syllabus units published yet.</p>
                </div>
              )}
            </div>

          </div>

          {/* Pricing & Checkout sidebar card (Right column) */}
          <div className="flex flex-col gap-6">
            <div className="glass-card rounded-3xl p-6 flex flex-col gap-5 border border-zinc-850">
              
              {/* Cover Thumbnail */}
              <div className="w-full aspect-video rounded-2xl bg-zinc-950 overflow-hidden relative border border-zinc-900">
                {course.thumbnail ? (
                  <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-tr from-purple-950/20 to-blue-950/20 text-purple-400">
                    <BookOpen className="w-10 h-10" />
                  </div>
                )}
              </div>

              {/* Price Tag */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-400 font-medium">Access Tier</span>
                <span className="text-2xl font-black text-white">
                  {course.price === 0 ? "Free" : `$${course.price}`}
                </span>
              </div>

              <div className="h-px bg-zinc-900" />

              {/* Enrollment action button */}
              {getSyllabusAction()}

              {/* Course Features highlights */}
              <div className="flex flex-col gap-3 mt-1">
                {[
                  "Self-paced curriculum access",
                  "AI note companion and streaming tutor chat",
                  "Auto-graded quizzes and progress metrics",
                  "Course completion certification",
                ].map((feat, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs text-zinc-400 leading-normal">
                    <CheckCircle className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}
