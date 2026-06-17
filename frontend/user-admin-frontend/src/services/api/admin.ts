import { apiRequest } from "./client";

export interface AdminTokenPayload {
  user_id: string | null;
  token: {
    access_token: string;
    expires_in_seconds: number;
    user_role: string;
  };
}

export interface BrokerSummary {
  broker_code: string;
  broker_name: string;
  company_name?: string | null;
  license_number?: string | null;
  registration_number?: string | null;
  contact_person_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  supported_insurance_types: string[];
  active_regions: string[];
  partner_provider_codes?: string[];
  notes?: string | null;
  status: string;
  created_by_admin?: string | null;
  last_key_rotated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  api_key?: string | null;
}

export interface ProviderSummary {
  provider_code: string;
  provider_name: string;
  company_name?: string | null;
  contact_email: string;
  contact_phone: string;
  supported_insurance_types: string[];
  supported_regions: string[];
  serviceable_products: string[];
  notes?: string | null;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AdminPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

function normalizePaginatedResponse<T>(
  payload: AdminPaginatedResponse<T> | T[],
  fallbackPage = 1,
  fallbackLimit = 10,
): AdminPaginatedResponse<T> {
  if (Array.isArray(payload)) {
    return {
      items: payload,
      total: payload.length,
      page: fallbackPage,
      limit: fallbackLimit,
    };
  }

  return {
    items: Array.isArray(payload.items) ? payload.items : [],
    total: typeof payload.total === "number" ? payload.total : 0,
    page: typeof payload.page === "number" ? payload.page : fallbackPage,
    limit: typeof payload.limit === "number" ? payload.limit : fallbackLimit,
  };
}

export interface AdminDashboardStats {
  total_applications: number;
  total_tickets: number;
  total_policies: number;
  total_brokers: number;
  total_audit_logs: number;
  pending_underwriting_reviews: number;
  application_status_breakdown: Array<{ status: string; count: number }>;
  ticket_status_breakdown: Array<{ status: string; count: number }>;
  policy_status_breakdown: Array<{ status: string; count: number }>;
  broker_status_breakdown: Array<{ status: string; count: number }>;
}

export interface AdminTicketSummary {
  ticket_reference: string;
  user_id: string;
  transaction_reference?: string | null;
  category: string;
  priority: string;
  status: string;
  subject: string;
  message: string;
  assigned_admin_id?: string | null;
  admin_response?: string | null;
  created_at: string;
  updated_at: string;
}

export const adminApi = {
  login(email: string, password: string) {
    return apiRequest<AdminTokenPayload>("/auth/admin/login", {
      method: "POST",
      body: { email, password },
    });
  },
  verifyLogin(email: string, otpCode: string) {
    return apiRequest<AdminTokenPayload>("/auth/admin/login/verify", {
      method: "POST",
      body: { email, otp_code: otpCode },
    });
  },
  getDashboard() {
    return apiRequest<AdminDashboardStats>("/admin/dashboard", {
      admin: true,
    });
  },
  listBrokers() {
    return apiRequest<BrokerSummary[]>("/admin/brokers", {
      admin: true,
    });
  },
  listProviders() {
    return apiRequest<ProviderSummary[]>("/admin/providers", {
      admin: true,
    });
  },
  createBroker(payload: {
    broker_name: string;
    broker_code: string;
    company_name?: string;
    license_number?: string;
    registration_number?: string;
    contact_person_name?: string;
    contact_email?: string;
    contact_phone?: string;
    supported_insurance_types: string[];
    active_regions: string[];
    partner_provider_codes: string[];
    notes?: string;
  }) {
    return apiRequest<BrokerSummary>("/admin/brokers", {
      admin: true,
      method: "POST",
      body: payload,
    });
  },
  createProvider(payload: {
    provider_name: string;
    provider_code: string;
    company_name?: string;
    contact_email: string;
    contact_phone: string;
    supported_insurance_types: string[];
    supported_regions: string[];
    serviceable_products: string[];
    notes?: string;
  }) {
    return apiRequest<ProviderSummary>("/admin/providers", {
      admin: true,
      method: "POST",
      body: payload,
    });
  },
  updateBrokerStatus(brokerCode: string, status: "ACTIVE" | "INACTIVE") {
    return apiRequest<BrokerSummary>(`/admin/brokers/${brokerCode}/status`, {
      admin: true,
      method: "PATCH",
      body: { status },
    });
  },
  updateProviderStatus(providerCode: string, status: "ACTIVE" | "INACTIVE") {
    return apiRequest<ProviderSummary>(`/admin/providers/${providerCode}/status`, {
      admin: true,
      method: "PATCH",
      body: { status },
    });
  },
  rotateBrokerKey(brokerCode: string) {
    return apiRequest<BrokerSummary>(`/admin/brokers/${brokerCode}/rotate-key`, {
      admin: true,
      method: "PUT",
      body: { reason: "Requested from admin UI." },
    });
  },
  listTransactions(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<Record<string, string | number>> | Array<Record<string, string | number>>>(
      `/admin/transactions?${params.toString()}`,
      {
        admin: true,
      },
    ).then((payload) => normalizePaginatedResponse(payload));
  },
  getTransactionDetail(reference: string) {
    return apiRequest<Record<string, string | number | null>>(`/admin/transactions/${reference}`, {
      admin: true,
    });
  },
  listPolicies(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<Record<string, string | number>> | Array<Record<string, string | number>>>(
      `/admin/policies?${params.toString()}`,
      {
        admin: true,
      },
    ).then((payload) => normalizePaginatedResponse(payload));
  },
  listPayments(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<Record<string, string | number>> | Array<Record<string, string | number>>>(
      `/admin/payments?${params.toString()}`,
      {
        admin: true,
      },
    ).then((payload) => normalizePaginatedResponse(payload));
  },
  listTickets(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<AdminTicketSummary> | AdminTicketSummary[]>(
      `/admin/tickets?${params.toString()}`,
      {
        admin: true,
      },
    ).then((payload) => normalizePaginatedResponse(payload));
  },
  getTicketDetail(ticketId: string) {
    return apiRequest<AdminTicketSummary>(`/admin/tickets/${ticketId}`, {
      admin: true,
    });
  },
  assignTicket(ticketId: string, adminId: string) {
    return apiRequest<AdminTicketSummary>(`/admin/tickets/${ticketId}/assignment`, {
      admin: true,
      method: "PATCH",
      body: { assigned_admin_id: adminId },
    });
  },
  updateTicketStatus(ticketId: string, status: string, adminResponse: string) {
    return apiRequest<AdminTicketSummary>(`/admin/tickets/${ticketId}/status`, {
      admin: true,
      method: "PATCH",
      body: { status, admin_response: adminResponse },
    });
  },
};
