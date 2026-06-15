type AuthMode = "customer" | "admin";

interface SessionState {
  customerToken: string | null;
  adminToken: string | null;
}

type AuthListener = (state: SessionState) => void;

const state: SessionState = {
  customerToken: null,
  adminToken: null,
};

const listeners = new Set<AuthListener>();

function emit() {
  listeners.forEach((listener) => listener({ ...state }));
}

/**
 * authStore keeps JWTs only in memory for the current browser session.
 * The backend should eventually move to httpOnly cookies for fully strict storage.
 */
export const authStore = {
  getState(): SessionState {
    return { ...state };
  },
  subscribe(listener: AuthListener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  setToken(mode: AuthMode, token: string) {
    if (mode === "customer") {
      state.customerToken = token;
    } else {
      state.adminToken = token;
    }
    emit();
  },
  clear(mode?: AuthMode) {
    if (!mode || mode === "customer") {
      state.customerToken = null;
    }
    if (!mode || mode === "admin") {
      state.adminToken = null;
    }
    emit();
  },
};
