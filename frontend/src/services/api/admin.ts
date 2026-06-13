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
  callback_url: string;
  webhook_url: string;
  status: string;
  created_by_admin?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  api_key?: string | null;
}

export interface AdminPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
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
  createBroker(payload: {
    broker_name: string;
    broker_code: string;
    callback_url: string;
    webhook_url: string;
  }) {
    return apiRequest<BrokerSummary>("/admin/brokers", {
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
  rotateBrokerKey(brokerCode: string) {
    return apiRequest<BrokerSummary>(`/admin/brokers/${brokerCode}/rotate-key`, {
      admin: true,
      method: "PUT",
      body: { reason: "Requested from admin UI." },
    });
  },
  listTransactions(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<Record<string, string | number>>>(`/admin/transactions?${params.toString()}`, {
      admin: true,
    });
  },
  getTransactionDetail(reference: string) {
    return apiRequest<Record<string, string | number | null>>(`/admin/transactions/${reference}`, {
      admin: true,
    });
  },
  listPolicies(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<Record<string, string | number>>>(`/admin/policies?${params.toString()}`, {
      admin: true,
    });
  },
  listPayments(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<Record<string, string | number>>>(`/admin/payments?${params.toString()}`, {
      admin: true,
    });
  },
  listTickets(params: URLSearchParams) {
    return apiRequest<AdminPaginatedResponse<AdminTicketSummary>>(`/admin/tickets?${params.toString()}`, {
      admin: true,
    });
  },
  getTicketDetail(ticketId: string) {
    return apiRequest<AdminTicketSummary>(`/admin/tickets/${ticketId}`, {
      admin: true,
    });
  },
  assignTicket(ticketId: string, adminId: string) {
    return apiRequest<AdminTicketSummary>(`/admin/tickets/${ticketId}/assign`, {
      admin: true,
      method: "PUT",
      body: { admin_id: adminId },
    });
  },
  updateTicketStatus(ticketId: string, status: string, adminResponse: string) {
    return apiRequest<AdminTicketSummary>(`/admin/tickets/${ticketId}/status`, {
      admin: true,
      method: "PUT",
      body: { status, admin_response: adminResponse },
    });
  },
};
