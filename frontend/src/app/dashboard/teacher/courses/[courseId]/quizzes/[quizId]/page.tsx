"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { quizService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { ArrowLeft, Plus, Trash2, Save, AlertCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

interface QuestionOption {
  text: string;
  is_correct: boolean;
}

interface EditQuestion {
  id?: string;
  question_text: string;
  question_type: "mcq" | "true_false";
  options: QuestionOption[];
  correct_answer: string;
  explanation: string;
  marks: number;
}

export default function EditQuizPage() {
  const { courseId, quizId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: quizData, isLoading: isQuizLoading } = useQuery({
    queryKey: ["teacherQuizDetails", quizId],
    queryFn: () => quizService.getDetailsTeacher(quizId as string),
    enabled: !!quizId,
  });

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [passingScore, setPassingScore] = useState(60);
  const [timeLimit, setTimeLimit] = useState<number | "">("");
  const [maxAttempts, setMaxAttempts] = useState(0);
  const [negativeMarking, setNegativeMarking] = useState(false);

  const [questions, setQuestions] = useState<EditQuestion[]>([]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (quizData) {
      setTitle(quizData.title || "");
      setDescription(quizData.description || "");
      setDifficulty(quizData.difficulty || "medium");
      setPassingScore(quizData.passing_score ?? 60);
      setTimeLimit(quizData.time_limit_minutes ?? "");
      setMaxAttempts(quizData.max_attempts ?? 0);
      setNegativeMarking(quizData.negative_marking ?? false);

      if (quizData.questions) {
        const loadedQuestions: EditQuestion[] = quizData.questions.map((q: any) => {
          const rawOptions = q.options || [];
          let options: QuestionOption[] = [];
          if (q.question_type === "true_false") {
            options = [
              { text: "True", is_correct: q.correct_answer === "True" },
              { text: "False", is_correct: q.correct_answer === "False" },
            ];
          } else {
            options = rawOptions.map((opt: any) => ({
              text: opt.text || "",
              is_correct: opt.is_correct || opt.text === q.correct_answer,
            }));
          }

          return {
            id: q.id,
            question_text: q.question_text || "",
            question_type: q.question_type || "mcq",
            options,
            correct_answer: q.correct_answer || "",
            explanation: q.explanation || "",
            marks: q.marks || 1,
          };
        });
        setQuestions(loadedQuestions);
      }
    }
  }, [quizData]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const addQuestion = () => {
    setQuestions((prev) => [
      ...prev,
      {
        question_text: "",
        question_type: "mcq",
        options: [
          { text: "", is_correct: true },
          { text: "", is_correct: false },
        ],
        correct_answer: "",
        explanation: "",
        marks: 1,
      },
    ]);
  };

  const removeQuestion = (qIndex: number) => {
    if (questions.length === 1) {
      toast.error("A quiz must have at least one question.");
      return;
    }
    setQuestions((prev) => prev.filter((_, idx) => idx !== qIndex));
  };

  const handleQuestionTextChange = (qIndex: number, text: string) => {
    setQuestions((prev) =>
      prev.map((q, idx) => (idx === qIndex ? { ...q, question_text: text } : q))
    );
  };

  const handleQuestionTypeChange = (qIndex: number, type: "mcq" | "true_false") => {
    setQuestions((prev) =>
      prev.map((q, idx) => {
        if (idx === qIndex) {
          const options =
            type === "true_false"
              ? [
                  { text: "True", is_correct: true },
                  { text: "False", is_correct: false },
                ]
              : [
                  { text: "", is_correct: true },
                  { text: "", is_correct: false },
                ];
          return {
            ...q,
            question_type: type,
            options,
            correct_answer: type === "true_false" ? "True" : "",
          };
        }
        return q;
      })
    );
  };

  const handleOptionTextChange = (qIndex: number, oIndex: number, text: string) => {
    setQuestions((prev) =>
      prev.map((q, idx) => {
        if (idx === qIndex) {
          const updatedOptions = q.options.map((opt, oIdx) =>
            oIdx === oIndex ? { ...opt, text } : opt
          );
          return { ...q, options: updatedOptions };
        }
        return q;
      })
    );
  };

  const handleOptionCorrectChange = (qIndex: number, oIndex: number) => {
    setQuestions((prev) =>
      prev.map((q, idx) => {
        if (idx === qIndex) {
          const updatedOptions = q.options.map((opt, oIdx) => ({
            ...opt,
            is_correct: oIdx === oIndex,
          }));
          return {
            ...q,
            options: updatedOptions,
            correct_answer: q.options[oIndex]?.text || "",
          };
        }
        return q;
      })
    );
  };

  const addOption = (qIndex: number) => {
    setQuestions((prev) =>
      prev.map((q, idx) => {
        if (idx === qIndex && q.question_type === "mcq") {
          return {
            ...q,
            options: [...q.options, { text: "", is_correct: false }],
          };
        }
        return q;
      })
    );
  };

  const removeOption = (qIndex: number, oIndex: number) => {
    setQuestions((prev) =>
      prev.map((q, idx) => {
        if (idx === qIndex && q.question_type === "mcq") {
          if (q.options.length <= 2) {
            toast.error("MCQ questions require at least 2 options.");
            return q;
          }
          const isRemovedCorrect = q.options[oIndex].is_correct;
          const updatedOptions = q.options.filter((_, oIdx) => oIdx !== oIndex);
          if (isRemovedCorrect && updatedOptions.length > 0) {
            updatedOptions[0].is_correct = true;
          }
          return { ...q, options: updatedOptions };
        }
        return q;
      })
    );
  };

  const handleExplanationChange = (qIndex: number, explanation: string) => {
    setQuestions((prev) =>
      prev.map((q, idx) => (idx === qIndex ? { ...q, explanation } : q))
    );
  };

  const handleMarksChange = (qIndex: number, marks: number) => {
    setQuestions((prev) =>
      prev.map((q, idx) => (idx === qIndex ? { ...q, marks: Math.max(0.1, marks) } : q))
    );
  };

  const saveMutation = useMutation({
    mutationFn: (data: any) => quizService.update(quizId as string, data),
    onSuccess: () => {
      toast.success("Quiz updated successfully!");
      queryClient.invalidateQueries({ queryKey: ["teacherQuizDetails", quizId] });
      queryClient.invalidateQueries({ queryKey: ["courseQuizzes", courseId] });
      router.push(`/dashboard/teacher/courses/${courseId}`);
    },
    onError: (err: any) => {
      console.error(err);
      toast.error(err.response?.data?.message || "Failed to save quiz updates.");
    },
  });

  const handleSave = () => {
    if (!title.trim()) {
      toast.error("Quiz title is required.");
      return;
    }

    // Validate questions
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i];
      if (!q.question_text.trim()) {
        toast.error(`Question ${i + 1} text is required.`);
        return;
      }
      if (q.question_type === "mcq") {
        for (let j = 0; j < q.options.length; j++) {
          if (!q.options[j].text.trim()) {
            toast.error(`Option ${j + 1} for Question ${i + 1} cannot be empty.`);
            return;
          }
        }
        const hasCorrect = q.options.some((opt) => opt.is_correct);
        if (!hasCorrect) {
          toast.error(`Question ${i + 1} must have at least one correct option.`);
          return;
        }
      }
    }

    const payload = {
      title,
      description,
      difficulty,
      passing_score: passingScore,
      negative_marking: negativeMarking,
      time_limit_minutes: timeLimit === "" ? null : Number(timeLimit),
      max_attempts: maxAttempts,
      questions: questions.map((q, idx) => {
        const correct_answer = q.question_type === "true_false" 
          ? q.correct_answer 
          : q.options.find(o => o.is_correct)?.text || "";

        return {
          question_text: q.question_text,
          question_type: q.question_type,
          options: q.question_type === "mcq" ? q.options : null,
          correct_answer,
          explanation: q.explanation || null,
          marks: q.marks,
          order_index: idx,
        };
      }),
    };

    saveMutation.mutate(payload);
  };

  if (isQuizLoading) {
    return (
      <DashboardLayout>
        <TableSkeleton />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="max-w-4xl mx-auto flex flex-col gap-6 text-left pb-12">
          {/* Header */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Link
                href={`/dashboard/teacher/courses/${courseId}`}
                className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <div>
                <h1 className="text-2xl font-extrabold text-white">Edit Quiz</h1>
                <p className="text-zinc-400 text-xs mt-0.5">Customize, add, or delete questions and adjust settings.</p>
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={saveMutation.isPending}
              className="glow-btn flex items-center gap-2 py-2.5 px-5 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-sm font-bold text-white rounded-xl shadow-md transition cursor-pointer"
            >
              {saveMutation.isPending ? "Saving..." : "Save Changes"}
              <Save className="w-4 h-4" />
            </button>
          </div>

          {/* Quiz Metadata Panel */}
          <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
            <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-wider">Quiz Parameters</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Quiz Title</label>
                <input
                  type="text"
                  placeholder="Calculus Quiz 1"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Difficulty Level</label>
                <select
                  value={difficulty}
                  onChange={(e: any) => setDifficulty(e.target.value)}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-zinc-450 uppercase">Description</label>
              <textarea
                rows={3}
                placeholder="Explain the coverage, intent, or instructions of this quiz..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Passing Score (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={passingScore}
                  onChange={(e) => setPassingScore(Number(e.target.value))}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Time Limit (mins)</label>
                <input
                  type="number"
                  placeholder="Unlimited"
                  value={timeLimit}
                  onChange={(e) => setTimeLimit(e.target.value ? Number(e.target.value) : "")}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Max Attempts</label>
                <input
                  type="number"
                  placeholder="Unlimited"
                  value={maxAttempts || ""}
                  onChange={(e) => setMaxAttempts(Number(e.target.value))}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
              </div>

              <div className="flex flex-col justify-end gap-2 pb-1">
                <label className="text-xs font-bold text-zinc-450 uppercase flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={negativeMarking}
                    onChange={(e) => setNegativeMarking(e.target.checked)}
                    className="w-4 h-4 bg-zinc-950 border-zinc-800 rounded focus:ring-purple-500"
                  />
                  Negative Marking
                </label>
              </div>
            </div>
          </div>

          {/* Questions Header */}
          <div className="flex items-center justify-between mt-4">
            <h2 className="text-lg font-bold text-white">Quiz Questions ({questions.length})</h2>
            <button
              onClick={addQuestion}
              className="flex items-center gap-1.5 py-2 px-4 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-sm font-semibold rounded-xl text-zinc-300 hover:text-white transition cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              Add Question
            </button>
          </div>

          {/* Questions List */}
          <div className="flex flex-col gap-6">
            {questions.map((q, qIdx) => (
              <div key={qIdx} className="glass-card rounded-3xl p-6 flex flex-col gap-4 relative border border-zinc-800">
                <button
                  onClick={() => removeQuestion(qIdx)}
                  className="absolute top-6 right-6 p-2 bg-red-950/20 hover:bg-red-900/20 text-red-400 hover:text-red-300 border border-red-900/30 rounded-xl transition cursor-pointer"
                  title="Remove Question"
                >
                  <Trash2 className="w-4 h-4" />
                </button>

                <div className="flex items-center gap-4 pr-12">
                  <span className="text-xs font-black text-purple-400 bg-purple-950/30 border border-purple-500/20 w-8 h-8 flex items-center justify-center rounded-xl shrink-0">
                    Q{qIdx + 1}
                  </span>
                  <div className="flex-grow">
                    <select
                      value={q.question_type}
                      onChange={(e) => handleQuestionTypeChange(qIdx, e.target.value as any)}
                      className="bg-zinc-950 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-1.5 text-xs focus:outline-none"
                    >
                      <option value="mcq">Multiple Choice (MCQ)</option>
                      <option value="true_false">True / False</option>
                    </select>
                  </div>
                </div>

                {/* Question Text */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-bold text-zinc-450 uppercase">Question Text</label>
                  <input
                    type="text"
                    placeholder="Question Text"
                    value={q.question_text}
                    onChange={(e) => handleQuestionTextChange(qIdx, e.target.value)}
                    className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                  />
                </div>

                {/* Question Options */}
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] font-bold text-zinc-450 uppercase">Answer Options & Correct Indicator</label>
                    {q.question_type === "mcq" && (
                      <button
                        onClick={() => addOption(qIdx)}
                        className="text-xs font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 cursor-pointer"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        Add Option
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-2.5">
                    {q.options.map((opt, oIdx) => (
                      <div key={oIdx} className="flex items-center gap-3">
                        <input
                          type="radio"
                          name={`correct-radio-${qIdx}`}
                          checked={opt.is_correct}
                          onChange={() => handleOptionCorrectChange(qIdx, oIdx)}
                          className="w-4 h-4 text-purple-600 bg-zinc-950 border-zinc-800 focus:ring-purple-500 shrink-0 cursor-pointer"
                        />
                        <input
                          type="text"
                          placeholder={q.question_type === "true_false" ? "" : `Option ${oIdx + 1}`}
                          disabled={q.question_type === "true_false"}
                          value={opt.text}
                          onChange={(e) => handleOptionTextChange(qIdx, oIdx, e.target.value)}
                          className="flex-grow bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3.5 py-2 text-xs focus:outline-none disabled:bg-zinc-900 disabled:text-zinc-500 disabled:border-zinc-850"
                        />
                        {q.question_type === "mcq" && (
                          <button
                            onClick={() => removeOption(qIdx, oIdx)}
                            className="p-2 text-zinc-500 hover:text-red-400 transition cursor-pointer"
                            title="Remove Option"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Explanation & Marks */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-2">
                  <div className="md:col-span-3 flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-zinc-450 uppercase">Explanation / Rationalization</label>
                    <input
                      type="text"
                      placeholder="Use power rule: d/dx(x^n) = nx^(n-1)."
                      value={q.explanation}
                      onChange={(e) => handleExplanationChange(qIdx, e.target.value)}
                      className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2 text-xs focus:outline-none"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-zinc-450 uppercase">Marks</label>
                    <input
                      type="number"
                      step="0.5"
                      value={q.marks}
                      onChange={(e) => handleMarksChange(qIdx, parseFloat(e.target.value) || 1)}
                      className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-3 py-2 text-xs focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
