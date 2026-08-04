"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assignmentService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { FileText, Award, CheckCircle, ChevronRight, Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

function SubmissionsContent() {
  const searchParams = useSearchParams();
  const assignmentId = searchParams.get("assignment_id");
  const queryClient = useQueryClient();

  const [selectedSubId, setSelectedSubId] = useState<string | null>(null);
  const [marks, setMarks] = useState<number>(0);
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch Submissions list
  const { data: submissions, isLoading } = useQuery({
    queryKey: ["submissionsList", assignmentId],
    queryFn: () => assignmentService.getSubmissions(assignmentId as string),
    enabled: !!assignmentId,
  });

  const gradeMutation = useMutation({
    mutationFn: (data: { submissionId: string; marks_obtained: number; feedback: string }) =>
      assignmentService.gradeSubmission(data.submissionId, {
        marks_obtained: data.marks_obtained,
        feedback: data.feedback,
      }),
    onSuccess: () => {
      toast.success("Submission graded successfully!");
      setSelectedSubId(null);
      setMarks(0);
      setFeedback("");
      queryClient.invalidateQueries({ queryKey: ["submissionsList", assignmentId] });
    },
    onError: () => {
      toast.error("Failed to submit grades.");
    },
  });

  const handleOpenGrader = (subId: string, currentMarks: number | null, currentFeedback: string | null) => {
    setSelectedSubId(subId);
    setMarks(currentMarks || 0);
    setFeedback(currentFeedback || "");
  };

  const handleGradeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubId) return;

    gradeMutation.mutate({
      submissionId: selectedSubId,
      marks_obtained: marks,
      feedback: feedback,
    });
  };

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">
          
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard/teacher"
              className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-3xl font-extrabold text-white">Grading Dashboard</h1>
              <p className="text-zinc-400 text-sm mt-1">Grade student submissions and provide structured critiques.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-2 items-start">
            
            {/* Submissions list (Left columns) */}
            <div className="lg:col-span-2 flex flex-col gap-4">
              {isLoading ? (
                <TableSkeleton />
              ) : submissions && submissions.length > 0 ? (
                <div className="glass-card rounded-3xl p-6 overflow-hidden">
                  <div className="overflow-x-auto w-full">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-zinc-800/80 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                          <th className="py-3 px-3">Student Name</th>
                          <th className="py-3 px-3">Submission Details</th>
                          <th className="py-3 px-3 text-center">Score Marks</th>
                          <th className="py-3 px-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {submissions.map((sub) => (
                          <tr key={sub.id} className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-950/20">
                            <td className="py-4 px-3 font-semibold text-white">
                              {sub.student?.full_name || "Student"}
                            </td>
                            <td className="py-4 px-3 text-xs text-zinc-400 max-w-[200px] truncate">
                              {sub.text_content || sub.file_name || "Files submitted"}
                            </td>
                            <td className="py-4 px-3 text-center text-sm font-bold text-purple-400">
                              {sub.marks_obtained !== null ? sub.marks_obtained : "-"}
                            </td>
                            <td className="py-4 px-3 text-right">
                              <button
                                onClick={() => handleOpenGrader(sub.id, sub.marks_obtained, sub.feedback)}
                                className="py-1.5 px-3 bg-zinc-900 border border-zinc-850 hover:border-zinc-700 text-xs font-bold text-zinc-300 hover:text-white rounded-xl transition cursor-pointer"
                              >
                                Grade
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
                  <FileText className="w-10 h-10 text-zinc-650 mb-2" />
                  <h3 className="text-base font-bold text-zinc-400">No submissions uploaded</h3>
                  <p className="text-xs text-zinc-500 mt-1">Students have not uploaded answers for this assignment yet.</p>
                </div>
              )}
            </div>

            {/* Grading dialog card (Right column) */}
            <div className="flex flex-col gap-4">
              {selectedSubId ? (
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4 border border-purple-500/25 bg-purple-950/5 animate-in fade-in slide-in-from-right-5 duration-200">
                  <h3 className="text-base font-bold text-white flex items-center gap-1.5">
                    <Award className="w-5 h-5 text-purple-400" />
                    Enter Grades
                  </h3>
                  <form onSubmit={handleGradeSubmit} className="flex flex-col gap-4 text-xs">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-zinc-450 uppercase tracking-wider">Marks Awarded</label>
                      <input
                        type="number"
                        value={marks}
                        onChange={(e) => setMarks(parseFloat(e.target.value) || 0)}
                        className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-zinc-450 uppercase tracking-wider">Critique & Feedback</label>
                      <textarea
                        rows={5}
                        placeholder="Write constructive suggestions or explanations..."
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none resize-none"
                      />
                    </div>

                    <div className="flex gap-2 mt-2">
                      <button
                        type="submit"
                        disabled={gradeMutation.isPending}
                        className="glow-btn flex-1 py-3 px-4 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-bold rounded-xl shadow-md transition flex items-center justify-center gap-1.5 cursor-pointer"
                      >
                        {gradeMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                        Save Grade
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelectedSubId(null)}
                        className="py-3 px-4 bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white rounded-xl font-bold transition"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <div className="glass-card rounded-3xl p-6 text-center py-12 flex flex-col items-center justify-center gap-3 border border-zinc-850">
                  <Award className="w-8 h-8 text-zinc-650" />
                  <h4 className="font-bold text-zinc-400 text-xs">Select Submission to Grade</h4>
                  <p className="text-[10px] text-zinc-550 leading-relaxed max-w-[180px]">
                    Click on the Grade button inside any table row on the left to grade marks.
                  </p>
                </div>
              )}
            </div>

          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}

export default function GradeSubmissionsPage() {
  return (
    <Suspense fallback={<DashboardLayout><TableSkeleton /></DashboardLayout>}>
      <SubmissionsContent />
    </Suspense>
  );
}
export const dynamic = "force-dynamic";

