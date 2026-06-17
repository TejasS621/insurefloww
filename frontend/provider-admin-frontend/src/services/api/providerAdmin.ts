import { providerApiRequest } from "./client";

export interface ProviderAdminAuthResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
}

export interface ProviderBrokerSummary {
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
  partner_provider_codes: string[];
  notes?: string | null;
  callback_url: string;
  webhook_url: string;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProviderBrokerCredentialResponse {
  broker_code: string;
  api_key: string;
  message: string;
}

export interface ProviderSyncStatusResponse {
  event_type: string;
  main_transaction_reference: string;
  status: string;
  retry_count: number;
  next_retry_at?: string | null;
  last_error?: string | null;
  updated_at: string;
}

export interface RetryProcessingResponse {
  processed_count: number;
  success_count: number;
  failed_count: number;
  records: ProviderSyncStatusResponse[];
}

export interface ProviderPolicyResponse {
  policy_number: string;
  provider_transaction_reference: string;
  main_transaction_reference: string;
  policy_status: string;
  coverage_amount: number;
  premium_amount: number;
  issue_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  policy_document_url?: string | null;
}

export const providerAdminApi = {
  login(email: string, password: string) {
    return providerApiRequest<ProviderAdminAuthResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    });
  },
  listBrokers() {
    return providerApiRequest<ProviderBrokerSummary[]>("/brokers");
  },
  registerBroker(payload: {
    broker_name: string;
    broker_code: string;
    company_name?: string;
    license_number?: string;
    registration_number?: string;
    contact_person_name?: string;
    contact_email?: string;
    contact_phone?: string;
    supported_insurance_types?: string[];
    active_regions?: string[];
    partner_provider_codes?: string[];
    callback_url?: string;
    webhook_url?: string;
    notes?: string;
    created_by_admin?: string;
  }) {
    return providerApiRequest<ProviderBrokerCredentialResponse>("/brokers/register", {
      method: "POST",
      body: payload,
    });
  },
  updateBrokerStatus(
    brokerCode: string,
    status: "ACTIVE" | "INACTIVE" | "SUSPENDED",
  ) {
    return providerApiRequest<ProviderBrokerSummary>(`/brokers/${brokerCode}/status`, {
      method: "PATCH",
      body: { status },
    });
  },
  rotateBrokerKey(
    brokerCode: string,
    reason = "Requested from provider admin UI.",
  ) {
    return providerApiRequest<ProviderBrokerCredentialResponse>(
      `/brokers/${brokerCode}/rotate-key`,
      {
        method: "PUT",
        body: { reason },
      },
    );
  },
  listSyncRetries() {
    return providerApiRequest<ProviderSyncStatusResponse[]>("/sync/retries");
  },
  processDueRetries(limit = 20) {
    return providerApiRequest<RetryProcessingResponse>("/sync/retries/process", {
      method: "POST",
      body: { limit },
    });
  },
  dispatchPolicySync(paymentReference: string) {
    return providerApiRequest<ProviderSyncStatusResponse>("/sync/dispatch", {
      method: "POST",
      body: { payment_reference: paymentReference },
    });
  },
  getPolicy(policyNumber: string) {
    return providerApiRequest<ProviderPolicyResponse>(`/policies/${policyNumber}`);
  },
  getPolicyDocument(policyNumber: string) {
    return providerApiRequest<Blob>(`/policies/${policyNumber}/document`);
  },
  downloadPolicyDocument(policyNumber: string) {
    return providerApiRequest<Blob>(`/policies/${policyNumber}/download`);
  },
};
