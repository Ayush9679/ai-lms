"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assignmentService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { TableSkeleton } from "@/components/shared/SkeletonLoaders";
import { PageTransition } from "@/components/shared/PageTransitions";
import { ArrowLeft, Save, AlertCircle, Trash2, Eye, EyeOff, Lock, Unlock } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function EditAssignmentPage() {
  const { courseId, assignmentId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: assignment, isLoading } = useQuery({
    queryKey: ["teacherAssignmentDetails", assignmentId],
    queryFn: () => assignmentService.getDetails(assignmentId as string),
    enabled: !!assignmentId,
  });

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [maxMarks, setMaxMarks] = useState(100);
  const [passingMarks, setPassingMarks] = useState(40);
  const [isPublished, setIsPublished] = useState(true);
  const [isClosed, setIsClosed] = useState(false);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (assignment) {
      setTitle(assignment.title || "");
      setDescription(assignment.description || "");
      setInstructions(assignment.instructions || "");
      
      // Convert ISO date string to datetime-local input format (YYYY-MM-DDTHH:MM)
      if (assignment.due_date) {
        const date = new Date(assignment.due_date);
        const pad = (num: number) => String(num).padStart(2, "0");
        const formatted = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
        setDueDate(formatted);
      } else {
        setDueDate("");
      }
      
      setMaxMarks(assignment.max_marks ?? 100);
      setPassingMarks(assignment.passing_marks ?? 40);
      setIsPublished(assignment.is_published ?? true);
      setIsClosed(assignment.is_closed ?? false);
    }
  }, [assignment]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const saveMutation = useMutation({
    mutationFn: (data: any) => assignmentService.update(assignmentId as string, data),
    onSuccess: () => {
      toast.success("Assignment updated successfully!");
      queryClient.invalidateQueries({ queryKey: ["teacherAssignmentDetails", assignmentId] });
      queryClient.invalidateQueries({ queryKey: ["courseAssignments", courseId] });
      router.push(`/dashboard/teacher/courses/${courseId}`);
    },
    onError: (err: any) => {
      console.error(err);
      toast.error(err.response?.data?.message || "Failed to update assignment.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => assignmentService.delete(assignmentId as string),
    onSuccess: () => {
      toast.success("Assignment deleted successfully!");
      queryClient.invalidateQueries({ queryKey: ["courseAssignments", courseId] });
      router.push(`/dashboard/teacher/courses/${courseId}`);
    },
    onError: (err: any) => {
      console.error(err);
      toast.error("Failed to delete assignment.");
    },
  });

  const handleSave = () => {
    if (!title.trim()) {
      toast.error("Assignment title is required.");
      return;
    }

    const payload = {
      title,
      description: description || null,
      instructions: instructions || null,
      due_date: dueDate ? new Date(dueDate).toISOString() : null,
      max_marks: Number(maxMarks),
      passing_marks: Number(passingMarks),
      is_published: isPublished,
      is_closed: isClosed,
    };

    saveMutation.mutate(payload);
  };

  const handleDelete = () => {
    if (confirm("Are you sure you want to delete this assignment permanently? This action is irreversible.")) {
      deleteMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <TableSkeleton />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="max-w-3xl mx-auto flex flex-col gap-6 text-left pb-12">
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
                <h1 className="text-2xl font-extrabold text-white">Edit Assignment</h1>
                <p className="text-zinc-400 text-xs mt-0.5">Modify parameters, deadline, instructions, or delete assignment.</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="p-2.5 bg-red-950/20 border border-red-900/30 text-red-400 hover:text-red-300 rounded-xl transition flex items-center justify-center cursor-pointer"
                title="Delete Assignment"
              >
                <Trash2 className="w-4.5 h-4.5" />
              </button>

              <button
                onClick={handleSave}
                disabled={saveMutation.isPending}
                className="glow-btn flex items-center gap-2 py-2.5 px-5 bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-sm font-bold text-white rounded-xl shadow-md transition cursor-pointer"
              >
                {saveMutation.isPending ? "Saving..." : "Save Changes"}
                <Save className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Form */}
          <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-zinc-450 uppercase">Assignment Title</label>
              <input
                type="text"
                placeholder="Midterm Homework Project"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-zinc-450 uppercase">Description / Overview</label>
              <textarea
                rows={4}
                placeholder="Describe the context of the homework or assignment objectives..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-zinc-450 uppercase">Instructions for Students</label>
              <textarea
                rows={5}
                placeholder="Step 1. Code the logic in python..."
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Maximum Marks</label>
                <input
                  type="number"
                  value={maxMarks}
                  onChange={(e) => setMaxMarks(Number(e.target.value))}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Passing Marks</label>
                <input
                  type="number"
                  value={passingMarks}
                  onChange={(e) => setPassingMarks(Number(e.target.value))}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-zinc-450 uppercase">Due Date & Time</label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full bg-zinc-950/45 border border-zinc-800 focus:border-purple-500/50 text-white rounded-xl px-4 py-3 text-sm focus:outline-none text-zinc-300"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-6 mt-2">
              <label className="text-xs font-bold text-zinc-450 uppercase flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={isPublished}
                  onChange={(e) => setIsPublished(e.target.checked)}
                  className="w-4 h-4 bg-zinc-950 border-zinc-800 rounded focus:ring-purple-500 cursor-pointer"
                />
                Published (Students can see it)
              </label>

              <label className="text-xs font-bold text-zinc-450 uppercase flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={isClosed}
                  onChange={(e) => setIsClosed(e.target.checked)}
                  className="w-4 h-4 bg-zinc-950 border-zinc-800 rounded focus:ring-purple-500 cursor-pointer"
                />
                Closed (Blocks new student submissions)
              </label>
            </div>
          </div>

          <div className="p-4 bg-zinc-900/40 border border-zinc-800 rounded-2xl flex gap-3 text-xs text-zinc-400 items-start">
            <AlertCircle className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-white">Publishing & Closure</p>
              <p className="mt-1 leading-relaxed">
                If un-published, students will not see this assignment in their dashboard list or curriculum syllabus sections. If marked closed, students will see assignment details but submission options will be locked.
              </p>
            </div>
          </div>
        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
