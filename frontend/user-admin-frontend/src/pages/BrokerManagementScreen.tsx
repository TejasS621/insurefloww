import { AlertTriangle, Check, Copy, Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorCard } from "../components/ui/ErrorCard";
import { Modal } from "../components/ui/Modal";
import { Skeleton } from "../components/ui/Skeleton";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TextareaField } from "../components/ui/TextareaField";
import { TextInput } from "../components/ui/TextInput";
import { adminApi, type BrokerSummary } from "../services/api/admin";
import { normalizeApiError } from "../utils/apiErrors";

type BrokerModalState =
  | "closed"
  | "register"
  | "registerKey"
  | "deactivateConfirm"
  | "rotateConfirm"
  | "rotateKey";

const INSURANCE_TYPE_OPTIONS = ["HEALTH", "LIFE", "VEHICLE", "TRAVEL", "HOME"] as const;

/**
 * BrokerManagementScreen now loads brokers from the API and applies optimistic broker updates.
 * Key reveal content is transient and cleared when the modal closes.
 */
export function BrokerManagementScreen() {
  const [modalState, setModalState] = useState<BrokerModalState>("closed");
  const [copied, setCopied] = useState(false);
  const [brokers, setBrokers] = useState<BrokerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [transientApiKey, setTransientApiKey] = useState<string | null>(null);
  const [selectedBrokerCode, setSelectedBrokerCode] = useState<string | null>(null);
  const [isRevealed, setIsRevealed] = useState(false);
  const [formValues, setFormValues] = useState({
    brokerName: "",
    brokerCode: "",
    companyName: "",
    licenseNumber: "",
    registrationNumber: "",
    contactPersonName: "",
    contactEmail: "",
    contactPhone: "",
    supportedInsuranceTypes: [] as string[],
    activeRegions: "",
    partnerProviderCodes: "",
    notes: "",
  });

  const [registerLoading, setRegisterLoading] = useState(false);
  const [rotateLoading, setRotateLoading] = useState(false);

  const loadBrokers = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await adminApi.listBrokers();
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

  const closeModal = () => {
    setModalState("closed");
    setTransientApiKey(null);
    setSelectedBrokerCode(null);
    setIsRevealed(false);
    setFormValues({
      brokerName: "",
      brokerCode: "",
      companyName: "",
      licenseNumber: "",
      registrationNumber: "",
      contactPersonName: "",
      contactEmail: "",
      contactPhone: "",
      supportedInsuranceTypes: [],
      activeRegions: "",
      partnerProviderCodes: "",
      notes: "",
    });
  };

  const parseCsvInput = (value: string) =>
    value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

  const toggleInsuranceType = (insuranceType: string) => {
    setFormValues((current) => ({
      ...current,
      supportedInsuranceTypes: current.supportedInsuranceTypes.includes(insuranceType)
        ? current.supportedInsuranceTypes.filter((item) => item !== insuranceType)
        : [...current.supportedInsuranceTypes, insuranceType],
    }));
  };

  const handleCopy = () => {
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const handleRegister = async () => {
    setRegisterLoading(true);
    setError("");
    try {
      const broker = await adminApi.createBroker({
        broker_name: formValues.brokerName,
        broker_code: formValues.brokerCode.toUpperCase(),
        company_name: formValues.companyName || undefined,
        license_number: formValues.licenseNumber || undefined,
        registration_number: formValues.registrationNumber || undefined,
        contact_person_name: formValues.contactPersonName || undefined,
        contact_email: formValues.contactEmail || undefined,
        contact_phone: formValues.contactPhone || undefined,
        supported_insurance_types: formValues.supportedInsuranceTypes,
        active_regions: parseCsvInput(formValues.activeRegions),
        partner_provider_codes: parseCsvInput(formValues.partnerProviderCodes),
        notes: formValues.notes || undefined,
      });
      setBrokers((current) => [broker, ...current]);
      setTransientApiKey(broker.api_key ?? "brk_live_****************");
      setModalState("registerKey");
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setRegisterLoading(false);
    }
  };

  const handleStatusUpdate = async (brokerCode: string, status: "ACTIVE" | "INACTIVE") => {
    const previous = brokers;
    setBrokers((current) =>
      current.map((broker) =>
        broker.broker_code === brokerCode ? { ...broker, status } : broker,
      ),
    );
    try {
      await adminApi.updateBrokerStatus(brokerCode, status);
    } catch (requestError) {
      setBrokers(previous);
      setError(normalizeApiError(requestError).message);
    }
  };

  const handleRotateKey = async () => {
    if (!selectedBrokerCode) {
      return;
    }
    setRotateLoading(true);
    setError("");
    try {
      const broker = await adminApi.rotateBrokerKey(selectedBrokerCode);
      setTransientApiKey(broker.api_key ?? "brk_live_****************");
      setModalState("rotateKey");
      await loadBrokers();
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setRotateLoading(false);
    }
  };

  return (
    <div className="if-screen-stack">
      <section className="if-section-heading">
        <div>
          <p className="if-eyebrow">Brokers</p>
          <h2>Broker registry</h2>
        </div>
        <Button onClick={() => setModalState("register")}>Register Broker</Button>
      </section>

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
            title="No Brokers Registered"
            description="There are currently no active brokers registered in the system."
            action={<Button onClick={() => setModalState("register")}>Register Broker</Button>}
          />
        ) : (
          <div className="if-table-wrap">
            <table className="if-data-table">
              <thead>
                <tr>
                  <th>Broker Code</th>
                  <th>Name</th>
                  <th>Insurance Types</th>
                  <th>Contact</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Last Key Rotation</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {brokers.map((broker) => (
                  <tr key={broker.broker_code}>
                    <td className="if-mono">{broker.broker_code}</td>
                    <td>
                      <div>{broker.broker_name}</div>
                      {broker.company_name ? (
                        <div className="if-inline-subtitle">{broker.company_name}</div>
                      ) : null}
                    </td>
                    <td>
                      {broker.supported_insurance_types.length > 0
                        ? broker.supported_insurance_types.join(", ")
                        : "Not specified"}
                    </td>
                    <td>
                      <div>{broker.contact_person_name || "No contact set"}</div>
                      <div className="if-inline-subtitle">
                        {broker.contact_email || broker.contact_phone || "No contact details"}
                      </div>
                    </td>
                    <td>
                      <StatusBadge status={broker.status === "ACTIVE" ? "issued" : "cancelled"}>
                        {broker.status}
                      </StatusBadge>
                    </td>
                    <td>{broker.created_at ? new Date(broker.created_at).toLocaleDateString("en-IN") : "N/A"}</td>
                    <td>
                      {broker.last_key_rotated_at
                        ? new Date(broker.last_key_rotated_at).toLocaleDateString("en-IN")
                        : "Not rotated"}
                    </td>
                    <td>
                      <div className="if-table-action-row">
                        <Button
                          onClick={() => {
                            setSelectedBrokerCode(broker.broker_code);
                            setModalState("rotateConfirm");
                          }}
                          variant="ghost"
                        >
                          Rotate Key
                        </Button>
                        <button
                          className="if-link-button if-link-button-danger"
                          onClick={() => {
                            setSelectedBrokerCode(broker.broker_code);
                            setModalState("deactivateConfirm");
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
        <Modal title="Register new broker" width="wide">
          <div className="if-form-stack">
            <TextInput
              label="Broker Name"
              onChange={(event) => setFormValues((current) => ({ ...current, brokerName: event.target.value }))}
              placeholder="Broker X Partners"
              value={formValues.brokerName}
            />
            <TextInput
              label="Broker Code"
              mono
              onChange={(event) =>
                setFormValues((current) => ({ ...current, brokerCode: event.target.value.toUpperCase() }))
              }
              placeholder="BROKERX"
              value={formValues.brokerCode}
            />
            <TextInput
              label="Company Name"
              onChange={(event) => setFormValues((current) => ({ ...current, companyName: event.target.value }))}
              placeholder="Demo Broker Pvt Ltd"
              value={formValues.companyName}
            />
            <TextInput
              label="Contact Person"
              onChange={(event) =>
                setFormValues((current) => ({ ...current, contactPersonName: event.target.value }))
              }
              placeholder="Priya Mehta"
              value={formValues.contactPersonName}
            />
            <TextInput
              label="Contact Email"
              onChange={(event) => setFormValues((current) => ({ ...current, contactEmail: event.target.value }))}
              placeholder="partnerships@broker.in"
              type="email"
              value={formValues.contactEmail}
            />
            <TextInput
              label="Contact Phone"
              onChange={(event) => setFormValues((current) => ({ ...current, contactPhone: event.target.value }))}
              placeholder="9876543210"
              value={formValues.contactPhone}
            />
            <TextInput
              label="Active Regions"
              helperText="Comma-separated, for example PAN_INDIA or MAHARASHTRA, KARNATAKA"
              onChange={(event) => setFormValues((current) => ({ ...current, activeRegions: event.target.value }))}
              placeholder="PAN_INDIA"
              value={formValues.activeRegions}
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
                Select all insurance types this broker can distribute.
              </span>
            </div>
            <TextInput
              label="Partner Provider Codes"
              helperText="Optional comma-separated provider codes"
              onChange={(event) =>
                setFormValues((current) => ({ ...current, partnerProviderCodes: event.target.value }))
              }
              placeholder="DEMO_PROVIDER, HDFC_ERGO"
              value={formValues.partnerProviderCodes}
            />
            <TextInput
              label="License Number"
              onChange={(event) => setFormValues((current) => ({ ...current, licenseNumber: event.target.value }))}
              placeholder="IRDAI-BRK-2026-001"
              value={formValues.licenseNumber}
            />
            <TextInput
              label="Registration Number"
              onChange={(event) =>
                setFormValues((current) => ({ ...current, registrationNumber: event.target.value }))
              }
              placeholder="REG-2026-BROKER-001"
              value={formValues.registrationNumber}
            />
            <TextareaField
              label="Notes"
              onChange={(event) => setFormValues((current) => ({ ...current, notes: event.target.value }))}
              placeholder="Optional internal note about this broker."
              rows={4}
              value={formValues.notes}
            />
          </div>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">
              Cancel
            </Button>
            <Button onClick={() => void handleRegister()} loading={registerLoading}>Register</Button>
          </div>
        </Modal>
      ) : null}

      {modalState === "registerKey" || modalState === "rotateKey" ? (
        <Modal width="wide">
          <div
            className="if-warning-banner"
            style={{
              background: "rgba(245, 158, 11, 0.1)",
              border: "1px solid rgba(245, 158, 11, 0.25)",
              borderRadius: "var(--radius-sm)",
              padding: "12px 16px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              color: "var(--if-warning)",
              marginBottom: "16px",
            }}
          >
            <AlertTriangle size={18} style={{ color: "var(--if-warning)" }} />
            <span style={{ fontSize: "14px", fontWeight: "500" }}>
              Save this API key now. It will not be shown again.
            </span>
          </div>
          <div
            className="if-key-display-field"
            style={{
              background: "rgba(0, 0, 0, 0.3)",
              border: "1px solid var(--if-border)",
              fontFamily: "var(--fs-mono)",
              fontSize: "14px",
              color: "var(--if-text-1)",
              padding: "12px 16px",
              borderRadius: "var(--radius-sm)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "20px",
              position: "relative",
            }}
          >
            <span style={{ wordBreak: "break-all" }}>
              {isRevealed
                ? (transientApiKey ?? "")
                : (transientApiKey ? "brk_live_" + "•".repeat(14) : "brk_live_•••••••••••••")}
            </span>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <button
                onClick={() => setIsRevealed(!isRevealed)}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--if-text-2)",
                  padding: "4px",
                  display: "flex",
                  alignItems: "center",
                }}
                type="button"
                aria-label={isRevealed ? "Hide key" : "Reveal key"}
              >
                {isRevealed ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
              <button
                onClick={() => {
                  if (transientApiKey) {
                    navigator.clipboard.writeText(transientApiKey);
                    handleCopy();
                  }
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: copied ? "var(--if-success)" : "var(--if-text-2)",
                  padding: "4px",
                  display: "flex",
                  alignItems: "center",
                  position: "relative",
                }}
                type="button"
                aria-label="Copy key"
              >
                {copied ? <Check size={18} /> : <Copy size={18} />}
                {copied && (
                  <span
                    style={{
                      position: "absolute",
                      bottom: "100%",
                      right: "50%",
                      transform: "translateX(50%) translateY(-8px)",
                      background: "var(--if-charcoal)",
                      color: "var(--if-text-inverse)",
                      fontSize: "12px",
                      padding: "4px 8px",
                      borderRadius: "4px",
                      whiteSpace: "nowrap",
                      border: "1px solid var(--if-border)",
                    }}
                  >
                    Copied!
                  </span>
                )}
              </button>
            </div>
          </div>
          <div className="if-modal-footer">
            <Button onClick={closeModal}>Done</Button>
          </div>
        </Modal>
      ) : null}

      {modalState === "rotateConfirm" ? (
        <Modal title="Rotate API key?">
          <p className="if-inline-subtitle">
            The current key will be invalidated immediately. A new key will be generated and shown once.
          </p>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">
              Cancel
            </Button>
            <Button className="if-button-danger" onClick={() => void handleRotateKey()} loading={rotateLoading}>
              Rotate Key
            </Button>
          </div>
        </Modal>
      ) : null}

      {modalState === "deactivateConfirm" ? (
        <Modal title="Update broker status?">
          <p className="if-inline-subtitle">
            This broker status will change immediately and broker API access will follow the updated lifecycle state.
          </p>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">
              Cancel
            </Button>
            <button
              className="if-button if-button-danger"
              onClick={() => {
                if (!selectedBrokerCode) {
                  return;
                }
                const selectedBroker = brokers.find((broker) => broker.broker_code === selectedBrokerCode);
                const nextStatus = selectedBroker?.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
                closeModal();
                void handleStatusUpdate(selectedBrokerCode, nextStatus);
              }}
              type="button"
            >
              Confirm
            </button>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
