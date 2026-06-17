import { mainApiRequest } from "./client";

export interface ProviderRegistrySummary {
  provider_code: string;
  provider_name: string;
  company_name?: string | null;
  contact_email: string;
  contact_phone: string;
  supported_insurance_types: string[];
  supported_regions: string[];
  serviceable_products: string[];
  notes?: string | null;
  status: "ACTIVE" | "INACTIVE" | "SUSPENDED";
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CreateProviderPayload {
  provider_name: string;
  provider_code: string;
  company_name?: string;
  contact_email: string;
  contact_phone: string;
  supported_insurance_types?: string[];
  supported_regions?: string[];
  serviceable_products?: string[];
  notes?: string;
}

export interface UpdateProviderPayload {
  provider_name: string;
  company_name?: string;
  contact_email: string;
  contact_phone: string;
  supported_insurance_types?: string[];
  supported_regions?: string[];
  serviceable_products?: string[];
  notes?: string;
}

export const providerRegistryApi = {
  listProviders() {
    return mainApiRequest<ProviderRegistrySummary[]>("/admin/providers");
  },
  createProvider(payload: CreateProviderPayload) {
    return mainApiRequest<ProviderRegistrySummary>("/admin/providers", {
      method: "POST",
      body: payload,
    });
  },
  updateProviderStatus(
    providerCode: string,
    status: ProviderRegistrySummary["status"],
    reason?: string,
  ) {
    return mainApiRequest<ProviderRegistrySummary>(`/admin/providers/${providerCode}/status`, {
      method: "PATCH",
      body: { status, reason },
    });
  },
  updateProvider(providerCode: string, payload: UpdateProviderPayload) {
    return mainApiRequest<ProviderRegistrySummary>(`/admin/providers/${providerCode}`, {
      method: "PUT",
      body: payload,
    });
  },
};
