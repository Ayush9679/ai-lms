"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { quizService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PageTransition } from "@/components/shared/PageTransitions";
import { ArrowLeft, Loader2, Sparkles, Brain } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

const aiQuizSchema = zod.object({
  title: zod.string().min(3, "Title must be at least 3 characters long"),
  difficulty: zod.enum(["easy", "medium", "hard"]),
  num_questions: zod.number().min(1).max(20),
  source_type: zod.enum(["text"]), // simplified for easy text pasting
  source_text: zod.string().min(15, "Please provide some source text for the AI to study"),
});

type AIQuizForm = zod.infer<typeof aiQuizSchema>;

export default function AIQuizGeneratorPage() {
  const { courseId } = useParams();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AIQuizForm>({
    resolver: zodResolver(aiQuizSchema),
    defaultValues: {
      difficulty: "medium",
      num_questions: 5,
      source_type: "text",
    },
  });

  const onSubmit = async (data: AIQuizForm) => {
    setIsSubmitting(true);
    try {
      await quizService.generateAI(courseId as string, data);
      toast.success("AI Quiz generated and saved successfully!");
      router.push(`/dashboard/teacher/courses/${courseId}`);
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to generate AI Quiz. Ensure your Gemini key is valid.");
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
              <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-purple-400" />
                AI Quiz Generator
              </h1>
              <p className="text-zinc-400 text-xs mt-0.5">Let Google Gemini AI design tailored practice questions.</p>
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6 relative overflow-hidden">
            {isSubmitting ? (
              <div className="py-12 flex flex-col items-center justify-center gap-4 text-center">
                <div className="w-16 h-16 rounded-full bg-purple-950/20 border border-purple-500/30 flex items-center justify-center animate-pulse">
                  <Brain className="w-8 h-8 text-purple-400 animate-spin" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Generating Quiz Questions</h3>
                  <p className="text-sm text-zinc-400 mt-1 max-w-xs mx-auto">
                    AI is scanning your text, formatting MCQ options, and structuring correct answers...
                  </p>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
                
                {/* Title */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Quiz Title</label>
                  <input
                    type="text"
                    placeholder="AI Generated Quiz - Calculus I"
                    {...register("title")}
                    className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                  />
                  {errors.title && (
                    <span className="text-xs text-red-400 font-semibold">{errors.title.message}</span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Difficulty */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Difficulty Level</label>
                    <select
                      {...register("difficulty")}
                      className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>

                  {/* Num Questions */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Question Count</label>
                    <input
                      type="number"
                      placeholder="5"
                      {...register("num_questions", { valueAsNumber: true })}
                      className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                    />
                    {errors.num_questions && (
                      <span className="text-xs text-red-400 font-semibold">{errors.num_questions.message}</span>
                    )}
                  </div>
                </div>

                {/* Source Text */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Source Materials / Lesson Paste</label>
                  <textarea
                    rows={8}
                    placeholder="Paste textbook definitions, lecture slides, or study guidelines..."
                    {...register("source_text")}
                    className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
                  />
                  {errors.source_text && (
                    <span className="text-xs text-red-400 font-semibold">{errors.source_text.message}</span>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="glow-btn mt-2 py-3.5 px-6 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-lg transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Sparkles className="w-4 h-4 text-white" />
                  Generate AI Quiz
                </button>
              </form>
            )}
          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
