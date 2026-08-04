"use client";

import React from "react";
import Link from "next/link";
import { Brain, Terminal, Send, Globe } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-zinc-900 bg-[#06060a] relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,rgba(168,85,247,0.02),transparent_50%)] -z-10" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12">
          {/* Logo & Info */}
          <div className="flex flex-col gap-4">
            <Link href="/" className="flex items-center gap-2 text-white font-bold text-lg">
              <div className="bg-gradient-to-tr from-purple-600 to-blue-500 p-1.5 rounded-xl flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="bg-gradient-to-r from-white via-white to-purple-400 bg-clip-text text-transparent tracking-wide font-extrabold">
                AI-LMS
              </span>
            </Link>
            <p className="text-sm text-zinc-500 leading-relaxed max-w-xs">
              Enterprise AI-powered Learning Management System built with Next.js, FastAPI, and Google Gemini AI.
            </p>
            <div className="flex items-center gap-4 text-zinc-400">
              <Link href="https://github.com" className="hover:text-white transition"><Terminal className="w-5 h-5" /></Link>
              <Link href="https://twitter.com" className="hover:text-white transition"><Send className="w-5 h-5" /></Link>
              <Link href="https://linkedin.com" className="hover:text-white transition"><Globe className="w-5 h-5" /></Link>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Platform</h4>
            <div className="flex flex-col gap-2.5">
              <Link href="/courses" className="text-sm text-zinc-400 hover:text-white transition">Explore Courses</Link>
              <Link href="/features" className="text-sm text-zinc-400 hover:text-white transition">AI Features</Link>
              <Link href="/pricing" className="text-sm text-zinc-400 hover:text-white transition">Pricing Plans</Link>
            </div>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Company</h4>
            <div className="flex flex-col gap-2.5">
              <Link href="/about" className="text-sm text-zinc-400 hover:text-white transition">About Us</Link>
              <Link href="/" className="text-sm text-zinc-400 hover:text-white transition">Contact</Link>
              <Link href="/" className="text-sm text-zinc-400 hover:text-white transition">Careers</Link>
            </div>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Legal</h4>
            <div className="flex flex-col gap-2.5">
              <Link href="/" className="text-sm text-zinc-400 hover:text-white transition">Privacy Policy</Link>
              <Link href="/" className="text-sm text-zinc-400 hover:text-white transition">Terms of Service</Link>
            </div>
          </div>
        </div>

        <div className="h-px bg-zinc-900 my-8 md:my-10" />

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-zinc-600">
          <p>© {new Date().getFullYear()} AI-LMS. All rights reserved.</p>
          <p>Engineered with Next.js & FastAPI</p>
        </div>
      </div>
    </footer>
  );
};
export default Footer;
