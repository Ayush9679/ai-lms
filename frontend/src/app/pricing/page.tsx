"use client";

import React from "react";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { ParticlesBackground } from "@/components/3d/Particles";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Check, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function PricingPage() {
  const tiers = [
    {
      name: "Tutor Free",
      price: "$0",
      desc: "Perfect for testing interactive lecture players and course syllabus directories.",
      feats: ["Access to all public courses", "Basic AI Chat queries", "Take quiz attempts"],
      action: "Get Started",
      color: "border-zinc-800/80",
    },
    {
      name: "Pro Learner",
      price: "$19",
      desc: "For serious students seeking unlimited Gemini AI helpers and custom calendars.",
      feats: ["Unlimited AI Chat sessions", "Draft lecture notes & PDF exports", "Generate study flashcards", "Personalized weekly plans"],
      action: "Upgrade Now",
      color: "border-purple-500/25 bg-purple-950/5 shadow-purple-500/5 shadow-lg",
    },
    {
      name: "Enterprise",
      price: "Custom",
      desc: "For colleges and schools looking to build full curricula and map custom roles.",
      feats: ["Multi-tenant administrator controls", "Advanced student progress analytics", "Unlimited course creation capabilities", "Dedicated Gemini token thresholds"],
      action: "Contact Sales",
      color: "border-zinc-800/80",
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
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white">Simple Pricing</h1>
              <p className="text-zinc-400 text-sm mt-2 max-w-md mx-auto">
                No hidden costs. Choose the tier that matches your study load.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
              {tiers.map((tier, i) => (
                <div
                  key={i}
                  className={`glass-card rounded-3xl p-6 flex flex-col justify-between border ${tier.color}`}
                >
                  <div className="flex flex-col gap-4">
                    <div>
                      <h3 className="text-base font-bold text-white uppercase tracking-wider">{tier.name}</h3>
                      <p className="text-xs text-zinc-550 mt-1">{tier.desc}</p>
                    </div>
                    <div className="flex items-baseline gap-1 mt-2">
                      <span className="text-3xl font-black text-white">{tier.price}</span>
                      {tier.price !== "Custom" && <span className="text-zinc-500 text-xs">/month</span>}
                    </div>

                    <div className="h-px bg-zinc-900/60 my-2" />

                    <div className="flex flex-col gap-3">
                      {tier.feats.map((feat, fIdx) => (
                        <div key={fIdx} className="flex items-start gap-2.5 text-xs text-zinc-400 leading-normal">
                          <Check className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                          <span>{feat}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <Link
                    href="/register"
                    className="glow-btn mt-8 w-full flex items-center justify-center gap-1.5 py-3 text-xs font-bold bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 text-white rounded-xl transition cursor-pointer"
                  >
                    {tier.action}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </PageTransition>
      </main>

      <Footer />
    </div>
  );
}
