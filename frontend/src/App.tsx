import {
  Bell,
  Blocks,
  ClipboardList,
  CreditCard,
  FileStack,
  FileText,
  Home,
  LayoutDashboard,
  LifeBuoy,
  ListOrdered,
  Shield,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "./components/ui/Button";
import { StatusBadge } from "./components/ui/StatusBadge";
import { useAsyncAction } from "./hooks/useAsyncAction";
import { LayoutShell } from "./layouts/LayoutShell";
import { AdminDashboardScreen } from "./pages/admin/AdminDashboardScreen";
import { AdminLoginScreen } from "./pages/admin/AdminLoginScreen";
import { AdminRecordsScreen } from "./pages/admin/AdminRecordsScreen";
import { AdminTicketsScreen } from "./pages/admin/AdminTicketsScreen";
import { BrokerManagementScreen } from "./pages/admin/BrokerManagementScreen";
import { ApplicationFlowScreen } from "./pages/application/ApplicationFlowScreen";
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

type PortalMode = "customer" | "admin";
type CustomerScreen = "landing" | "application" | "quotes" | "payment" | "dashboard" | "support";
type AdminScreen = "dashboard" | "brokers" | "transactions" | "policies" | "payments" | "tickets";
type InsuranceType = "HEALTH" | "LIFE" | "VEHICLE" | "TRAVEL" | "HOME";

interface SectionState<T> {
  loading: boolean;
  error?: string;
  data: T;
}

/**
 * App wires the customer and admin UI flows to the API layer.
 * Session tokens stay in memory for the active browser run and all async paths expose loading and error states.
 */
export default function App() {
  const [portalMode, setPortalMode] = useState<PortalMode>("customer");
  const [customerScreen, setCustomerScreen] = useState<CustomerScreen>("landing");
  const [adminScreen, setAdminScreen] = useState<AdminScreen>("dashboard");
  const [customerToken, setCustomerToken] = useState<string | null>(authStore.getState().customerToken);
  const [adminToken, setAdminToken] = useState<string | null>(authStore.getState().adminToken);
  const [selectedInsuranceType, setSelectedInsuranceType] = useState<InsuranceType>("HEALTH");
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpError, setOtpError] = useState("");
  const [formError, setFormError] = useState("");
  const [resumedApplication, setResumedApplication] = useState<ApplicationSummary | null>(null);
  const [transactionReference, setTransactionReference] = useState<string | null>(null);
  const [quotes, setQuotes] = useState<ApplicationQuote[]>([]);
  const [quotesLoading, setQuotesLoading] = useState(false);
  const [quotesError, setQuotesError] = useState("");
  const [paymentSession, setPaymentSession] = useState<PaymentSession | null>(null);
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

  const sendOtpAction = useAsyncAction();
  const verifyOtpAction = useAsyncAction();
  const submitApplicationAction = useAsyncAction();
  const selectQuoteAction = useAsyncAction();
  const paymentAction = useAsyncAction();
  const ticketAction = useAsyncAction();

  useEffect(() => {
    return authStore.subscribe((state) => {
      setCustomerToken(state.customerToken);
      setAdminToken(state.adminToken);
    });
  }, []);

  useEffect(() => {
    if (!customerToken && (customerScreen === "dashboard" || customerScreen === "support")) {
      setCustomerScreen("landing");
    }
  }, [customerScreen, customerToken]);

  const customerNavItems = useMemo(
    () => [
      {
        label: "Home",
        icon: Home,
        active: customerScreen === "landing" || customerScreen === "application" || customerScreen === "quotes" || customerScreen === "payment",
        onClick: () => setCustomerScreen("landing"),
      },
      {
        label: "Policies",
        icon: FileText,
        active: customerScreen === "dashboard",
        onClick: () => setCustomerScreen("dashboard"),
      },
      {
        label: "Tickets",
        icon: LifeBuoy,
        active: customerScreen === "support",
        onClick: () => setCustomerScreen("support"),
      },
      {
        label: "Profile",
        icon: UserRound,
        active: false,
        onClick: () => setCustomerScreen("dashboard"),
      },
    ],
    [customerScreen],
  );

  const adminNavItems = useMemo(
    () => [
      { label: "Dashboard", icon: LayoutDashboard, active: adminScreen === "dashboard", onClick: () => setAdminScreen("dashboard") },
      { label: "Brokers", icon: Blocks, active: adminScreen === "brokers", onClick: () => setAdminScreen("brokers") },
      { label: "Transactions", icon: ListOrdered, active: adminScreen === "transactions", onClick: () => setAdminScreen("transactions") },
      { label: "Policies", icon: FileStack, active: adminScreen === "policies", onClick: () => setAdminScreen("policies") },
      { label: "Payments", icon: CreditCard, active: adminScreen === "payments", onClick: () => setAdminScreen("payments") },
      { label: "Tickets", icon: ClipboardList, active: adminScreen === "tickets", onClick: () => setAdminScreen("tickets") },
    ],
    [adminScreen],
  );

  const loadDashboardData = async () => {
    setApplicationsState((current) => ({ ...current, loading: true, error: undefined }));
    setPoliciesState((current) => ({ ...current, loading: true, error: undefined }));
    setTicketsState((current) => ({ ...current, loading: true, error: undefined }));

    const [applicationsResult, policiesResult, ticketsResult] = await Promise.allSettled([
      customerApi.getMyApplications(),
      customerApi.getMyPolicies(),
      customerApi.getMyTickets(),
    ]);

    setApplicationsState({
      loading: false,
      data: applicationsResult.status === "fulfilled" ? applicationsResult.value : [],
      error:
        applicationsResult.status === "rejected"
          ? normalizeApiError(applicationsResult.reason).message
          : undefined,
    });
    setPoliciesState({
      loading: false,
      data: policiesResult.status === "fulfilled" ? policiesResult.value : [],
      error:
        policiesResult.status === "rejected"
          ? normalizeApiError(policiesResult.reason).message
          : undefined,
    });
    setTicketsState({
      loading: false,
      data: ticketsResult.status === "fulfilled" ? ticketsResult.value : [],
      error:
        ticketsResult.status === "rejected"
          ? normalizeApiError(ticketsResult.reason).message
          : undefined,
    });
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
      } catch (error) {
        setOtpError(normalizeApiError(error).message);
      }
    });
  };

  const handleCustomerOtpVerify = async (mobileNumber: string, otpCode: string) => {
    await verifyOtpAction.run(async () => {
      try {
        const payload = await customerApi.verifyOtp(mobileNumber, otpCode);
        authStore.setToken("customer", payload.token.access_token);
        setOtpError("");
      } catch (error) {
        setOtpError("Incorrect code. Please try again.");
        throw error;
      }
    });
  };

  const handleApplicationSubmit = async (
    payload: Parameters<typeof customerApi.createApplication>[0],
  ) => {
    await submitApplicationAction.run(async () => {
      setFormError("");
      setQuotesLoading(true);
      setQuotesError("");
      try {
        const application = await customerApi.createApplication(payload);
        setResumedApplication(application.quotes.length > 0 ? application : null);
        setTransactionReference(application.transaction_reference);
        setQuotes(application.quotes);
        setCustomerScreen("quotes");
      } catch (error) {
        setFormError(normalizeApiError(error).message);
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
        setCustomerScreen("payment");
        setQuotesError("");
      } catch (error) {
        setQuotes(previousQuotes);
        setQuotesError(normalizeApiError(error).message);
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
          setCustomerScreen("dashboard");
          return;
        }
        if (status.payment_status === "FAILED") {
          setPaymentStatus("failed");
          setPaymentError("Payment failed. Please retry the payment flow.");
          return;
        }
      } catch (error) {
        setPaymentError(normalizeApiError(error).message);
      }
    }
    setPaymentStatus("failed");
    setPaymentError("Payment verification timed out. Please retry.");
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
        await openPaymentCheckout(session);
        setPaymentStatus("verifying");
        await pollPaymentStatus(transactionReference);
      } catch (error) {
        setPaymentStatus("failed");
        setPaymentError(normalizeApiError(error).message);
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

  if (portalMode === "admin" && !adminToken) {
    return (
      <div>
        <div className="if-portal-switch">
          <Button onClick={() => setPortalMode("customer")} variant="ghost">
            Customer Portal
          </Button>
          <Button>Admin Portal</Button>
        </div>
        <AdminLoginScreen />
      </div>
    );
  }

  if (portalMode === "admin") {
    return (
      <LayoutShell
        navProps={{
          notificationCount: 4,
          rightSlot: (
            <>
              <StatusBadge status="admin">Admin</StatusBadge>
              <Button variant="ghost" iconOnly ariaLabel="Notifications">
                <Bell size={18} />
              </Button>
              <button className="if-avatar-button" type="button" aria-label="Open admin menu">
                AD
              </button>
              <Button onClick={() => setPortalMode("customer")} variant="ghost">
                Customer
              </Button>
            </>
          ),
        }}
        sidebarProps={{
          title: "Admin Console",
          items: adminNavItems,
        }}
      >
        {adminScreen === "dashboard" ? <AdminDashboardScreen /> : null}
        {adminScreen === "brokers" ? <BrokerManagementScreen /> : null}
        {adminScreen === "transactions" ? <AdminRecordsScreen view="transactions" /> : null}
        {adminScreen === "policies" ? <AdminRecordsScreen view="policies" /> : null}
        {adminScreen === "payments" ? <AdminRecordsScreen view="payments" /> : null}
        {adminScreen === "tickets" ? <AdminTicketsScreen /> : null}
      </LayoutShell>
    );
  }

  return (
    <LayoutShell
      navProps={{
        notificationCount: customerToken ? 2 : undefined,
        rightSlot: (
          <>
            <Button onClick={() => setPortalMode("admin")} variant="ghost">
              Admin
            </Button>
            {customerToken ? (
              <>
                <Button variant="ghost" iconOnly ariaLabel="Notifications">
                  <Bell size={18} />
                </Button>
                <button className="if-avatar-button" type="button" aria-label="Open user menu">
                  CU
                </button>
              </>
            ) : null}
          </>
        ),
      }}
      bottomNavProps={{
        items: customerNavItems,
      }}
    >
      {customerScreen === "landing" ? (
        <LandingScreen
          onSelectType={(type) => {
            setSelectedInsuranceType(type.toUpperCase() as InsuranceType);
            setCustomerScreen("application");
          }}
        />
      ) : null}
      {customerScreen === "application" ? (
        <ApplicationFlowScreen
          formError={formError}
          insuranceType={selectedInsuranceType}
          isAuthenticated={Boolean(customerToken)}
          isSendingOtp={sendOtpAction.isLoading}
          isSubmitting={submitApplicationAction.isLoading}
          isVerifyingOtp={verifyOtpAction.isLoading}
          onBackToLanding={() => setCustomerScreen("landing")}
          onSendOtp={handleCustomerOtpRequest}
          onSubmit={handleApplicationSubmit}
          onVerifyOtp={handleCustomerOtpVerify}
          otpError={otpError}
          otpRequested={otpRequested}
          resumedApplication={resumedApplication}
        />
      ) : null}
      {customerScreen === "quotes" ? (
        <QuoteComparisonScreen
          error={quotesError}
          isProceeding={selectQuoteAction.isLoading}
          loading={quotesLoading}
          onBack={() => setCustomerScreen("application")}
          onProceed={handleQuoteProceed}
          onRetry={() => setCustomerScreen("application")}
          quotes={quotes}
          transactionReference={transactionReference}
        />
      ) : null}
      {customerScreen === "payment" ? (
        <PaymentInitiationScreen
          error={paymentError}
          onProceed={handlePaymentInitiation}
          onRetry={handlePaymentInitiation}
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
          onDownloadPolicy={handleDownloadPolicy}
          onOpenSupport={() => setCustomerScreen("support")}
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
          onSubmit={handleSubmitTicket}
          submitError={ticketSubmitError}
          tickets={ticketsState.data}
        />
      ) : null}
    </LayoutShell>
  );
}
