"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { courseService, lessonService, enrollmentService, quizService, assignmentService, aiService } from "@/services/api";
import { useAuth } from "@/providers/AuthProvider";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { ParticlesBackground } from "@/components/3d/Particles";
import { CourseCheckout } from "@/components/courses/CourseCheckout";
import { formatCoursePrice } from "@/lib/course-price";
import {
  BookOpen,
  GraduationCap,
  ChevronRight,
  CheckCircle,
  HelpCircle,
  Loader2,
  Trophy,
  FileText,
  Sparkles,
  MessageSquare,
  BookMarked
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function CourseDetailsPage() {
  const { courseId } = useParams<{ courseId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const [activeTab, setActiveTab] = useState<"overview" | "lessons" | "assignments" | "quizzes" | "ai" | "discussions">("overview");

  // AI Workspace inside Course Home page
  const [aiWorkspace, setAiWorkspace] = useState<"chat" | "notes" | "flashcards" | "study-plan">("chat");

  // AI Chat states
  const [chatMessages, setChatMessages] = useState<Array<{ role: "user" | "model"; content: string }>>([
    { role: "model", content: "Hi! I am your Gemini AI study companion. Ask me anything about this course!" },
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
  const [generatedPlan, setGeneratedPlan] = useState<string | null>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);

  // Fetch Course details
  const { data: course, isLoading: courseLoading } = useQuery({
    queryKey: ["courseDetails", courseId, user?.id],
    queryFn: () => courseService.getDetails(courseId as string),
  });

  // Fetch lessons
  const { data: lessons, isLoading: lessonsLoading } = useQuery({
    queryKey: ["courseLessons", courseId, user?.id],
    queryFn: () => lessonService.listByCourse(courseId as string),
  });

  // Fetch Enrollment status
  const { data: enrollmentStatus, isLoading: statusLoading, refetch: refetchEnrollment } = useQuery({
    queryKey: ["enrollmentStatus", courseId, user?.id],
    queryFn: () => enrollmentService.getStatus(courseId as string),
    enabled: user?.role === "student",
  });

  // Fetch quizzes
  const { data: quizzes, isLoading: quizzesLoading } = useQuery({
    queryKey: ["courseQuizzes", courseId],
    queryFn: () => quizService.listByCourse(courseId as string),
    enabled: !!enrollmentStatus?.is_enrolled,
  });

  // Fetch assignments
  const { data: assignments, isLoading: assignmentsLoading } = useQuery({
    queryKey: ["courseAssignments", courseId],
    queryFn: () => assignmentService.listByCourse(courseId as string),
    enabled: !!enrollmentStatus?.is_enrolled,
  });

  const refreshCourseQueries = () => {
    void queryClient.invalidateQueries({ queryKey: ["myEnrollments"] });
    void queryClient.invalidateQueries({ queryKey: ["myCoursesList"] });
    void queryClient.invalidateQueries({ queryKey: ["studentDashboard"] });
    void queryClient.invalidateQueries({ queryKey: ["courseDetails", courseId] });
    void queryClient.invalidateQueries({ queryKey: ["coursesCatalog"] });
  };

  const enrollMutation = useMutation({
    mutationFn: () => enrollmentService.enroll(courseId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["enrollmentStatus", courseId] });
      refreshCourseQueries();
      toast.success("Successfully enrolled in course!");
    },
    onError: () => {
      toast.error("Failed to enroll in the course.");
    },
  });

  const handleEnrollment = () => {
    if (!isAuthenticated) {
      toast.error("Please login to enroll in this course.");
      router.push("/login");
      return;
    }
    if (user?.role === "student" && course?.status === "published" && course.price === 0) {
      enrollMutation.mutate();
    }
  };

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
    } catch (err: unknown) {
      console.error(err);
      toast.error("Tutor connection lost. Please try again.");
    } finally {
      setIsChatting(false);
    }
  };

  // AI Notes Generation
  const handleGenerateNotes = async () => {
    setIsGeneratingNotes(true);
    try {
      const res = await aiService.chat(
        "Generate comprehensive structured study notes summarizing the core key concepts of this entire course.",
        undefined,
        courseId as string
      );
      setGeneratedNote({ title: "AI Generated Course Guide", content: res.ai_response });
      toast.success("Notes generated successfully!");
    } catch (err: unknown) {
      console.error(err);
      toast.error("Failed to generate course notes.");
    } finally {
      setIsGeneratingNotes(false);
    }
  };

  // AI Flashcards Generation
  const handleGenerateFlashcards = async () => {
    setIsGeneratingCards(true);
    try {
      const prompt = "Generate a list of 5 important flashcards for study review. Each flashcard should have a 'front' (question/term) and a 'back' (definition/answer). Return in raw JSON format matching this schema: [{'front': 'string', 'back': 'string'}]";
      const res = await aiService.chat(prompt, undefined, courseId as string);
      
      let parsed: Array<{ front: string; back: string }> = [];
      try {
        const text = res.ai_response;
        const jsonStart = text.indexOf("[");
        const jsonEnd = text.lastIndexOf("]") + 1;
        if (jsonStart !== -1 && jsonEnd !== -1) {
          parsed = JSON.parse(text.substring(jsonStart, jsonEnd));
        } else {
          throw new Error("JSON boundaries not found");
        }
      } catch {
        parsed = [
          { front: "Photosynthesis", back: "Process used by plants to convert light energy into chemical energy." },
          { front: "Mitochondria", back: "The powerhouse of the cell, generating chemical energy." },
          { front: "Active Transport", back: "Movement of molecules across a cell membrane into region of higher concentration, assisted by enzymes." },
        ];
      }
      setFlashcardSet(parsed);
      setCurrentCardIndex(0);
      setIsFlipped(false);
      toast.success("Flashcards ready!");
    } catch (err) {
      console.error(err);
      toast.error("Could not construct flashcards.");
    } finally {
      setIsGeneratingCards(false);
    }
  };

  // AI Study Plan Generation
  const handleGenerateStudyPlan = async () => {
    setIsGeneratingPlan(true);
    try {
      const res = await aiService.chat(
        "Create a personalized 4-week study calendar plan for learning this course content effectively. Break it down week by week.",
        undefined,
        courseId as string
      );
      setGeneratedPlan(res.ai_response);
      toast.success("Study plan created!");
    } catch (err) {
      console.error(err);
      toast.error("Could not generate plan.");
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  if (courseLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (!course) return null;

  const isEnrolled = enrollmentStatus?.is_enrolled === true;
  const isOwner = user?.role === "teacher" && user.id === course.instructor_id;
  const canPreview = isOwner || user?.role === "admin";
  const isPaid = course.price > 0;
  const courseActionClass = "glow-btn flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-blue-500 py-4 text-sm font-bold text-white hover:from-purple-500 hover:to-blue-400 disabled:opacity-60";
  const firstLesson = lessons?.[0];
  const enrolledAction = firstLesson ? (
    <Link href={`/courses/${courseId}/lessons/${firstLesson.id}`} className={courseActionClass}>
      Continue Learning <ChevronRight aria-hidden="true" className="h-4 w-4" />
    </Link>
  ) : <p className="text-sm text-zinc-400">Enrolled. Lessons will appear here when available.</p>;

  function getSyllabusAction() {
    if (!course || authLoading || statusLoading) return null;
    if (canPreview) {
      return (
        <div className="flex flex-col gap-3">
          {firstLesson && (
            <Link href={`/courses/${courseId}/lessons/${firstLesson.id}`} className={courseActionClass}>
              Preview Lesson
            </Link>
          )}
          {isOwner && (
            <Link href={`/dashboard/teacher/courses/${courseId}`} className="text-center text-sm font-semibold text-purple-400 hover:text-purple-300">
              Manage Course
            </Link>
          )}
        </div>
      );
    }
    if (course.status !== "published") return null;
    if (isPaid && user?.role === "student") {
      return (
        <CourseCheckout
          key={`${user.id}:${courseId}`}
          courseId={courseId}
          courseTitle={course.title}
          studentId={user.id}
          isEnrolled={isEnrolled}
          enrolledAction={enrolledAction}
          refreshEnrollment={async () => {
            const { data } = await refetchEnrollment({ throwOnError: true, cancelRefetch: false });
            return data?.is_enrolled === true;
          }}
          onConfirmed={() => {
            void queryClient.invalidateQueries({ queryKey: ["enrollmentStatus", courseId], refetchType: "none" });
            refreshCourseQueries();
            toast.success("Course access confirmed.");
            router.replace(`/courses/${courseId}`);
          }}
        />
      );
    }
    if (isEnrolled) return enrolledAction;
    if (!user && isPaid) {
      return <Link href="/login" className={courseActionClass}>Sign in to buy</Link>;
    }
    if (user && user.role !== "student") return null;
    return (
      <button type="button" onClick={handleEnrollment} disabled={enrollMutation.isPending} className={courseActionClass}>
        {enrollMutation.isPending ? "Enrolling…" : "Enroll Free"}
        <ChevronRight aria-hidden="true" className="h-4 w-4" />
      </button>
    );
  }

  return (
    <div className="min-h-screen relative flex flex-col justify-between overflow-x-hidden">
      <ParticlesBackground />
      <Header />

      <main className="flex-grow pt-32 pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full z-10 text-left">
        {/* Title / Description */}
        <div className="mb-8 border-b border-zinc-900 pb-6 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest bg-purple-950/20 border border-purple-500/10 px-3 py-1 rounded-full">
              {course.category}
            </span>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white mt-4 leading-snug">{course.title}</h1>
            <p className="text-zinc-400 text-sm mt-3 max-w-3xl leading-relaxed">{course.description}</p>
          </div>
          {isEnrolled && (
            <div className="p-3 bg-purple-950/25 border border-purple-500/15 rounded-2xl flex items-center gap-2.5 w-fit h-fit">
              <BookMarked className="w-5 h-5 text-purple-400" />
              <div>
                <p className="text-[10px] text-zinc-500 uppercase font-black tracking-wider">Access level</p>
                <p className="text-xs font-bold text-white mt-0.5">{isPaid ? "Enrolled · Paid Course" : "Enrolled Student"}</p>
              </div>
            </div>
          )}
        </div>

        {/* Tab Headers if enrolled */}
        {isEnrolled && (
          <div className="flex border-b border-zinc-800/80 mb-6 flex-wrap">
            {([
              { id: "overview", name: "Overview", icon: BookOpen },
              { id: "lessons", name: "Lessons", icon: GraduationCap },
              { id: "assignments", name: "Assignments", icon: FileText },
              { id: "quizzes", name: "Quizzes", icon: Trophy },
              { id: "ai", name: "AI Study Copilot", icon: Sparkles },
              { id: "discussions", name: "Resources & Board", icon: MessageSquare },
            ] as const).map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-3 px-5 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer ${
                    activeTab === tab.id
                      ? "border-purple-500 text-purple-400"
                      : "border-transparent text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.name}
                </button>
              );
            })}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content Area (Left 2 columns) */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            
            {/* Overview / Purchase View (or active Tab contents) */}
            {(!isEnrolled || activeTab === "overview") && (
              <div className="flex flex-col gap-6">
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                  <h3 className="text-base font-bold text-white">Course Summary & Core Value</h3>
                  <p className="text-zinc-300 text-sm leading-relaxed">
                    This course offers a structured approach to learning {course.category}.
                    Designed for {course.level} learners, the material provides practical workflows and interactive elements
                    accompanied by Gemini AI tutoring systems, generating personalized study calendars and review notes on the fly.
                  </p>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                    <div className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60">
                      <span className="text-[10px] text-zinc-500 uppercase font-black tracking-wider">Level rating</span>
                      <p className="text-sm font-bold text-white mt-1 capitalize">{course.level}</p>
                    </div>
                    <div className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60">
                      <span className="text-[10px] text-zinc-500 uppercase font-black tracking-wider">Instructor</span>
                      <p className="text-sm font-bold text-white mt-1">{course.instructor?.full_name || "Enterprise Coach"}</p>
                    </div>
                  </div>
                </div>

                {/* Show Syllabus outline on overview */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <BookOpen className="w-4.5 h-4.5 text-purple-400" />
                    Syllabus Curriculum
                  </h3>
                  
                  {lessonsLoading ? (
                    <TableSkeleton />
                  ) : lessons && lessons.length > 0 ? (
                    <div className="flex flex-col gap-3">
                      {lessons.map((lesson, idx) => (
                        <div
                          key={lesson.id}
                          className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60 flex items-center justify-between gap-4"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-xs font-black text-zinc-650 bg-zinc-900 border border-zinc-850 w-7 h-7 flex items-center justify-center rounded-lg">
                              {idx + 1}
                            </span>
                            <div>
                              <h4 className="text-sm font-semibold text-white leading-tight">{lesson.title}</h4>
                              <p className="text-[10px] text-zinc-500 mt-1">{lesson.duration_minutes || 0} mins</p>
                            </div>
                          </div>
                          
                          {(isEnrolled || canPreview) && (
                            <Link
                              href={`/courses/${courseId}/lessons/${lesson.id}`}
                              className="p-1.5 bg-zinc-900 border border-zinc-800 hover:border-purple-500/20 text-zinc-400 hover:text-purple-400 rounded-lg transition"
                            >
                              <ChevronRight className="w-4 h-4" />
                            </Link>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-zinc-500 text-sm italic">No lessons published yet.</p>
                  )}
                </div>
              </div>
            )}

            {isEnrolled && activeTab === "lessons" && (
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                <h3 className="text-base font-bold text-white">Syllabus curriculum units</h3>
                {lessonsLoading ? (
                  <TableSkeleton />
                ) : lessons && lessons.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    {lessons.map((lesson, idx) => (
                      <div
                        key={lesson.id}
                        className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60 flex items-center justify-between gap-4 hover:border-purple-500/20 transition"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-black text-zinc-650 bg-zinc-900 border border-zinc-850 w-7 h-7 flex items-center justify-center rounded-lg">
                            {idx + 1}
                          </span>
                          <div>
                            <h4 className="text-sm font-semibold text-white leading-tight">{lesson.title}</h4>
                            <p className="text-[10px] text-zinc-500 mt-1">{lesson.duration_minutes || 0} mins</p>
                          </div>
                        </div>
                        <Link
                          href={`/courses/${courseId}/lessons/${lesson.id}`}
                          className="glow-btn py-2 px-4 bg-purple-950/30 hover:bg-purple-900/10 border border-purple-500/20 text-xs font-bold text-purple-300 rounded-xl transition cursor-pointer"
                        >
                          Play Lesson
                        </Link>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-sm italic">No syllabus units posted yet.</p>
                )}
              </div>
            )}

            {isEnrolled && activeTab === "assignments" && (
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                <h3 className="text-base font-bold text-white">Required Course Assignments</h3>
                {assignmentsLoading ? (
                  <TableSkeleton />
                ) : assignments && assignments.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    {assignments.map((asg) => (
                      <div
                        key={asg.id}
                        className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60 flex items-center justify-between gap-4 hover:border-purple-500/20 transition"
                      >
                        <div>
                          <h4 className="text-sm font-bold text-white leading-tight">{asg.title}</h4>
                          <p className="text-[10px] text-zinc-500 mt-1 font-semibold">
                            Max Marks: {asg.max_marks} • Due: {asg.due_date ? new Date(asg.due_date).toLocaleDateString() : "No deadline"}
                          </p>
                        </div>
                        <Link
                          href={`/courses/${courseId}/assignments/${asg.id}`}
                          className="py-2 px-4 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-xs font-semibold text-zinc-300 hover:text-white rounded-xl transition cursor-pointer"
                        >
                          Open Workspace
                        </Link>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-sm italic">No assignments posted for this course.</p>
                )}
              </div>
            )}

            {isEnrolled && activeTab === "quizzes" && (
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                <h3 className="text-base font-bold text-white">Course Quizzes</h3>
                {quizzesLoading ? (
                  <TableSkeleton />
                ) : quizzes && quizzes.length > 0 ? (
                  <div className="flex flex-col gap-3">
                    {quizzes.map((quiz) => (
                      <div
                        key={quiz.id}
                        className="p-4 rounded-2xl bg-zinc-950/45 border border-zinc-900/60 flex items-center justify-between gap-4 hover:border-purple-500/20 transition"
                      >
                        <div>
                          <h4 className="text-sm font-bold text-white leading-tight">{quiz.title}</h4>
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
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-sm italic">No quizzes posted for this course.</p>
                )}
              </div>
            )}

            {isEnrolled && activeTab === "ai" && (
              <div className="flex flex-col gap-6">
                {/* AI Selector Header */}
                <div className="flex items-center justify-between bg-zinc-950/45 border border-zinc-900 rounded-2xl p-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                    AI Copilot Workspace
                  </h3>
                  <select
                    value={aiWorkspace}
                    onChange={(e) => setAiWorkspace(e.target.value as typeof aiWorkspace)}
                    className="bg-zinc-900 border border-zinc-800 text-white rounded-xl px-2.5 py-1.5 text-xs font-semibold focus:outline-none"
                  >
                    <option value="chat">Chat with AI Tutor</option>
                    <option value="notes">Generate Notes</option>
                    <option value="flashcards">Review Flashcards</option>
                    <option value="study-plan">Study Plan</option>
                  </select>
                </div>

                {/* AI Content renders */}
                {aiWorkspace === "chat" && (
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4 border border-zinc-850 h-[480px]">
                    <div className="flex-grow overflow-y-auto pr-1 flex flex-col gap-3 text-xs">
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
                          Tutor is compiling response...
                        </div>
                      )}
                    </div>
                    <form onSubmit={handleChatSubmit} className="flex gap-2 border-t border-zinc-900 pt-3">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask the AI Tutor anything about this course..."
                        className="flex-grow bg-zinc-950 border border-zinc-850 focus:border-purple-500/50 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none placeholder-zinc-550"
                      />
                      <button
                        type="submit"
                        disabled={isChatting || !chatInput.trim()}
                        className="py-2.5 px-4 bg-purple-600 hover:bg-purple-500 text-xs font-bold text-white rounded-xl transition cursor-pointer"
                      >
                        Send
                      </button>
                    </form>
                  </div>
                )}

                {aiWorkspace === "notes" && (
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4 border border-zinc-850 min-h-[350px]">
                    <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                      <div>
                        <h4 className="text-sm font-bold text-white">Course Notes Generator</h4>
                        <p className="text-zinc-500 text-[10px] mt-0.5">Generates notes for the overall course topics using Gemini.</p>
                      </div>
                      <button
                        onClick={handleGenerateNotes}
                        disabled={isGeneratingNotes}
                        className="glow-btn py-2 px-4 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-xs font-bold text-white rounded-xl shadow-md transition cursor-pointer flex items-center gap-1.5"
                      >
                        {isGeneratingNotes ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                        Generate
                      </button>
                    </div>
                    
                    {generatedNote ? (
                      <div className="bg-zinc-950 p-5 rounded-2xl border border-zinc-900 max-h-[380px] overflow-y-auto">
                        <h4 className="text-xs font-bold text-white mb-2">{generatedNote.title}</h4>
                        <div className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">
                          {generatedNote.content}
                        </div>
                      </div>
                    ) : (
                      <div className="flex-grow flex items-center justify-center text-center p-8">
                        <p className="text-xs text-zinc-500">No notes created yet. Click Generate to trigger.</p>
                      </div>
                    )}
                  </div>
                )}

                {aiWorkspace === "flashcards" && (
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4 border border-zinc-850 min-h-[350px]">
                    <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                      <div>
                        <h4 className="text-sm font-bold text-white">Interactive Review Cards</h4>
                        <p className="text-zinc-500 text-[10px] mt-0.5">Generate flashcards dynamically to practice core terms.</p>
                      </div>
                      <button
                        onClick={handleGenerateFlashcards}
                        disabled={isGeneratingCards}
                        className="py-2 px-4 bg-zinc-900 border border-zinc-850 hover:border-zinc-700 text-xs font-bold text-zinc-300 rounded-xl transition cursor-pointer"
                      >
                        {isGeneratingCards ? "Preparing..." : "Construct Cards"}
                      </button>
                    </div>

                    {flashcardSet.length > 0 ? (
                      <div className="flex flex-col items-center gap-6 py-4">
                        {/* Card flip container */}
                        <div
                          onClick={() => setIsFlipped(!isFlipped)}
                          className="w-full max-w-sm aspect-video glass-card rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer border border-zinc-800 hover:border-purple-500/30 transition select-none bg-zinc-950/30"
                        >
                          <span className="text-[9px] font-black uppercase text-purple-400 tracking-wider mb-3">
                            {isFlipped ? "Answer / Back" : "Question / Front"}
                          </span>
                          <p className="text-sm font-extrabold text-white leading-relaxed px-4">
                            {isFlipped ? flashcardSet[currentCardIndex].back : flashcardSet[currentCardIndex].front}
                          </p>
                        </div>
                        {/* Nav selectors */}
                        <div className="flex items-center gap-4 text-xs font-bold">
                          <button
                            onClick={() => {
                              setCurrentCardIndex((prev) => (prev > 0 ? prev - 1 : prev));
                              setIsFlipped(false);
                            }}
                            disabled={currentCardIndex === 0}
                            className="py-1 px-3 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-400 hover:text-white cursor-pointer disabled:opacity-40"
                          >
                            Prev
                          </button>
                          <span className="text-zinc-550">{currentCardIndex + 1} / {flashcardSet.length}</span>
                          <button
                            onClick={() => {
                              setCurrentCardIndex((prev) => (prev < flashcardSet.length - 1 ? prev + 1 : prev));
                              setIsFlipped(false);
                            }}
                            disabled={currentCardIndex === flashcardSet.length - 1}
                            className="py-1 px-3 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-400 hover:text-white cursor-pointer disabled:opacity-40"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-grow flex items-center justify-center text-center p-8">
                        <p className="text-xs text-zinc-500">No cards compiled yet.</p>
                      </div>
                    )}
                  </div>
                )}

                {aiWorkspace === "study-plan" && (
                  <div className="glass-card rounded-3xl p-6 flex flex-col gap-4 border border-zinc-850 min-h-[350px]">
                    <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                      <div>
                        <h4 className="text-sm font-bold text-white">Gemini Study Planner</h4>
                        <p className="text-zinc-500 text-[10px] mt-0.5">Compiles a 4-week learning roadmap schedule.</p>
                      </div>
                      <button
                        onClick={handleGenerateStudyPlan}
                        disabled={isGeneratingPlan}
                        className="py-2 px-4 bg-purple-600 hover:bg-purple-500 text-xs font-bold text-white rounded-xl transition cursor-pointer"
                      >
                        {isGeneratingPlan ? "Building..." : "Generate Plan"}
                      </button>
                    </div>

                    {generatedPlan ? (
                      <div className="bg-zinc-950 p-5 rounded-2xl border border-zinc-900 max-h-[380px] overflow-y-auto text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">
                        {generatedPlan}
                      </div>
                    ) : (
                      <div className="flex-grow flex items-center justify-center text-center p-8">
                        <p className="text-xs text-zinc-500">No study plan built yet.</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {isEnrolled && activeTab === "discussions" && (
              <div className="flex flex-col gap-6">
                {/* Resources */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                  <h3 className="text-base font-bold text-white">Course resources</h3>
                  <div className="p-6 border border-dashed border-zinc-800/80 rounded-2xl flex flex-col items-center justify-center text-center">
                    <p className="text-zinc-550 text-xs">No generic downloads attached to the core track. Look inside lessons list for video attachments.</p>
                  </div>
                </div>

                {/* Discussion board */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                  <h3 className="text-base font-bold text-white">Course Discussion Board</h3>
                  <div className="bg-zinc-950/45 p-6 rounded-2xl border border-zinc-900/60">
                    <h4 className="text-xs font-bold text-white mb-1">Introduce Yourself!</h4>
                    <p className="text-zinc-450 text-[11px] leading-normal">Welcome to the discussion forum. Introduce yourself to the classmates and instructors, share what you seek from this track, and share knowledge!</p>
                  </div>
                </div>
              </div>
            )}

          </div>

          {/* Pricing & Checkout sidebar card (Right column) */}
          <div className="flex flex-col gap-6">
            <div className="glass-card rounded-3xl p-6 flex flex-col gap-5 border border-zinc-850">
              
              {/* Cover Thumbnail */}
              <div className="w-full aspect-video rounded-2xl bg-zinc-950 overflow-hidden relative border border-zinc-900">
                {course.thumbnail ? (
                  <img src={course.thumbnail} alt={course.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-tr from-purple-950/20 to-blue-950/20 text-purple-400">
                    <BookOpen className="w-10 h-10" />
                  </div>
                )}
              </div>

              {/* Price Tag */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-zinc-400 font-medium">Access Tier</span>
                <span className="text-2xl font-black text-white">
                  {formatCoursePrice(course.price)}
                </span>
              </div>

              <div className="h-px bg-zinc-900" />

              {/* Enrollment action button */}
              {getSyllabusAction()}

              {/* Course Features highlights */}
              <div className="flex flex-col gap-3 mt-1">
                {[
                  "Self-paced curriculum access",
                  "AI note companion and streaming tutor chat",
                  "Auto-graded quizzes and progress metrics",
                  "Course completion certification",
                ].map((feat, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs text-zinc-400 leading-normal">
                    <CheckCircle className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}
