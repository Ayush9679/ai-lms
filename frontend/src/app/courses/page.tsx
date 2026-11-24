"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { courseService } from "@/services/api";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { CourseCardSkeleton } from "@/components/shared/SkeletonLoaders";
import { ParticlesBackground } from "@/components/3d/Particles";
import { PageTransition } from "@/components/shared/PageTransitions";
import { Search, SlidersHorizontal, BookOpen, GraduationCap } from "lucide-react";

export default function CoursesCatalogPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedLevel, setSelectedLevel] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const { data, isLoading } = useQuery({
    queryKey: ["coursesCatalog", searchTerm, selectedLevel, selectedCategory],
    queryFn: () =>
      courseService.listPublic({
        search: searchTerm || undefined,
        level: selectedLevel !== "all" ? selectedLevel : undefined,
        category: selectedCategory !== "all" ? selectedCategory : undefined,
      }),
  });

  const categories = ["all", "Computer Science", "Mathematics", "Science", "Business"];

  return (
    <div className="min-h-screen relative flex flex-col justify-between overflow-x-hidden">
      {/* 3D background */}
      <ParticlesBackground />

      <Header />

      <main className="flex-grow pt-32 pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full z-10 text-left">
        
        {/* Catalog Header */}
        <div className="mb-10">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white">Course Library</h1>
          <p className="text-zinc-400 text-sm mt-2">Explore our collection of expert-led courses and AI tutoring modules.</p>
        </div>

        {/* SEARCH & FILTERS CONTROLS */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          
          {/* Search Input */}
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              placeholder="Search courses by title, keywords, or topics..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-2xl pl-11 pr-4 py-3 text-sm focus:outline-none transition-all"
            />
          </div>

          {/* Level Filter */}
          <div className="flex items-center gap-3 shrink-0">
            <SlidersHorizontal className="w-4 h-4 text-zinc-500" />
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-2xl px-4 py-3 text-sm focus:outline-none transition-all"
            >
              <option value="all">All Difficulty Levels</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>

        {/* CATEGORY TAGS */}
        <div className="flex flex-wrap gap-2.5 mb-10">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`py-2 px-4 rounded-xl text-xs font-bold capitalize transition border ${
                selectedCategory === cat
                  ? "bg-purple-950/30 text-purple-300 border-purple-500/35"
                  : "bg-zinc-950/45 text-zinc-400 border-zinc-800/80 hover:border-zinc-700"
              }`}
            >
              {cat === "all" ? "All Tracks" : cat}
            </button>
          ))}
        </div>

        {/* COURSE GRID */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <CourseCardSkeleton key={i} />
            ))}
          </div>
        ) : data && data.items && data.items.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.items.map((course) => (
              <Link
                key={course.id}
                href={`/courses/${course.id}`}
                className="glass-card rounded-3xl overflow-hidden p-4 flex flex-col gap-4 group cursor-pointer hover:scale-[1.01]"
              >
                {/* Thumbnail */}
                <div className="w-full aspect-video rounded-2xl bg-zinc-950 overflow-hidden relative border border-zinc-850/60">
                  {course.thumbnail ? (
                    <img
                      src={course.thumbnail}
                      alt={course.title}
                      className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-tr from-purple-950/30 to-blue-950/30 text-purple-400">
                      <BookOpen className="w-8 h-8" />
                      <span className="text-[10px] uppercase font-bold tracking-wider mt-2">AI-LMS Hub</span>
                    </div>
                  )}
                  {/* Difficulty Tag */}
                  <span className="absolute top-3 left-3 bg-black/60 backdrop-blur-md text-[10px] font-bold text-zinc-300 uppercase tracking-widest px-2.5 py-1 rounded-full border border-white/5">
                    {course.level}
                  </span>
                </div>

                {/* Info */}
                <div className="flex-1 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs text-zinc-500">
                    <span className="font-semibold">{course.category || "General"}</span>
                    <span>{course.total_lessons} lessons</span>
                  </div>
                  <h3 className="text-base font-bold text-white leading-snug group-hover:text-purple-300 transition-colors">
                    {course.title}
                  </h3>
                  <p className="text-xs text-zinc-400 line-clamp-2 mt-1 leading-relaxed">
                    {course.description || "Master these skills through comprehensive structures and AI-powered test questions."}
                  </p>
                </div>

                <div className="h-px bg-zinc-900/60 my-1" />

                {/* Footer Info */}
                <div className="flex items-center justify-between mt-auto">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-extrabold text-purple-400 uppercase border border-purple-500/10">
                      {course.instructor_name[0]}
                    </div>
                    <span className="text-xs text-zinc-400 font-semibold truncate max-w-[120px]">
                      {course.instructor_name}
                    </span>
                  </div>
                  <span className="text-sm font-black text-white">
                    {course.price === 0 ? "Free" : new Intl.NumberFormat("en-IN", { style: "currency", currency: course.currency ?? "INR" }).format(course.price)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
            <BookOpen className="w-10 h-10 text-zinc-600 mb-2 animate-bounce" />
            <h3 className="text-base font-bold text-white">No Courses Found</h3>
            <p className="text-sm text-zinc-500 mt-1">Try adapting your search parameters or category filter.</p>
          </div>
        )}

      </main>

      <Footer />
    </div>
  );
}
