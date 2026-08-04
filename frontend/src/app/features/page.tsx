"use client";

import React from "react";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { ParticlesBackground } from "@/components/3d/Particles";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Sparkles, Play, Trophy, Users, Shield, Cpu } from "lucide-react";

export default function FeaturesPage() {
  const specs = [
    {
      title: "Google Gemini 1.5 Integration",
      desc: "Instant text parsing, code block validation, and context-aware responses directly referenced from uploaded PDFs.",
      icon: Cpu,
    },
    {
      title: "Interactive Video Player",
      desc: "Seamlessly streams course lecture videos while displaying slide decks and hosting AI helper sidebars.",
      icon: Play,
    },
    {
      title: "Manual & AI Quiz Builders",
      desc: "Generate random MCQs based on custom difficulties, complete with correct options validation and detailed explanations.",
      icon: Trophy,
    },
    {
      title: "Role-Based Navigation",
      desc: "Separate dashboard layouts tailored for students (progress trackers), teachers (grading managers), and administrators.",
      icon: Users,
    },
    {
      title: "Axios Token Auto-Refresh",
      desc: "Robust security layer using JWT access token expirations and automatic background rotation using refresh cookies.",
      icon: Shield,
    },
    {
      title: "Interactive Notes & Flashcards",
      desc: "Convert text or transcripts into structured guides and playable flip flashcard blocks instantly.",
      icon: Sparkles,
    },
  ];

  return (
    <div className="min-h-screen relative flex flex-col justify-between overflow-x-hidden">
      <ParticlesBackground />
      <Header />

      <main className="flex-grow pt-32 pb-20 max-w-5xl mx-auto px-4 w-full z-10 text-left">
        <PageTransition>
          <div className="flex flex-col gap-10">
            <div className="text-center mb-6">
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white">Platform Capabilities</h1>
              <p className="text-zinc-400 text-sm mt-2 max-w-md mx-auto">
                Explore the modular subsystems that power our Enterprise AI Learning Management System.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {specs.map((spec, i) => {
                const Icon = spec.icon;
                return (
                  <div key={i} className="glass-card rounded-2xl p-6 flex flex-col gap-4">
                    <div className="p-3 bg-purple-950/40 rounded-xl flex items-center justify-center w-fit text-purple-400">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex flex-col gap-2">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wide">{spec.title}</h3>
                      <p className="text-xs text-zinc-400 leading-relaxed">{spec.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </PageTransition>
      </main>

      <Footer />
    </div>
  );
}
