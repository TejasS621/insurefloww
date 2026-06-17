import type { ReactNode } from "react";

interface ModalProps {
  title?: string;
  children: ReactNode;
  width?: "default" | "wide";
}

/**
 * Modal provides the shared overlay surface for confirmations and broker flows.
 * Admin actions like registration and key rotation mount their content inside it.
 */
export function Modal({ title, children, width = "default" }: ModalProps) {
  return (
    <div className="if-overlay">
      <div className={`if-modal-card ${width === "wide" ? "if-modal-card-wide" : ""}`}>
        {title ? <h2 className="if-modal-title">{title}</h2> : null}
        {children}
      </div>
    </div>
  );
}
