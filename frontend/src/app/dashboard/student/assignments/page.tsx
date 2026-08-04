"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { assignmentService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { FileText, CheckCircle, Clock } from "lucide-react";

export default function MyAssignmentsPage() {
  const { data: submissions, isLoading } = useQuery({
    queryKey: ["myAssignmentsListFull"],
    queryFn: assignmentService.getMySubmissions,
  });

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">
          
          <div>
            <h1 className="text-3xl font-extrabold text-white">Assignments Tracker</h1>
            <p className="text-zinc-400 text-sm mt-1">Review the grades and feedback for your homework submissions.</p>
          </div>

          {isLoading ? (
            <TableSkeleton />
          ) : submissions && submissions.length > 0 ? (
            <div className="glass-card rounded-3xl p-6 overflow-hidden">
              <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800/80 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                      <th className="py-3 px-3">Subject / Files</th>
                      <th className="py-3 px-3 text-center">Marks Obtained</th>
                      <th className="py-3 px-3 text-center">Status</th>
                      <th className="py-3 px-3 text-right">Submitted Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {submissions.map((sub) => (
                      <tr key={sub.id} className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-950/20">
                        <td className="py-4 px-3 font-semibold text-white">
                          {sub.file_name || "Text Submission answers"}
                        </td>
                        <td className="py-4 px-3 text-center text-zinc-350">
                          {sub.marks_obtained !== null ? (
                            <span className="font-bold text-purple-400">{sub.marks_obtained}</span>
                          ) : (
                            "Pending"
                          )}
                        </td>
                        <td className="py-4 px-3 text-center">
                          {sub.graded_at ? (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-green-400">
                              <CheckCircle className="w-3.5 h-3.5" />
                              GRADED
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-blue-400">
                              <Clock className="w-3.5 h-3.5 animate-spin" />
                              SUBMITTED
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-3 text-right text-xs text-zinc-500">
                          {new Date(sub.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
              <FileText className="w-10 h-10 text-zinc-600 mb-2" />
              <h3 className="text-base font-bold text-white">No Homework Submitted</h3>
              <p className="text-sm text-zinc-500 mt-1">Assignments are posted in individual lesson pages.</p>
            </div>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
