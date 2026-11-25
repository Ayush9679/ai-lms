/**
 * Razorpay checkout recovery helpers.
 *
 * Kept browser/framework agnostic so the state machine can be unit-tested
 * with node:test without a DOM. The CourseCheckout component supplies the
 * session-scoped storage and drives the UI from these decisions.
 */

export type RecoveryStatus =
  | "created"
  | "pending"
  | "authorized"
  | "captured"
  | "enrolled"
  | "unknown";

export interface OrderStatus {
  razorpay_order_id: string;
  course_id: string;
  status: RecoveryStatus;
  safe_to_retry: boolean;
  attempt_status: "failed" | null;
}

export type RecoveryAction =
  | { action: "confirmed"; message: string }
  | { action: "refresh"; message: string }
  | { action: "wait"; message: string; canCheck: boolean }
  | { action: "resume"; message: string };

/**
 * Map a backend /payments/status response (plus the current enrollment state)
 * to a UI action. Enrollment is only trusted from the backend; the browser
 * checkout callback is never used alone to grant access.
 */
export function decideRecovery(
  status: OrderStatus,
  currentlyEnrolled: boolean,
): RecoveryAction {
  if (currentlyEnrolled) {
    return { action: "confirmed", message: "You already have access to this course." };
  }
  switch (status.status) {
    case "enrolled":
      return { action: "confirmed", message: "Purchase confirmed. Your course is ready." };
    case "captured":
      return {
        action: "refresh",
        message: "Payment captured. Course access is being finalized; check status shortly.",
      };
    case "created":
      if (status.safe_to_retry) {
        return {
          action: "resume",
          message: "A pending order is ready. Resume with the same checkout.",
        };
      }
      return {
        action: "wait",
        message: "Your order is not ready to retry yet. Check again shortly.",
        canCheck: true,
      };
    case "authorized":
      return {
        action: "wait",
        message: "Payment is authorized but not yet captured. Do not pay again; check status shortly.",
        canCheck: true,
      };
    case "pending":
      return {
        action: "wait",
        message: "Payment is still being processed. Do not start a new purchase; check status before retrying.",
        canCheck: true,
      };
    case "unknown":
    default:
      return {
        action: "wait",
        message: "Payment state is unclear. Check status before trying again.",
        canCheck: true,
      };
  }
}

/** Transient errors (429 rate limit, timeouts, 5xx, network) are retryable. */
export function isTransientError(error: unknown): boolean {
  if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
    return true;
  }
  const status = (error as { response?: { status?: number } })?.response?.status;
  if (status === undefined) return true; // no HTTP status = network-level failure
  return status === 408 || status === 429 || status >= 500;
}

export const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Retry a callable with exponential backoff while failures are transient
 * (429 rate limits, timeouts, gateway errors). Non-transient errors (e.g.
 * 403/404) surface immediately and are never retried.
 */
export async function withBackoff<T>(
  attempt: () => Promise<T>,
  options: { attempts?: number; baseDelayMs?: number; maxDelayMs?: number } = {},
): Promise<T> {
  const attempts = options.attempts ?? 4;
  const baseDelayMs = options.baseDelayMs ?? 1000;
  const maxDelayMs = options.maxDelayMs ?? 10000;
  let delay = baseDelayMs;
  for (let i = 0; i < attempts; i++) {
    try {
      return await attempt();
    } catch (error) {
      const last = i === attempts - 1;
      if (last || !isTransientError(error)) throw error;
      await sleep(delay);
      delay = Math.min(delay * 2, maxDelayMs);
    }
  }
  throw new Error("Transient failure");
}

// ---------------------------------------------------------------------------
// Pending order reference storage
// ---------------------------------------------------------------------------

export function checkoutStorageKey(studentId: string, courseId: string): string {
  return `ai-lms:checkout:${studentId}:${courseId}`;
}

export interface PendingOrderRef {
  orderId: string;
  phase: "pending" | "captured";
}

export function serializeRef(ref: PendingOrderRef): string {
  return JSON.stringify(ref);
}

export function parseRef(raw: string | null): PendingOrderRef | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { orderId?: unknown; phase?: unknown };
    if (
      typeof parsed.orderId === "string" &&
      /^order_[A-Za-z0-9]+$/.test(parsed.orderId)
    ) {
      return {
        orderId: parsed.orderId,
        phase: parsed.phase === "captured" ? "captured" : "pending",
      };
    }
  } catch {
    // Ignore malformed or tampered storage values.
  }
  return null;
}

type WebStorage = Pick<Storage, "getItem" | "setItem" | "removeItem"> | undefined;

export function readPendingOrder(storage: WebStorage, key: string): PendingOrderRef | null {
  if (!storage) return null;
  return parseRef(storage.getItem(key));
}

export function writePendingOrder(storage: WebStorage, key: string, ref: PendingOrderRef): void {
  if (storage) storage.setItem(key, serializeRef(ref));
}

export function clearPendingOrder(storage: WebStorage, key: string): void {
  if (storage) storage.removeItem(key);
}