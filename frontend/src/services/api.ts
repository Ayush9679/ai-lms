import { apiClient, clearTokens, setTokens } from "@/lib/api-client";
import {
  User,
  UserRole,
  Course,
  CourseSummary,
  CourseFile,
  Lesson,
  LessonSummary,
  LessonProgress,
  Enrollment,
  Quiz,
  QuizAttempt,
  Assignment,
  AssignmentSubmission,
  AIChatSession,
  AIChatMessage,
  GeneratedNote,
  StudyPlan,
  FlashcardSet,
  StudentDashboardData,
  TeacherDashboardData,
  AdminDashboardData,
} from "@/types";

interface PresignedUploadGrant {
  upload_url: string;
  upload_token: string;
  expires_in: number;
}

type UploadProgress = (percent: number) => void;

async function directObjectUpload(
  resourceType: "course" | "lesson",
  resourceId: string,
  assetType: "thumbnail" | "video" | "pdf" | "file",
  file: File,
  signal?: AbortSignal,
  onProgress?: UploadProgress,
  originalName?: string,
): Promise<void> {
  const { data: grant } = await apiClient.post<PresignedUploadGrant>("/uploads/presign", {
    resource_type: resourceType,
    resource_id: resourceId,
    asset_type: assetType,
    mime_type: file.type,
    size_bytes: file.size,
    ...(originalName ? { original_name: originalName } : {}),
  });

  try {
    await new Promise<void>((resolve, reject) => {
      if (signal?.aborted) {
        reject(new DOMException("Upload cancelled", "AbortError"));
        return;
      }
      const request = new XMLHttpRequest();
      request.open("PUT", grant.upload_url);
      request.setRequestHeader("Content-Type", file.type);
      request.setRequestHeader("If-None-Match", "*");
      request.upload.onprogress = (event) => {
        if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100));
      };
      request.onload = () => request.status >= 200 && request.status < 300
        ? resolve()
        : reject(new Error(`Storage upload failed (${request.status}). Retry the upload.`));
      request.onerror = () => reject(new Error("Storage upload failed. Check your connection and retry."));
      request.onabort = () => reject(new DOMException("Upload cancelled", "AbortError"));
      signal?.addEventListener("abort", () => request.abort(), { once: true });
      if (signal?.aborted) request.abort();
      else request.send(file);
    });
    if (signal?.aborted) throw new DOMException("Upload cancelled", "AbortError");
    await apiClient.post("/uploads/complete", { upload_token: grant.upload_token });
  } catch (error) {
    await apiClient.post("/uploads/cancel", { upload_token: grant.upload_token }).catch(() => undefined);
    throw error;
  }
}

// =============================================================================
// AUTHENTICATION SERVICES
// =============================================================================
export const authService = {
  async register(data: any): Promise<{ user: User; verification_token: string }> {
    const res = await apiClient.post("/auth/register", data);
    return res.data;
  },

  async login(data: any): Promise<{ access_token: string; refresh_token: string; token_type: string }> {
    const res = await apiClient.post("/auth/login", data);
    setTokens(res.data.access_token, res.data.refresh_token);
    return res.data;
  },

  async getMe(): Promise<User> {
    const res = await apiClient.get("/auth/me");
    return res.data;
  },

  async verifyEmail(token: string): Promise<User> {
    const res = await apiClient.post(`/auth/verify-email?token=${token}`);
    return res.data;
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const res = await apiClient.post("/auth/forgot-password", { email });
    return res.data;
  },

  async resetPassword(data: any): Promise<{ message: string }> {
    const res = await apiClient.post("/auth/reset-password", data);
    return res.data;
  },

  async changePassword(data: any): Promise<{ message: string }> {
    const res = await apiClient.post("/auth/change-password", data);
    return res.data;
  },

  logout() {
    clearTokens();
  },
};

