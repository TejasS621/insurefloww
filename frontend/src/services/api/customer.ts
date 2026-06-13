import { apiRequest } from "./client";

export interface AuthTokenPayload {
  user_id: string | null;
  token: {
    access_token: string;
    expires_in_seconds: number;
    user_role: string;
  };
}

export interface ApplicationQuote {
  quote_id: string;
  provider_name: string;
  plan_code: string;
  plan_name: string;
  base_premium: number;
  tax_amount: number;
  total_premium: number;
  coverage_amount: number;
  available_addons: Array<{
    addon_code: string;
    addon_name: string;
    addon_price: number;
  }>;
  quote_status: string;
  expires_at: string | null;
}

export interface ApplicationSummary {
  application_reference: string;
  transaction_reference: string | null;
  insurance_type: string;
  personal_details: {
    first_name: string;
    last_name: string;
    email: string;
    mobile_number: string;
    date_of_birth: string;
    gender: string;
    address_line_1: string;
    address_line_2?: string | null;
    city: string;
    state: string;
    pincode: string;
  };
  health_details?: {
    height_cm?: number | null;
    weight_kg?: number | null;
    calculated_bmi?: number | null;
    smoker: boolean;
    diabetes: boolean;
    blood_pressure: boolean;
    heart_ailments: boolean;
    pre_existing_disease: boolean;
    other_conditions: string[];
  } | null;
  coverage_details: {
    insurance_type: string;
    coverage_amount: number;
    sum_insured?: number | null;
    tenure_years?: number | null;
    relation?: string | null;
    insured_members?: number | null;
    pan_india_cover: boolean;
  };
  application_status: string;
  quotes: ApplicationQuote[];
  created_at: string;
  updated_at: string;
}

export interface PaymentSession {
  payment_reference: string;
  payment_url?: string | null;
  gateway?: string | null;
  razorpay_key_id?: string | null;
  razorpay_order_id?: string | null;
  provider_payment_reference?: string | null;
  amount: number;
  currency: string;
  available_payment_methods: string[];
  status: string;
}

