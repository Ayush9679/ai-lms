"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assignmentService, enrollmentService } from "@/services/api";
import { useAuth } from "@/providers/AuthProvider";
import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { ParticlesBackground } from "@/components/3d/Particles";
import { PageTransition } from "@/components/shared/PageTransitions";
import { ArrowLeft, Loader2, FileText, CheckCircle2, Upload, AlertCircle } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function TakeAssignmentPage() {
  const { courseId, assignmentId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();

  // Enrollment guard
  const { data: enrollmentStatus, isLoading: enrollmentLoading } = useQuery({
    queryKey: ["enrollmentStatus", courseId],
    queryFn: () => enrollmentService.getStatus(courseId as string),
    enabled: isAuthenticated,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (!enrollmentLoading && enrollmentStatus && !enrollmentStatus.is_enrolled) {
      router.replace(`/courses/${courseId}`);
    }
  }, [isAuthenticated, enrollmentLoading, enrollmentStatus, courseId, router]);

  const [textContent, setTextContent] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch Assignment details
  const { data: assignment, isLoading: assignmentLoading } = useQuery({
    queryKey: ["assignmentTaking", assignmentId],
    queryFn: () => assignmentService.getDetails(assignmentId as string),
  });

  // Fetch my submissions for this assignment to see if already graded/submitted
  const { data: mySubmissions, isLoading: submissionLoading } = useQuery({
    queryKey: ["myAssignmentSubmissions"],
    queryFn: () => assignmentService.getMySubmissions(),
  });

  const activeSubmission = mySubmissions?.find((s) => s.assignment_id === assignmentId);

  const handleSubmitText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textContent.trim() && !selectedFile) {
      toast.error("Please provide some text or choose a file to upload.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (selectedFile) {
        await assignmentService.submitFile(assignmentId as string, selectedFile);
      } else {
        await assignmentService.submitText(assignmentId as string, textContent);
      }
      toast.success("Assignment submitted successfully!");
      queryClient.invalidateQueries({ queryKey: ["myAssignmentSubmissions"] });
      setTextContent("");
      setSelectedFile(null);
    } catch (err: any) {
      console.error(err);
      toast.error("Submission failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (assignmentLoading || submissionLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (!assignment) return null;

  return (
    <div className="min-h-screen bg-[#020204] flex flex-col justify-between overflow-x-hidden">
      <ParticlesBackground />
      <Header />

      <main className="flex-grow pt-32 pb-20 max-w-3xl mx-auto px-4 w-full z-10 text-left">
        
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Link
            href={`/courses/${courseId}`}
            className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white leading-snug">{assignment.title}</h1>
            <p className="text-xs text-zinc-400 mt-1">
              Max Marks: {assignment.max_marks} • Due: {assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : "No deadline"}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          {/* Instructions card */}
          <div className="glass-card rounded-3xl p-6 flex flex-col gap-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-purple-400" />
              Description & Guidelines
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              {assignment.description || "Submit your answers using the text box or files uploader below."}
            </p>
            {assignment.instructions && (
              <div className="mt-2 pt-2 border-t border-zinc-900">
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-wide">Instructions</p>
                <p className="text-xs text-zinc-400 leading-relaxed mt-1">{assignment.instructions}</p>
              </div>
            )}
          </div>

          {activeSubmission ? (
            /* SUBMISSION STATUS CARD */
            <PageTransition>
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4 border-t-2 border-t-green-500">
                <div className="flex items-center gap-2 text-green-400 text-sm font-bold">
                  <CheckCircle2 className="w-5 h-5 text-green-400 fill-green-400/10" />
                  Assignment Submitted
                </div>
                
                <div className="p-4 bg-zinc-950/45 border border-zinc-900 rounded-2xl flex flex-col gap-3 text-xs">
                  <div>
                    <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Submitted Text</span>
                    <p className="text-zinc-300 mt-1">{activeSubmission.text_content || activeSubmission.file_name || "Files uploaded."}</p>
                  </div>
                  
                  {activeSubmission.marks_obtained !== null ? (
                    <div className="border-t border-zinc-900 pt-3 flex flex-col gap-2">
                      <span className="text-[10px] text-purple-450 font-bold uppercase tracking-wider">Grade Result</span>
                      <p className="text-sm font-bold text-white">
                        Score: <span className="text-purple-400">{activeSubmission.marks_obtained}</span> / {assignment.max_marks} marks
                      </p>
                      {activeSubmission.feedback && (
                        <div className="p-3 bg-purple-950/10 border border-purple-500/5 rounded-xl mt-1 text-zinc-400 leading-relaxed">
                          <p className="font-bold text-purple-400 text-[10px] uppercase">Teacher Feedback</p>
                          <p className="mt-1">{activeSubmission.feedback}</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="border-t border-zinc-900 pt-3 flex items-center gap-2 text-zinc-500">
                      <AlertCircle className="w-4 h-4" />
                      Pending instructor grading.
                    </div>
                  )}
                </div>
              </div>
            </PageTransition>
          ) : (
            /* SUBMIT FORM */
            <PageTransition>
              <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
                <h3 className="text-sm font-bold text-white">Submit Workspace</h3>
                <form onSubmit={handleSubmitText} className="flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">Submission Answers Text</label>
                    <textarea
                      rows={6}
                      placeholder="Paste your source code or text answers here..."
                      value={textContent}
                      onChange={(e) => setTextContent(e.target.value)}
                      className="w-full bg-zinc-950/45 border border-zinc-800/80 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-zinc-400 uppercase tracking-wide">File Attachment (Optional)</label>
                    <input
                      type="file"
                      onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                      className="hidden"
                      id="asg-file-input"
                    />
                    <label
                      htmlFor="asg-file-input"
                      className="w-full flex items-center gap-3 p-3 bg-zinc-950/45 border border-zinc-800/80 hover:border-zinc-700/80 text-xs font-semibold text-zinc-450 hover:text-zinc-300 rounded-xl cursor-pointer transition"
                    >
                      <Upload className="w-4 h-4 text-zinc-500" />
                      {selectedFile ? selectedFile.name : "Select worksheet file to attach"}
                    </label>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="glow-btn py-3.5 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-sm font-bold text-white rounded-2xl flex items-center justify-center gap-1.5 shadow-lg shadow-purple-500/10 cursor-pointer mt-2"
                  >
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    Submit Assignment
                  </button>
                </form>
              </div>
            </PageTransition>
          )}
        </div>

      </main>

      <Footer />
    </div>
  );
}
