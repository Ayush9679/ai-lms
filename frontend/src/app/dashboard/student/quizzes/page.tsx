"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { quizService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Trophy, CheckCircle, XCircle } from "lucide-react";

export default function QuizHistoryPage() {
  const { data: history, isLoading } = useQuery({
    queryKey: ["studentQuizHistoryFull"],
    queryFn: quizService.getStudentHistory,
  });

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">
          
          <div>
            <h1 className="text-3xl font-extrabold text-white">Quiz Achievements</h1>
            <p className="text-zinc-400 text-sm mt-1">Review your practice attempts and graded score cards.</p>
          </div>

          {isLoading ? (
            <TableSkeleton />
          ) : history && history.length > 0 ? (
            <div className="glass-card rounded-3xl p-6 overflow-hidden">
              <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800/80 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                      <th className="py-3 px-3">Quiz Name</th>
                      <th className="py-3 px-3 text-center">Score Marks</th>
                      <th className="py-3 px-3 text-center">Percentage</th>
                      <th className="py-3 px-3 text-center">Grade Result</th>
                      <th className="py-3 px-3 text-right">Attempt Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((attempt) => (
                      <tr key={attempt.id} className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-950/20">
                        <td className="py-4 px-3 font-semibold text-white">
                          {attempt.quiz?.title || "AI Generated Quiz"}
                        </td>
                        <td className="py-4 px-3 text-center text-zinc-350">
                          {attempt.score} / {attempt.max_score}
                        </td>
                        <td className="py-4 px-3 text-center font-bold text-zinc-300">
                          {attempt.percentage}%
                        </td>
                        <td className="py-4 px-3 text-center">
                          {attempt.passed ? (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-green-400">
                              <CheckCircle className="w-3.5 h-3.5" />
                              PASSED
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-red-400">
                              <XCircle className="w-3.5 h-3.5" />
                              FAILED
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-3 text-right text-xs text-zinc-500">
                          {new Date(attempt.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
              <Trophy className="w-10 h-10 text-zinc-600 mb-2" />
              <h3 className="text-base font-bold text-white">No Quizzes Evaluated</h3>
              <p className="text-sm text-zinc-500 mt-1">Start playing a lesson and click on Quizzes tab to take tests.</p>
            </div>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