export interface PolicySummary {
  policy_number: string;
  transaction_reference?: string | null;
  payment_reference?: string | null;
  policy_status: string;
  coverage_amount: number;
  premium_amount: number;
  issue_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  document_url?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TicketSummary {
  ticket_reference: string;
  transaction_reference?: string | null;
  category: string;
  priority: string;
  status: string;
  subject: string;
  message: string;
  admin_response?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentStatusResponse {
  payment_status: string;
  transaction_status?: string;
  provider_payment_reference?: string | null;
}

export interface CustomerApplicationPayload {
  insuranceType: "HEALTH" | "LIFE" | "VEHICLE" | "TRAVEL" | "HOME";
  fullName: string;
  mobileNumber: string;
  email: string;
  dateOfBirth: string;
  gender: "MALE" | "FEMALE" | "OTHER";
  coverageAmount: number;
  tenureYears: number;
  guestIdentifier?: string;
  healthConditions: string[];
  smoker?: boolean;
  insuredMembers?: string[];
  heightCm?: number | null;
  weightKg?: number | null;
}

function splitName(fullName: string) {
  const parts = fullName.trim().split(/\s+/);
  return {
    firstName: parts[0] ?? "Customer",
    lastName: parts.slice(1).join(" ") || "User",
  };
}

function normalizeDateOfBirth(dateOfBirth: string) {
  const trimmed = dateOfBirth.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return trimmed;
  }

  const slashMatch = trimmed.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (slashMatch) {
    const [, day, month, year] = slashMatch;
    return `${year}-${month}-${day}`;
  }

  return trimmed;
}

export const customerApi = {
  requestOtp(mobileNumber: string) {
    return apiRequest<{ mobile_number: string; expires_in_seconds: number }>("/auth/login/otp", {
      method: "POST",
      body: { mobile_number: mobileNumber },
    });
  },
  verifyOtp(mobileNumber: string, otpCode: string) {
    return apiRequest<AuthTokenPayload>("/auth/login/verify", {
      method: "POST",
      body: { mobile_number: mobileNumber, otp_code: otpCode },
    });
  },
  createApplication(payload: CustomerApplicationPayload) {
    const { firstName, lastName } = splitName(payload.fullName);
    const normalizedDateOfBirth = normalizeDateOfBirth(payload.dateOfBirth);
    const calculatedBmi =
      payload.insuranceType === "HEALTH" &&
      payload.heightCm &&
      payload.heightCm > 0 &&
      payload.weightKg &&
      payload.weightKg > 0
        ? Number((payload.weightKg / ((payload.heightCm / 100) ** 2)).toFixed(2))
        : null;

    return apiRequest<ApplicationSummary>("/applications", {
      method: "POST",
      body: {
        insurance_type: payload.insuranceType,
        guest_identifier: payload.guestIdentifier ?? `guest-${payload.mobileNumber}`,
        personal_details: {
          first_name: firstName,
          last_name: lastName,
          email: payload.email || `guest.${payload.mobileNumber}@insurefloww.com`,
          mobile_number: payload.mobileNumber,
          date_of_birth: normalizedDateOfBirth,
          gender: payload.gender,
          address_line_1: "Customer address line 1",
          city: "Mumbai",
          state: "Maharashtra",
          pincode: "400001",
        },
        health_details:
          payload.insuranceType === "HEALTH"
            ? {
                height_cm: payload.heightCm ?? null,
                weight_kg: payload.weightKg ?? null,
                calculated_bmi: calculatedBmi,
                smoker: payload.smoker ?? false,
                diabetes: payload.healthConditions.includes("Diabetes"),
                blood_pressure: payload.healthConditions.includes("Hypertension"),
                heart_ailments: payload.healthConditions.includes("Cardiac History"),
                pre_existing_disease: payload.healthConditions.length > 0,
                other_conditions: payload.healthConditions,
              }
            : null,
        coverage_details: {
          insurance_type: payload.insuranceType,
          coverage_amount: payload.coverageAmount,
          tenure_years: payload.tenureYears,
          relation:
            payload.insuranceType === "HEALTH" && (payload.insuredMembers?.length ?? 0) > 1
              ? "FAMILY"
              : "SELF",
          insured_members:
            payload.insuranceType === "HEALTH"
              ? Math.max(payload.insuredMembers?.length ?? 1, 1)
              : 1,
          sum_insured: payload.coverageAmount,
          pan_india_cover: true,
        },
        idempotency_key: crypto.randomUUID(),
      },
    });
  },
  selectQuote(quoteId: string, selectedAddons: string[]) {
    return apiRequest<ApplicationQuote>(`/quotes/select/${quoteId}`, {
      method: "POST",
      body: {
        selected_addons: selectedAddons,
        idempotency_key: crypto.randomUUID(),
      },
    });
  },
  initiatePayment(transactionReference: string, selectedPaymentMethod?: string) {
    return apiRequest<PaymentSession>(`/payments/initiate/${transactionReference}`, {
      method: "POST",
      body: {
        selected_payment_method: selectedPaymentMethod ?? null,
      },
    });
  },
  getPaymentStatus(transactionReference: string) {
    return apiRequest<PaymentStatusResponse>(`/payments/status/${transactionReference}`);
  },
  getMyApplications() {
    return apiRequest<ApplicationSummary[]>("/applications/me");
  },
  getMyPolicies() {
    return apiRequest<PolicySummary[]>("/policies/me");
  },
  getPolicyDownload(policyNumber: string) {
    return apiRequest<Blob>(`/policies/${policyNumber}/download`);
  },
  getPaymentReceipt(reference: string) {
    return apiRequest<Blob>(`/payments/receipt/${reference}`);
  },
  createTicket(payload: {
    category: string;
    priority: string;
    subject: string;
    message: string;
    transactionReference?: string;
  }) {
    return apiRequest<TicketSummary>("/tickets", {
      method: "POST",
      body: {
        transaction_reference: payload.transactionReference ?? null,
        category: payload.category,
        priority: payload.priority,
        subject: payload.subject,
        message: payload.message,
      },
    });
  },
  getMyTickets() {
    return apiRequest<TicketSummary[]>("/tickets/me");
  },
};
