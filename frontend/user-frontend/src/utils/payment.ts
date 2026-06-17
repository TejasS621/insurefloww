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
export async function openPaymentCheckout(
  session: PaymentSession,
  onSuccess: (response: any) => void,
  onDismiss: () => void,
) {
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
      handler: function (response: any) {
        onSuccess(response);
      },
      modal: {
        ondismiss: function () {
          onDismiss();
        },
      },
    });

    if (checkout) {
      checkout.open();
      return;
    }
  }

  if (session.payment_url) {
    const popup = window.open(
      session.payment_url,
      "insureflow_payment_checkout",
      "width=520,height=780,scrollbars=yes,resizable=yes"
    );
    if (!popup) {
      throw new Error("The payment window was blocked by the browser.");
    }
    popup.focus();

    const expectedOrigin = new URL(session.payment_url, window.location.href).origin;
    let completed = false;
    const openedAt = Date.now();

    const cleanup = () => {
      window.removeEventListener("message", handleMessage);
      window.clearInterval(closeWatcher);
    };

    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== expectedOrigin) {
        return;
      }
      if (event.data?.type !== "INSUREFLOW_PAYMENT_SUCCESS") {
        return;
      }

      completed = true;
      cleanup();
      onSuccess(event.data);
    };

    window.addEventListener("message", handleMessage);

    const closeWatcher = window.setInterval(() => {
      if (Date.now() - openedAt < 1500) {
        return;
      }
      if (!popup.closed) {
        return;
      }
      cleanup();
      if (!completed) {
        onDismiss();
      }
    }, 500);

    return;
  }

  throw new Error("No supported payment checkout payload was returned by the API.");
}