// =============================================================================
// COURSE SERVICES
// =============================================================================
export const courseService = {
  async listPublic(params?: any): Promise<{ items: CourseSummary[]; total: number; page: number; pages: number }> {
    const res = await apiClient.get("/courses/", { params });
    return res.data;
  },

  async listTaught(): Promise<CourseSummary[]> {
    const res = await apiClient.get("/courses/my");
    return res.data;
  },

  async getDetails(id: string): Promise<Course> {
    const res = await apiClient.get(`/courses/${id}`);
    return res.data;
  },

  async create(data: any): Promise<Course> {
    const res = await apiClient.post("/courses/", data);
    return res.data;
  },

  async update(id: string, data: any): Promise<Course> {
    const res = await apiClient.patch(`/courses/${id}`, data);
    return res.data;
  },

  async delete(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/courses/${id}`);
    return res.data;
  },

  async duplicate(id: string): Promise<CourseSummary> {
    const res = await apiClient.post(`/courses/${id}/duplicate`);
    return res.data;
  },

  async uploadThumbnail(id: string, file: File, signal?: AbortSignal): Promise<Course> {
    await directObjectUpload("course", id, "thumbnail", file, signal);
    return this.getDetails(id);
  },

  async uploadFile(id: string, file: File, fileType: string): Promise<CourseFile> {
    await directObjectUpload("course", id, "file", file, undefined, undefined, file.name);
    const files = await this.listFiles(id);
    const uploaded = [...files].reverse().find((item) => item.original_name === file.name && item.size_bytes === file.size);
    if (!uploaded) throw new Error(`Upload completed, but the ${fileType} file record could not be loaded.`);
    return uploaded;
  },

  async listFiles(id: string): Promise<CourseFile[]> {
    const res = await apiClient.get(`/courses/${id}/files`);
    return res.data;
  },

  async search(params: any): Promise<{ items: CourseSummary[]; total: number; page: number; pages: number }> {
    const res = await apiClient.get("/search/courses", { params });
    return res.data;
  },
};

// =============================================================================
// LESSON SERVICES
// =============================================================================
export const lessonService = {
  async listByCourse(courseId: string): Promise<LessonSummary[]> {
    const res = await apiClient.get(`/courses/${courseId}/lessons`);
    return res.data;
  },

  async getDetails(id: string): Promise<Lesson> {
    const res = await apiClient.get(`/lessons/${id}`);
    return res.data;
  },

  async create(courseId: string, data: any): Promise<Lesson> {
    const res = await apiClient.post(`/courses/${courseId}/lessons`, data);
    return res.data;
  },

  async update(id: string, data: any): Promise<Lesson> {
    const res = await apiClient.patch(`/lessons/${id}`, data);
    return res.data;
  },

  async delete(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/lessons/${id}`);
    return res.data;
  },

  async uploadVideo(id: string, file: File, signal?: AbortSignal, onProgress?: UploadProgress): Promise<Lesson> {
    await directObjectUpload("lesson", id, "video", file, signal, onProgress);
    return this.getDetails(id);
  },

  async uploadPdf(id: string, file: File, signal?: AbortSignal): Promise<Lesson> {
    await directObjectUpload("lesson", id, "pdf", file, signal);
    return this.getDetails(id);
  },

  async uploadThumbnail(id: string, file: File, signal?: AbortSignal): Promise<Lesson> {
    await directObjectUpload("lesson", id, "thumbnail", file, signal);
    return this.getDetails(id);
  },

  async updateProgress(id: string, data: { is_completed: boolean; watch_time_seconds: number; completion_percentage: number }): Promise<LessonProgress> {
    const res = await apiClient.post(`/lessons/${id}/progress`, data);
    return res.data;
  },

  async getProgress(id: string): Promise<LessonProgress> {
    const res = await apiClient.get(`/lessons/${id}/progress`);
    return res.data;
  },
};

