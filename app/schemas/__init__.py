"""AI-LMS schemas package."""
from app.schemas.ai import (
    AIQuizGenerationResult,
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionSummary,
    Flashcard,
    FlashcardSetResponse,
    GenerateFlashcardsRequest,
    GenerateNotesRequest,
    GenerateNotesResponse,
    GenerateStudyPlanRequest,
    RecommendationResponse,
    StudyPlanResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.schemas.assignment import (
    AssignmentResponse,
    CreateAssignmentRequest,
    GradeSubmissionRequest,
    SubmissionResponse,
    SubmissionWithStudent,
    SubmitAssignmentRequest,
    UpdateAssignmentRequest,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.common import (
    BaseSchema,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
)
from app.schemas.course import (
    CourseSummary,
    CourseFileResponse,
    CourseResponse,
    CourseSearchParams,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from app.schemas.enrollment import (
    EnrollmentResponse,
    EnrollmentWithCourse,
    EnrollmentWithStudent,
    EnrollRequest,
)
from app.schemas.lesson import (
    CreateLessonRequest,
    LessonProgressResponse,
    LessonProgressUpdate,
    LessonResponse,
    LessonSummary,
    UpdateLessonRequest,
)
from app.schemas.quiz import (
    CreateQuizRequest,
    CreateQuestionRequest,
    GenerateQuizRequest,
    QuizAnswerResponse,
    QuizAttemptResponse,
    QuizAttemptSummary,
    QuizResponse,
    QuizSummary,
    QuestionWithAnswer,
    SubmitAttemptRequest,
    UpdateQuizRequest,
)
from app.schemas.user import (
    AdminUpdateUserRequest,
    UpdateProfileRequest,
    UserListResponse,
    UserPublic,
    UserSummary,
)
from app.schemas.dashboard import (
    StudentDashboardOut,
    TeacherDashboardOut,
    AdminDashboardOut,
)
