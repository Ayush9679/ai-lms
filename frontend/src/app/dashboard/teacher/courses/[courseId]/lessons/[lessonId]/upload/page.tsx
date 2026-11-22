"use client";

import React, { useRef, useState } from "react";
import { useParams } from "next/navigation";
import { lessonService } from "@/services/api";
import { useQueryClient } from "@tanstack/react-query";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { PageTransition } from "@/components/shared/PageTransitions";
import { ArrowLeft, Upload, File, Film, Loader2 } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

export default function LessonAssetUploadPage() {
  const { courseId, lessonId } = useParams();
  const queryClient = useQueryClient();
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);
  const [isUploadingPdf, setIsUploadingPdf] = useState(false);
  const videoAbort = useRef<AbortController | null>(null);
  const pdfAbort = useRef<AbortController | null>(null);

  const handleVideoUpload = async () => {
    if (!videoFile) return;
    setIsUploadingVideo(true);
    videoAbort.current = new AbortController();
    try {
      await lessonService.uploadVideo(lessonId as string, videoFile, videoAbort.current.signal);
      await queryClient.invalidateQueries({ queryKey: ["courseLessons", courseId] });
      toast.success("Lesson video uploaded successfully!");
      setVideoFile(null);
    } catch (err: any) {
      if (err?.name === "AbortError") toast("Video upload cancelled.");
      else toast.error(err?.response?.data?.message ?? err?.message ?? "Failed to upload lesson video.");
    } finally {
      setIsUploadingVideo(false);
    }
  };

  const handlePdfUpload = async () => {
    if (!pdfFile) return;
    setIsUploadingPdf(true);
    pdfAbort.current = new AbortController();
    try {
      await lessonService.uploadPdf(lessonId as string, pdfFile, pdfAbort.current.signal);
      await queryClient.invalidateQueries({ queryKey: ["lesson", lessonId] });
      toast.success("Lesson PDF worksheet uploaded successfully!");
      setPdfFile(null);
    } catch (err: any) {
      if (err?.name === "AbortError") toast("PDF upload cancelled.");
      else toast.error(err?.response?.data?.message ?? err?.message ?? "Failed to upload lesson PDF.");
    } finally {
      setIsUploadingPdf(false);
    }
  };

  return (
    <DashboardLayout>
      <PageTransition>
        <div className="max-w-2xl mx-auto flex flex-col gap-6 text-left">
          
          <div className="flex items-center gap-3">
            <Link
              href={`/dashboard/teacher/courses/${courseId}`}
              className="p-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl transition text-zinc-300 hover:text-white flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-extrabold text-white">Upload Lesson Assets</h1>
              <p className="text-zinc-400 text-xs mt-0.5">Attach lecture MP4 recordings or PDF study notes.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-2">
            
            {/* Video Card */}
            <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
              <div className="p-3 bg-purple-950/40 rounded-2xl flex items-center justify-center w-fit text-purple-400">
                <Film className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Lecture Video</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">Upload MP4, WebM, or Ogg video. Maximum 2048 MB. A failed single PUT must be retried from the beginning.</p>
              
              <input
                type="file"
                accept="video/mp4"
                onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                className="hidden"
                id="video-upload-input"
              />
              <label
                htmlFor="video-upload-input"
                className="w-full flex flex-col items-center justify-center py-6 px-4 border border-dashed border-zinc-850 hover:border-zinc-700/80 rounded-2xl cursor-pointer bg-zinc-950/20 hover:bg-zinc-950/45 transition-all text-center"
              >
                <Upload className="w-6 h-6 text-zinc-500 mb-2" />
                <span className="text-xs font-semibold text-zinc-300">
                  {videoFile ? videoFile.name : "Select MP4 File"}
                </span>
              </label>

              {isUploadingVideo ? (
                <button type="button" onClick={() => videoAbort.current?.abort()} className="mt-2 rounded-xl border border-zinc-800 py-3 text-xs text-zinc-300">Cancel video upload</button>
              ) : videoFile && (
                <button
                  onClick={handleVideoUpload}
                  disabled={isUploadingVideo}
                  className="glow-btn py-3 px-4 text-xs font-semibold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl shadow-md transition flex items-center justify-center gap-1.5 cursor-pointer mt-2"
                >
                  {isUploadingVideo && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Upload Video
                </button>
              )}
            </div>

            {/* PDF Card */}
            <div className="glass-card rounded-3xl p-6 flex flex-col gap-4">
              <div className="p-3 bg-blue-950/40 rounded-2xl flex items-center justify-center w-fit text-blue-400">
                <File className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Worksheet Notes</h3>
              <p className="text-xs text-zinc-500 leading-relaxed">Attach readings, slides, or study worksheets (PDF only).</p>

              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                className="hidden"
                id="pdf-upload-input"
              />
              <label
                htmlFor="pdf-upload-input"
                className="w-full flex flex-col items-center justify-center py-6 px-4 border border-dashed border-zinc-850 hover:border-zinc-700/80 rounded-2xl cursor-pointer bg-zinc-950/20 hover:bg-zinc-950/45 transition-all text-center"
              >
                <Upload className="w-6 h-6 text-zinc-500 mb-2" />
                <span className="text-xs font-semibold text-zinc-300">
                  {pdfFile ? pdfFile.name : "Select PDF File"}
                </span>
              </label>

              {isUploadingPdf ? (
                <button type="button" onClick={() => pdfAbort.current?.abort()} className="mt-2 rounded-xl border border-zinc-800 py-3 text-xs text-zinc-300">Cancel PDF upload</button>
              ) : pdfFile && (
                <button
                  onClick={handlePdfUpload}
                  disabled={isUploadingPdf}
                  className="glow-btn py-3 px-4 text-xs font-semibold bg-gradient-to-r from-purple-600 to-blue-500 text-white rounded-xl shadow-md transition flex items-center justify-center gap-1.5 cursor-pointer mt-2"
                >
                  {isUploadingPdf && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Upload PDF
                </button>
              )}
            </div>

          </div>

        </div>
      </PageTransition>
    </DashboardLayout>
  );
}
