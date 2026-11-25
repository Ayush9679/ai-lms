import type { CheckoutResponse, PaymentOrder } from "@/services/payments";

interface CheckoutOptions {
  key: string;
  order_id: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  handler: (response: CheckoutResponse) => void;
  modal: { confirm_close: boolean; ondismiss: () => void };
  retry: { enabled: boolean };
  theme: { color: string };
}

interface CheckoutInstance {
  on(event: "payment.failed", listener: () => void): void;
  open(): void;
}

type RazorpayConstructor = new (options: CheckoutOptions) => CheckoutInstance;

declare global {
  interface Window {
    Razorpay?: RazorpayConstructor;
  }
}

let scriptLoad: Promise<RazorpayConstructor> | undefined;

function loadCheckout(): Promise<RazorpayConstructor> {
  if (window.Razorpay) return Promise.resolve(window.Razorpay);
  if (!scriptLoad) {
    scriptLoad = new Promise<RazorpayConstructor>((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;

      const fail = () => {
        window.clearTimeout(timeout);
        script.remove();
        reject(new Error("Razorpay Checkout could not load."));
      };
      const timeout = window.setTimeout(fail, 12_000);
      script.onerror = fail;
      script.onload = () => {
        window.clearTimeout(timeout);
        if (window.Razorpay) resolve(window.Razorpay);
        else fail();
      };
      document.head.append(script);
    }).catch((error: unknown) => {
      scriptLoad = undefined;
      throw error;
    });
  }
  return scriptLoad;
}

export async function prepareCheckout(
  order: PaymentOrder,
  courseTitle: string,
  callbacks: {
    onResponse: (response: CheckoutResponse) => void;
    onFailure: () => void;
    onDismiss: () => void;
  },
): Promise<CheckoutInstance> {
  if (
    !/^rzp_test_[A-Za-z0-9]+$/.test(order.razorpay_key_id) ||
    !/^order_[A-Za-z0-9]+$/.test(order.razorpay_order_id) ||
    order.currency !== "INR" ||
    !Number.isSafeInteger(order.amount) ||
    order.amount <= 0
  ) {
    throw new Error("Invalid Razorpay Test Mode order.");
  }

  const Razorpay = await loadCheckout();
  const checkout = new Razorpay({
    key: order.razorpay_key_id,
    order_id: order.razorpay_order_id,
    amount: order.amount,
    currency: order.currency,
    name: "AI-LMS",
    description: courseTitle,
    handler: callbacks.onResponse,
    modal: { confirm_close: true, ondismiss: callbacks.onDismiss },
    retry: { enabled: false },
    theme: { color: "#7c3aed" },
  });
  checkout.on("payment.failed", callbacks.onFailure);
  return checkout;
}
