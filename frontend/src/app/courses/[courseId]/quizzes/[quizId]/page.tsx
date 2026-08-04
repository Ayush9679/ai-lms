"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { quizService, enrollmentService } from "@/services/api";
import { useAuth } from "@/providers/AuthProvider";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { ParticlesBackground } from "@/components/3d/Particles";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Trophy, ArrowLeft, Loader2, CheckCircle2, XCircle, HelpCircle } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function TakeQuizPage() {
  const { courseId, quizId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();

  // Enrollment guard
  const { data: enrollmentStatus, isLoading: enrollmentLoading } = useQuery({
    queryKey: ["enrollmentStatus", courseId],
    queryFn: () => enrollmentService.getStatus(courseId as string),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (!enrollmentLoading && enrollmentStatus && !enrollmentStatus.is_enrolled) {
      router.replace(`/courses/${courseId}`);
    }
  }, [isAuthenticated, enrollmentLoading, enrollmentStatus, courseId, router]);

  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [attemptResult, setAttemptResult] = useState<any | null>(null);

  // Fetch Quiz details (with questions list)
  const { data: quiz, isLoading } = useQuery({
    queryKey: ["quizTaking", quizId],
    queryFn: () => quizService.getDetails(quizId as string),
  });

  const submitMutation = useMutation({
    mutationFn: (answersArray: Array<{ question_id: string; given_answer: string }>) =>
      quizService.submitAttempt(quizId as string, {
        answers: answersArray,
        time_taken_seconds: 45,
      }),
    onSuccess: (data) => {
      setAttemptResult(data);
      toast.success("Quiz submitted successfully!");
      queryClient.invalidateQueries({ queryKey: ["studentQuizHistory"] });
    },
    onError: (err: any) => {
      console.error(err);
      toast.error(err.response?.data?.message || "Failed to submit attempt.");
    },
  });

  const handleSelectOption = (questionId: string, optionText: string) => {
    if (attemptResult) return; // quiz already submitted
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionText,
    }));
  };

  const handleQuizSubmit = () => {
    if (!quiz?.questions) return;
    
    // Map record to array of items
    const payload = quiz.questions.map((q) => ({
      question_id: q.id,
      given_answer: answers[q.id] || "",
    }));

    submitMutation.mutate(payload);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (!quiz) return null;

  return (
    <div className="min-h-screen bg-[#020204] flex flex-col justify-between overflow-x-hidden">
      <ParticlesBackground />
      <Header />

      <main className="flex-grow pt-32 pb-20 max-w-3xl mx-auto px-4 w-full z-10 text-left">
        
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Link
            href={`/courses/${courseId}`}
            className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white leading-snug">{quiz.title}</h1>
            <p className="text-xs text-zinc-400 mt-1">Passing: {quiz.passing_score}% • Max Attempts: {quiz.max_attempts || "Unlimited"}</p>
          </div>
        </div>

        {attemptResult ? (
          /* QUIZ SCORE RESULTS PANEL */
          <PageTransition>
            <div className="flex flex-col gap-6">
              <div className="glass-card rounded-3xl p-8 flex flex-col items-center justify-center gap-4 text-center border-t-2 border-t-purple-500">
                <Trophy className="w-12 h-12 text-purple-400" />
                <div>
                  <h2 className="text-2xl font-black text-white">Quiz Completed</h2>
                  <p className="text-sm text-zinc-400 mt-1">
                    Graded Score: <span className="text-purple-400 font-bold">{attemptResult.score}</span> / {attemptResult.max_score} marks
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 w-full max-w-sm mt-4 bg-zinc-950/40 p-4 border border-zinc-900 rounded-2xl">
                  <div className="text-center">
                    <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Percentage</p>
                    <p className="text-lg font-bold text-white mt-1">{attemptResult.percentage}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Result</p>
                    <p className={`text-lg font-bold mt-1 ${attemptResult.passed ? "text-green-400" : "text-red-400"}`}>
                      {attemptResult.passed ? "PASSED" : "FAILED"}
                    </p>
                  </div>
                </div>

                <Link
                  href={`/courses/${courseId}`}
                  className="w-full max-w-sm mt-2 flex items-center justify-center gap-2 text-sm bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-bold py-3.5 rounded-xl shadow-md transition cursor-pointer"
                >
                  Return to Course Space
                </Link>
              </div>

              {/* Questions Review list */}
              <div className="flex flex-col gap-4 mt-2">
                <h3 className="text-base font-bold text-white">Answer Verification</h3>
                {quiz.questions?.map((q, idx) => {
                  const studentAns = answers[q.id];
                  const isCorrect = studentAns?.trim().toLowerCase() === q.correct_answer?.trim().toLowerCase() ||
                    q.options?.find((opt) => opt.text === studentAns)?.is_correct;

                  return (
                    <div key={q.id} className="glass-card rounded-2xl p-6 flex flex-col gap-4">
                      <div className="flex items-start justify-between gap-4">
                        <h4 className="text-sm font-bold text-white flex gap-2">
                          <span className="text-zinc-500">{idx + 1}.</span>
                          {q.question_text}
                        </h4>
                        {isCorrect ? (
                          <span className="flex items-center gap-1 text-xs font-bold text-green-400 shrink-0">
                            <CheckCircle2 className="w-4 h-4 text-green-400 fill-green-400/10" />
                            Correct
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs font-bold text-red-400 shrink-0">
                            <XCircle className="w-4 h-4 text-red-400 fill-red-400/10" />
                            Incorrect
                          </span>
                        )}
                      </div>

                      {/* Display options */}
                      {q.options && (
                        <div className="grid grid-cols-1 gap-2">
                          {q.options.map((opt, oIdx) => {
                            const isSelected = opt.text === studentAns;
                            const isCorrectOpt = opt.is_correct;
                            return (
                              <div
                                key={oIdx}
                                className={`p-3 rounded-xl border text-xs font-semibold flex items-center justify-between transition ${
                                  isCorrectOpt
                                    ? "bg-green-950/20 text-green-300 border-green-500/20"
                                    : isSelected
                                    ? "bg-red-950/20 text-red-300 border-red-500/20"
                                    : "bg-zinc-950/40 text-zinc-450 border-zinc-900/60"
                                }`}
                              >
                                <span>{opt.text}</span>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Explanation */}
                      {q.explanation && (
                        <div className="p-3 bg-purple-950/10 border border-purple-500/5 rounded-xl flex gap-2.5 text-xs mt-2 text-zinc-400">
                          <HelpCircle className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                          <div>
                            <p className="font-bold text-purple-400">AI Explanation</p>
                            <p className="mt-1 leading-relaxed">{q.explanation}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </PageTransition>
        ) : (
          /* QUIZ QUESTIONS TAKING FLOW */
          <PageTransition>
            <div className="flex flex-col gap-6">
              {quiz.questions && quiz.questions.length > 0 ? (
                quiz.questions.map((q, idx) => (
                  <div key={q.id} className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                    <h3 className="text-sm font-bold text-white flex gap-2 leading-relaxed">
                      <span className="text-zinc-500">{idx + 1}.</span>
                      {q.question_text}
                    </h3>

                    {/* Renders MCQ option buttons */}
                    {q.options && (
                      <div className="grid grid-cols-1 gap-3 mt-1">
                        {q.options.map((opt, oIdx) => {
                          const isSelected = answers[q.id] === opt.text;
                          return (
                            <button
                              key={oIdx}
                              onClick={() => handleSelectOption(q.id, opt.text)}
                              className={`p-3 rounded-xl border text-xs font-semibold text-left transition cursor-pointer ${
                                isSelected
                                  ? "bg-purple-950/30 text-purple-300 border-purple-500/40"
                                  : "bg-zinc-950/45 text-zinc-400 border-zinc-900 hover:border-zinc-800"
                              }`}
                            >
                              {opt.text}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center">
                  <p className="text-zinc-500 text-sm">This quiz has no questions.</p>
                </div>
              )}

              {quiz.questions && quiz.questions.length > 0 && (
                <button
                  onClick={handleQuizSubmit}
                  disabled={submitMutation.isPending}
                  className="glow-btn py-4 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-sm font-bold text-white rounded-2xl flex items-center justify-center gap-1.5 shadow-lg shadow-purple-500/10 cursor-pointer mt-4"
                >
                  {submitMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                  Submit Answers
                </button>
              )}
            </div>
          </PageTransition>
        )}

      </main>

      <Footer />
    </div>
  );
}
