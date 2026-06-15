import { useEffect, useState } from "react";

import { Button } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { Modal } from "../../components/ui/Modal";
import { Skeleton } from "../../components/ui/Skeleton";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { TextareaField } from "../../components/ui/TextareaField";
import { TextInput } from "../../components/ui/TextInput";
import { adminApi, type ProviderSummary } from "../../services/api/admin";
import { normalizeApiError } from "../../utils/apiErrors";

const INSURANCE_TYPE_OPTIONS = ["HEALTH", "LIFE", "VEHICLE", "TRAVEL", "HOME"] as const;

/**
 * ProviderManagementScreen lets admins inspect the provider registry and onboard new providers.
 * Technical webhook wiring stays internal while the UI focuses on business and contact details.
 */
export function ProviderManagementScreen() {
  const [providers, setProviders] = useState<ProviderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);
  const [statusLoadingCode, setStatusLoadingCode] = useState<string | null>(null);
  const [formValues, setFormValues] = useState({
    providerName: "",
    providerCode: "",
    companyName: "",
    contactEmail: "",
    contactPhone: "",
    supportedInsuranceTypes: [] as string[],
    supportedRegions: "",
    serviceableProducts: "",
    notes: "",
  });

  const parseCsvInput = (value: string) =>
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

  const loadProviders = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await adminApi.listProviders();
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

  const closeModal = () => {
    setModalOpen(false);
    setFormValues({
      providerName: "",
      providerCode: "",
      companyName: "",
      contactEmail: "",
      contactPhone: "",
      supportedInsuranceTypes: [],
      supportedRegions: "",
      serviceableProducts: "",
      notes: "",
    });
  };

  const toggleInsuranceType = (insuranceType: string) => {
    setFormValues((current) => ({
      ...current,
      supportedInsuranceTypes: current.supportedInsuranceTypes.includes(insuranceType)
        ? current.supportedInsuranceTypes.filter((item) => item !== insuranceType)
        : [...current.supportedInsuranceTypes, insuranceType],
    }));
  };

  const handleRegister = async () => {
    setRegisterLoading(true);
    setError("");
    try {
      const provider = await adminApi.createProvider({
        provider_name: formValues.providerName,
        provider_code: formValues.providerCode.toUpperCase(),
        company_name: formValues.companyName || undefined,
        contact_email: formValues.contactEmail,
        contact_phone: formValues.contactPhone,
        supported_insurance_types: formValues.supportedInsuranceTypes,
        supported_regions: parseCsvInput(formValues.supportedRegions),
        serviceable_products: parseCsvInput(formValues.serviceableProducts),
        notes: formValues.notes || undefined,
      });
      setProviders((current) => [provider, ...current]);
      closeModal();
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setRegisterLoading(false);
    }
  };

  const handleStatusUpdate = async (providerCode: string, status: "ACTIVE" | "INACTIVE") => {
    setStatusLoadingCode(providerCode);
    setError("");
    const previous = providers;
    setProviders((current) =>
      current.map((provider) =>
        provider.provider_code === providerCode ? { ...provider, status } : provider,
      ),
    );
    try {
      await adminApi.updateProviderStatus(providerCode, status);
    } catch (requestError) {
      setProviders(previous);
      setError(normalizeApiError(requestError).message);
    } finally {
      setStatusLoadingCode(null);
    }
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Providers</p>
          <h2>Provider registry</h2>
        </div>
        <Button onClick={() => setModalOpen(true)}>Register Provider</Button>
      </section>

      {error ? <ErrorCard message={error} onRetry={() => void loadProviders()} /> : null}

      <section className="if-surface-card">
        {loading ? (
          <div className="if-skeleton-stack">
            <Skeleton height={56} />
            <Skeleton height={56} />
            <Skeleton height={56} />
          </div>
        ) : providers.length === 0 ? (
          <EmptyState
            title="No Providers Registered"
            description="There are currently no providers available in the registry."
            action={<Button onClick={() => setModalOpen(true)}>Register Provider</Button>}
          />
        ) : (
          <div className="if-table-wrap">
            <table className="if-data-table">
              <thead>
                <tr>
                  <th>Provider Code</th>
                  <th>Name</th>
                  <th>Insurance Types</th>
                  <th>Regions</th>
                  <th>Contact</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((provider) => (
                  <tr key={provider.provider_code}>
                    <td className="if-mono">{provider.provider_code}</td>
                    <td>
                      <div>{provider.provider_name}</div>
                      {provider.company_name ? (
                        <div className="if-inline-subtitle">{provider.company_name}</div>
                      ) : null}
                    </td>
                    <td>
                      {provider.supported_insurance_types.length > 0
                        ? provider.supported_insurance_types.join(", ")
                        : "Not specified"}
                    </td>
                    <td>
                      {provider.supported_regions.length > 0
                        ? provider.supported_regions.join(", ")
                        : "Not specified"}
                    </td>
                    <td>
                      <div>{provider.contact_email}</div>
                      <div className="if-inline-subtitle">{provider.contact_phone}</div>
                    </td>
                    <td>
                      <StatusBadge status={provider.status === "ACTIVE" ? "issued" : "cancelled"}>
                        {provider.status}
                      </StatusBadge>
                    </td>
                    <td>
                      <div className="if-table-action-row">
                        <Button
                          loading={statusLoadingCode === provider.provider_code}
                          onClick={() => {
                            void handleStatusUpdate(
                              provider.provider_code,
                              provider.status === "ACTIVE" ? "INACTIVE" : "ACTIVE",
                            );
                          }}
                          variant="ghost"
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

      {modalOpen ? (
        <Modal title="Register new provider" width="wide">
          <div className="if-form-stack">
            <TextInput
              label="Provider Name"
              onChange={(event) => setFormValues((current) => ({ ...current, providerName: event.target.value }))}
              placeholder="Example Health Insurance"
              value={formValues.providerName}
            />
            <TextInput
              label="Provider Code"
              mono
              onChange={(event) =>
                setFormValues((current) => ({ ...current, providerCode: event.target.value.toUpperCase() }))
              }
              placeholder="EXAMPLE_HEALTH"
              value={formValues.providerCode}
            />
            <TextInput
              label="Company Name"
              onChange={(event) => setFormValues((current) => ({ ...current, companyName: event.target.value }))}
              placeholder="Example Health Insurance Co. Ltd."
              value={formValues.companyName}
            />
            <TextInput
              label="Contact Email"
              onChange={(event) => setFormValues((current) => ({ ...current, contactEmail: event.target.value }))}
              placeholder="support@example.com"
              type="email"
              value={formValues.contactEmail}
            />
            <TextInput
              label="Contact Phone"
              onChange={(event) => setFormValues((current) => ({ ...current, contactPhone: event.target.value }))}
              placeholder="9876543210"
              value={formValues.contactPhone}
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
              <span className="if-helper-text">
                Select all insurance types this provider supports.
              </span>
            </div>
            <TextInput
              label="Supported Regions"
              helperText="Comma-separated, for example PAN_INDIA or MAHARASHTRA, KARNATAKA"
              onChange={(event) =>
                setFormValues((current) => ({ ...current, supportedRegions: event.target.value }))
              }
              placeholder="PAN_INDIA"
              value={formValues.supportedRegions}
            />
            <TextInput
              label="Serviceable Products"
              helperText="Comma-separated, for example Retail Health, Family Floater"
              onChange={(event) =>
                setFormValues((current) => ({ ...current, serviceableProducts: event.target.value }))
              }
              placeholder="Retail Health, Corporate Health"
              value={formValues.serviceableProducts}
            />
            <TextareaField
              label="Notes"
              onChange={(event) => setFormValues((current) => ({ ...current, notes: event.target.value }))}
              placeholder="Optional internal note about this provider."
              rows={4}
              value={formValues.notes}
            />
          </div>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">
              Cancel
            </Button>
            <Button loading={registerLoading} onClick={() => void handleRegister()}>
              Register
            </Button>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
