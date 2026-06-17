import { buildApiError } from "../../utils/apiErrors";
import { CHATBOT_API_BASE_URL } from "./config";
import type { ApiFailureResponse, ApiResponse } from "./types";

export interface ChatSessionSnapshot {
  session_id: string;
  authenticated: boolean;
  current_flow: string;
  insurance_type?: string | null;
  application_reference?: string | null;
  transaction_reference?: string | null;
  selected_quote_id?: string | null;
  policy_number?: string | null;
}

export interface ChatMessageData {
  reply: string;
  intent: string;
  ui_action: string;
  payload: Record<string, unknown>;
  missing_fields: string[];
  suggested_replies: string[];
  session_state: ChatSessionSnapshot;
}

export interface ChatMessageRequest {
  session_id: string;
  message: string;
  intent_hint?: string;
  payload?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

async function chatbotRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${CHATBOT_API_BASE_URL}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
    });
  } catch {
    throw buildApiError(
      503,
      "Unable to reach the chatbot service. Please make sure the chat bot is running.",
      [{ type: "network_error", detail: "Chatbot service is unreachable." }],
    );
  }

  const payload = (await response.json()) as ApiResponse<T> | ApiFailureResponse;

  if (!response.ok || !payload.success) {
    const message = payload.message ?? "Chatbot request failed.";
    const errors = "errors" in payload ? payload.errors : [];
    throw buildApiError(response.status, message, errors);
  }

  return payload.data;
}

export const chatbotApi = {
  sendMessage(request: ChatMessageRequest) {
    return chatbotRequest<ChatMessageData>("/chat/message", {
      method: "POST",
      body: JSON.stringify({
        session_id: request.session_id,
        message: request.message,
        intent_hint: request.intent_hint,
        payload: request.payload ?? {},
        metadata: request.metadata ?? {},
      }),
    });
  },
};
