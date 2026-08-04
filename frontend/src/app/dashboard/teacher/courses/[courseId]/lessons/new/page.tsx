"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { lessonService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PageTransition } from "@/components/shared/PageTransitions";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

const lessonSchema = zod.object({
  title: zod.string().min(3, "Title must be at least 3 characters long"),
  content: zod.string().min(10, "Content must be at least 10 characters long").nullable().optional(),
  duration_minutes: zod.number().min(0, "Duration must be positive").nullable().optional(),
  order_index: zod.number().min(0),
});

type LessonForm = zod.infer<typeof lessonSchema>;

export default function NewLessonPage() {
  const { courseId } = useParams();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LessonForm>({
    resolver: zodResolver(lessonSchema),
    defaultValues: {
      duration_minutes: 10,
      order_index: 0,
    },
  });

  const onSubmit = async (data: LessonForm) => {
    setIsSubmitting(true);
    try {
      await lessonService.create(courseId as string, data);
      toast.success("Lesson created successfully!");
      router.push(`/dashboard/teacher/courses/${courseId}`);
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to create lesson.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="max-w-2xl mx-auto flex flex-col gap-6 text-left">
          
          <div className="flex items-center gap-3">
            <Link
              href={`/dashboard/teacher/courses/${courseId}`}
              className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-extrabold text-white">Add Lesson</h1>
              <p className="text-zinc-400 text-xs mt-0.5">Define another lesson block in the syllabus timeline.</p>
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              
              {/* Title */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Lesson Title</label>
                <input
                  type="text"
                  placeholder="Lexical Scoping and Closures"
                  {...register("title")}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
                {errors.title && (
                  <span className="text-xs text-red-400 font-semibold">{errors.title.message}</span>
                )}
              </div>

              {/* Content */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Lesson Content (Text / MD)</label>
                <textarea
                  rows={6}
                  placeholder="Provide lesson transcript, guides, or core explanations..."
                  {...register("content")}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
                />
                {errors.content && (
                  <span className="text-xs text-red-400 font-semibold">{errors.content.message}</span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Duration */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Duration (Mins)</label>
                  <input
                    type="number"
                    placeholder="15"
                    {...register("duration_minutes", { valueAsNumber: true })}
                    className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                  />
                  {errors.duration_minutes && (
                    <span className="text-xs text-red-400 font-semibold">{errors.duration_minutes.message}</span>
                  )}
                </div>

                {/* Order Index */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Sort Order Index</label>
                  <input
                    type="number"
                    placeholder="0"
                    {...register("order_index", { valueAsNumber: true })}
                    className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                  />
                  {errors.order_index && (
                    <span className="text-xs text-red-400 font-semibold">{errors.order_index.message}</span>
                  )}
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="glow-btn mt-2 py-3.5 px-6 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-lg transition flex items-center justify-center gap-2 cursor-pointer"
              >
                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                Create Lesson
              </button>
            </form>
          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
