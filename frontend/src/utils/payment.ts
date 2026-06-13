import type { PaymentSession } from "../services/api/customer";

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => {
      open: () => void;
    };
  }
}

const RAZORPAY_CHECKOUT_URL = "https://checkout.razorpay.com/v1/checkout.js";

let razorpayScriptPromise: Promise<void> | null = null;

function loadRazorpayScript() {
  if (window.Razorpay) {
    return Promise.resolve();
  }

  if (razorpayScriptPromise) {
    return razorpayScriptPromise;
  }

  razorpayScriptPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>(
      `script[src="${RAZORPAY_CHECKOUT_URL}"]`,
    );

    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(), { once: true });
      existingScript.addEventListener("error", () => reject(new Error("Failed to load Razorpay checkout.")), {
        once: true,
      });
      return;
    }

    const script = document.createElement("script");
    script.src = RAZORPAY_CHECKOUT_URL;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Razorpay checkout."));
    document.body.appendChild(script);
  });

  return razorpayScriptPromise;
}

/**
 * openPaymentCheckout opens Razorpay when the backend returns checkout identifiers.
 * It falls back to a provider-hosted payment URL so the payment flow remains MVP-friendly.
 */
export async function openPaymentCheckout(session: PaymentSession) {
  if (session.gateway?.toUpperCase() === "RAZORPAY" && session.razorpay_key_id && session.razorpay_order_id) {
    await loadRazorpayScript();

    if (!window.Razorpay) {
      throw new Error("Razorpay checkout is unavailable in the current browser session.");
    }

    const checkout = new window.Razorpay({
      key: session.razorpay_key_id,
      order_id: session.razorpay_order_id,
      amount: session.amount,
      currency: session.currency,
      name: "InsureFlow",
      description: "Insurance premium payment",
      notes: {
        payment_reference: session.payment_reference,
        provider_payment_reference: session.provider_payment_reference ?? "",
      },
    });

    if (checkout) {
      checkout.open();
      return;
    }
  }

  if (session.payment_url) {
    window.open(session.payment_url, "_blank", "noopener,noreferrer");
    return;
  }

  throw new Error("No supported payment checkout payload was returned by the API.");
}
