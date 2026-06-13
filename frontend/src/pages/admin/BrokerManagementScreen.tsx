import { Check, Copy, KeyRound } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "../../components/ui/Button";
import { ErrorCard } from "../../components/ui/ErrorCard";
import { Modal } from "../../components/ui/Modal";
import { Skeleton } from "../../components/ui/Skeleton";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { TextInput } from "../../components/ui/TextInput";
import { adminApi, type BrokerSummary } from "../../services/api/admin";
import { normalizeApiError } from "../../utils/apiErrors";

type BrokerModalState =
  | "closed"
  | "register"
  | "registerKey"
  | "deactivateConfirm"
  | "rotateConfirm"
  | "rotateKey";

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
  const [formValues, setFormValues] = useState({
    brokerName: "",
    brokerCode: "",
    callbackUrl: "",
    webhookUrl: "",
  });

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
  };

  const handleCopy = () => {
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const handleRegister = async () => {
    try {
      const broker = await adminApi.createBroker({
        broker_name: formValues.brokerName,
        broker_code: formValues.brokerCode.toUpperCase(),
        callback_url: formValues.callbackUrl,
        webhook_url: formValues.webhookUrl,
      });
      setBrokers((current) => [broker, ...current]);
      setTransientApiKey(broker.api_key ?? "brk_live_****************");
      setModalState("registerKey");
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
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
    try {
      const broker = await adminApi.rotateBrokerKey(selectedBrokerCode);
      setTransientApiKey(broker.api_key ?? "brk_live_****************");
      setModalState("rotateKey");
      await loadBrokers();
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
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
          <ErrorCard message="No brokers registered yet." />
        ) : (
          <div className="if-table-wrap">
            <table className="if-data-table">
              <thead>
                <tr>
                  <th>Broker Code</th>
                  <th>Name</th>
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
                    <td>{broker.broker_name}</td>
                    <td>
                      <StatusBadge status={broker.status === "ACTIVE" ? "issued" : "cancelled"}>
                        {broker.status}
                      </StatusBadge>
                    </td>
                    <td>{broker.created_at ? new Date(broker.created_at).toLocaleDateString("en-IN") : "N/A"}</td>
                    <td>{broker.updated_at ? new Date(broker.updated_at).toLocaleDateString("en-IN") : "N/A"}</td>
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
              label="Callback URL"
              onChange={(event) => setFormValues((current) => ({ ...current, callbackUrl: event.target.value }))}
              placeholder="https://broker.example.com/callback"
              value={formValues.callbackUrl}
            />
            <TextInput
              label="Webhook URL"
              onChange={(event) => setFormValues((current) => ({ ...current, webhookUrl: event.target.value }))}
              placeholder="https://broker.example.com/webhook"
              value={formValues.webhookUrl}
            />
          </div>
          <div className="if-modal-footer">
            <Button onClick={closeModal} variant="ghost">
              Cancel
            </Button>
            <Button onClick={() => void handleRegister()}>Register</Button>
          </div>
        </Modal>
      ) : null}

      {modalState === "registerKey" || modalState === "rotateKey" ? (
        <Modal width="wide">
          <div className="if-warning-banner">
            Save this API key now. It will not be shown again.
          </div>
          <div className="if-key-reveal-card">
            <div className="if-key-row">
              <div className="if-key-text if-mono">{transientApiKey ?? "brk_live_****************"}</div>
              <Button iconOnly onClick={handleCopy} variant="ghost">
                {copied ? <Check size={18} /> : <Copy size={18} />}
              </Button>
            </div>
            <div className="if-key-hint">
              <KeyRound size={16} />
              This key is not cached after the modal is closed.
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
            <button className="if-button if-button-danger" onClick={() => void handleRotateKey()} type="button">
              Rotate Key
            </button>
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
