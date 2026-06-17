import {
  Bell,
  FileText,
  Home,
  LifeBuoy,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "./components/ui/Button";
import { CustomerChatbotWidget } from "./components/chat/CustomerChatbotWidget";
import { useAsyncAction } from "./hooks/useAsyncAction";
import { LayoutShell } from "./layouts/LayoutShell";
import { ApplicationFlowScreen } from "./pages/application/ApplicationFlowScreen";
import { CustomerLoginScreen } from "./pages/auth/CustomerLoginScreen";
import { CustomerDashboardScreen } from "./pages/dashboard/CustomerDashboardScreen";
import { LandingScreen } from "./pages/landing/LandingScreen";
import { PaymentInitiationScreen } from "./pages/payment/PaymentInitiationScreen";
import { QuoteComparisonScreen } from "./pages/quotes/QuoteComparisonScreen";
import { SupportTicketScreen } from "./pages/support/SupportTicketScreen";
import {
  CUSTOMER_PAYMENT_POLL_INTERVAL_MS,
  CUSTOMER_PAYMENT_POLL_LIMIT,
  POLICY_POLL_INTERVAL_MS,
  POLICY_POLL_TIMEOUT_MS,
} from "./services/api/config";
import {
  customerApi,
  type ApplicationQuote,
  type ApplicationSummary,
  type PaymentSession,
  type PolicySummary,
  type TicketSummary,
} from "./services/api/customer";
import { authStore } from "./store/authStore";
import { downloadBlob } from "./utils/download";
import { normalizeApiError } from "./utils/apiErrors";
import { openPaymentCheckout } from "./utils/payment";

type CustomerScreen = "landing" | "login" | "application" | "quotes" | "payment" | "dashboard" | "support";
type InsuranceType = "HEALTH" | "LIFE" | "VEHICLE" | "TRAVEL" | "HOME";
type CustomerLoginTarget = "application" | "dashboard" | "support";

interface PaymentBreakdown {
  insuranceType: InsuranceType;
  providerName: string;
  planName: string;
  basePremium: number;
  taxAmount: number;
  addonAmount: number;
  totalAmount: number;
  selectedAddons: Array<{
    addon_code: string;
    addon_name: string;
    addon_price: number;
  }>;
}

interface SectionState<T> {
  loading: boolean;
  error?: string;
  data: T;
}

interface AppHistoryState {
  customerScreen: CustomerScreen;
}

/**
 * App wires the customer UI flow to the API layer.
 * Session tokens stay in memory for the active browser run and all async paths expose loading and error states.
 */
export default function App() {
  const [customerScreen, setCustomerScreen] = useState<CustomerScreen>("landing");
  const [customerToken, setCustomerToken] = useState<string | null>(authStore.getState().customerToken);
  const [selectedInsuranceType, setSelectedInsuranceType] = useState<InsuranceType>("HEALTH");
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpError, setOtpError] = useState("");
  const [formError, setFormError] = useState("");
  const [customerMobileNumber, setCustomerMobileNumber] = useState("");
  const [customerOtpCode, setCustomerOtpCode] = useState("");
  const [customerLoginTarget, setCustomerLoginTarget] = useState<CustomerLoginTarget>("application");
  const [resumedApplication, setResumedApplication] = useState<ApplicationSummary | null>(null);
  const [latestApplicationPayload, setLatestApplicationPayload] = useState<Parameters<typeof customerApi.createApplication>[0] | null>(null);
  const [transactionReference, setTransactionReference] = useState<string | null>(null);
  const [quotes, setQuotes] = useState<ApplicationQuote[]>([]);
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [quotesError, setQuotesError] = useState("");
  const [paymentSession, setPaymentSession] = useState<PaymentSession | null>(null);
  const [paymentBreakdown, setPaymentBreakdown] = useState<PaymentBreakdown | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<"idle" | "initiating" | "verifying" | "failed" | "success">("idle");
  const [paymentError, setPaymentError] = useState("");
  const [applicationsState, setApplicationsState] = useState<SectionState<ApplicationSummary[]>>({
    loading: false,
    data: [],
  });
  const [policiesState, setPoliciesState] = useState<SectionState<PolicySummary[]>>({
    loading: false,
    data: [],
  });
  const [ticketsState, setTicketsState] = useState<SectionState<TicketSummary[]>>({
    loading: false,
    data: [],
  });
  const [ticketSubmitError, setTicketSubmitError] = useState("");

  // Phase 4 states
  const [otpAttemptsRemaining, setOtpAttemptsRemaining] = useState(3);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [paymentCountdown, setPaymentCountdown] = useState(30);
  const [tooManyRequestsMessage, setTooManyRequestsMessage] = useState<string | null>(null);

  const buildHistoryState = (
    overrides: Partial<AppHistoryState> = {},
  ): AppHistoryState => ({
    customerScreen,
    ...overrides,
  });

  const syncHistory = (
    nextState: AppHistoryState,
    options?: { replace?: boolean },
  ) => {
    if (typeof window === "undefined") {
      return;
    }
    if (options?.replace) {
      window.history.replaceState(nextState, "");
      return;
    }
    window.history.pushState(nextState, "");
  };

  const navigateCustomerScreen = (
    nextScreen: CustomerScreen,
    options?: { replace?: boolean },
  ) => {
    setCustomerScreen(nextScreen);
    syncHistory(buildHistoryState({ customerScreen: nextScreen }), options);
  };

  const checkRateLimit = (error: unknown) => {
    const apiError = normalizeApiError(error);
    if (apiError.status === 429) {
      setTooManyRequestsMessage(apiError.message);
      window.setTimeout(() => setTooManyRequestsMessage(null), 8000);
    }
  };

  const sendOtpAction = useAsyncAction();
  const verifyOtpAction = useAsyncAction();
  const submitApplicationAction = useAsyncAction();
  const selectQuoteAction = useAsyncAction();
  const paymentAction = useAsyncAction();
  const ticketAction = useAsyncAction();

  useEffect(() => {
    return authStore.subscribe((state) => {
      setCustomerToken(state.customerToken);
    });
  }, []);

  useEffect(() => {
    const initialState = window.history.state as AppHistoryState | null;
    if (!initialState || !initialState.customerScreen) {
      syncHistory(buildHistoryState(), { replace: true });
    }

    const handlePopState = (event: PopStateEvent) => {
      const state = event.state as AppHistoryState | null;
      if (!state) {
        return;
      }
      setCustomerScreen(state.customerScreen);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    if (!customerToken && (customerScreen === "dashboard" || customerScreen === "support")) {
      setCustomerLoginTarget(customerScreen === "support" ? "support" : "dashboard");
      navigateCustomerScreen("login", { replace: true });
    }
  }, [customerScreen, customerToken]);

  const resetCustomerAuthFlow = () => {
    setOtpRequested(false);
    setOtpError("");
    setCustomerOtpCode("");
    setOtpAttemptsRemaining(3);
  };

  const openCustomerLogin = (target: CustomerLoginTarget) => {
    resetCustomerAuthFlow();
    setCustomerLoginTarget(target);
    navigateCustomerScreen("login");
  };

  const customerNavItems = useMemo(
    () => [
      {
        label: "Home",
        icon: Home,
        active:
          customerScreen === "landing" ||
          customerScreen === "login" ||
          customerScreen === "application" ||
          customerScreen === "quotes" ||
          customerScreen === "payment",
        onClick: () => navigateCustomerScreen("landing"),
      },
      {
        label: "Policies",
        icon: FileText,
        active: customerScreen === "dashboard",
        onClick: () => {
          if (customerToken) {
            navigateCustomerScreen("dashboard");
            return;
          }
          openCustomerLogin("dashboard");
        },
      },
      {
        label: "Tickets",
        icon: LifeBuoy,
        active: customerScreen === "support",
        onClick: () => {
          if (customerToken) {
            navigateCustomerScreen("support");
            return;
          }
          openCustomerLogin("support");
        },
      },
      {
        label: "Profile",
        icon: UserRound,
        active: false,
        onClick: () => navigateCustomerScreen("dashboard"),
      },
    ],
    [customerScreen, customerToken],
  );



  const customerDisplayName = useMemo(() => {
    const source = applicationsState.data[0] ?? resumedApplication;
    if (!source) {
      return "Customer";
    }
    return [source.personal_details.first_name, source.personal_details.last_name]
      .filter(Boolean)
      .join(" ")
      .trim() || "Customer";
  }, [applicationsState.data, resumedApplication]);

  const customerInitials = useMemo(() => {
    return customerDisplayName
      .split(/\s+/)
      .filter(Boolean)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("")
      .slice(0, 2) || "CU";
  }, [customerDisplayName]);

  const loadDashboardData = async () => {
    setApplicationsState((current) => ({ ...current, loading: true, error: undefined }));
    setPoliciesState((current) => ({ ...current, loading: true, error: undefined }));
    setTicketsState((current) => ({ ...current, loading: true, error: undefined }));

    await Promise.all([
      customerApi.getMyApplications()
        .then((data) => setApplicationsState({ loading: false, data }))
        .catch((err) => {
          setApplicationsState({
            loading: false,
            data: [],
            error: normalizeApiError(err).message,
          });
          checkRateLimit(err);
        }),
      customerApi.getMyPolicies()
        .then((data) => setPoliciesState({ loading: false, data }))
        .catch((err) => {
          setPoliciesState({
            loading: false,
            data: [],
            error: normalizeApiError(err).message,
          });
          checkRateLimit(err);
        }),
      customerApi.getMyTickets()
        .then((data) => setTicketsState({ loading: false, data }))
        .catch((err) => {
          setTicketsState({
            loading: false,
            data: [],
            error: normalizeApiError(err).message,
          });
          checkRateLimit(err);
        }),
    ]);
  };

  useEffect(() => {
    if (customerScreen === "dashboard" && customerToken) {
      void loadDashboardData();
    }
  }, [customerScreen, customerToken]);

  useEffect(() => {
    if (customerScreen !== "dashboard" || !customerToken) {
      return undefined;
    }
    const startedAt = Date.now();
    const interval = window.setInterval(() => {
      const hasPendingPolicy = policiesState.data.some((policy) => policy.policy_status !== "ISSUED");
      if (!hasPendingPolicy || Date.now() - startedAt > POLICY_POLL_TIMEOUT_MS) {
        window.clearInterval(interval);
        return;
      }
      void loadDashboardData();
    }, POLICY_POLL_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [customerScreen, customerToken, policiesState.data]);

  const handleCustomerOtpRequest = async (mobileNumber: string) => {
    await sendOtpAction.run(async () => {
      try {
        await customerApi.requestOtp(mobileNumber);
        setOtpRequested(true);
        setOtpError("");
        setOtpAttemptsRemaining(3);
      } catch (error) {
        setOtpError(normalizeApiError(error).message);
        checkRateLimit(error);
      }
    });
  };

  const handleCustomerOtpVerify = async (mobileNumber: string, otpCode: string) => {
    await verifyOtpAction.run(async () => {
      try {
        const payload = await customerApi.verifyOtp(mobileNumber, otpCode);
        authStore.setToken("customer", payload.token.access_token);
        setOtpError("");
        setOtpAttemptsRemaining(3);
        navigateCustomerScreen(customerLoginTarget);
      } catch (error) {
        const remaining = Math.max(0, otpAttemptsRemaining - 1);
        setOtpAttemptsRemaining(remaining);
        setOtpError(`Incorrect code. ${remaining} attempts remaining.`);
        checkRateLimit(error);
        throw error;
      }
    });
  };

  const handleApplicationSubmit = async (
    payload: Parameters<typeof customerApi.createApplication>[0],
  ) => {
    await submitApplicationAction.run(async () => {
      setFormError("");
      setFieldErrors({});
      setQuotesLoading(true);
      setQuotesError("");
      setLatestApplicationPayload(payload);
      try {
        const application = await customerApi.createApplication(payload);
        if (!application.quotes.length) {
          setFormError(
            "Application was saved, but no quotes were returned yet. Please check that the quote service is running and try again.",
          );
          return;
        }
        setResumedApplication(application.quotes.length > 0 ? application : null);
        setPaymentSession(null);
        setPaymentBreakdown(null);
        setPaymentStatus("idle");
        setPaymentError("");
        setTransactionReference(application.transaction_reference);
        setQuotes(application.quotes);
        navigateCustomerScreen("quotes");
      } catch (error) {
        const apiError = normalizeApiError(error);
        if (apiError.status === 422) {
          setFieldErrors(apiError.fieldErrors);
          if (!Object.keys(apiError.fieldErrors).length) {
            setFormError(apiError.message);
          }
        } else {
          setFormError(apiError.message);
        }
        checkRateLimit(error);
      } finally {
        setQuotesLoading(false);
      }
    });
  };

  const handleQuoteProceed = async (quoteId: string, selectedAddons: string[]) => {
    await selectQuoteAction.run(async () => {
      const previousQuotes = quotes;
      setQuotes((current) =>
        current.map((quote) =>
          quote.quote_id === quoteId ? { ...quote, quote_status: "SELECTED" } : quote,
        ),
      );
      try {
        await customerApi.selectQuote(quoteId, selectedAddons);
        const selectedQuote = previousQuotes.find((quote) => quote.quote_id === quoteId);
        if (selectedQuote) {
          const selectedAddonObjects = selectedQuote.available_addons.filter((addon) =>
            selectedAddons.includes(addon.addon_code),
          );
          const addonAmount = selectedAddonObjects.reduce((total, addon) => total + addon.addon_price, 0);
          setPaymentSession(null);
          setPaymentBreakdown({
            insuranceType: selectedInsuranceType,
            providerName: selectedQuote.provider_name,
            planName: selectedQuote.plan_name,
            basePremium: selectedQuote.base_premium,
            taxAmount: selectedQuote.tax_amount,
            addonAmount,
            totalAmount: selectedQuote.total_premium + addonAmount,
            selectedAddons: selectedAddonObjects,
          });
        }
        setPaymentStatus("idle");
        setPaymentError("");
        navigateCustomerScreen("payment");
        setQuotesError("");
      } catch (error) {
        setQuotes(previousQuotes);
        setQuotesError(normalizeApiError(error).message);
        checkRateLimit(error);
      }
    });
  };

  const pollPaymentStatus = async (reference: string) => {
    for (let pollCount = 0; pollCount < CUSTOMER_PAYMENT_POLL_LIMIT; pollCount += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, CUSTOMER_PAYMENT_POLL_INTERVAL_MS));
      try {
        const status = await customerApi.getPaymentStatus(reference);
        if (status.payment_status === "SUCCESS" || status.transaction_status === "POLICY_ISSUED") {
          setPaymentStatus("success");
          if (customerToken) {
            navigateCustomerScreen("dashboard");
          }
          return;
        }
        if (status.payment_status === "FAILED") {
          setPaymentStatus("failed");
          setPaymentError("Payment failed. Please retry the payment flow.");
          return;
        }
      } catch (error) {
        checkRateLimit(error);
      }
    }
    setPaymentStatus("failed");
    setPaymentError("Payment verification timed out. Please retry.");
  };

  const startPaymentVerification = async (reference: string) => {
    setPaymentStatus("verifying");
    setPaymentError("");
    setPaymentCountdown(30);
    const timer = window.setInterval(() => {
      setPaymentCountdown((curr) => {
        if (curr <= 1) {
          window.clearInterval(timer);
          return 0;
        }
        return curr - 1;
      });
    }, 1000);

    try {
      await pollPaymentStatus(reference);
    } finally {
      window.clearInterval(timer);
    }
  };

  const handlePaymentInitiation = async () => {
    if (!transactionReference) {
      setPaymentError("A transaction reference is required before payment can start.");
      return;
    }

    await paymentAction.run(async () => {
      setPaymentStatus("initiating");
      setPaymentError("");
      try {
        const session = await customerApi.initiatePayment(transactionReference);
        setPaymentSession(session);
        setPaymentBreakdown((current) =>
          current
            ? {
                ...current,
                totalAmount: session.amount,
              }
            : current,
        );
        await openPaymentCheckout(
          session,
          async () => {
            await startPaymentVerification(transactionReference);
          },
          () => {
            void startPaymentVerification(transactionReference);
          }
        );
      } catch (error) {
        setPaymentStatus("failed");
        setPaymentError(normalizeApiError(error).message);
        checkRateLimit(error);
      }
    });
  };

  const handleDownloadPolicy = async (policyNumber: string) => {
    const blob = await customerApi.getPolicyDownload(policyNumber);
    downloadBlob(blob, `${policyNumber}.pdf`);
  };

  const handleViewReceipt = async (reference: string) => {
    const blob = await customerApi.getPaymentReceipt(reference);
    downloadBlob(blob, `${reference}-receipt.pdf`);
  };

  const handleSubmitTicket = async (payload: {
    category: string;
    priority: string;
    subject: string;
    message: string;
  }) => {
    await ticketAction.run(async () => {
      setTicketSubmitError("");
      try {
        await customerApi.createTicket(payload);
        await loadDashboardData();
      } catch (error) {
        setTicketSubmitError(normalizeApiError(error).message);
      }
    });
  };



  return (
    <LayoutShell
      navProps={{
        notificationCount: customerToken ? 2 : undefined,
        rightSlot: (
          <>
            {customerToken ? (
              <>
                <Button variant="ghost" iconOnly ariaLabel="Notifications">
                  <Bell size={18} />
                </Button>
                <button className="if-avatar-button" type="button" aria-label="Open user menu">
                  {customerInitials}
                </button>
              </>
            ) : (
              <Button
                onClick={() => openCustomerLogin("dashboard")}
              >
                Customer Login
              </Button>
            )}
          </>
        ),
      }}
      bottomNavProps={{
        items: customerNavItems,
      }}
    >
      {tooManyRequestsMessage && (
        <div
          className="if-warning-banner"
          style={{
            background: "rgba(245, 158, 11, 0.15)",
            border: "1px solid var(--if-warning)",
            borderRadius: "var(--radius-sm)",
            color: "var(--if-warning)",
            padding: "12px 16px",
            fontSize: "14px",
            fontWeight: 500,
            textAlign: "center",
            marginBottom: "20px",
          }}
        >
          Warning: {tooManyRequestsMessage}
        </div>
      )}

      {paymentStatus === "verifying" && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "var(--if-overlay-bg)",
            zIndex: 9999,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "24px",
          }}
        >
          <div className="if-spinner-violet" />
          <h2 style={{ color: "var(--if-text-inverse)", fontSize: "24px", fontWeight: 600, margin: 0 }}>
            Verifying payment...
          </h2>
          <div
            style={{
              fontFamily: "var(--fs-mono)",
              fontSize: "36px",
              color: "var(--if-cyan)",
              fontWeight: 700,
            }}
          >
            {paymentCountdown}s
          </div>
        </div>
      )}

      {customerScreen === "landing" ? (
        <LandingScreen
          onLogin={() => openCustomerLogin("dashboard")}
          onSelectType={(type) => {
            setSelectedInsuranceType(type.toUpperCase() as InsuranceType);
            navigateCustomerScreen("application");
          }}
        />
      ) : null}
      {customerScreen === "login" ? (
        <CustomerLoginScreen
          isSendingOtp={sendOtpAction.isLoading}
          isVerifyingOtp={verifyOtpAction.isLoading}
          mobileNumber={customerMobileNumber}
          onBack={() => navigateCustomerScreen("landing")}
          onMobileNumberChange={setCustomerMobileNumber}
          onOtpCodeChange={setCustomerOtpCode}
          onSendOtp={() => handleCustomerOtpRequest(customerMobileNumber)}
          onVerifyOtp={() => handleCustomerOtpVerify(customerMobileNumber, customerOtpCode)}
          otpCode={customerOtpCode}
          otpError={otpError}
          otpRequested={otpRequested}
        />
      ) : null}
      {customerScreen === "application" ? (
        <ApplicationFlowScreen
          formError={formError}
          fieldErrors={fieldErrors}
          insuranceType={selectedInsuranceType}
          initialMobileNumber={customerMobileNumber}
          isSubmitting={submitApplicationAction.isLoading}
          onBackToLanding={() => navigateCustomerScreen("landing")}
          onSubmit={handleApplicationSubmit}
          resumedApplication={resumedApplication}
        />
      ) : null}
      {customerScreen === "quotes" ? (
        <QuoteComparisonScreen
          error={quotesError}
          isProceeding={selectQuoteAction.isLoading}
          loading={quotesLoading}
          onBack={() => navigateCustomerScreen("application")}
          onProceed={handleQuoteProceed}
          onRetry={() => navigateCustomerScreen("application")}
          quotes={quotes}
          transactionReference={transactionReference}
        />
      ) : null}
      {customerScreen === "payment" ? (
        <PaymentInitiationScreen
          error={paymentError}
          isAuthenticated={Boolean(customerToken)}
          onBackHome={() => navigateCustomerScreen("landing")}
          onLoginToTrack={() => openCustomerLogin("dashboard")}
          onOpenDashboard={() => navigateCustomerScreen("dashboard")}
          onProceed={handlePaymentInitiation}
          onRetry={handlePaymentInitiation}
          paymentBreakdown={paymentBreakdown}
          paymentSession={paymentSession}
          paymentStatus={paymentStatus}
        />
      ) : null}
      {customerScreen === "dashboard" ? (
        <CustomerDashboardScreen
          applicationsState={{
            ...applicationsState,
            onRetry: () => void loadDashboardData(),
          }}
          customerDisplayName={customerDisplayName}
          onDownloadPolicy={handleDownloadPolicy}
          onOpenSupport={() => navigateCustomerScreen("support")}
          onViewReceipt={handleViewReceipt}
          policiesState={{
            ...policiesState,
            onRetry: () => void loadDashboardData(),
          }}
          ticketsState={{
            ...ticketsState,
            onRetry: () => void loadDashboardData(),
          }}
        />
      ) : null}
      {customerScreen === "support" ? (
        <SupportTicketScreen
          error={ticketsState.error}
          isSubmitting={ticketAction.isLoading}
          loading={ticketsState.loading}
          onRetry={() => void loadDashboardData()}
          onSubmit={async (p) => {
            try {
              await handleSubmitTicket(p);
            } catch (err) {
              checkRateLimit(err);
            }
          }}
          submitError={ticketSubmitError}
          tickets={ticketsState.data}
        />
      ) : null}
      <CustomerChatbotWidget
        applicationPayload={latestApplicationPayload}
        currentScreen={customerScreen}
        customerMobileNumber={customerMobileNumber}
        transactionReference={transactionReference}
      />
    </LayoutShell>
  );
}
