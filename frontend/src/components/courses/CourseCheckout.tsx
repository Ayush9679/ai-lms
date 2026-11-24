"use client";

import { isAxiosError } from "axios";
import { ChevronRight, Loader2 } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { prepareCheckout } from "@/lib/razorpay-checkout";
import { paymentService, type CheckoutResponse } from "@/services/payments";

interface CourseCheckoutProps {
  courseId: string;
  courseTitle: string;
  studentId: string;
  isEnrolled: boolean;
  enrolledAction: ReactNode;
  refreshEnrollment: () => Promise<boolean>;
  onConfirmed: () => void;
}

type StoredStatus = "pending" | "captured";
type CheckoutState = {
  phase: "ready" | "starting" | "checkout" | "checking" | "pending" | "confirmed";
  message?: string;
};

const pendingMessage =
  "Payment confirmation is pending. Check status before making another payment.";
const capturedMessage =
  "Payment captured. Course access could not be refreshed yet. Check status to update it.";

function readStatus(key: string): StoredStatus | null {
  try {
    const status = window.localStorage.getItem(key);
    return status === "pending" || status === "captured" ? status : null;
  } catch {
    return null;
  }
}

function saveStatus(key: string, status: StoredStatus | null) {
  try {
    if (status) window.localStorage.setItem(key, status);
    else window.localStorage.removeItem(key);
  } catch {
    // Checkout can still recover in memory when browser storage is unavailable.
  }
}

export function CourseCheckout({
  courseId,
  courseTitle,
  studentId,
  isEnrolled,
  enrolledAction,
  refreshEnrollment,
  onConfirmed,
}: CourseCheckoutProps) {
  const storageKey = `ai-lms:checkout:${studentId}:${courseId}`;
  const [state, setState] = useState<CheckoutState>(() => {
    const status = readStatus(storageKey);
    return status
      ? { phase: "pending", message: status === "captured" ? capturedMessage : pendingMessage }
      : { phase: "ready" };
  });
  const busy = useRef(false);
  const mounted = useRef(true);
  const checkoutResponse = useRef<CheckoutResponse | null>(null);
  const captured = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    if (isEnrolled) saveStatus(storageKey, null);
  }, [isEnrolled, storageKey]);

  async function reconcile() {
    if (!mounted.current) return;
    setState({ phase: "checking", message: "Checking payment and course access…" });

    const response = checkoutResponse.current;
    captured.current ||= readStatus(storageKey) === "captured";
    if (response && !captured.current) {
      try {
        const payment = await paymentService.verify(response);
        if (payment.status === "captured" && payment.razorpay_payment_id === response.razorpay_payment_id) {
          captured.current = true;
          checkoutResponse.current = null;
          saveStatus(storageKey, "captured");
        }
      } catch {
        // An authorized payment, timeout or webhook race can leave verification inconclusive.
      }
    }

    try {
      if (mounted.current && await refreshEnrollment()) {
        saveStatus(storageKey, null);
        checkoutResponse.current = null;
        if (mounted.current) {
          setState({ phase: "confirmed", message: "Purchase confirmed. Your course is ready." });
          onConfirmed();
        }
        return;
      }
    } catch {
      // Keep the recovery action available if enrollment cannot be refreshed.
    } finally {
      busy.current = false;
    }

    if (mounted.current) {
      setState({ phase: "pending", message: captured.current ? capturedMessage : pendingMessage });
    }
  }

  async function startCheckout() {
    if (busy.current || isEnrolled || state.phase !== "ready") return;
    busy.current = true;
    if (readStatus(storageKey)) {
      await reconcile();
      return;
    }

    setState({ phase: "starting" });
    let opening = false;

    try {
      if (await refreshEnrollment()) {
        busy.current = false;
        if (mounted.current) {
          setState({ phase: "confirmed", message: "You already have access to this course." });
          onConfirmed();
        }
        return;
      }
      if (!mounted.current) return;

      const order = await paymentService.createOrder(courseId);
      if (!mounted.current) return;
      let settled = false;
      let failed = false;
      const checkout = await prepareCheckout(order, courseTitle, {
        onResponse: (response) => {
          if (settled || !mounted.current) return;
          settled = true;
          if (response?.razorpay_order_id === order.razorpay_order_id &&
              typeof response.razorpay_payment_id === "string" &&
              typeof response.razorpay_signature === "string") {
            checkoutResponse.current = response;
          }
          void reconcile();
        },
        onFailure: () => {
          if (settled || !mounted.current) return;
          failed = true;
          setState({
            phase: "checkout",
            message: "Razorpay reported a failed payment. Close Checkout to return to the course.",
          });
        },
        onDismiss: () => {
          if (settled || !mounted.current) return;
          settled = true;
          saveStatus(storageKey, null);
          busy.current = false;
          setState({ phase: "ready", message: failed ? "Payment failed." : "Checkout cancelled." });
        },
      });
      if (!mounted.current) return;

      // Mark the attempt before opening so a reload cannot immediately start another payment.
      saveStatus(storageKey, "pending");
      opening = true;
      setState({ phase: "checkout" });
      checkout.open();
    } catch (error: unknown) {
      if (!mounted.current) return;
      const status = isAxiosError(error) ? error.response?.status : undefined;
      if (opening || status === 409) {
        saveStatus(storageKey, "pending");
        await reconcile();
        return;
      }
      busy.current = false;
      setState({
        phase: "ready",
        message: status === 404
          ? "Test Checkout is currently unavailable for this course."
          : "Checkout could not start. Please try again.",
      });
    }
  }

  function checkPayment() {
    if (busy.current) return;
    busy.current = true;
    void reconcile();
  }

  const processing = state.phase === "starting" || state.phase === "checkout" || state.phase === "checking";
  return (
    <div className="flex flex-col gap-3">
      {state.message && (state.phase !== "pending" || !isEnrolled) && (
        <p role="status" className="text-sm leading-relaxed text-zinc-300">{state.message}</p>
      )}
      {isEnrolled ? enrolledAction : (
        <button
          type="button"
          disabled={processing || state.phase === "confirmed"}
          onClick={state.phase === "pending" ? checkPayment : () => { void startCheckout(); }}
          className="glow-btn flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-purple-600 to-blue-500 py-4 text-sm font-bold text-white hover:from-purple-500 hover:to-blue-400 disabled:cursor-wait disabled:opacity-60"
        >
          {processing && <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />}
          {state.phase === "starting" && "Opening Checkout…"}
          {state.phase === "checkout" && "Checkout open"}
          {state.phase === "checking" && "Checking payment…"}
          {state.phase === "pending" && "Check payment status"}
          {state.phase === "confirmed" && "Purchase confirmed"}
          {state.phase === "ready" && <>Buy Course <ChevronRight aria-hidden="true" className="h-4 w-4" /></>}
        </button>
      )}
    </div>
  );
}
