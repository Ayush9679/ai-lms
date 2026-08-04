"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { aiService, courseService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import {
  Sparkles,
  MessageSquare,
  FileText,
  Trophy,
  Calendar,
  Send,
  Loader2,
  Trash,
  Plus,
  Brain,
  Copy,
  Download,
  Lightbulb,
  CheckCircle,
} from "lucide-react";
import toast from "react-hot-toast";

export default function AISpaceMasterDashboard() {
  const queryClient = useQueryClient();
  const [activeTool, setActiveTool] = useState<"chat" | "notes" | "flashcards" | "planner">("chat");

  // 1. CHAT STATES
  const [chatSessions, setChatSessions] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<any[]>([
    { role: "model", content: "Welcome to your Gemini AI workspace! Ask me anything, or choose an AI tool from the options above." },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatting, setIsChatting] = useState(false);

  // 2. NOTES STATES
  const [notesSourceText, setNotesSourceText] = useState("");
  const [notesTitle, setNotesTitle] = useState("");
  const [generatedNote, setGeneratedNote] = useState<any | null>(null);
  const [isGeneratingNotes, setIsGeneratingNotes] = useState(false);

  // 3. FLASHCARDS STATES
  const [flashcardTitle, setFlashcardTitle] = useState("");
  const [flashcardText, setFlashcardText] = useState("");
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [currentCardIdx, setCurrentCardIdx] = useState(0);
  const [isCardFlipped, setIsCardFlipped] = useState(false);
  const [isGeneratingCards, setIsGeneratingCards] = useState(false);

  // 4. STUDY PLAN STATES
  const [planTopics, setPlanTopics] = useState("");
  const [planDurationWeeks, setPlanDurationWeeks] = useState(4);
  const [planHoursPerDay, setPlanHoursPerDay] = useState(1);
  const [generatedPlan, setGeneratedPlan] = useState<any | null>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);

  // Fetch courses list for selector
  const { data: courses } = useQuery({
    queryKey: ["myDashboardCourses"],
    queryFn: () => courseService.listPublic(),
  });

  // Queries
  const { data: savedSessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ["chatSessions"],
    queryFn: aiService.getChatSessions,
    enabled: activeTool === "chat",
  });

  const { data: savedNotes } = useQuery({
    queryKey: ["myNotes"],
    queryFn: aiService.getMyNotes,
    enabled: activeTool === "notes",
  });

  const { data: savedFlashcards } = useQuery({
    queryKey: ["myFlashcards"],
    queryFn: aiService.getMyFlashcards,
    enabled: activeTool === "flashcards",
  });

  const { data: savedPlans } = useQuery({
    queryKey: ["myPlans"],
    queryFn: aiService.getMyStudyPlans,
    enabled: activeTool === "planner",
  });

  // Chat message submission
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatting) return;

    const userMsg = chatInput.trim();
    setChatMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setChatInput("");
    setIsChatting(true);

    try {
      const res = await aiService.chat(userMsg, selectedSessionId || undefined);
      if (!selectedSessionId) {
        setSelectedSessionId(res.session_id);
        queryClient.invalidateQueries({ queryKey: ["chatSessions"] });
      }
      setChatMessages((prev) => [...prev, { role: "model", content: res.ai_response }]);
    } catch (err: any) {
      console.error(err);
      toast.error("AI chat failed. Try again.");
    } finally {
      setIsChatting(false);
    }
  };

  // Generate Notes
  const handleGenerateNotes = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notesSourceText.trim() || !notesTitle.trim()) {
      toast.error("Please enter a title and paste some study text.");
      return;
    }
    setIsGeneratingNotes(true);
    try {
      const res = await aiService.generateNotes({
        source_type: "text",
        source_text: notesSourceText,
        title: notesTitle,
      });
      setGeneratedNote(res);
      queryClient.invalidateQueries({ queryKey: ["myNotes"] });
      toast.success("AI Notes generated successfully!");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to generate AI notes.");
    } finally {
      setIsGeneratingNotes(false);
    }
  };

  // Generate Flashcards
  const handleGenerateFlashcards = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flashcardTitle.trim() || !flashcardText.trim()) {
      toast.error("Please enter a title and paste study notes.");
      return;
    }
    setIsGeneratingCards(true);
    try {
      const res = await aiService.generateFlashcards({
        source_type: "text",
        source_text: flashcardText,
        num_cards: 5,
        title: flashcardTitle,
      });
      setFlashcards(res.cards);
      setCurrentCardIdx(0);
      setIsCardFlipped(false);
      queryClient.invalidateQueries({ queryKey: ["myFlashcards"] });
      toast.success("AI Flashcards created!");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to generate flashcards.");
    } finally {
      setIsGeneratingCards(false);
    }
  };

  // Generate Study Plan
  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!planTopics.trim()) {
      toast.error("Please specify at least one study topic.");
      return;
    }
    setIsGeneratingPlan(true);
    try {
      const res = await aiService.generateStudyPlan({
        topics: [planTopics],
        duration_weeks: planDurationWeeks,
        hours_per_day: planHoursPerDay,
      });
      setGeneratedPlan(res.plan_data);
      queryClient.invalidateQueries({ queryKey: ["myPlans"] });
      toast.success("AI study plan compiled!");
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to compile study plan.");
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  // Mock export to PDF
  const exportToPDF = (title: string, content: string) => {
    toast.success(`Exporting "${title}" to PDF... (Download started)`);
  };

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="flex flex-col gap-6 text-left">
          
          {/* Header */}
          <div>
            <h1 className="text-3xl font-extrabold text-white flex items-center gap-2">
              <Sparkles className="w-8 h-8 text-purple-400" />
              Gemini AI Center
            </h1>
            <p className="text-zinc-400 text-sm mt-1">Converse with AI tutors, generate slide summaries, study cards, and timeline plans.</p>
          </div>

          {/* AI TOOL BAR CHANGER */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 border-b border-zinc-900 pb-4">
            {[
              { id: "chat", name: "AI Chat Tutor", icon: MessageSquare },
              { id: "notes", name: "AI Note Builder", icon: FileText },
              { id: "flashcards", name: "Study Flashcards", icon: Trophy },
              { id: "planner", name: "Study Planner", icon: Calendar },
            ].map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTool(t.id as any)}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border text-sm font-semibold transition cursor-pointer ${
                    activeTool === t.id
                      ? "bg-purple-950/30 text-purple-300 border-purple-500/30"
                      : "bg-zinc-950/45 text-zinc-450 border-zinc-900 hover:border-zinc-800"
                  }`}
                >
                  <Icon className="w-4.5 h-4.5" />
                  {t.name}
                </button>
              );
            })}
          </div>

          {/* ACTIVE TOOL VIEWPORT */}
          <div className="flex-1 min-h-[500px]">
            {activeTool === "chat" && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">
                {/* Chat sessions sidebar */}
                <div className="glass-card rounded-3xl p-4 flex flex-col gap-3 h-[450px]">
                  <div className="flex items-center justify-between border-b border-zinc-900 pb-2">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Chat Logs</h3>
                    <button
                      onClick={() => {
                        setSelectedSessionId(null);
                        setChatMessages([{ role: "model", content: "Hi! Let's start a fresh chat session." }]);
                      }}
                      className="p-1 text-zinc-450 hover:text-white rounded-lg hover:bg-zinc-900 transition"
                      title="New Chat"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto flex flex-col gap-1.5 pr-1">
                    {sessionsLoading ? (
                      <Loader2 className="w-6 h-6 text-purple-500 animate-spin mx-auto mt-4" />
                    ) : savedSessions && savedSessions.length > 0 ? (
                      savedSessions.map((s) => (
                        <button
                          key={s.id}
                          onClick={async () => {
                            setSelectedSessionId(s.id);
                            setIsChatting(true);
                            try {
                              const hist = await aiService.getChatHistory(s.id);
                              setChatMessages(hist.messages);
                            } catch {
                              toast.error("Failed to load chat history.");
                            } finally {
                              setIsChatting(false);
                            }
                          }}
                          className={`text-left text-xs p-2.5 rounded-xl border truncate transition ${
                            selectedSessionId === s.id
                              ? "bg-purple-950/20 text-purple-300 border-purple-500/15"
                              : "bg-zinc-950/20 text-zinc-400 border-transparent hover:border-zinc-800"
                          }`}
                        >
                          {s.title}
                        </button>
                      ))
                    ) : (
                      <span className="text-zinc-650 text-center py-8 text-[11px]">No saved chat logs.</span>
                    )}
                  </div>
                </div>

                {/* Chat window viewport */}
                <div className="md:col-span-3 glass-card rounded-3xl p-6 flex flex-col justify-between h-[450px] border border-zinc-850">
                  <div className="flex-grow overflow-y-auto flex flex-col gap-4 pr-2 max-h-[340px]">
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`p-3.5 rounded-2xl text-xs leading-relaxed max-w-[85%] ${
                          msg.role === "user"
                            ? "bg-purple-950/20 border border-purple-500/10 text-purple-200 self-end text-right"
                            : "bg-zinc-950 border border-zinc-900 text-zinc-300 self-start text-left"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    ))}
                    {isChatting && (
                      <div className="p-3.5 rounded-2xl bg-zinc-950 border border-zinc-900 text-zinc-400 text-xs self-start text-left flex items-center gap-2">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        AI Tutor is formulating a response...
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleChatSubmit} className="flex gap-2 border-t border-zinc-900 pt-4 mt-auto">
                    <input
                      type="text"
                      placeholder="Ask Gemini AI study questions..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      className="flex-grow bg-zinc-950/45 border border-zinc-850 focus:border-purple-500/50 text-white text-xs rounded-xl px-4 py-3 focus:outline-none"
                    />
                    <button
                      type="submit"
                      disabled={isChatting}
                      className="p-3.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl transition flex items-center justify-center shrink-0 cursor-pointer"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </form>
                </div>
              </div>
            )}

            {activeTool === "notes" && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                
                {/* Generation Form */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                  <h3 className="text-base font-bold text-white flex items-center gap-1.5">
                    <Brain className="w-4.5 h-4.5 text-purple-400" />
                    Draft Lecture Notes
                  </h3>
                  <form onSubmit={handleGenerateNotes} className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Notes Title</label>
                      <input
                        type="text"
                        placeholder="Calculus Limits Notes"
                        value={notesTitle}
                        onChange={(e) => setNotesTitle(e.target.value)}
                        className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Lecture / Textbook Paste</label>
                      <textarea
                        rows={7}
                        placeholder="Paste lecture logs, textbook notes, or transcripts..."
                        value={notesSourceText}
                        onChange={(e) => setNotesSourceText(e.target.value)}
                        className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none resize-none"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isGeneratingNotes}
                      className="glow-btn py-3 px-4 text-xs font-semibold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
                    >
                      {isGeneratingNotes && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      Generate Study Guide
                    </button>
                  </form>
                </div>

                {/* Display Area */}
                <div className="md:col-span-2 flex flex-col gap-4">
                  {generatedNote ? (
                    <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                      <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                        <h4 className="font-bold text-white text-base">{generatedNote.title}</h4>
                        <div className="flex gap-2">
                          <button
                            onClick={() => copyToClipboard(generatedNote.content)}
                            className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 hover:text-white rounded-xl transition flex items-center justify-center"
                            title="Copy to clipboard"
                          >
                            <Copy className="w-4.5 h-4.5" />
                          </button>
                          <button
                            onClick={() => exportToPDF(generatedNote.title, generatedNote.content)}
                            className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 hover:text-white rounded-xl transition flex items-center justify-center"
                            title="Download PDF"
                          >
                            <Download className="w-4.5 h-4.5" />
                          </button>
                        </div>
                      </div>
                      <div className="text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap max-h-[300px] overflow-y-auto pr-1">
                        {generatedNote.content}
                      </div>
                    </div>
                  ) : (
                    <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
                      <Lightbulb className="w-10 h-10 text-zinc-600 mb-2" />
                      <h4 className="font-bold text-white text-sm">No notes compiled yet</h4>
                      <p className="text-xs text-zinc-500 mt-1 max-w-[220px]">
                        Paste textbook explanations on the left to structure study sheets.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTool === "flashcards" && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                
                {/* Inputs */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                  <h3 className="text-base font-bold text-white">Create Flashcard Deck</h3>
                  <form onSubmit={handleGenerateFlashcards} className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Deck Title</label>
                      <input
                        type="text"
                        placeholder="Geometry Formula Deck"
                        value={flashcardTitle}
                        onChange={(e) => setFlashcardTitle(e.target.value)}
                        className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Study Materials</label>
                      <textarea
                        rows={7}
                        placeholder="Paste formulas, notes, or definitions to quiz yourself on..."
                        value={flashcardText}
                        onChange={(e) => setFlashcardText(e.target.value)}
                        className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none resize-none"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isGeneratingCards}
                      className="glow-btn py-3 px-4 text-xs font-semibold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
                    >
                      {isGeneratingCards && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      Generate Deck
                    </button>
                  </form>
                </div>

                {/* Card player */}
                <div className="md:col-span-2 flex flex-col gap-4">
                  {flashcards.length > 0 ? (
                    <div className="glass-card rounded-3xl p-6 flex flex-col justify-between h-[360px]">
                      <div
                        onClick={() => setIsCardFlipped(!isCardFlipped)}
                        className="flex-1 flex flex-col items-center justify-center p-6 text-center cursor-pointer border border-zinc-900 rounded-2xl hover:border-purple-500/10 transition-all select-none"
                      >
                        <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest mb-2">
                          {isCardFlipped ? "Answer" : "Question"}
                        </span>
                        <p className="text-base font-bold text-white max-w-sm leading-relaxed">
                          {isCardFlipped ? flashcards[currentCardIdx].back : flashcards[currentCardIdx].front}
                        </p>
                      </div>

                      <div className="flex items-center justify-between mt-4">
                        <span className="text-xs text-zinc-500 font-bold">
                          Card {currentCardIdx + 1} of {flashcards.length}
                        </span>
                        <div className="flex gap-2">
                          <button
                            disabled={currentCardIdx === 0}
                            onClick={() => {
                              setCurrentCardIdx((c) => c - 1);
                              setIsCardFlipped(false);
                            }}
                            className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-850 rounded-lg text-xs font-semibold text-white disabled:opacity-40 transition"
                          >
                            Prev
                          </button>
                          <button
                            disabled={currentCardIdx === flashcards.length - 1}
                            onClick={() => {
                              setCurrentCardIdx((c) => c + 1);
                              setIsCardFlipped(false);
                            }}
                            className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-850 rounded-lg text-xs font-semibold text-white disabled:opacity-40 transition"
                          >
                            Next
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
                      <Trophy className="w-10 h-10 text-zinc-600 mb-2" />
                      <h4 className="font-bold text-white text-sm">No flashcards loaded</h4>
                      <p className="text-xs text-zinc-500 mt-1 max-w-[220px]">
                        Draft a deck using formulas or definitions on the left.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTool === "planner" && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                
                {/* Planner inputs */}
                <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                  <h3 className="text-base font-bold text-white">Scaffold Study Timeline</h3>
                  <form onSubmit={handleGeneratePlan} className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Core Subject / Topics</label>
                      <input
                        type="text"
                        placeholder="Relational Database Architecture"
                        value={planTopics}
                        onChange={(e) => setPlanTopics(e.target.value)}
                        className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Weeks Duration</label>
                        <input
                          type="number"
                          value={planDurationWeeks}
                          onChange={(e) => setPlanDurationWeeks(parseInt(e.target.value) || 4)}
                          className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none"
                        />
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Hours / Day</label>
                        <input
                          type="number"
                          value={planHoursPerDay}
                          onChange={(e) => setPlanHoursPerDay(parseInt(e.target.value) || 1)}
                          className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2.5 text-xs focus:outline-none"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isGeneratingPlan}
                      className="glow-btn py-3 px-4 text-xs font-semibold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
                    >
                      {isGeneratingPlan && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      Compile Calendar
                    </button>
                  </form>
                </div>

                {/* Calendar displays */}
                <div className="md:col-span-2 flex flex-col gap-4">
                  {generatedPlan ? (
                    <div className="glass-card rounded-3xl p-6 flex flex-col gap-3 text-xs leading-relaxed max-h-[380px] overflow-y-auto">
                      <h4 className="font-bold text-white text-sm mb-2">Weekly Schedule Breakdown</h4>
                      {Object.keys(generatedPlan).map((week) => (
                        <div key={week} className="p-3 bg-zinc-950/45 border border-zinc-900 rounded-xl flex flex-col gap-1">
                          <p className="font-bold text-purple-400 uppercase tracking-wider text-[10px]">{week}</p>
                          <p className="text-zinc-300 leading-relaxed mt-0.5">{generatedPlan[week]}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-20 border border-dashed border-zinc-800/80 rounded-3xl flex flex-col items-center justify-center text-center">
                      <Calendar className="w-10 h-10 text-zinc-600 mb-2" />
                      <h4 className="font-bold text-white text-sm">No plan compiled yet</h4>
                      <p className="text-xs text-zinc-500 mt-1 max-w-[220px]">
                        Submit a subject and study constraints to draft customized timelines.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
