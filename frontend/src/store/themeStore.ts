type Theme = "light" | "dark";
type ThemeListener = (theme: Theme) => void;

let currentTheme: Theme = "light";

if (typeof window !== "undefined") {
  currentTheme = (localStorage.getItem("if-theme") as Theme) || "light";
}

const listeners = new Set<ThemeListener>();

function emit() {
  listeners.forEach((listener) => listener(currentTheme));
}

/**
 * themeStore manages the active light/dark theme mode,
 * syncing it to localStorage and setting the root document attribute.
 */
export const themeStore = {
  getTheme(): Theme {
    return currentTheme;
  },
  subscribe(listener: ThemeListener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  setTheme(theme: Theme) {
    currentTheme = theme;
    if (typeof window !== "undefined") {
      localStorage.setItem("if-theme", theme);
    }
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", theme);
    }
    emit();
  },
  toggleTheme() {
    this.setTheme(currentTheme === "light" ? "dark" : "light");
  },
};

// Immediately apply theme state on module load
if (typeof document !== "undefined") {
  document.documentElement.setAttribute("data-theme", currentTheme);
}
