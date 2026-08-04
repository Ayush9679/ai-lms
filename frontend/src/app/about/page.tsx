"use client";

import React from "react";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { ParticlesBackground } from "@/components/3d/Particles";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Brain, Heart, Target } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="min-h-screen relative flex flex-col justify-between overflow-x-hidden">
      <ParticlesBackground />
      <Header />

      <main className="flex-grow pt-32 pb-20 max-w-4xl mx-auto px-4 w-full z-10 text-left">
        <PageTransition>
          <div className="flex flex-col gap-10">
            <div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white">Our Mission</h1>
              <p className="text-zinc-400 text-sm mt-2 leading-relaxed">
                Reimagining student curricula by weaving AI companions directly into textbook guidelines, lesson media, and weekly planners.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass-card rounded-2xl p-6 flex flex-col gap-3">
                <Brain className="w-8 h-8 text-purple-400" />
                <h3 className="text-sm font-bold text-white uppercase">AI Companion</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Tutor context-aware chats that explain lexical scopes and mathematical algorithms in real time.
                </p>
              </div>

              <div className="glass-card rounded-2xl p-6 flex flex-col gap-3">
                <Target className="w-8 h-8 text-blue-400" />
                <h3 className="text-sm font-bold text-white uppercase">Strict Analytics</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Deep quiz audits and submission records that identify study gaps and recommended reading tracks.
                </p>
              </div>

              <div className="glass-card rounded-2xl p-6 flex flex-col gap-3">
                <Heart className="w-8 h-8 text-pink-400" />
                <h3 className="text-sm font-bold text-white uppercase">Open Source</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Built on modern API structures with Next.js, FastAPI, and robust PostgreSQL schemas.
                </p>
              </div>
            </div>

            <div className="glass-card rounded-3xl p-8 flex flex-col gap-4">
              <h3 className="text-lg font-bold text-white">Our Story</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Founded in 2026, AI-LMS was built by principal software engineers aiming to solve N+1 study bottlenecks. By building an enterprise-grade Learning Management System that links student progress records with Gemini 1.5 Flash LLM context APIs, we empower students to learn at 3x efficiency, bypassing plain passive readings.
              </p>
            </div>
          </div>
        </PageTransition>
      </main>

      <Footer />
    </div>
  );
}