// =============================================================================
// ENROLLMENT SERVICES
// =============================================================================
export const enrollmentService = {
  async enroll(courseId: string): Promise<Enrollment> {
    const res = await apiClient.post("/enrollments/", { course_id: courseId });
    return res.data;
  },

  async listMy(): Promise<Enrollment[]> {
    const res = await apiClient.get("/enrollments/my");
    return res.data;
  },

  async drop(courseId: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/enrollments/${courseId}`);
    return res.data;
  },

  async listStudents(courseId: string): Promise<Enrollment[]> {
    const res = await apiClient.get(`/enrollments/courses/${courseId}/students`);
    return res.data;
  },

  async getStatus(courseId: string): Promise<{ is_enrolled: boolean; status?: string; progress?: number }> {
    const res = await apiClient.get(`/enrollments/${courseId}/status`);
    return res.data;
  },
};

// =============================================================================
// QUIZ SERVICES
// =============================================================================
export const quizService = {
  async listByCourse(courseId: string): Promise<Quiz[]> {
    const res = await apiClient.get(`/courses/${courseId}/quizzes`);
    return res.data;
  },

  async getDetails(id: string): Promise<Quiz> {
    const res = await apiClient.get(`/quizzes/${id}`);
    return res.data;
  },

  async getDetailsTeacher(id: string): Promise<any> {
    const res = await apiClient.get(`/quizzes/${id}/teacher`);
    return res.data;
  },

  async create(courseId: string, data: any): Promise<Quiz> {
    const res = await apiClient.post(`/courses/${courseId}/quizzes`, data);
    return res.data;
  },

  async generateAI(courseId: string, data: any): Promise<Quiz> {
    const res = await apiClient.post(`/courses/${courseId}/quizzes/ai-generate`, data);
    return res.data;
  },

  async update(id: string, data: any): Promise<Quiz> {
    const res = await apiClient.patch(`/quizzes/${id}`, data);
    return res.data;
  },

  async delete(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/quizzes/${id}`);
    return res.data;
  },

  async submitAttempt(id: string, data: { answers: Array<{ question_id: string; given_answer: string }>; time_taken_seconds: number }): Promise<QuizAttempt> {
    const res = await apiClient.post(`/quizzes/${id}/attempts`, data);
    return res.data;
  },

  async getMyAttempts(id: string): Promise<QuizAttempt[]> {
    const res = await apiClient.get(`/quizzes/${id}/my-attempts`);
    return res.data;
  },

  async getStudentHistory(): Promise<QuizAttempt[]> {
    const res = await apiClient.get("/quizzes/students/quiz-history");
    return res.data;
  },
};

// =============================================================================
// ASSIGNMENT SERVICES
// =============================================================================
export const assignmentService = {
  async create(courseId: string, data: any): Promise<Assignment> {
    const res = await apiClient.post(`/courses/${courseId}/assignments`, data);
    return res.data;
  },

  async listByCourse(courseId: string): Promise<Assignment[]> {
    const res = await apiClient.get(`/courses/${courseId}/assignments`);
    return res.data;
  },

  async getDetails(id: string): Promise<Assignment> {
    const res = await apiClient.get(`/assignments/${id}`);
    return res.data;
  },

  async update(id: string, data: any): Promise<Assignment> {
    const res = await apiClient.patch(`/assignments/${id}`, data);
    return res.data;
  },

  async delete(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/assignments/${id}`);
    return res.data;
  },

  async submitText(id: string, textContent: string): Promise<AssignmentSubmission> {
    const res = await apiClient.post(`/assignments/${id}/submit`, { text_content: textContent });
    return res.data;
  },

  async submitFile(id: string, file: File): Promise<AssignmentSubmission> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiClient.post(`/assignments/${id}/submit-file`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  async getSubmissions(id: string): Promise<AssignmentSubmission[]> {
    const res = await apiClient.get(`/assignments/${id}/submissions`);
    return res.data;
  },

  async gradeSubmission(submissionId: string, data: { marks_obtained: number; feedback: string }): Promise<AssignmentSubmission> {
    const res = await apiClient.patch(`/submissions/${submissionId}/grade`, data);
    return res.data;
  },

  async getMySubmissions(): Promise<AssignmentSubmission[]> {
    const res = await apiClient.get("/my-submissions");
    return res.data;
  },
};

// =============================================================================
// AI CORE SERVICES
// =============================================================================
export const aiService = {
  async chat(message: string, sessionId?: string, courseId?: string): Promise<{ ai_response: string; session_id: string; message_count: number }> {
    const res = await apiClient.post("/ai/chat", { message, session_id: sessionId, course_id: courseId });
    return res.data;
  },

  async getChatSessions(): Promise<AIChatSession[]> {
    const res = await apiClient.get("/ai/chat/sessions");
    return res.data;
  },

  async getChatHistory(sessionId: string): Promise<{ session_id: string; messages: AIChatMessage[] }> {
    const res = await apiClient.get(`/ai/chat/sessions/${sessionId}`);
    return res.data;
  },

  async deleteChatSession(sessionId: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/ai/chat/sessions/${sessionId}`);
    return res.data;
  },

  async generateNotes(data: { source_type: "lesson" | "text"; source_id?: string; source_text?: string; title: string }): Promise<GeneratedNote> {
    const res = await apiClient.post("/ai/notes/generate", data);
    return res.data;
  },

  async getMyNotes(): Promise<GeneratedNote[]> {
    const res = await apiClient.get("/ai/notes");
    return res.data;
  },

  async summarize(data: { source_type: "lesson" | "text"; source_id?: string; source_text?: string; length: "short" | "medium" | "long" }): Promise<{ summary: string; key_points: string[] }> {
    const res = await apiClient.post("/ai/summarize", data);
    return res.data;
  },

  async generateFlashcards(data: { source_type: "lesson" | "text"; source_id?: string; source_text?: string; num_cards: number; title: string }): Promise<FlashcardSet> {
    const res = await apiClient.post("/ai/flashcards/generate", data);
    return res.data;
  },

  async getMyFlashcards(): Promise<FlashcardSet[]> {
    const res = await apiClient.get("/ai/flashcards");
    return res.data;
  },

  async generateStudyPlan(data: { course_id?: string; topics: string[]; duration_weeks: number; hours_per_day: number; goals?: string }): Promise<StudyPlan> {
    const res = await apiClient.post("/ai/study-plan/generate", data);
    return res.data;
  },

  async getMyStudyPlans(): Promise<StudyPlan[]> {
    const res = await apiClient.get("/ai/study-plans");
    return res.data;
  },

  async getRecommendations(courseId?: string): Promise<{ next_lessons: any[]; weak_topics: string[]; practice_quiz_difficulty: string }> {
    const res = await apiClient.get("/ai/recommendations", { params: { course_id: courseId } });
    return res.data;
  },
};

