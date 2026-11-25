"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { courseService } from "@/services/api";
import { useQueryClient } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PageTransition } from "@/components/shared/PageTransitions";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

const courseSchema = zod.object({
  title: zod.string().min(3, "Title must be at least 3 characters long"),
  description: zod.string().min(10, "Description must be at least 10 characters long"),
  category: zod.string().min(2, "Category is required"),
  level: zod.enum(["beginner", "intermediate", "advanced"]),
  price: zod.number().finite().min(0, "Price must be positive or zero").refine((value) => Math.round(value * 100) === value * 100, "Use no more than two decimal places"),
});

type CourseForm = zod.infer<typeof courseSchema>;

export default function NewCoursePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    control,
  } = useForm<CourseForm>({
    resolver: zodResolver(courseSchema),
    defaultValues: {
      level: "beginner",
      price: 0,
    },
  });
  const selectedPrice = useWatch({ control, name: "price" });

  const onSubmit = async (data: CourseForm) => {
    setIsSubmitting(true);
    try {
      const course = await courseService.create(data);
      queryClient.invalidateQueries({ queryKey: ["teacherCourses"] });
      queryClient.invalidateQueries({ queryKey: ["teacherDashboard"] });
      queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
      toast.success("Course created successfully!");
      router.push(`/dashboard/teacher/courses/${course.id}`);
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to create course. Try again.");
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
              href="/dashboard/teacher"
              className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-extrabold text-white">Create Course</h1>
              <p className="text-zinc-400 text-xs mt-0.5">Scaffold a new learning track for your students.</p>
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              {/* Title */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Course Title</label>
                <input
                  type="text"
                  placeholder="Introduction to Programming"
                  {...register("title")}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
                {errors.title && (
                  <span className="text-xs text-red-400 font-semibold">{errors.title.message}</span>
                )}
              </div>

              {/* Description */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Course Description</label>
                <textarea
                  rows={4}
                  placeholder="Provide a detailed description of what students will master..."
                  {...register("description")}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
                />
                {errors.description && (
                  <span className="text-xs text-red-400 font-semibold">{errors.description.message}</span>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Category */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Category</label>
                  <input
                    type="text"
                    placeholder="Computer Science"
                    {...register("category")}
                    className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                  />
                  {errors.category && (
                    <span className="text-xs text-red-400 font-semibold">{errors.category.message}</span>
                  )}
                </div>

                {/* Level */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Difficulty Level</label>
                  <select
                    {...register("level")}
                    className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none select-none appearance-none"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
              </div>

              {/* Price */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Course price</label>
                <select aria-label="Course pricing" value={selectedPrice > 0 ? "paid" : "free"} onChange={(event) => setValue("price", event.target.value === "free" ? 0 : 1, { shouldValidate: true })} className="w-full bg-zinc-950/45 border border-zinc-800 text-white rounded-xl px-4 py-3 text-sm">
                  <option value="free">Free</option><option value="paid">Paid</option>
                </select>
                {selectedPrice > 0 && <>
                  <label className="text-xs text-zinc-400">Price (INR)</label>
                  <input aria-label="Price in Indian rupees" type="number" min="0.01" step="0.01" placeholder="499.00" {...register("price", { valueAsNumber: true })} className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none" />
                  <p className="text-xs text-amber-300">Paid courses are sold via Razorpay Checkout in INR (Test Mode).</p>
                </>}
                {errors.price && (
                  <span className="text-xs text-red-400 font-semibold">{errors.price.message}</span>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="glow-btn mt-2 py-3.5 px-6 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-lg transition flex items-center justify-center gap-2 cursor-pointer"
              >
                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                Create Course
              </button>
            </form>
          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
