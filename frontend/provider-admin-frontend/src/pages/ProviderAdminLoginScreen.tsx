import { useState } from "react";

import { Button } from "../components/ui/Button";
import { PasswordField } from "../components/ui/PasswordField";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TextInput } from "../components/ui/TextInput";
import { useAsyncAction } from "../hooks/useAsyncAction";
import { providerAdminApi } from "../services/api/providerAdmin";
import { authStore } from "../store/authStore";
import { normalizeApiError } from "../utils/apiErrors";

export function ProviderAdminLoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const signInAction = useAsyncAction();

  const handleLogin = async () => {
    await signInAction.run(async () => {
      try {
        const payload = await providerAdminApi.login(email, password);
        authStore.setToken(payload.access_token);
        setErrorMessage("");
      } catch (error) {
        setErrorMessage(normalizeApiError(error).message);
      }
    });
  };

  return (
    <div className="if-admin-auth-shell">
      <div className="if-admin-auth-card">
        <div
          className="if-admin-auth-brand"
          style={{ fontSize: "22px", margin: "0 auto var(--space-2)", textAlign: "center" }}
        >
          InsureFlow
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "var(--space-6)" }}>
          <StatusBadge status="admin">Provider Admin</StatusBadge>
        </div>
        <h2
          style={{
            fontSize: "22px",
            color: "var(--if-text-1)",
            textAlign: "center",
            marginBottom: "var(--space-6)",
            marginTop: 0,
          }}
        >
          Sign in to provider console
        </h2>
        <div className="if-form-stack">
          <TextInput
            label="Email"
            onChange={(event) => {
              setEmail(event.target.value);
              if (errorMessage) setErrorMessage("");
            }}
            placeholder="Enter provider admin email"
            type="email"
            value={email}
          />
          <PasswordField
            label="Password"
            onChange={(event) => {
              setPassword(event.target.value);
              if (errorMessage) setErrorMessage("");
            }}
            placeholder="Enter password"
            value={password}
          />
          {errorMessage ? (
            <span className="if-error-text" style={{ marginTop: "4px", display: "block" }}>
              {errorMessage}
            </span>
          ) : null}
          <Button
            className="if-button-full"
            loading={signInAction.isLoading}
            onClick={() => void handleLogin()}
          >
            Sign in
          </Button>
        </div>
      </div>
    </div>
  );
}
