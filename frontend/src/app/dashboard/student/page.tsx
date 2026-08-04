"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { dashboardService, enrollmentService, quizService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { StatsSkeleton, TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  GraduationCap,
  BookOpen,
  Trophy,
  Flame,
  ChevronRight,
  Sparkles,
  Calendar,
  Clock,
  FileText,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function StudentDashboard() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(timer);
  }, []);

  // Fetch Dashboard Stats
  const { data: dashboardData, isLoading: statsLoading } = useQuery({
    queryKey: ["studentDashboard"],
    queryFn: dashboardService.getStudent,
  });

  // Fetch Quiz history for charts
  const { data: quizHistory } = useQuery({
    queryKey: ["studentQuizHistory"],
    queryFn: quizService.getStudentHistory,
  });

  // Fetch My Enrollments
  const { data: enrollments } = useQuery({
    queryKey: ["myEnrollments"],
    queryFn: enrollmentService.listMy,
  });

  const chartData = quizHistory
    ? quizHistory
        .slice()
        .reverse()
        .map((attempt) => ({
          name: attempt.quiz?.title || "Quiz",
          score: attempt.percentage,
        }))
    : [];

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-8 text-left">
          
          {/* Welcoming Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold text-white">Student Hub</h1>
              <p className="text-zinc-400 text-sm mt-1">Review your enrollments, quiz achievements, and AI recommendations.</p>
            </div>
            <Link
              href="/courses"
              className="glow-btn flex items-center justify-center gap-2 py-3 px-5 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-md transition w-fit"
            >
              Explore Course Catalog
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          {/* LOADING STATE */}
          {statsLoading ? (
            <div className="flex flex-col gap-6">
              <StatsSkeleton />
              <TableSkeleton />
            </div>
          ) : (
            <>
              {/* STATS CARDS */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
                {/* Stats 1 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-purple-950/40 border border-purple-500/10 flex items-center justify-center">
                      <BookOpen className="w-6 h-6 text-purple-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Courses</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.progress_summary.total_courses || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Total Enrolled Courses</p>
                </div>

                {/* Stats 2 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-blue-950/40 border border-blue-500/10 flex items-center justify-center">
                      <GraduationCap className="w-6 h-6 text-blue-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Avg Progress</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {Math.round(dashboardData?.progress_summary.average_progress || 0)}%
                  </h3>
                  <p className="text-xs text-zinc-400">Course completion average</p>
                </div>

                {/* Stats 3 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-pink-950/40 border border-pink-500/10 flex items-center justify-center">
                      <Trophy className="w-6 h-6 text-pink-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Quiz average</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {Math.round(dashboardData?.quiz_summary.average_score || 0)}%
                  </h3>
                  <p className="text-xs text-zinc-400">Across {dashboardData?.quiz_summary.total_quizzes_taken || 0} quizzes</p>
                </div>

                {/* Stats 4 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-orange-950/40 border border-orange-500/10 flex items-center justify-center">
                      <Flame className="w-6 h-6 text-orange-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Streak</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">5 Days</h3>
                  <p className="text-xs text-zinc-400">Active learning streak</p>
                </div>
              </div>

              {/* CORE DASHBOARD DETAILS */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Left Columns (Charts & Activities) */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                  {/* Quiz Progress Chart */}
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Trophy className="w-4 h-4 text-purple-400" />
                      Quiz Performance Progress
                    </h3>
                    <div className="h-64 w-full">
                      {mounted && chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                              <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f1f23" vertical={false} />
                            <XAxis dataKey="name" stroke="#52525b" fontSize={10} tickLine={false} />
                            <YAxis domain={[0, 100]} stroke="#52525b" fontSize={10} tickLine={false} />
                            <Tooltip
                              contentStyle={{
                                background: "rgba(20, 20, 25, 0.9)",
                                border: "1px solid rgba(255, 255, 255, 0.08)",
                                borderRadius: "12px",
                                color: "#fff",
                                fontSize: "12px",
                              }}
                            />
                            <Area type="monotone" dataKey="score" stroke="#a855f7" strokeWidth={2.5} fillOpacity={1} fill="url(#colorScore)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center border border-dashed border-zinc-800/80 rounded-2xl">
                          <p className="text-sm text-zinc-500">Take your first quiz to display performance metrics.</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* My Enrolled Courses Progress */}
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-purple-400" />
                      My Active Courses
                    </h3>
                    <div className="flex flex-col gap-3">
                      {enrollments && enrollments.length > 0 ? (
                        enrollments.map((enr) => (
                          <div key={enr.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-zinc-950/40 border border-zinc-900/60">
                            <div>
                              <h4 className="text-sm font-bold text-white">{enr.course?.title}</h4>
                              <p className="text-xs text-zinc-500 mt-1">Completed: {enr.completed_lessons} lessons</p>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="flex flex-col text-right">
                                <span className="text-xs font-semibold text-zinc-300">{Math.round(enr.progress)}%</span>
                                <div className="w-24 bg-zinc-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                                  <div className="bg-purple-600 h-full rounded-full" style={{ width: `${enr.progress}%` }} />
                                </div>
                              </div>
                              <Link
                                href={`/courses/${enr.course_id}`}
                                className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white"
                              >
                                <ChevronRight className="w-4 h-4" />
                              </Link>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="py-8 flex flex-col items-center justify-center border border-dashed border-zinc-800/80 rounded-2xl">
                          <p className="text-sm text-zinc-500">You are not enrolled in any courses yet.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Column (Sidebar Items) */}
                <div className="flex flex-col gap-6">
                  {/* Recommendations panel */}
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      AI Next-Steps
                    </h3>
                    <div className="flex flex-col gap-3">
                      <div className="p-4 rounded-2xl bg-purple-950/15 border border-purple-500/10 flex flex-col gap-2">
                        <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest">Recommended Topic</span>
                        <h4 className="text-sm font-bold text-white">Advanced Function Closures</h4>
                        <p className="text-xs text-zinc-400 leading-relaxed">AI notes indicate weakness in Lexical scoping. Review lesson 3.</p>
                        <Link
                          href="/ai"
                          className="mt-2 text-xs font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 w-fit"
                        >
                          Ask AI Tutor
                          <ChevronRight className="w-3 h-3" />
                        </Link>
                      </div>
                      
                      <div className="p-4 rounded-2xl bg-zinc-950/40 border border-zinc-900/60 flex flex-col gap-2">
                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Recommended Task</span>
                        <h4 className="text-sm font-bold text-white">Generate Practice Quiz</h4>
                        <p className="text-xs text-zinc-400 leading-relaxed">Test yourself on closed definitions before the final test.</p>
                        <Link
                          href="/ai"
                          className="mt-2 text-xs font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1 w-fit"
                        >
                          Generate Quiz
                          <ChevronRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  </div>

                  {/* Calendar Widget */}
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-purple-400" />
                      Study Scheduler
                    </h3>
                    <div className="p-4 rounded-2xl bg-zinc-950/40 border border-zinc-900/60 flex flex-col gap-3">
                      <div className="flex items-center gap-3">
                        <Clock className="w-4 h-4 text-purple-400" />
                        <div>
                          <p className="text-xs font-bold text-white">Daily Learning Goal</p>
                          <p className="text-[10px] text-zinc-500 mt-0.5">1 hour / day • 45m left</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <FileText className="w-4 h-4 text-blue-400" />
                        <div>
                          <p className="text-xs font-bold text-white">Closing Assignment</p>
                          <p className="text-[10px] text-zinc-500 mt-0.5">Calculus homework • Due tomorrow</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </>
          )}

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
