import { apiClient } from "@/lib/api-client";

export interface PaymentOrder {
  razorpay_key_id: string;
  razorpay_order_id: string;
  amount: number;
  currency: string;
}

export interface CheckoutResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

interface VerifiedPayment {
  razorpay_payment_id: string;
  status: string;
}

export type RecoveryStatus =
  | "created"
  | "pending"
  | "authorized"
  | "captured"
  | "enrolled"
  | "unknown";

export interface OrderStatusResponse {
  razorpay_order_id: string;
  course_id: string;
  status: RecoveryStatus;
  safe_to_retry: boolean;
  attempt_status: "failed" | null;
}

const timeout = 15_000;

export const paymentService = {
  async createOrder(courseId: string): Promise<PaymentOrder> {
    const response = await apiClient.post<PaymentOrder>(
      "/payments/create-order", { course_id: courseId }, { timeout },
    );
    return response.data;
  },

  async verify(checkout: CheckoutResponse): Promise<VerifiedPayment> {
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = checkout;
    const response = await apiClient.post<VerifiedPayment>(
      "/payments/verify", { razorpay_order_id, razorpay_payment_id, razorpay_signature }, { timeout },
    );
    return response.data;
  },

  async checkStatus(razorpay_order_id: string): Promise<OrderStatusResponse> {
    const response = await apiClient.post<OrderStatusResponse>(
      "/payments/status", { razorpay_order_id }, { timeout },
    );
    return response.data;
  },
};
