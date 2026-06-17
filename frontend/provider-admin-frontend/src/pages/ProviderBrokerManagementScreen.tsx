import { Check, Copy, Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorCard } from "../components/ui/ErrorCard";
import { Modal } from "../components/ui/Modal";
import { Skeleton } from "../components/ui/Skeleton";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TextareaField } from "../components/ui/TextareaField";
import { TextInput } from "../components/ui/TextInput";
import { providerAdminApi, type ProviderBrokerSummary } from "../services/api/providerAdmin";
import type { FieldErrorMap } from "../services/api/types";
import { normalizeApiError } from "../utils/apiErrors";

type BrokerModalState = "closed" | "register" | "registerKey" | "toggleStatus" | "rotateKey";

const INSURANCE_TYPE_OPTIONS = ["HEALTH", "LIFE", "VEHICLE", "TRAVEL", "HOME"] as const;

function mapBrokerFieldErrors(fieldErrors: FieldErrorMap): FieldErrorMap {
  return {
    brokerName: fieldErrors.broker_name ?? fieldErrors.brokerName ?? "",
    brokerCode: fieldErrors.broker_code ?? fieldErrors.brokerCode ?? "",
    companyName: fieldErrors.company_name ?? fieldErrors.companyName ?? "",
    contactPersonName:
      fieldErrors.contact_person_name ?? fieldErrors.contactPersonName ?? "",
    contactEmail: fieldErrors.contact_email ?? fieldErrors.contactEmail ?? "",
    contactPhone: fieldErrors.contact_phone ?? fieldErrors.contactPhone ?? "",
    callbackUrl: fieldErrors.callback_url ?? fieldErrors.callbackUrl ?? "",
    webhookUrl: fieldErrors.webhook_url ?? fieldErrors.webhookUrl ?? "",
    activeRegions: fieldErrors.active_regions ?? fieldErrors.activeRegions ?? "",
    notes: fieldErrors.notes ?? "",
    supportedInsuranceTypes:
      fieldErrors.supported_insurance_types ?? fieldErrors.supportedInsuranceTypes ?? "",
  };
}

