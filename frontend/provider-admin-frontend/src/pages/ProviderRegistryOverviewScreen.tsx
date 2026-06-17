import { useEffect, useMemo, useState } from "react";

import { Button } from "../components/ui/Button";
import { Drawer } from "../components/ui/Drawer";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorCard } from "../components/ui/ErrorCard";
import { Modal } from "../components/ui/Modal";
import { SelectField } from "../components/ui/SelectField";
import { Skeleton } from "../components/ui/Skeleton";
import { StatCard } from "../components/ui/StatCard";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TextareaField } from "../components/ui/TextareaField";
import { TextInput } from "../components/ui/TextInput";
import {
  providerRegistryApi,
  type ProviderRegistrySummary,
} from "../services/api/providerRegistry";
import type { FieldErrorMap } from "../services/api/types";
import { normalizeApiError } from "../utils/apiErrors";

type ProviderModalState = "closed" | "register" | "toggleStatus";
type ProviderStatusFilter = "ALL" | "ACTIVE" | "INACTIVE" | "SUSPENDED";

const INSURANCE_TYPE_OPTIONS = ["HEALTH", "LIFE", "VEHICLE", "TRAVEL", "HOME"] as const;

interface ProviderFormState {
  providerName: string;
  providerCode: string;
  companyName: string;
  contactEmail: string;
  contactPhone: string;
  supportedInsuranceTypes: string[];
  supportedRegions: string;
  serviceableProducts: string;
  notes: string;
}

interface ProviderEditState {
  providerName: string;
  companyName: string;
  contactEmail: string;
  contactPhone: string;
  supportedInsuranceTypes: string[];
  supportedRegions: string;
  serviceableProducts: string;
  notes: string;
}

const EMPTY_PROVIDER_FORM: ProviderFormState = {
  providerName: "",
  providerCode: "",
  companyName: "",
  contactEmail: "",
  contactPhone: "",
  supportedInsuranceTypes: [],
  supportedRegions: "",
  serviceableProducts: "",
  notes: "",
};

const EMPTY_PROVIDER_EDIT: ProviderEditState = {
  providerName: "",
  companyName: "",
  contactEmail: "",
  contactPhone: "",
  supportedInsuranceTypes: [],
  supportedRegions: "",
  serviceableProducts: "",
  notes: "",
};

function toCsv(values: string[]): string {
  return values.join(", ");
}

function parseCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toProviderEditState(provider: ProviderRegistrySummary): ProviderEditState {
  return {
    providerName: provider.provider_name,
    companyName: provider.company_name ?? "",
    contactEmail: provider.contact_email,
    contactPhone: provider.contact_phone,
    supportedInsuranceTypes: provider.supported_insurance_types,
    supportedRegions: toCsv(provider.supported_regions),
    serviceableProducts: toCsv(provider.serviceable_products),
    notes: provider.notes ?? "",
  };
}

function mapProviderFieldErrors(fieldErrors: FieldErrorMap): FieldErrorMap {
  return {
    providerName: fieldErrors.provider_name ?? fieldErrors.providerName ?? "",
    providerCode: fieldErrors.provider_code ?? fieldErrors.providerCode ?? "",
    companyName: fieldErrors.company_name ?? fieldErrors.companyName ?? "",
    contactEmail: fieldErrors.contact_email ?? fieldErrors.contactEmail ?? "",
    contactPhone: fieldErrors.contact_phone ?? fieldErrors.contactPhone ?? "",
    supportedInsuranceTypes:
      fieldErrors.supported_insurance_types ?? fieldErrors.supportedInsuranceTypes ?? "",
    supportedRegions: fieldErrors.supported_regions ?? fieldErrors.supportedRegions ?? "",
    serviceableProducts:
      fieldErrors.serviceable_products ?? fieldErrors.serviceableProducts ?? "",
    notes: fieldErrors.notes ?? "",
  };
}

