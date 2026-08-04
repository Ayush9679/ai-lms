"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { StatsSkeleton, TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Users, BookOpen, GraduationCap, ShieldAlert, Activity } from "lucide-react";

export default function AdminDashboard() {
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ["adminDashboard"],
    queryFn: dashboardService.getAdmin,
  });

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-8 text-left">
          
          {/* Header */}
          <div>
            <h1 className="text-3xl font-extrabold text-white">Admin Command Center</h1>
            <p className="text-zinc-400 text-sm mt-1">Global platform metrics, user counts, and audit logs.</p>
          </div>

          {isLoading ? (
            <div className="flex flex-col gap-6">
              <StatsSkeleton />
              <TableSkeleton />
            </div>
          ) : (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
                {/* Metric 1 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-purple-950/40 border border-purple-500/10 flex items-center justify-center">
                      <Users className="w-6 h-6 text-purple-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Users</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.metrics.total_users || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Registered platform accounts</p>
                </div>

                {/* Metric 2 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-blue-950/40 border border-blue-500/10 flex items-center justify-center">
                      <GraduationCap className="w-6 h-6 text-blue-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Students</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.metrics.total_students || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Active student profiles</p>
                </div>

                {/* Metric 3 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-pink-950/40 border border-pink-500/10 flex items-center justify-center">
                      <BookOpen className="w-6 h-6 text-pink-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Courses</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.metrics.total_courses || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Total courses mapped</p>
                </div>

                {/* Metric 4 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-green-950/40 border border-green-500/10 flex items-center justify-center">
                      <Activity className="w-6 h-6 text-green-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Enrollments</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.metrics.total_enrollments || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Total active enrollment joins</p>
                </div>
              </div>

              {/* Active Logs / User audits */}
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="w-4.5 h-4.5 text-purple-400" />
                  Recent System Events
                </h3>
                <div className="flex flex-col gap-3.5 mt-2">
                  {dashboardData?.recent_activity && dashboardData.recent_activity.length > 0 ? (
                    dashboardData.recent_activity.map((act: any, idx: number) => (
                      <div
                        key={idx}
                        className="py-3 px-4 rounded-xl bg-zinc-950/45 border border-zinc-900/60 text-xs text-zinc-400 flex items-center justify-between"
                      >
                        <span>{act.message || "System parameter modified"}</span>
                        <span className="text-[10px] text-zinc-600 font-bold">
                          {act.timestamp ? new Date(act.timestamp).toLocaleDateString() : "Just now"}
                        </span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-zinc-500 text-center py-6">No platform audits recorded.</p>
                  )}
                </div>
              </div>
            </>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