export function ProviderBrokerManagementScreen() {
  const [modalState, setModalState] = useState<BrokerModalState>("closed");
  const [brokers, setBrokers] = useState<ProviderBrokerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [transientApiKey, setTransientApiKey] = useState<string | null>(null);
  const [selectedBrokerCode, setSelectedBrokerCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [isRevealed, setIsRevealed] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [registerFieldErrors, setRegisterFieldErrors] = useState<FieldErrorMap>({});
  const [credentialMessage, setCredentialMessage] = useState("");
  const [formValues, setFormValues] = useState({
    brokerName: "",
    brokerCode: "",
    companyName: "",
    contactPersonName: "",
    contactEmail: "",
    contactPhone: "",
    callbackUrl: "",
    webhookUrl: "",
    activeRegions: "",
    notes: "",
    supportedInsuranceTypes: [] as string[],
  });

  const loadBrokers = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await providerAdminApi.listBrokers();
      setBrokers(response);
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadBrokers();
  }, []);

  useEffect(() => {
    if (!successMessage) return;
    const timeoutId = window.setTimeout(() => setSuccessMessage(""), 3000);
    return () => window.clearTimeout(timeoutId);
  }, [successMessage]);

  const closeModal = () => {
    setModalState("closed");
    setSelectedBrokerCode(null);
    setTransientApiKey(null);
    setIsRevealed(false);
    setCopied(false);
    setRegisterFieldErrors({});
    setCredentialMessage("");
  };

  const resetForm = () => {
    setFormValues({
      brokerName: "",
      brokerCode: "",
      companyName: "",
      contactPersonName: "",
      contactEmail: "",
      contactPhone: "",
      callbackUrl: "",
      webhookUrl: "",
      activeRegions: "",
      notes: "",
      supportedInsuranceTypes: [],
    });
    setRegisterFieldErrors({});
  };

  const parseCsvInput = (value: string) =>
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

  const toggleInsuranceType = (insuranceType: string) => {
    setRegisterFieldErrors((current) => ({ ...current, supportedInsuranceTypes: "" }));
    setFormValues((current) => ({
      ...current,
      supportedInsuranceTypes: current.supportedInsuranceTypes.includes(insuranceType)
        ? current.supportedInsuranceTypes.filter((item) => item !== insuranceType)
        : [...current.supportedInsuranceTypes, insuranceType],
    }));
  };

  const handleRegister = async () => {
    setSubmitLoading(true);
    setError("");
    setSuccessMessage("");
    setRegisterFieldErrors({});
    try {
      const response = await providerAdminApi.registerBroker({
        broker_name: formValues.brokerName,
        broker_code: formValues.brokerCode.toUpperCase(),
        company_name: formValues.companyName || undefined,
        contact_person_name: formValues.contactPersonName || undefined,
        contact_email: formValues.contactEmail || undefined,
        contact_phone: formValues.contactPhone || undefined,
        supported_insurance_types: formValues.supportedInsuranceTypes,
        active_regions: parseCsvInput(formValues.activeRegions),
        callback_url: formValues.callbackUrl || undefined,
        webhook_url: formValues.webhookUrl || undefined,
        notes: formValues.notes || undefined,
        created_by_admin: "provider-admin-ui",
      });
      setTransientApiKey(response.api_key);
      setCredentialMessage("Broker registered successfully.");
      setModalState("registerKey");
      resetForm();
      await loadBrokers();
      setSuccessMessage("Broker registered successfully.");
    } catch (requestError) {
      const normalizedError = normalizeApiError(requestError);
      setError(normalizedError.message);
      setRegisterFieldErrors(mapBrokerFieldErrors(normalizedError.fieldErrors));
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!selectedBrokerCode) return;
    const current = brokers.find((broker) => broker.broker_code === selectedBrokerCode);
    if (!current) return;
    setSubmitLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const nextStatus = current.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
      await providerAdminApi.updateBrokerStatus(
        selectedBrokerCode,
        nextStatus,
      );
      closeModal();
      await loadBrokers();
      setSuccessMessage(`Broker status updated to ${nextStatus}.`);
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleRotateKey = async () => {
    if (!selectedBrokerCode) return;
    setSubmitLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const response = await providerAdminApi.rotateBrokerKey(selectedBrokerCode);
      setTransientApiKey(response.api_key);
      setCredentialMessage("Broker API key rotated successfully.");
      setModalState("registerKey");
      await loadBrokers();
      setSuccessMessage("Broker API key rotated successfully.");
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Provider Brokers</p>
          <h2>Broker registry</h2>
        </div>
        <Button onClick={() => setModalState("register")}>Register Broker</Button>
      </section>

      {successMessage ? <div className="if-banner if-banner-success">{successMessage}</div> : null}
      {error ? <ErrorCard message={error} onRetry={() => void loadBrokers()} /> : null}

      <section className="if-surface-card">
        {loading ? (
          <div className="if-skeleton-stack">
            <Skeleton height={56} />
            <Skeleton height={56} />
            <Skeleton height={56} />
          </div>
        ) : brokers.length === 0 ? (
          <EmptyState
            title="No Provider Brokers"
            description="Register the first broker to enable provider-side partner operations."
            action={<Button onClick={() => setModalState("register")}>Register Broker</Button>}
          />
        ) : (
          <div className="if-table-wrap">
            <table className="if-data-table">
              <thead>
                <tr>
                  <th>Broker Code</th>
                  <th>Name</th>
                  <th>Callback URL</th>
                  <th>Webhook URL</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {brokers.map((broker) => (
                  <tr key={broker.broker_code}>
                    <td className="if-mono">{broker.broker_code}</td>
                    <td>
                      <div>{broker.broker_name}</div>
                      <div className="if-inline-subtitle">{broker.company_name || "No company name"}</div>
                    </td>
                    <td className="if-mono">{broker.callback_url}</td>
                    <td className="if-mono">{broker.webhook_url}</td>
                    <td>
                      <StatusBadge status={broker.status === "ACTIVE" ? "issued" : "cancelled"}>
                        {broker.status}
                      </StatusBadge>
                    </td>
                    <td>{broker.updated_at ? new Date(broker.updated_at).toLocaleString("en-IN") : "N/A"}</td>
                    <td>
                      <div className="if-table-action-row">
                        <Button
                          onClick={() => {
                            setSelectedBrokerCode(broker.broker_code);
                            setModalState("rotateKey");
                          }}
                          variant="ghost"
                        >
                          Rotate Key
                        </Button>
                        <button
                          className="if-link-button if-link-button-danger"
                          onClick={() => {
                            setSelectedBrokerCode(broker.broker_code);
                            setModalState("toggleStatus");
                          }}
                          type="button"
                        >
                          {broker.status === "ACTIVE" ? "Deactivate" : "Activate"}
                        </button>
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
        <Modal title="Register provider broker" width="wide">
          <div className="if-form-stack">
            <TextInput label="Broker Name" error={registerFieldErrors.brokerName} value={formValues.brokerName} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, brokerName: "" })); setFormValues((current) => ({ ...current, brokerName: event.target.value })); }} />
            <TextInput label="Broker Code" mono error={registerFieldErrors.brokerCode} value={formValues.brokerCode} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, brokerCode: "" })); setFormValues((current) => ({ ...current, brokerCode: event.target.value.toUpperCase() })); }} />
            <TextInput label="Company Name" error={registerFieldErrors.companyName} value={formValues.companyName} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, companyName: "" })); setFormValues((current) => ({ ...current, companyName: event.target.value })); }} />
            <TextInput label="Contact Person" error={registerFieldErrors.contactPersonName} value={formValues.contactPersonName} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, contactPersonName: "" })); setFormValues((current) => ({ ...current, contactPersonName: event.target.value })); }} />
            <TextInput label="Contact Email" type="email" error={registerFieldErrors.contactEmail} value={formValues.contactEmail} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, contactEmail: "" })); setFormValues((current) => ({ ...current, contactEmail: event.target.value })); }} />
            <TextInput label="Contact Phone" error={registerFieldErrors.contactPhone} value={formValues.contactPhone} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, contactPhone: "" })); setFormValues((current) => ({ ...current, contactPhone: event.target.value })); }} />
            <TextInput label="Callback URL" error={registerFieldErrors.callbackUrl} value={formValues.callbackUrl} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, callbackUrl: "" })); setFormValues((current) => ({ ...current, callbackUrl: event.target.value })); }} />
            <TextInput label="Webhook URL" error={registerFieldErrors.webhookUrl} value={formValues.webhookUrl} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, webhookUrl: "" })); setFormValues((current) => ({ ...current, webhookUrl: event.target.value })); }} />
            <TextInput
              label="Active Regions"
              error={registerFieldErrors.activeRegions}
              helperText="Comma-separated, for example PAN_INDIA or MAHARASHTRA"
              value={formValues.activeRegions}
              onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, activeRegions: "" })); setFormValues((current) => ({ ...current, activeRegions: event.target.value })); }}
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
            <TextareaField label="Notes" error={registerFieldErrors.notes} rows={4} value={formValues.notes} onChange={(event) => { setRegisterFieldErrors((current) => ({ ...current, notes: "" })); setFormValues((current) => ({ ...current, notes: event.target.value })); }} />
            <div className="if-modal-footer">
              <Button onClick={closeModal} variant="ghost">Cancel</Button>
              <Button loading={submitLoading} onClick={() => void handleRegister()}>Register</Button>
            </div>
          </div>
        </Modal>
      ) : null}

      {modalState === "registerKey" ? (
        <Modal title="Broker API key generated">
          {credentialMessage ? (
            <div className="if-banner if-banner-success">
              {credentialMessage}
            </div>
          ) : null}
          <div className="if-banner if-banner-warning">
            Save this API key now. It will not be shown again.
          </div>
          <div className="if-key-reveal">
            <span className="if-mono">{isRevealed ? transientApiKey : "brk_live_••••••••••••••••"}</span>
            <div className="if-key-actions">
              <Button iconOnly ariaLabel="Toggle API key visibility" onClick={() => setIsRevealed((current) => !current)} variant="ghost">
                {isRevealed ? <EyeOff size={18} /> : <Eye size={18} />}
              </Button>
              <Button
                iconOnly
                ariaLabel="Copy API key"
                onClick={async () => {
                  if (!transientApiKey) return;
                  await navigator.clipboard.writeText(transientApiKey);
                  setCopied(true);
                  window.setTimeout(() => setCopied(false), 2000);
                }}
                variant="ghost"
              >
                {copied ? <Check size={18} /> : <Copy size={18} />}
              </Button>
            </div>
          </div>
          <div className="if-modal-footer">
            <Button onClick={closeModal}>Done</Button>
          </div>
        </Modal>
      ) : null}

      {modalState === "toggleStatus" ? (
        <Modal title="Change broker status">
          <p className="if-inline-subtitle">This will immediately update the selected broker status.</p>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">Cancel</Button>
            <Button loading={submitLoading} onClick={() => void handleToggleStatus()}>Confirm</Button>
          </div>
        </Modal>
      ) : null}

      {modalState === "rotateKey" ? (
        <Modal title="Rotate broker key">
          <p className="if-inline-subtitle">The current broker API key will be invalidated immediately.</p>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">Cancel</Button>
            <Button loading={submitLoading} onClick={() => void handleRotateKey()}>Rotate Key</Button>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
