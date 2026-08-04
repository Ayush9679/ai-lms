"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { enrollmentService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { BookOpen, ChevronRight } from "lucide-react";

export default function MyCoursesPage() {
  const { data: enrollments, isLoading } = useQuery({
    queryKey: ["myCoursesList"],
    queryFn: enrollmentService.listMy,
  });

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">
          
          <div>
            <h1 className="text-3xl font-extrabold text-white">My Active Tracks</h1>
            <p className="text-zinc-400 text-sm mt-1">Review the tracks you have joined and check progress ratios.</p>
          </div>

          {isLoading ? (
            <TableSkeleton />
          ) : enrollments && enrollments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {enrollments.map((enr) => (
                <div key={enr.id} className="glass-card rounded-3xl p-5 flex flex-col gap-4 justify-between">
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">{enr.course?.category || "General"}</span>
                    <h3 className="text-base font-bold text-white leading-snug">{enr.course?.title}</h3>
                    <p className="text-xs text-zinc-400 line-clamp-2 mt-1">{enr.course?.description}</p>
                  </div>

                  <div className="flex items-center justify-between border-t border-zinc-900/60 pt-4 mt-2">
                    <div className="flex flex-col">
                      <span className="text-xs font-semibold text-zinc-300">Progress: {Math.round(enr.progress)}%</span>
                      <div className="w-32 bg-zinc-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                        <div className="bg-purple-600 h-full rounded-full" style={{ width: `${enr.progress}%` }} />
                      </div>
                    </div>

                    <Link
                      href={`/courses/${enr.course_id}`}
                      className="glow-btn flex items-center justify-center gap-1 py-2 px-4 text-xs font-semibold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl shadow-md transition cursor-pointer"
                    >
                      Continue
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
              <BookOpen className="w-10 h-10 text-zinc-600 mb-2" />
              <h3 className="text-base font-bold text-white">No Enrollments Joined</h3>
              <p className="text-sm text-zinc-500 mt-1">Explore our course catalog and pick a track to begin!</p>
            </div>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
