import { Check, Copy, KeyRound } from "lucide-react";
import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { TextInput } from "../../components/ui/TextInput";
import { StatusBadge } from "../../components/ui/StatusBadge";

type BrokerModalState =
  | "closed"
  | "register"
  | "registerKey"
  | "deactivateConfirm"
  | "rotateConfirm"
  | "rotateKey";

/**
 * BrokerManagementScreen covers broker registration and key rotation.
 * It keeps destructive actions behind confirmations and never shows full keys by default.
 */
export function BrokerManagementScreen() {
  const [modalState, setModalState] = useState<BrokerModalState>("closed");
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
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

      <section className="if-surface-card">
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
              <tr>
                <td className="if-mono">MAINAPP</td>
                <td>InsureFlow Main App</td>
                <td>
                  <StatusBadge status="issued">Active</StatusBadge>
                </td>
                <td>10 Jun 2026</td>
                <td>12 Jun 2026</td>
                <td>
                  <div className="if-table-action-row">
                    <Button onClick={() => setModalState("rotateConfirm")} variant="ghost">
                      Rotate Key
                    </Button>
                    <button
                      className="if-link-button if-link-button-danger"
                      onClick={() => setModalState("deactivateConfirm")}
                      type="button"
                    >
                      Deactivate
                    </button>
                  </div>
                </td>
              </tr>
              <tr>
                <td className="if-mono">BROKX</td>
                <td>Broker X Partners</td>
                <td>
                  <StatusBadge status="cancelled">Inactive</StatusBadge>
                </td>
                <td>08 Jun 2026</td>
                <td>09 Jun 2026</td>
                <td>
                  <div className="if-table-action-row">
                    <Button variant="ghost">Rotate Key</Button>
                    <button className="if-link-button if-link-button-danger" type="button">
                      Deactivate
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {modalState === "register" ? (
        <Modal title="Register new broker" width="wide">
          <div className="if-form-stack">
            <TextInput label="Broker Name" placeholder="Broker X Partners" />
            <TextInput label="Broker Code" mono placeholder="BROKERX" />
            <TextInput label="Callback URL" placeholder="https://broker.example.com/callback" />
            <TextInput label="Webhook URL" placeholder="https://broker.example.com/webhook" />
          </div>
          <div className="if-modal-footer">
            <Button onClick={() => setModalState("closed")} variant="ghost">
              Cancel
            </Button>
            <Button onClick={() => setModalState("registerKey")}>Register</Button>
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
              <div className="if-key-text if-mono">brk_live_****************</div>
              <Button iconOnly onClick={handleCopy} variant="ghost">
                {copied ? <Check size={18} /> : <Copy size={18} />}
              </Button>
            </div>
            <div className="if-key-hint">
              <KeyRound size={16} />
              Reveal only on copy action and store securely.
            </div>
          </div>
          <div className="if-modal-footer">
            <Button onClick={() => setModalState("closed")}>Done</Button>
          </div>
        </Modal>
      ) : null}

      {modalState === "rotateConfirm" ? (
        <Modal title="Rotate API key?">
          <p className="if-inline-subtitle">
            The current key will be invalidated immediately. A new key will be generated and shown
            once.
          </p>
          <div className="if-modal-footer">
            <Button onClick={() => setModalState("closed")} variant="ghost">
              Cancel
            </Button>
            <button className="if-button if-button-danger" onClick={() => setModalState("rotateKey")} type="button">
              Rotate Key
            </button>
          </div>
        </Modal>
      ) : null}

      {modalState === "deactivateConfirm" ? (
        <Modal title="Deactivate broker?">
          <p className="if-inline-subtitle">
            The broker integration will be disabled immediately and new requests will be rejected
            until reactivated.
          </p>
          <div className="if-modal-footer">
            <Button onClick={() => setModalState("closed")} variant="ghost">
              Cancel
            </Button>
            <button className="if-button if-button-danger" onClick={() => setModalState("closed")} type="button">
              Deactivate
            </button>
          </div>
        </Modal>
      ) : null}
    </div>
  );
}
