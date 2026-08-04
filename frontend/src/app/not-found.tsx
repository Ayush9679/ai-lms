"use client";

import React from "react";
import Link from "next/link";
import { ParticlesBackground } from "@/components/3d/Particles";
import { Brain, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center relative px-4 text-center">
      {/* Background anim */}
      <ParticlesBackground />

      <div className="relative z-10 flex flex-col items-center gap-6 max-w-md">
        <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-3 rounded-2xl flex items-center justify-center animate-bounce">
          <Brain className="w-8 h-8 text-white" />
        </div>

        <div>
          <h1 className="text-6xl font-black text-white">404</h1>
          <h2 className="text-xl font-bold text-zinc-300 mt-2">Workspace Lost in Space</h2>
          <p className="text-xs text-zinc-500 mt-2 leading-relaxed">
            The study page or administrative dashboard you are seeking does not exist or has been archived.
          </p>
        </div>

        <Link
          href="/"
          className="glow-btn py-3.5 px-6 text-sm font-bold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl shadow-lg transition flex items-center gap-2 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Safety
        </Link>
      </div>
    </div>
  );
}
