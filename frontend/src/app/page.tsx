"use client";

import React from "react";
import Link from "next/link";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { AIBrainCanvas } from "@/components/3d/AIBrain";
import { ParticlesBackground } from "@/components/3d/Particles";
import { useAuth } from "@/providers/AuthProvider";
import {
  Brain,
  Sparkles,
  BookOpen,
  Trophy,
  Users,
  Terminal,
  Shield,
  Zap,
  ArrowRight,
  CheckCircle,
  HelpCircle,
  Video,
} from "lucide-react";
import { motion } from "framer-motion";

export default function LandingPage() {
  const { isAuthenticated, user } = useAuth();

  const features = [
    {
      title: "Interactive AI Tutor",
      desc: "Instant conversational guidance inside the player workspace, context-aware of your course files.",
      icon: Brain,
      color: "from-pink-500 to-rose-500",
    },
    {
      title: "Automated Quiz Generator",
      desc: "Generate quizzes based on lessons, transcripts, or uploaded textbooks instantly with custom difficulty settings.",
      icon: Sparkles,
      color: "from-purple-500 to-indigo-500",
    },
    {
      title: "Dynamic Study Planner",
      desc: "Weekly personalized planners mapped dynamically to your available study hours and core exams calendar.",
      icon: Trophy,
      color: "from-blue-500 to-cyan-500",
    },
    {
      title: "Video & PDF Player Workspace",
      desc: "A cohesive player that pairs video files with lecture note modules and real-time AI helpers.",
      icon: Video,
      color: "from-teal-500 to-emerald-500",
    },
  ];

  const companies = ["Vercel", "OpenAI", "Cursor", "Linear", "Stripe", "Tesla"];

  const getDashboardUrl = () => {
    return user ? `/dashboard/${user.role}` : "/login";
  };

  return (
    <div className="min-h-screen relative flex flex-col justify-between overflow-x-hidden">
      {/* 3D background */}
      <ParticlesBackground />

      {/* Navigation Header */}
      <Header />

      {/* HERO SECTION */}
      <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex flex-col lg:flex-row items-center gap-12 z-10">
        
        {/* Hero Left (Text) */}
        <div className="flex-1 flex flex-col text-left">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-purple-500/20 bg-purple-950/20 text-purple-300 text-xs font-semibold uppercase tracking-wider mb-6 w-fit"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Next-Gen Learning Experience
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-[1.1] mb-6"
          >
            Empower Your Study Journey with{" "}
            <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
              Gemini AI
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base sm:text-lg text-zinc-400 leading-relaxed mb-8 max-w-xl"
          >
            Scaffold interactive note modules, generate study calendars, practice real-time MCQ quizzes, and converse with an AI Tutor context-aware of your course documents.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4"
          >
            {isAuthenticated ? (
              <Link
                href={getDashboardUrl()}
                className="glow-btn px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-bold rounded-2xl flex items-center justify-center gap-2 shadow-lg hover:shadow-purple-500/20 transition-all cursor-pointer"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link
                  href="/register"
                  className="glow-btn px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-bold rounded-2xl flex items-center justify-center gap-2 shadow-lg hover:shadow-purple-500/20 transition-all cursor-pointer"
                >
                  Start Learning Free
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/courses"
                  className="px-8 py-4 bg-zinc-950/45 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/60 text-white font-semibold rounded-2xl flex items-center justify-center transition"
                >
                  Explore Courses
                </Link>
              </>
            )}
          </motion.div>
        </div>

        {/* Hero Right (3D Brain) */}
        <div className="flex-1 w-full flex items-center justify-center min-h-[300px]">
          <motion.div
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.15 }}
            className="w-full max-w-lg aspect-square relative"
          >
            {/* Glow backing */}
            <div className="absolute inset-0 bg-radial-gradient-mask pointer-events-none" />
            <div className="absolute inset-20 bg-purple-500/8 rounded-full blur-[80px] -z-10 pointer-events-none animate-pulse-slow" />
            <AIBrainCanvas />
          </motion.div>
        </div>
      </section>

      {/* COMPANIES SECTION */}
      <section className="relative border-y border-zinc-900 bg-zinc-950/20 py-10 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex flex-col md:flex-row items-center justify-between gap-6">
          <p className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Trusted by students at
          </p>
          <div className="flex flex-wrap items-center gap-x-10 gap-y-4">
            {companies.map((c) => (
              <span key={c} className="text-lg font-extrabold text-zinc-600 hover:text-zinc-400 transition tracking-tight">
                {c}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CORE FEATURES */}
      <section className="relative py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Core Ecosystem</h2>
          <p className="text-zinc-400 max-w-xl mx-auto leading-relaxed">
            Everything you need to master complex subjects, powered by state-of-the-art AI.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={i}
                className="glass-card rounded-3xl p-8 flex gap-6 text-left relative overflow-hidden group hover:scale-[1.01]"
              >
                {/* Glow dot hover */}
                <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition" />
                <div className={`p-4 rounded-2xl bg-gradient-to-tr ${f.color} flex items-center justify-center shrink-0 w-14 h-14 h-fit`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex flex-col gap-2">
                  <h3 className="text-lg font-bold text-white">{f.title}</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">{f.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* FAQ SECTION */}
      <section className="relative py-20 border-t border-zinc-900 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-white mb-4">Frequently Asked Questions</h2>
          <p className="text-zinc-400 max-w-md mx-auto">Got questions? We have answers.</p>
        </div>

        <div className="max-w-3xl mx-auto flex flex-col gap-4 text-left">
          {[
            {
              q: "How does the AI Tutor work?",
              a: "The AI Tutor utilizes Google Gemini 1.5 Flash API to analyze your courses and lessons. By querying context-aware documents, it responds to questions in real time, explaining code blocks or generating summary flashcards.",
            },
            {
              q: "Can teachers upload materials and track student progress?",
              a: "Yes! Teachers have a full course dashboard to manage lessons, upload PDF worksheets or MP4 videos, create quiz templates, view enrollment metrics, and grade assignments.",
            },
            {
              q: "Is there a limit on AI requests?",
              a: "To ensure fair usage, AI endpoints have rate-limiting of 10 requests per minute per user. This helps maintain stable performance for all users.",
            },
          ].map((faq, i) => (
            <div key={i} className="glass-card rounded-2xl p-6 flex gap-4">
              <HelpCircle className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
              <div className="flex flex-col gap-2">
                <h4 className="text-base font-bold text-white">{faq.q}</h4>
                <p className="text-sm text-zinc-400 leading-relaxed">{faq.a}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}
