"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import {
  GraduationCap,
  BookOpen,
  Trophy,
  Sparkles,
  User as UserIcon,
  Settings,
  LogOut,
  Menu,
  X,
  Brain,
  FileText,
  BarChart,
  Users,
  Compass,
  ArrowLeftRight,
} from "lucide-react";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const { user, logout, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-blue-500 animate-spin flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <p className="text-sm text-zinc-400 font-medium">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Define sidebar menu options based on role
  const getMenuLinks = () => {
    const studentLinks = [
      { name: "Dashboard", href: "/dashboard/student", icon: GraduationCap },
      { name: "All Courses", href: "/courses", icon: Compass },
      { name: "My Enrollments", href: "/dashboard/student/courses", icon: BookOpen },
      { name: "Quiz History", href: "/dashboard/student/quizzes", icon: Trophy },
      { name: "Assignments", href: "/dashboard/student/assignments", icon: FileText },
      { name: "AI Learning Space", href: "/ai", icon: Sparkles },
    ];

    const teacherLinks = [
      { name: "Dashboard", href: "/dashboard/teacher", icon: BarChart },
      { name: "Manage Courses", href: "/dashboard/teacher/courses", icon: BookOpen },
      { name: "Grade Submissions", href: "/dashboard/teacher/submissions", icon: FileText },
      { name: "AI Tools", href: "/ai", icon: Sparkles },
    ];

    const adminLinks = [
      { name: "Dashboard", href: "/dashboard/admin", icon: BarChart },
      { name: "Users Directory", href: "/dashboard/admin/users", icon: Users },
      { name: "Courses Manager", href: "/dashboard/admin/courses", icon: BookOpen },
      { name: "AI Tools", href: "/ai", icon: Sparkles },
    ];

    const commonLinks = [
      { name: "Profile", href: "/dashboard/profile", icon: UserIcon },
      { name: "Settings", href: "/dashboard/settings", icon: Settings },
    ];

    let base: Array<{ name: string; href: string; icon: any }> = [];
    if (user.role === "student") base = studentLinks;
    else if (user.role === "teacher") base = teacherLinks;
    else if (user.role === "admin") base = adminLinks;

    return [...base, ...commonLinks];
  };

  const links = getMenuLinks();

  const isActive = (href: string) => {
    if (href === "/ai" && pathname.startsWith("/ai")) return true;
    if (href === "/courses" && pathname.startsWith("/courses")) return true;
    return pathname === href;
  };

  return (
    <div className="min-h-screen bg-[#030306] flex">
      {/* BACKGROUND EFFECTS */}
      <div className="absolute inset-0 bg-grid radial-gradient-mask -z-10 pointer-events-none" />
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-purple-950/5 rounded-full blur-[120px] -z-10 pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-blue-950/5 rounded-full blur-[100px] -z-10 pointer-events-none" />

      {/* DESKTOP SIDEBAR */}
      <aside className="hidden lg:flex flex-col w-64 glass-panel border-y-0 border-l-0 p-4 shrink-0">
        <Link href="/" className="flex items-center gap-2.5 px-3 py-4 mb-6">
          <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-2 rounded-2xl flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="bg-gradient-to-r from-white via-white to-purple-400 bg-clip-text text-transparent font-extrabold text-lg tracking-wide">
            AI-LMS
          </span>
        </Link>

        {/* Navigation */}
        <nav className="flex-1 flex flex-col gap-1">
          {links.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold transition border border-transparent ${
                  active
                    ? "bg-purple-950/30 text-purple-300 border-purple-500/10 shadow-sm shadow-purple-500/5"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40"
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? "text-purple-400" : "text-zinc-400"}`} />
                {link.name}
              </Link>
            );
          })}
        </nav>

        {/* User Card */}
        <div className="border-t border-zinc-900 pt-4 flex flex-col gap-3">
          <div className="flex items-center gap-3 px-3">
            {user.profile_image ? (
              <img
                src={user.profile_image}
                alt={user.full_name}
                className="w-9 h-9 rounded-full object-cover"
              />
            ) : (
              <div className="w-9 h-9 rounded-full bg-purple-600 flex items-center justify-center font-bold text-white text-sm">
                {user.full_name[0].toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-white truncate">{user.full_name}</p>
              <p className="text-xs text-zinc-500 capitalize">{user.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2.5 px-4 py-2.5 rounded-2xl text-sm font-semibold text-red-400 hover:text-red-300 hover:bg-red-950/15 border border-transparent hover:border-red-900/20 transition text-left"
          >
            <LogOut className="w-4 h-4" />
            Log out
          </button>
        </div>
      </aside>

      {/* MOBILE HEADER & CONTAINER */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden glass-panel border-x-0 border-t-0 p-4 flex items-center justify-between z-30 shrink-0">
          <Link href="/" className="flex items-center gap-2">
            <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-1.5 rounded-xl flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="font-extrabold text-base text-white tracking-wide">AI-LMS</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-zinc-400 hover:text-white p-1.5 rounded-full hover:bg-zinc-900/50"
          >
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-10 relative">
          {children}
        </main>
      </div>

      {/* MOBILE DRAWER SIDEBAR */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="fixed top-0 bottom-0 left-0 w-64 glass-panel border-y-0 border-l-0 p-4 z-50 lg:hidden flex flex-col animate-in slide-in-from-left duration-250">
            <Link href="/" className="flex items-center gap-2.5 px-3 py-4 mb-6" onClick={() => setSidebarOpen(false)}>
              <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-2 rounded-2xl flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="font-extrabold text-lg text-white tracking-wide">AI-LMS</span>
            </Link>

            <nav className="flex-1 flex flex-col gap-1">
              {links.map((link) => {
                const Icon = link.icon;
                const active = isActive(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold transition border border-transparent ${
                      active
                        ? "bg-purple-950/30 text-purple-300 border-purple-500/10"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/40"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {link.name}
                  </Link>
                );
              })}
            </nav>

            <div className="border-t border-zinc-900 pt-4 flex flex-col gap-3">
              <div className="flex items-center gap-3 px-3">
                {user.profile_image ? (
                  <img
                    src={user.profile_image}
                    alt={user.full_name}
                    className="w-9 h-9 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-purple-600 flex items-center justify-center font-bold text-white text-sm">
                    {user.full_name[0].toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="text-sm font-bold text-white leading-none mb-1">{user.full_name}</p>
                  <p className="text-xs text-zinc-500 capitalize">{user.role}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setSidebarOpen(false);
                  logout();
                }}
                className="w-full flex items-center gap-2.5 px-4 py-2.5 rounded-2xl text-sm font-semibold text-red-400 hover:text-red-300 hover:bg-red-950/15 transition text-left"
              >
                <LogOut className="w-4 h-4" />
                Log out
              </button>
            </div>
          </aside>
        </>
      )}
    </div>
  );
};
export default DashboardLayout;
