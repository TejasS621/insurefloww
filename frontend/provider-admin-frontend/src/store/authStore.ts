interface SessionState {
  providerAdminToken: string | null;
}

type AuthListener = (state: SessionState) => void;

const state: SessionState = {
  providerAdminToken: null,
};

const listeners = new Set<AuthListener>();

function emit() {
  listeners.forEach((listener) => listener({ ...state }));
}

export const authStore = {
  getState(): SessionState {
    return { ...state };
  },
  subscribe(listener: AuthListener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  setToken(token: string) {
    state.providerAdminToken = token;
    emit();
  },
  clear() {
    state.providerAdminToken = null;
    emit();
  },
};
