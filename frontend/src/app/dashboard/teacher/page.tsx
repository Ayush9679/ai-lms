"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { StatsSkeleton, TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  BookOpen,
  Users,
  Trophy,
  Plus,
  ChevronRight,
  TrendingUp,
  Settings,
  Edit3,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function TeacherDashboard() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(timer);
  }, []);

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ["teacherDashboard"],
    queryFn: dashboardService.getTeacher,
  });

  const barChartData = dashboardData
    ? dashboardData.course_list.map((c) => ({
        name: c.title.length > 15 ? c.title.substring(0, 15) + "..." : c.title,
        students: c.enrollments_count,
        progress: Math.round(c.average_progress),
      }))
    : [];

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-8 text-left">
          
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold text-white">Instructor Workspace</h1>
              <p className="text-zinc-400 text-sm mt-1">Review student progress, update lessons, and deploy new quizzes.</p>
            </div>
            <Link
              href="/dashboard/teacher/courses/new"
              className="glow-btn flex items-center justify-center gap-2 py-3 px-5 text-sm font-semibold bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white rounded-xl shadow-md transition w-fit"
            >
              <Plus className="w-4 h-4" />
              Create New Course
            </Link>
          </div>

          {isLoading ? (
            <div className="flex flex-col gap-6">
              <StatsSkeleton />
              <TableSkeleton />
            </div>
          ) : (
            <>
              {/* Stats Row */}
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
                    {dashboardData?.course_stats.total_courses || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Total Courses Created</p>
                </div>

                {/* Stats 2 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-blue-950/40 border border-blue-500/10 flex items-center justify-center">
                      <Users className="w-6 h-6 text-blue-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Students</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.student_stats.total_students || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Total Student Enrolled</p>
                </div>

                {/* Stats 3 */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-pink-950/40 border border-pink-500/10 flex items-center justify-center">
                      <Trophy className="w-6 h-6 text-pink-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Quizzes</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.quiz_stats.total_quizzes_built || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Active Quizzes Generated</p>
                </div>

                {/* Recent student activity from the teacher dashboard API */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div className="p-3 rounded-2xl bg-green-950/40 border border-green-500/10 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-green-400" />
                    </div>
                    <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Earnings</span>
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    {dashboardData?.student_stats.active_students_this_month || 0}
                  </h3>
                  <p className="text-xs text-zinc-400">Students active this month</p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Course List table */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-purple-400" />
                      Active Courses Directory
                    </h3>
                    <div className="overflow-x-auto w-full">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b border-zinc-800/80 text-xs font-bold text-zinc-500 uppercase tracking-wider">
                            <th className="py-3.5 px-3">Course Title</th>
                            <th className="py-3.5 px-3 text-center">Students</th>
                            <th className="py-3.5 px-3 text-center">Avg Progress</th>
                            <th className="py-3.5 px-3 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {dashboardData?.course_list && dashboardData.course_list.length > 0 ? (
                            dashboardData.course_list.map((course) => (
                              <tr key={course.id} className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-950/20">
                                <td className="py-4 px-3">
                                  <div>
                                    <p className="text-sm font-bold text-white leading-normal">{course.title}</p>
                                    <p className="text-[10px] text-zinc-500 mt-1 uppercase font-semibold">
                                      {course.lessons_count} lessons • {course.quizzes_count} quizzes
                                    </p>
                                  </div>
                                </td>
                                <td className="py-4 px-3 text-center text-sm font-semibold text-zinc-300">
                                  {course.enrollments_count}
                                </td>
                                <td className="py-4 px-3 text-center">
                                  <span className="text-xs font-bold text-purple-400">
                                    {Math.round(course.average_progress)}%
                                  </span>
                                </td>
                                <td className="py-4 px-3 text-right">
                                  <div className="flex items-center justify-end gap-2">
                                    <Link
                                      href={`/dashboard/teacher/courses/${course.id}`}
                                      className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
                                      title="Edit Course"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                    </Link>
                                    <Link
                                      href={`/courses/${course.id}`}
                                      className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
                                      title="View Details"
                                    >
                                      <ChevronRight className="w-4 h-4" />
                                    </Link>
                                  </div>
                                </td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={4} className="py-8 text-center text-sm text-zinc-500">
                                You have not created any courses yet.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Course Metrics Chart sidebar */}
                <div className="flex flex-col gap-6">
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                      <Users className="w-4 h-4 text-purple-400" />
                      Enrollment Ratios
                    </h3>
                    <div className="h-64 w-full">
                      {mounted && barChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={barChartData} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f1f23" vertical={false} />
                            <XAxis dataKey="name" stroke="#52525b" fontSize={10} tickLine={false} />
                            <YAxis stroke="#52525b" fontSize={10} tickLine={false} />
                            <Tooltip
                              contentStyle={{
                                background: "rgba(20, 20, 25, 0.9)",
                                border: "1px solid rgba(255, 255, 255, 0.08)",
                                borderRadius: "12px",
                                color: "#fff",
                                fontSize: "12px",
                              }}
                            />
                            <Bar dataKey="students" fill="#a855f7" radius={[6, 6, 0, 0]} maxBarSize={30} />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-full flex items-center justify-center border border-dashed border-zinc-800/80 rounded-2xl">
                          <p className="text-sm text-zinc-500">No student enrollment metrics to chart.</p>
                        </div>
                      )}
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
