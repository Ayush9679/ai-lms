export type UserRole = "student" | "teacher" | "admin";

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  profile_image: string | null;
}

export interface User extends UserSummary {
  bio: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export type CourseLevel = "beginner" | "intermediate" | "advanced";
export type CourseStatus = "draft" | "published" | "archived";

export interface Course {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  category: string | null;
  level: CourseLevel;
  status: CourseStatus;
  thumbnail: string | null;
  price: number;
  instructor_id: string;
  instructor?: UserSummary;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface CourseSummary {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  category: string | null;
  level: CourseLevel;
  status: CourseStatus;
  thumbnail: string | null;
  price: number;
  instructor_name: string;
  total_lessons: number;
  total_students: number;
  created_at: string;
}

export type FileType = "image" | "video" | "document" | "assignment" | "other";

export interface CourseFile {
  id: string;
  course_id: string;
  uploaded_by: string | null;
  file_name: string;
  original_name: string;
  file_path: string;
  file_type: FileType;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  content: string | null;
  thumbnail: string | null;
  video_url: string | null;
  video_status: "pending" | "uploading" | "ready" | "failed";
  pdf_url: string | null;
  transcript: string | null;
  duration_minutes: number | null;
  order_index: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface LessonSummary {
  id: string;
  title: string;
  duration_minutes: number | null;
  order_index: number;
  is_published: boolean;
  video_status: "pending" | "uploading" | "ready" | "failed";
  has_video: boolean;
  has_pdf: boolean;
}

export interface LessonProgress {
  id: string;
  lesson_id: string;
  user_id: string;
  is_completed: boolean;
  watch_time_seconds: number;
  completion_percentage: number;
  created_at: string;
  updated_at: string;
}

export type EnrollmentStatus = "active" | "completed" | "dropped" | "pending";

export interface Enrollment {
  id: string;
  student_id: string;
  course_id: string;
  status: EnrollmentStatus;
  progress: number;
  completed_lessons: number;
  created_at: string;
  updated_at: string;
  course?: Course;
  student?: UserSummary;
}

export type QuestionType = "mcq" | "true_false" | "subjective";
export type DifficultyLevel = "easy" | "medium" | "hard";

export interface QuestionOption {
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: string;
  quiz_id: string;
  question_text: string;
  question_type: QuestionType;
  options: QuestionOption[] | null;
  correct_answer: string | null;
  explanation: string | null;
  marks: number;
  order_index: number;
  created_at: string;
}

export interface Quiz {
  id: string;
  course_id: string;
  lesson_id: string | null;
  created_by: string;
  title: string;
  description: string | null;
  difficulty: DifficultyLevel;
  passing_score: number;
  negative_marking: boolean;
  negative_marks_per_wrong: number;
  time_limit_minutes: number | null;
  is_ai_generated: boolean;
  max_attempts: number;
  created_at: string;
  updated_at: string;
  questions?: Question[];
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  student_id: string;
  score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  time_taken_seconds: number | null;
  attempt_number: number;
  created_at: string;
  updated_at: string;
  quiz?: Quiz;
}

export interface QuizAnswer {
  id: string;
  attempt_id: string;
  question_id: string;
  given_answer: string | null;
  is_correct: boolean | null;
  marks_awarded: number;
  created_at: string;
}

export interface Assignment {
  id: string;
  course_id: string;
  created_by: string;
  title: string;
  description: string | null;
  instructions: string | null;
  due_date: string | null;
  max_marks: number;
  passing_marks: number;
  is_published?: boolean;
  is_closed?: boolean;
  submission_count?: number;
  created_at: string;
  updated_at: string;
}

export interface AssignmentSubmission {
  id: string;
  assignment_id: string;
  student_id: string;
  file_url: string | null;
  file_name: string | null;
  text_content: string | null;
  marks_obtained: number | null;
  feedback: string | null;
  graded_by: string | null;
  graded_at: string | null;
  created_at: string;
  updated_at: string;
  student?: UserSummary;
}

// AI Modules
export interface AIChatSession {
  id: string;
  user_id: string;
  course_id: string | null;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AIChatMessage {
  id: string;
  session_id: string;
  role: "user" | "model";
  content: string;
  created_at: string;
}

export interface GeneratedNote {
  id: string;
  user_id: string;
  course_id: string | null;
  lesson_id: string | null;
  title: string;
  source_type: string;
  content: string;
  summary: string | null;
  created_at: string;
}

export interface StudyPlan {
  id: string;
  user_id: string;
  course_id: string | null;
  title: string;
  duration_weeks: number;
  plan_data: unknown; // Weekly JSON breakdown
  is_active: boolean;
  created_at: string;
}

export interface Flashcard {
  front: string;
  back: string;
}

export interface FlashcardSet {
  id: string;
  user_id: string;
  course_id: string | null;
  lesson_id: string | null;
  title: string;
  cards: Flashcard[];
  card_count: number;
  created_at: string;
}

// Dashboard statistics
export interface StudentDashboardData {
  enrolled_courses: unknown[];
  progress_summary: {
    total_courses: number;
    completed_courses: number;
    average_progress: number;
  };
  recent_activity: unknown[];
  quiz_summary: {
    total_quizzes_taken: number;
    passed_quizzes: number;
    average_score: number;
  };
  recommended_courses: CourseSummary[];
}

export interface TeacherDashboardData {
  course_stats: {
    total_courses: number;
    published_courses: number;
    draft_courses: number;
  };
  student_stats: {
    total_students: number;
    active_students_this_month: number;
  };
  quiz_stats: {
    total_quizzes_built: number;
  };
  course_list: Array<{
    id: string;
    title: string;
    status: string;
    enrollments_count: number;
    average_progress: number;
    lessons_count: number;
    quizzes_count: number;
  }>;
  recent_activity: unknown[];
}

export interface AdminDashboardData {
  metrics: {
    total_users: number;
    total_students: number;
    total_teachers: number;
    total_courses: number;
    total_enrollments: number;
  };
  recent_activity: unknown[];
  system_logs: unknown[];
}
