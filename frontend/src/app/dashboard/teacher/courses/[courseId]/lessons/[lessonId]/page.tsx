"use client";

import { useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Trash } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";
import { lessonService } from "@/services/api";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PageTransition } from "@/components/shared/PageTransitions";
import type { Lesson } from "@/types";

export default function EditLessonPage() {
  const { courseId, lessonId } = useParams<{ courseId: string; lessonId: string }>();
  const { data: lesson, isLoading } = useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: () => lessonService.getDetails(lessonId),
  });

  if (isLoading) return <DashboardLayout><div className="p-8 text-zinc-400">Loading lesson...</div></DashboardLayout>;
  if (!lesson) return <DashboardLayout><div className="p-8 text-zinc-400">Lesson unavailable.</div></DashboardLayout>;
  return <LessonEditor key={lesson.id} lesson={lesson} courseId={courseId} lessonId={lessonId} />;
}

function LessonEditor({ lesson, courseId, lessonId }: { lesson: Lesson; courseId: string; lessonId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const thumbnailAbort = useRef<AbortController | null>(null);
  const [form, setForm] = useState({
    title: lesson.title,
    content: lesson.content ?? "",
    transcript: lesson.transcript ?? "",
    duration_minutes: lesson.duration_minutes?.toString() ?? "",
    order_index: String(lesson.order_index),
    is_published: lesson.is_published,
  });
  const saveMutation = useMutation({
    mutationFn: () => lessonService.update(lessonId, {
      title: form.title,
      content: form.content || null,
      transcript: form.transcript || null,
      duration_minutes: form.duration_minutes ? Number(form.duration_minutes) : null,
      order_index: Number(form.order_index),
      is_published: form.is_published,
    }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["courseLessons", courseId] });
      await queryClient.invalidateQueries({ queryKey: ["lesson", lessonId] });
      toast.success("Lesson updated.");
      router.push(`/dashboard/teacher/courses/${courseId}`);
    },
    onError: () => toast.error("Could not update the lesson."),
  });
  const deleteMutation = useMutation({
    mutationFn: () => lessonService.delete(lessonId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["courseLessons", courseId] });
      toast.success("Lesson deleted.");
      router.push(`/dashboard/teacher/courses/${courseId}`);
    },
    onError: () => toast.error("Could not delete the lesson."),
  });
  const thumbnailMutation = useMutation({
    mutationFn: ({ file, signal }: { file: File; signal: AbortSignal }) =>
      lessonService.uploadThumbnail(lessonId, file, signal),
    onSuccess: async (updatedLesson) => {
      queryClient.setQueryData(["lesson", lessonId], updatedLesson);
      await queryClient.invalidateQueries({ queryKey: ["courseLessons", courseId] });
      toast.success("Lesson thumbnail updated.");
    },
    onError: (error: any) => {
      if (error?.name !== "AbortError") toast.error(error?.response?.data?.message ?? "Could not upload lesson thumbnail.");
    },
  });
  const fieldClass = "w-full rounded-xl border border-zinc-800 bg-zinc-950/45 px-4 py-3 text-sm text-white focus:border-purple-500/50 focus:outline-none";

  return <DashboardLayout><PageTransition>
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href={`/dashboard/teacher/courses/${courseId}`} className="rounded-xl border border-zinc-800 p-2 text-zinc-300"><ArrowLeft className="h-4 w-4" /></Link>
          <div><h1 className="text-2xl font-extrabold text-white">Edit lesson</h1><p className="mt-1 text-xs text-zinc-500">Update lesson content and syllabus order.</p></div>
        </div>
        <button type="button" onClick={() => { if (confirm("Delete this lesson?")) deleteMutation.mutate(); }} disabled={deleteMutation.isPending} className="rounded-xl border border-red-900/40 p-3 text-red-400" aria-label="Delete lesson"><Trash className="h-4 w-4" /></button>
      </div>
      <form onSubmit={(event) => { event.preventDefault(); saveMutation.mutate(); }} className="glass-card flex flex-col gap-4 rounded-3xl p-6">
        <div className="flex items-center gap-3">
          <label className="cursor-pointer rounded-xl border border-zinc-800 px-4 py-3 text-sm text-zinc-300">
            {thumbnailMutation.isPending ? "Uploading thumbnail…" : lesson.thumbnail ? "Replace lesson thumbnail" : "Upload lesson thumbnail"}
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" className="sr-only" disabled={thumbnailMutation.isPending} onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                thumbnailAbort.current = new AbortController();
                thumbnailMutation.mutate({ file, signal: thumbnailAbort.current.signal });
              }
              event.currentTarget.value = "";
            }} />
          </label>
          {thumbnailMutation.isPending && <button type="button" onClick={() => thumbnailAbort.current?.abort()} className="text-xs text-zinc-400">Cancel upload</button>}
        </div>
        <label className="flex flex-col gap-2 text-xs font-bold uppercase tracking-wide text-zinc-400">Title<input required minLength={2} maxLength={500} className={fieldClass} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
        <label className="flex flex-col gap-2 text-xs font-bold uppercase tracking-wide text-zinc-400">Content<textarea maxLength={100000} rows={7} className={fieldClass} value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} /></label>
        <label className="flex flex-col gap-2 text-xs font-bold uppercase tracking-wide text-zinc-400">Transcript<textarea maxLength={200000} rows={4} className={fieldClass} value={form.transcript} onChange={(e) => setForm({ ...form, transcript: e.target.value })} /></label>
        <div className="grid grid-cols-2 gap-4">
          <label className="flex flex-col gap-2 text-xs font-bold uppercase tracking-wide text-zinc-400">Duration in minutes<input type="number" min="1" max="600" className={fieldClass} value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} /></label>
          <label className="flex flex-col gap-2 text-xs font-bold uppercase tracking-wide text-zinc-400">Order<input type="number" min="0" className={fieldClass} value={form.order_index} onChange={(e) => setForm({ ...form, order_index: e.target.value })} /></label>
        </div>
        <label className="flex items-center gap-3 text-sm text-zinc-300"><input type="checkbox" checked={form.is_published} onChange={(e) => setForm({ ...form, is_published: e.target.checked })} />Lesson is published</label>
        <button disabled={saveMutation.isPending} className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-blue-500 px-6 py-3.5 text-sm font-semibold text-white disabled:opacity-60">{saveMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Save lesson</button>
      </form>
    </div>
  </PageTransition></DashboardLayout>;
}