// =============================================================================
// DASHBOARD & ANALYTICS SERVICES
// =============================================================================
export const dashboardService = {
  async getStudent(): Promise<StudentDashboardData> {
    const res = await apiClient.get("/dashboard/student");
    return res.data;
  },

  async getTeacher(): Promise<TeacherDashboardData> {
    const res = await apiClient.get("/dashboard/teacher");
    return res.data;
  },

  async getAdmin(): Promise<AdminDashboardData> {
    const res = await apiClient.get("/dashboard/admin");
    return res.data;
  },
};

// =============================================================================
// USER MANAGEMENT SERVICES (Admin)
// =============================================================================
export const userService = {
  async listAll(params?: { role?: string; page?: number; page_size?: number }): Promise<{ items: User[]; total: number; page: number; pages: number }> {
    const res = await apiClient.get("/users/", { params });
    return res.data;
  },

  async getById(id: string): Promise<User> {
    const res = await apiClient.get(`/users/${id}`);
    return res.data;
  },

  async adminUpdate(id: string, data: { role?: string; is_active?: boolean; is_verified?: boolean }): Promise<User> {
    const res = await apiClient.patch(`/users/${id}`, data);
    return res.data;
  },

  async adminDelete(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/users/${id}`);
    return res.data;
  },
};

// =============================================================================
// ADMIN COURSE SERVICES (Admin — sees all courses including drafts)
// =============================================================================
export const adminCourseService = {
  async listAll(params?: { page?: number; page_size?: number; q?: string }): Promise<{ items: CourseSummary[]; total: number; page: number; pages: number }> {
    const res = await apiClient.get("/courses/", { params: { ...params, status: undefined } });
    return res.data;
  },

  async forcePublish(id: string, status: "published" | "draft" | "archived"): Promise<CourseSummary> {
    const res = await apiClient.patch(`/courses/${id}`, { status });
    return res.data;
  },

  async forceDelete(id: string): Promise<{ message: string }> {
    const res = await apiClient.delete(`/courses/${id}`);
    return res.data;
  },
};