export function ProviderRegistryOverviewScreen() {
  const [providers, setProviders] = useState<ProviderRegistrySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [modalState, setModalState] = useState<ProviderModalState>("closed");
  const [selectedProviderCode, setSelectedProviderCode] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<ProviderStatusFilter>("ALL");
  const [drawerProviderCode, setDrawerProviderCode] = useState<string | null>(null);
  const [isEditingDrawer, setIsEditingDrawer] = useState(false);
  const [registerFieldErrors, setRegisterFieldErrors] = useState<FieldErrorMap>({});
  const [editFieldErrors, setEditFieldErrors] = useState<FieldErrorMap>({});
  const [formValues, setFormValues] = useState<ProviderFormState>(EMPTY_PROVIDER_FORM);
  const [editValues, setEditValues] = useState<ProviderEditState>(EMPTY_PROVIDER_EDIT);

  const selectedProvider = useMemo(
    () =>
      drawerProviderCode
        ? providers.find((provider) => provider.provider_code === drawerProviderCode) ?? null
        : null,
    [drawerProviderCode, providers],
  );

  const summary = useMemo(() => {
    const active = providers.filter((provider) => provider.status === "ACTIVE").length;
    const inactive = providers.filter((provider) => provider.status === "INACTIVE").length;
    const suspended = providers.filter((provider) => provider.status === "SUSPENDED").length;
    return {
      total: providers.length,
      active,
      inactive,
      suspended,
    };
  }, [providers]);

  const filteredProviders = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return providers.filter((provider) => {
      const matchesStatus = statusFilter === "ALL" || provider.status === statusFilter;
      const matchesSearch =
        normalizedSearch.length === 0
          ? true
          : [
              provider.provider_code,
              provider.provider_name,
              provider.company_name ?? "",
              provider.contact_email,
              provider.contact_phone,
            ]
              .join(" ")
              .toLowerCase()
              .includes(normalizedSearch);

      return matchesStatus && matchesSearch;
    });
  }, [providers, searchTerm, statusFilter]);

  const loadProviders = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await providerRegistryApi.listProviders();
      setProviders(response);
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadProviders();
  }, []);

  useEffect(() => {
    if (!successMessage) return;
    const timeoutId = window.setTimeout(() => setSuccessMessage(""), 3000);
    return () => window.clearTimeout(timeoutId);
  }, [successMessage]);

  useEffect(() => {
    if (!selectedProvider) {
      setEditValues(EMPTY_PROVIDER_EDIT);
      setEditFieldErrors({});
      setIsEditingDrawer(false);
      return;
    }
    setEditValues(toProviderEditState(selectedProvider));
    setEditFieldErrors({});
    setIsEditingDrawer(false);
  }, [selectedProvider]);

  const resetForm = () => {
    setFormValues(EMPTY_PROVIDER_FORM);
    setRegisterFieldErrors({});
  };

  const closeModal = () => {
    setModalState("closed");
    setSelectedProviderCode(null);
    setRegisterFieldErrors({});
  };

  const toggleInsuranceType = (insuranceType: string) => {
    setRegisterFieldErrors((current) => ({ ...current, supportedInsuranceTypes: "" }));
    setFormValues((current) => ({
      ...current,
      supportedInsuranceTypes: current.supportedInsuranceTypes.includes(insuranceType)
        ? current.supportedInsuranceTypes.filter((item) => item !== insuranceType)
        : [...current.supportedInsuranceTypes, insuranceType],
    }));
  };

  const toggleDrawerInsuranceType = (insuranceType: string) => {
    setEditFieldErrors((current) => ({ ...current, supportedInsuranceTypes: "" }));
    setEditValues((current) => ({
      ...current,
      supportedInsuranceTypes: current.supportedInsuranceTypes.includes(insuranceType)
        ? current.supportedInsuranceTypes.filter((item) => item !== insuranceType)
        : [...current.supportedInsuranceTypes, insuranceType],
    }));
  };

  const handleCreateProvider = async () => {
    setSubmitLoading(true);
    setError("");
    setSuccessMessage("");
    setRegisterFieldErrors({});
    try {
      await providerRegistryApi.createProvider({
        provider_name: formValues.providerName,
        provider_code: formValues.providerCode.toUpperCase(),
        company_name: formValues.companyName || undefined,
        contact_email: formValues.contactEmail,
        contact_phone: formValues.contactPhone,
        supported_insurance_types: formValues.supportedInsuranceTypes,
        supported_regions: parseCsv(formValues.supportedRegions),
        serviceable_products: parseCsv(formValues.serviceableProducts),
        notes: formValues.notes || undefined,
      });
      resetForm();
      closeModal();
      await loadProviders();
      setSuccessMessage("Provider registered successfully.");
    } catch (requestError) {
      const normalizedError = normalizeApiError(requestError);
      setError(normalizedError.message);
      setRegisterFieldErrors(mapProviderFieldErrors(normalizedError.fieldErrors));
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!selectedProviderCode) return;
    const current = providers.find((provider) => provider.provider_code === selectedProviderCode);
    if (!current) return;

    setSubmitLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const nextStatus = current.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
      await providerRegistryApi.updateProviderStatus(
        selectedProviderCode,
        nextStatus,
        `Requested from provider admin UI. Previous status: ${current.status}.`,
      );
      closeModal();
      await loadProviders();
      setSuccessMessage(`Provider status updated to ${nextStatus}.`);
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleUpdateProvider = async () => {
    if (!selectedProvider) return;

    setSubmitLoading(true);
    setError("");
    setSuccessMessage("");
    setEditFieldErrors({});
    try {
      await providerRegistryApi.updateProvider(selectedProvider.provider_code, {
        provider_name: editValues.providerName,
        company_name: editValues.companyName || undefined,
        contact_email: editValues.contactEmail,
        contact_phone: editValues.contactPhone,
        supported_insurance_types: editValues.supportedInsuranceTypes,
        supported_regions: parseCsv(editValues.supportedRegions),
        serviceable_products: parseCsv(editValues.serviceableProducts),
        notes: editValues.notes || undefined,
      });
      await loadProviders();
      setIsEditingDrawer(false);
      setSuccessMessage("Provider details saved successfully.");
    } catch (requestError) {
      const normalizedError = normalizeApiError(requestError);
      setError(normalizedError.message);
      setEditFieldErrors(mapProviderFieldErrors(normalizedError.fieldErrors));
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Providers</p>
          <h2>Provider registry</h2>
        </div>
        <Button onClick={() => setModalState("register")}>Register Provider</Button>
      </section>

      <section className="if-stats-grid">
        <StatCard label="Total Providers" value={String(summary.total)} variant="stat-1" />
        <StatCard label="Active Providers" value={String(summary.active)} variant="stat-2" />
        <StatCard label="Inactive Providers" value={String(summary.inactive)} variant="stat-3" />
        <StatCard label="Suspended Providers" value={String(summary.suspended)} variant="navy" />
      </section>

      {successMessage ? <div className="if-banner if-banner-success">{successMessage}</div> : null}
      {error ? <ErrorCard message={error} onRetry={() => void loadProviders()} /> : null}

      <section className="if-surface-card">
        <div className="if-form-grid" style={{ marginBottom: "var(--space-6)" }}>
          <TextInput
            label="Search providers"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            helperText="Search by code, name, company, email, or phone"
          />
          <SelectField
            label="Status filter"
            options={[
              { label: "All statuses", value: "ALL" },
              { label: "Active", value: "ACTIVE" },
              { label: "Inactive", value: "INACTIVE" },
              { label: "Suspended", value: "SUSPENDED" },
            ]}
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as ProviderStatusFilter)}
          />
        </div>

        {loading ? (
          <div className="if-skeleton-stack">
            <Skeleton height={56} />
            <Skeleton height={56} />
            <Skeleton height={56} />
          </div>
        ) : filteredProviders.length === 0 ? (
          <EmptyState
            title={providers.length === 0 ? "No Providers Registered" : "No Matching Providers"}
            description={
              providers.length === 0
                ? "Register the first provider so provider admins can manage insurer relationships from this console."
                : "Try changing the search text or status filter to find another provider."
            }
            action={
              providers.length === 0 ? (
                <Button onClick={() => setModalState("register")}>Register Provider</Button>
              ) : (
                <Button
                  variant="ghost"
                  onClick={() => {
                    setSearchTerm("");
                    setStatusFilter("ALL");
                  }}
                >
                  Clear Filters
                </Button>
              )
            }
          />
        ) : (
          <div className="if-table-wrap">
            <table className="if-data-table">
              <thead>
                <tr>
                  <th>Provider Code</th>
                  <th>Name</th>
                  <th>Contact</th>
                  <th>Insurance Types</th>
                  <th>Regions</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProviders.map((provider) => (
                  <tr key={provider.provider_code}>
                    <td className="if-mono">{provider.provider_code}</td>
                    <td>
                      <div>{provider.provider_name}</div>
                      <div className="if-inline-subtitle">
                        {provider.company_name || "No company name"}
                      </div>
                    </td>
                    <td>
                      <div>{provider.contact_email}</div>
                      <div className="if-inline-subtitle">{provider.contact_phone}</div>
                    </td>
                    <td>{provider.supported_insurance_types.join(", ") || "N/A"}</td>
                    <td>{provider.supported_regions.join(", ") || "N/A"}</td>
                    <td>
                      <StatusBadge
                        status={
                          provider.status === "ACTIVE"
                            ? "issued"
                            : provider.status === "SUSPENDED"
                              ? "failed"
                              : "cancelled"
                        }
                      >
                        {provider.status}
                      </StatusBadge>
                    </td>
                    <td>
                      {provider.updated_at
                        ? new Date(provider.updated_at).toLocaleString("en-IN")
                        : "N/A"}
                    </td>
                    <td>
                      <div className="if-table-action-row">
                        <Button variant="ghost" onClick={() => setDrawerProviderCode(provider.provider_code)}>
                          View
                        </Button>
                        <Button
                          variant="ghost"
                          onClick={() => {
                            setSelectedProviderCode(provider.provider_code);
                            setModalState("toggleStatus");
                          }}
                        >
                          {provider.status === "ACTIVE" ? "Deactivate" : "Activate"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {modalState === "register" ? (
        <Modal title="Register provider" width="wide">
          <div className="if-form-stack">
            <TextInput
              label="Provider Name"
              error={registerFieldErrors.providerName}
              value={formValues.providerName}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, providerName: "" }));
                setFormValues((current) => ({ ...current, providerName: event.target.value }));
              }}
            />
            <TextInput
              label="Provider Code"
              mono
              error={registerFieldErrors.providerCode}
              value={formValues.providerCode}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, providerCode: "" }));
                setFormValues((current) => ({
                  ...current,
                  providerCode: event.target.value.toUpperCase(),
                }));
              }}
            />
            <TextInput
              label="Company Name"
              error={registerFieldErrors.companyName}
              value={formValues.companyName}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, companyName: "" }));
                setFormValues((current) => ({ ...current, companyName: event.target.value }));
              }}
            />
            <TextInput
              label="Contact Email"
              type="email"
              error={registerFieldErrors.contactEmail}
              value={formValues.contactEmail}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, contactEmail: "" }));
                setFormValues((current) => ({ ...current, contactEmail: event.target.value }));
              }}
            />
            <TextInput
              label="Contact Phone"
              error={registerFieldErrors.contactPhone}
              value={formValues.contactPhone}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, contactPhone: "" }));
                setFormValues((current) => ({ ...current, contactPhone: event.target.value }));
              }}
            />
            <TextInput
              label="Supported Regions"
              error={registerFieldErrors.supportedRegions}
              helperText="Comma-separated, for example PAN_INDIA, MAHARASHTRA, KARNATAKA"
              value={formValues.supportedRegions}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, supportedRegions: "" }));
                setFormValues((current) => ({
                  ...current,
                  supportedRegions: event.target.value,
                }));
              }}
            />
            <TextInput
              label="Serviceable Products"
              error={registerFieldErrors.serviceableProducts}
              helperText="Comma-separated, for example FAMILY_FLOATER, TERM_LIFE"
              value={formValues.serviceableProducts}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, serviceableProducts: "" }));
                setFormValues((current) => ({
                  ...current,
                  serviceableProducts: event.target.value,
                }));
              }}
            />
            <div className="if-field">
              <span className="if-group-label">Insurance Types</span>
              <div className="if-pill-group">
                {INSURANCE_TYPE_OPTIONS.map((insuranceType) => (
                  <button
                    key={insuranceType}
                    className={`if-pill ${formValues.supportedInsuranceTypes.includes(insuranceType) ? "is-active" : ""}`}
                    onClick={() => toggleInsuranceType(insuranceType)}
                    type="button"
                  >
                    {insuranceType}
                  </button>
                ))}
              </div>
              {registerFieldErrors.supportedInsuranceTypes ? (
                <span className="if-error-text">{registerFieldErrors.supportedInsuranceTypes}</span>
              ) : null}
            </div>
            <TextareaField
              label="Notes"
              error={registerFieldErrors.notes}
              rows={4}
              value={formValues.notes}
              onChange={(event) => {
                setRegisterFieldErrors((current) => ({ ...current, notes: "" }));
                setFormValues((current) => ({ ...current, notes: event.target.value }));
              }}
            />
            <div className="if-modal-footer">
              <Button onClick={closeModal} variant="ghost">
                Cancel
              </Button>
              <Button loading={submitLoading} onClick={() => void handleCreateProvider()}>
                Register
              </Button>
            </div>
          </div>
        </Modal>
      ) : null}

      {modalState === "toggleStatus" ? (
        <Modal title="Change provider status">
          <p className="if-inline-subtitle">
            This will immediately update the selected provider status in the platform registry.
          </p>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">
              Cancel
            </Button>
            <Button loading={submitLoading} onClick={() => void handleToggleStatus()}>
              Confirm
            </Button>
          </div>
        </Modal>
      ) : null}

      {selectedProvider ? (
        <Drawer
          title={`Provider ${selectedProvider.provider_code}`}
          width="wide"
          onClose={() => {
            setDrawerProviderCode(null);
            setIsEditingDrawer(false);
          }}
        >
          <div className="if-form-stack">
            {isEditingDrawer ? (
              <>
                <div className="if-grid-two">
                  <TextInput
                    label="Provider Name"
                    error={editFieldErrors.providerName}
                    value={editValues.providerName}
                    onChange={(event) => {
                      setEditFieldErrors((current) => ({ ...current, providerName: "" }));
                      setEditValues((current) => ({ ...current, providerName: event.target.value }));
                    }}
                  />
                  <TextInput
                    label="Company Name"
                    error={editFieldErrors.companyName}
                    value={editValues.companyName}
                    onChange={(event) => {
                      setEditFieldErrors((current) => ({ ...current, companyName: "" }));
                      setEditValues((current) => ({ ...current, companyName: event.target.value }));
                    }}
                  />
                </div>
                <div className="if-grid-two">
                  <TextInput
                    label="Contact Email"
                    type="email"
                    error={editFieldErrors.contactEmail}
                    value={editValues.contactEmail}
                    onChange={(event) => {
                      setEditFieldErrors((current) => ({ ...current, contactEmail: "" }));
                      setEditValues((current) => ({ ...current, contactEmail: event.target.value }));
                    }}
                  />
                  <TextInput
                    label="Contact Phone"
                    error={editFieldErrors.contactPhone}
                    value={editValues.contactPhone}
                    onChange={(event) => {
                      setEditFieldErrors((current) => ({ ...current, contactPhone: "" }));
                      setEditValues((current) => ({ ...current, contactPhone: event.target.value }));
                    }}
                  />
                </div>
                <TextInput
                  label="Supported Regions"
                  error={editFieldErrors.supportedRegions}
                  helperText="Comma-separated regions"
                  value={editValues.supportedRegions}
                  onChange={(event) => {
                    setEditFieldErrors((current) => ({ ...current, supportedRegions: "" }));
                    setEditValues((current) => ({ ...current, supportedRegions: event.target.value }));
                  }}
                />
                <TextInput
                  label="Serviceable Products"
                  error={editFieldErrors.serviceableProducts}
                  helperText="Comma-separated products"
                  value={editValues.serviceableProducts}
                  onChange={(event) => {
                    setEditFieldErrors((current) => ({ ...current, serviceableProducts: "" }));
                    setEditValues((current) => ({
                      ...current,
                      serviceableProducts: event.target.value,
                    }));
                  }}
                />
                <div className="if-field">
                  <span className="if-group-label">Insurance Types</span>
                  <div className="if-pill-group">
                    {INSURANCE_TYPE_OPTIONS.map((insuranceType) => (
                      <button
                        key={insuranceType}
                        className={`if-pill ${editValues.supportedInsuranceTypes.includes(insuranceType) ? "is-active" : ""}`}
                        onClick={() => toggleDrawerInsuranceType(insuranceType)}
                        type="button"
                      >
                        {insuranceType}
                      </button>
                    ))}
                  </div>
                  {editFieldErrors.supportedInsuranceTypes ? (
                    <span className="if-error-text">{editFieldErrors.supportedInsuranceTypes}</span>
                  ) : null}
                </div>
                <TextareaField
                  label="Notes"
                  error={editFieldErrors.notes}
                  rows={4}
                  value={editValues.notes}
                  onChange={(event) => {
                    setEditFieldErrors((current) => ({ ...current, notes: "" }));
                    setEditValues((current) => ({ ...current, notes: event.target.value }));
                  }}
                />
                <div className="if-surface-card">
                  <p className="if-eyebrow">Provider Code</p>
                  <p className="if-inline-subtitle if-mono">{selectedProvider.provider_code}</p>
                </div>
              </>
            ) : (
              <>
                <div className="if-grid-two">
                  <div className="if-surface-card">
                    <p className="if-eyebrow">Identity</p>
                    <h3 style={{ marginTop: 0 }}>{selectedProvider.provider_name}</h3>
                    <p className="if-inline-subtitle">
                      {selectedProvider.company_name || "No company name provided"}
                    </p>
                    <div style={{ marginTop: "var(--space-4)" }}>
                      <StatusBadge
                        status={
                          selectedProvider.status === "ACTIVE"
                            ? "issued"
                            : selectedProvider.status === "SUSPENDED"
                              ? "failed"
                              : "cancelled"
                        }
                      >
                        {selectedProvider.status}
                      </StatusBadge>
                    </div>
                  </div>

                  <div className="if-surface-card">
                    <p className="if-eyebrow">Contact</p>
                    <div className="if-list-stack">
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Email</p>
                          <p className="if-inline-subtitle">{selectedProvider.contact_email}</p>
                        </div>
                      </div>
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Phone</p>
                          <p className="if-inline-subtitle">{selectedProvider.contact_phone}</p>
                        </div>
                      </div>
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Provider Code</p>
                          <p className="if-inline-subtitle if-mono">{selectedProvider.provider_code}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="if-grid-two">
                  <div className="if-surface-card">
                    <p className="if-eyebrow">Coverage Scope</p>
                    <div className="if-list-stack">
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Insurance Types</p>
                          <p className="if-inline-subtitle">
                            {selectedProvider.supported_insurance_types.join(", ") || "Not specified"}
                          </p>
                        </div>
                      </div>
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Supported Regions</p>
                          <p className="if-inline-subtitle">
                            {selectedProvider.supported_regions.join(", ") || "Not specified"}
                          </p>
                        </div>
                      </div>
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Serviceable Products</p>
                          <p className="if-inline-subtitle">
                            {selectedProvider.serviceable_products.join(", ") || "Not specified"}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="if-surface-card">
                    <p className="if-eyebrow">Record Info</p>
                    <div className="if-list-stack">
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Created</p>
                          <p className="if-inline-subtitle">
                            {selectedProvider.created_at
                              ? new Date(selectedProvider.created_at).toLocaleString("en-IN")
                              : "N/A"}
                          </p>
                        </div>
                      </div>
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Last Updated</p>
                          <p className="if-inline-subtitle">
                            {selectedProvider.updated_at
                              ? new Date(selectedProvider.updated_at).toLocaleString("en-IN")
                              : "N/A"}
                          </p>
                        </div>
                      </div>
                      <div className="if-list-row">
                        <div>
                          <p className="if-list-title">Notes</p>
                          <p className="if-inline-subtitle">
                            {selectedProvider.notes || "No notes added for this provider."}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            <div className="if-modal-footer">
              {isEditingDrawer ? (
                <>
                  <Button variant="ghost" onClick={() => setIsEditingDrawer(false)}>
                    Cancel Edit
                  </Button>
                  <Button loading={submitLoading} onClick={() => void handleUpdateProvider()}>
                    Save Changes
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="ghost" onClick={() => setDrawerProviderCode(null)}>
                    Close
                  </Button>
                  <Button variant="ghost" onClick={() => setIsEditingDrawer(true)}>
                    Edit Provider
                  </Button>
                  <Button
                    onClick={() => {
                      setSelectedProviderCode(selectedProvider.provider_code);
                      setDrawerProviderCode(null);
                      setModalState("toggleStatus");
                    }}
                  >
                    {selectedProvider.status === "ACTIVE" ? "Deactivate Provider" : "Activate Provider"}
                  </Button>
                </>
              )}
            </div>
          </div>
        </Drawer>
      ) : null}
    </div>
  );
}
