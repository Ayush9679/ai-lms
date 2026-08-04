"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  lessonService,
  courseService,
  aiService,
  quizService,
  assignmentService,
} from "@/services/api";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  ArrowLeft,
  BookOpen,
  Sparkles,
  ChevronRight,
  MessageSquare,
  Play,
  File,
  Loader2,
  CheckCircle2,
  Send,
  Copy,
  Download,
  Lightbulb,
  Clock,
  ExternalLink,
  Trophy,
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function LessonPlayerPage() {
  const { courseId, lessonId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Tabs for the main area
  const [playerTab, setPlayerTab] = useState<"content" | "discussions" | "quizzes" | "assignments">("content");
  // Sub-workspace for the AI Companion (Right sidebar)
  const [aiWorkspace, setAiWorkspace] = useState<"chat" | "notes" | "flashcards" | "study-plan">("chat");

  // AI Chat states
  const [chatMessages, setChatMessages] = useState<Array<{ role: "user" | "model"; content: string }>>([
    { role: "model", content: "Hi! I am your Gemini AI study companion. Ask me anything about this lesson!" },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatSessionId, setChatSessionId] = useState<string | undefined>(undefined);
  const [isChatting, setIsChatting] = useState(false);

  // AI Notes states
  const [generatedNote, setGeneratedNote] = useState<{ title: string; content: string } | null>(null);
  const [isGeneratingNotes, setIsGeneratingNotes] = useState(false);

  // AI Flashcards states
  const [flashcardSet, setFlashcardSet] = useState<Array<{ front: string; back: string }>>([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isGeneratingCards, setIsGeneratingCards] = useState(false);

  // Study plan states
  const [generatedPlan, setGeneratedPlan] = useState<any | null>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);

  // Fetch Course details
  const { data: course } = useQuery({
    queryKey: ["courseDetails", courseId],
    queryFn: () => courseService.getDetails(courseId as string),
  });

  // Fetch current lesson
  const { data: lesson, isLoading: lessonLoading } = useQuery({
    queryKey: ["lessonDetails", lessonId],
    queryFn: () => lessonService.getDetails(lessonId as string),
  });

  // Fetch lessons list
  const { data: lessons } = useQuery({
    queryKey: ["courseLessons", courseId],
    queryFn: () => lessonService.listByCourse(courseId as string),
  });

  // Fetch lesson progress
  const { data: progress } = useQuery({
    queryKey: ["lessonProgress", lessonId],
    queryFn: () => lessonService.getProgress(lessonId as string),
  });

  // Fetch quizzes
  const { data: quizzes } = useQuery({
    queryKey: ["courseQuizzes", courseId],
    queryFn: () => quizService.listByCourse(courseId as string),
  });

  // Fetch assignments
  const { data: assignments } = useQuery({
    queryKey: ["courseAssignments", courseId],
    queryFn: () => assignmentService.listByCourse(courseId as string),
  });

  // Mutation for updating progress completeness
  const progressMutation = useMutation({
    mutationFn: (completed: boolean) =>
      lessonService.updateProgress(lessonId as string, {
        is_completed: completed,
        watch_time_seconds: 120,
        completion_percentage: completed ? 100 : 0,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lessonProgress", lessonId] });
      toast.success("Progress saved!");
    },
  });

  // AI Chat Submission
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatting) return;

    const userMsg = chatInput.trim();
    setChatMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setChatInput("");
    setIsChatting(true);

    try {
      const res = await aiService.chat(userMsg, chatSessionId, courseId as string);
      setChatSessionId(res.session_id);
      setChatMessages((prev) => [...prev, { role: "model", content: res.ai_response }]);
    } catch (err: any) {
      console.error(err);
      toast.error("AI chat failed. Try again.");
    } finally {
      setIsChatting(false);
    }
  };

  // Generate Notes
  const handleGenerateNotes = async () => {
    if (!lesson) return;
    setIsGeneratingNotes(true);
    try {
      const text = lesson.content || `Notes for lesson: ${lesson.title}`;
      const res = await aiService.generateNotes({
        source_type: "text",
        source_text: text,
        title: `AI Lecture Notes: ${lesson.title}`,
      });
      setGeneratedNote({ title: res.title, content: res.content });
      toast.success("Notes generated by Gemini!");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to generate AI notes.");
    } finally {
      setIsGeneratingNotes(false);
    }
  };

  // Generate Flashcards
  const handleGenerateFlashcards = async () => {
    if (!lesson) return;
    setIsGeneratingCards(true);
    try {
      const text = lesson.content || `Flashcards study for: ${lesson.title}`;
      const res = await aiService.generateFlashcards({
        source_type: "text",
        source_text: text,
        num_cards: 5,
        title: `AI Flashcards: ${lesson.title}`,
      });
      setFlashcardSet(res.cards);
      setCurrentCardIndex(0);
      setIsFlipped(false);
      toast.success("Study Flashcards generated!");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to generate flashcards.");
    } finally {
      setIsGeneratingCards(false);
    }
  };

  // Generate Study Plan
  const handleGeneratePlan = async () => {
    setIsGeneratingPlan(true);
    try {
      const res = await aiService.generateStudyPlan({
        course_id: courseId as string,
        topics: [lesson?.title || "Course topics"],
        duration_weeks: 4,
        hours_per_day: 1,
      });
      setGeneratedPlan(res.plan_data);
      toast.success("Personalized study calendar ready!");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to generate plan.");
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  if (lessonLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (!lesson) return null;

  return (
    <div className="min-h-screen bg-[#020204] flex flex-col justify-between overflow-x-hidden">
      <Header />

      <main className="flex-grow pt-24 px-4 md:px-8 max-w-7xl mx-auto w-full flex flex-col lg:flex-row gap-6 text-left">
        
        {/* Left main viewport (Lesson details, player tabs) */}
        <div className="flex-1 flex flex-col gap-6">
          
          {/* Breadcrumb Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Link
                href={`/courses/${courseId}`}
                className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <div>
                <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-semibold">
                  {course?.title}
                </p>
                <h1 className="text-xl font-bold text-white mt-1 leading-snug">{lesson.title}</h1>
              </div>
            </div>

            <button
              onClick={() => progressMutation.mutate(!progress?.is_completed)}
              disabled={progressMutation.isPending}
              className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold border transition cursor-pointer ${
                progress?.is_completed
                  ? "bg-purple-950/20 text-purple-300 border-purple-500/30"
                  : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-300"
              }`}
            >
              <CheckCircle2 className={`w-4 h-4 ${progress?.is_completed ? "text-purple-400 fill-purple-400/20" : ""}`} />
              {progress?.is_completed ? "Lesson Completed" : "Mark as Completed"}
            </button>
          </div>

          {/* Media Player Layer */}
          <div className="w-full aspect-video rounded-3xl bg-zinc-950 border border-zinc-900 overflow-hidden relative flex items-center justify-center">
            {lesson.video_url ? (
              <video src={lesson.video_url} controls className="w-full h-full object-contain" />
            ) : lesson.pdf_url ? (
              <div className="w-full h-full flex flex-col items-center justify-center gap-4 text-center p-8 bg-zinc-950">
                <File className="w-16 h-16 text-purple-400" />
                <div>
                  <h4 className="text-sm font-bold text-white">Lesson Slides Worksheet</h4>
                  <p className="text-xs text-zinc-500 mt-1">This lesson is accompanied by a study document.</p>
                </div>
                <a
                  href={lesson.pdf_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 px-4 py-2 text-xs bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 hover:text-white rounded-xl transition font-semibold"
                >
                  Open PDF Slides
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-center p-8 bg-gradient-to-tr from-purple-950/20 to-blue-950/20 text-purple-400">
                <BookOpen className="w-12 h-12" />
                <span className="text-xs font-bold uppercase tracking-wider mt-3">Text Lesson Workspace</span>
              </div>
            )}
          </div>

          {/* Main viewport Tabs */}
          <div className="flex border-b border-zinc-900">
            {(["content", "quizzes", "assignments"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setPlayerTab(tab)}
                className={`py-3 px-4 text-xs font-bold border-b-2 capitalize transition ${
                  playerTab === tab
                    ? "border-purple-500 text-purple-400"
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {tab === "content" ? "Lecture Guide" : tab}
              </button>
            ))}
          </div>

          {/* Tab Contents */}
          <div className="py-2">
            {playerTab === "content" && (
              <div className="prose prose-invert max-w-none text-zinc-300 text-sm leading-relaxed flex flex-col gap-4">
                {lesson.content ? (
                  <p>{lesson.content}</p>
                ) : (
                  <p className="text-zinc-500 italic">No syllabus explanations added. Use AI Tutor sidebar to inspect notes.</p>
                )}
              </div>
            )}

            {playerTab === "quizzes" && (
              <div className="flex flex-col gap-3">
                <h3 className="text-sm font-bold text-white mb-2">Available Quizzes</h3>
                {quizzes && quizzes.length > 0 ? (
                  quizzes.map((quiz) => (
                    <div
                      key={quiz.id}
                      className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60 flex items-center justify-between"
                    >
                      <div>
                        <h4 className="text-sm font-bold text-white">{quiz.title}</h4>
                        <p className="text-[10px] text-zinc-500 mt-1 uppercase font-semibold">
                          Passing: {quiz.passing_score}% • Max Attempts: {quiz.max_attempts || "Unlimited"}
                        </p>
                      </div>
                      <Link
                        href={`/courses/${courseId}/quizzes/${quiz.id}`}
                        className="glow-btn py-2 px-4 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-xs font-semibold text-white rounded-xl shadow-md transition cursor-pointer"
                      >
                        Start Quiz
                      </Link>
                    </div>
                  ))
                ) : (
                  <p className="text-zinc-500 text-sm">No quizzes posted for this course.</p>
                )}
              </div>
            )}

            {playerTab === "assignments" && (
              <div className="flex flex-col gap-3">
                <h3 className="text-sm font-bold text-white mb-2">Required Course Assignments</h3>
                {assignments && assignments.length > 0 ? (
                  assignments.map((asg) => (
                    <div
                      key={asg.id}
                      className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60 flex items-center justify-between"
                    >
                      <div>
                        <h4 className="text-sm font-bold text-white">{asg.title}</h4>
                        <p className="text-[10px] text-zinc-500 mt-1 font-semibold">
                          Max Marks: {asg.max_marks} • Due: {asg.due_date ? new Date(asg.due_date).toLocaleDateString() : "No deadline"}
                        </p>
                      </div>
                      <Link
                        href={`/courses/${courseId}/assignments/${asg.id}`}
                        className="py-2 px-4 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white rounded-xl transition"
                      >
                        Open Workspace
                      </Link>
                    </div>
                  ))
                ) : (
                  <p className="text-zinc-500 text-sm">No assignments posted for this course.</p>
                )}
              </div>
            )}
          </div>

        </div>

        {/* Right column: AI Workspace Side Panel */}
        <div className="w-full lg:w-96 shrink-0 flex flex-col gap-4">
          <div className="glass-card rounded-3xl p-5 border border-zinc-850 flex flex-col gap-4 h-[600px]">
            
            {/* Header select */}
            <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-purple-400" />
                AI Learning Copilot
              </h3>
              <select
                value={aiWorkspace}
                onChange={(e) => setAiWorkspace(e.target.value as any)}
                className="bg-zinc-950/45 border border-zinc-850 focus:border-purple-500/50 text-white rounded-xl px-2.5 py-1.5 text-xs font-semibold focus:outline-none"
              >
                <option value="chat">Ask AI Tutor</option>
                <option value="notes">Lecture Notes</option>
                <option value="flashcards">Flipping Flashcards</option>
                <option value="study-plan">Study Calendar</option>
              </select>
            </div>

            {/* AI Workspace view selectors */}
            <div className="flex-grow overflow-y-auto flex flex-col">
              
              {/* 1. CHAT WORKSPACE */}
              {aiWorkspace === "chat" && (
                <div className="flex flex-col h-full justify-between">
                  <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-3 max-h-[420px] text-xs">
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${
                          msg.role === "user"
                            ? "bg-purple-950/20 border border-purple-500/10 text-purple-200 self-end text-right"
                            : "bg-zinc-950 border border-zinc-900 text-zinc-300 self-start text-left"
                        }`}
                      >
                        <p>{msg.content}</p>
                      </div>
                    ))}
                    {isChatting && (
                      <div className="p-3 rounded-2xl bg-zinc-950 border border-zinc-900 text-zinc-400 self-start text-left flex items-center gap-2">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Tutor is thinking...
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleChatSubmit} className="flex gap-2 border-t border-zinc-900 pt-3 mt-auto">
                    <input
                      type="text"
                      placeholder="Ask AI about scopes..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      className="flex-1 bg-zinc-950/45 border border-zinc-850 focus:border-purple-500/50 text-white text-xs rounded-xl px-3 py-2.5 focus:outline-none"
                    />
                    <button
                      type="submit"
                      disabled={isChatting}
                      className="p-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl transition flex items-center justify-center"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </form>
                </div>
              )}

              {/* 2. NOTES WORKSPACE */}
              {aiWorkspace === "notes" && (
                <div className="flex flex-col gap-4 h-full text-xs">
                  {generatedNote ? (
                    <div className="flex flex-col gap-3 flex-grow justify-between">
                      <div className="p-4 rounded-2xl bg-zinc-950 border border-zinc-900 overflow-y-auto max-h-[360px] leading-relaxed">
                        <h4 className="font-bold text-white text-sm mb-2">{generatedNote.title}</h4>
                        <p className="whitespace-pre-line text-zinc-300">{generatedNote.content}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => copyToClipboard(generatedNote.content)}
                          className="flex-1 py-2.5 px-3 bg-zinc-900 hover:bg-zinc-850 border border-zinc-850 text-white font-bold rounded-xl flex items-center justify-center gap-1 transition"
                        >
                          <Copy className="w-3.5 h-3.5" />
                          Copy Notes
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="my-auto py-12 flex flex-col items-center justify-center gap-4 text-center">
                      <Lightbulb className="w-10 h-10 text-purple-400" />
                      <div>
                        <h4 className="font-bold text-white">Generate Structured Notes</h4>
                        <p className="text-[11px] text-zinc-500 mt-1 max-w-[200px]">
                          AI scans the lesson content to generate formatted guides with code clips.
                        </p>
                      </div>
                      <button
                        onClick={handleGenerateNotes}
                        disabled={isGeneratingNotes}
                        className="glow-btn py-2.5 px-5 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
                      >
                        {isGeneratingNotes ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Formatting...
                          </>
                        ) : (
                          "Generate Lesson Notes"
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* 3. FLASHCARDS WORKSPACE */}
              {aiWorkspace === "flashcards" && (
                <div className="flex flex-col gap-4 h-full justify-between text-xs">
                  {flashcardSet.length > 0 ? (
                    <div className="flex flex-col gap-4 flex-grow justify-between">
                      {/* Card viewport */}
                      <div
                        onClick={() => setIsFlipped(!isFlipped)}
                        className="w-full aspect-[4/3] rounded-2xl bg-zinc-950 border border-zinc-900 flex items-center justify-center p-6 text-center cursor-pointer hover:border-purple-500/20 transition-all select-none"
                      >
                        <div className="flex flex-col gap-2">
                          <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest">
                            {isFlipped ? "Answer" : "Question"}
                          </span>
                          <p className="text-sm font-bold text-white leading-relaxed">
                            {isFlipped ? flashcardSet[currentCardIndex].back : flashcardSet[currentCardIndex].front}
                          </p>
                        </div>
                      </div>

                      {/* Controls */}
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-[10px] text-zinc-500 font-bold">
                          Card {currentCardIndex + 1} of {flashcardSet.length}
                        </span>
                        <div className="flex gap-2">
                          <button
                            disabled={currentCardIndex === 0}
                            onClick={() => {
                              setCurrentCardIndex((c) => c - 1);
                              setIsFlipped(false);
                            }}
                            className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-850 rounded-lg text-white font-semibold disabled:opacity-40 transition"
                          >
                            Prev
                          </button>
                          <button
                            disabled={currentCardIndex === flashcardSet.length - 1}
                            onClick={() => {
                              setCurrentCardIndex((c) => c + 1);
                              setIsFlipped(false);
                            }}
                            className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-850 rounded-lg text-white font-semibold disabled:opacity-40 transition"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="my-auto py-12 flex flex-col items-center justify-center gap-4 text-center">
                      <Trophy className="w-10 h-10 text-pink-400" />
                      <div>
                        <h4 className="font-bold text-white">Generate Study Flashcards</h4>
                        <p className="text-[11px] text-zinc-500 mt-1 max-w-[200px]">
                          Create interactive flipping Q&A decks based on the syllabus.
                        </p>
                      </div>
                      <button
                        onClick={handleGenerateFlashcards}
                        disabled={isGeneratingCards}
                        className="glow-btn py-2.5 px-5 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
                      >
                        {isGeneratingCards ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Analyzing...
                          </>
                        ) : (
                          "Generate Flashcards"
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* 4. STUDY PLAN */}
              {aiWorkspace === "study-plan" && (
                <div className="flex flex-col gap-4 h-full justify-between text-xs">
                  {generatedPlan ? (
                    <div className="p-4 rounded-2xl bg-zinc-950 border border-zinc-900 overflow-y-auto max-h-[380px] leading-relaxed flex flex-col gap-3">
                      <h4 className="font-bold text-white text-sm">AI Study Schedule</h4>
                      {Object.keys(generatedPlan).map((weekKey) => (
                        <div key={weekKey} className="border-b border-zinc-900 pb-2 last:border-0">
                          <p className="text-purple-400 font-bold uppercase text-[10px] tracking-wide">{weekKey}</p>
                          <p className="text-zinc-300 mt-1">{generatedPlan[weekKey]}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="my-auto py-12 flex flex-col items-center justify-center gap-4 text-center">
                      <Clock className="w-10 h-10 text-blue-400" />
                      <div>
                        <h4 className="font-bold text-white">Build Study Plan Calendar</h4>
                        <p className="text-[11px] text-zinc-500 mt-1 max-w-[200px]">
                          Map out weekly timelines to cover materials ahead of finals dates.
                        </p>
                      </div>
                      <button
                        onClick={handleGeneratePlan}
                        disabled={isGeneratingPlan}
                        className="glow-btn py-2.5 px-5 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white font-bold rounded-xl flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
                      >
                        {isGeneratingPlan ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Mapping...
                          </>
                        ) : (
                          "Generate Study Plan"
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}

            </div>
          </div>
        </div>

      </main>

      <Footer />
    </div>
  );
}
