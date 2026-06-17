import {
  Bot,
  CheckCircle2,
  Copy,
  MessageCircleMore,
  RotateCcw,
  Send,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { normalizeApiError } from "../../utils/apiErrors";
import { Button } from "../ui/Button";
import { chatbotApi, type ChatMessageData } from "../../services/api/chatbot";
import type { CustomerApplicationPayload } from "../../services/api/customer";

interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  text: string;
  data?: ChatMessageData;
  createdAt: string;
}

interface ChatbotQuoteAddon {
  addon_code: string;
  addon_name: string;
  addon_price: number;
}



const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface CustomerChatbotWidgetProps {
  applicationPayload: CustomerApplicationPayload | null;
  currentScreen: string;
  customerMobileNumber?: string;
  transactionReference?: string | null;
}

interface HealthQuoteFormState {
  fullName: string;
  mobileNumber: string;
  email: string;
  dateOfBirth: string;
  gender: "MALE" | "FEMALE" | "OTHER";
  addressLine1: string;
  city: string;
  state: string;
  pincode: string;
  coverageAmount: string;
  tenureYears: string;
  insuredMembers: string;
  heightCm: string;
  weightKg: string;
  smoker: boolean;
  diabetes: boolean;
  bloodPressure: boolean;
  heartAilments: boolean;
  preExistingDisease: boolean;
  otherConditions: string;
}

type QuoteFieldKey =
  | "fullName"
  | "mobileNumber"
  | "email"
  | "dateOfBirth"
  | "gender"
  | "addressLine1"
  | "city"
  | "state"
  | "pincode"
  | "coverageAmount"
  | "tenureYears"
  | "insuredMembers"
  | "heightCm"
  | "weightKg"
  | "smoker"
  | "diabetes"
  | "bloodPressure"
  | "heartAilments"
  | "preExistingDisease"
  | "otherConditions";

interface QuoteConversationField {
  keys: QuoteFieldKey[];
  question: string;
  parse: (answer: string) => { ok: true; values: Partial<HealthQuoteFormState> } | { ok: false; error: string };
}

function createSessionId() {
  return `if-chat-${crypto.randomUUID()}`;
}

function buildChatbotQuotePayload(
  payload: CustomerApplicationPayload,
): Record<string, unknown> {
  const nameParts = payload.fullName.trim().split(/\s+/);
  const firstName = nameParts[0] ?? "Customer";
  const lastName = nameParts.slice(1).join(" ") || "User";
  const calculatedBmi =
    payload.insuranceType === "HEALTH" &&
    payload.heightCm &&
    payload.heightCm > 0 &&
    payload.weightKg &&
    payload.weightKg > 0
      ? Number((payload.weightKg / ((payload.heightCm / 100) ** 2)).toFixed(2))
      : null;

  return {
    insurance_type: payload.insuranceType,
    guest_identifier: payload.guestIdentifier ?? `guest-${payload.mobileNumber}`,
    personal_details: {
      first_name: firstName,
      last_name: lastName,
      email: payload.email || `guest.${payload.mobileNumber}@insurefloww.com`,
      mobile_number: payload.mobileNumber,
      date_of_birth: payload.dateOfBirth.includes("/")
        ? payload.dateOfBirth.replace(
            /^(\d{2})\/(\d{2})\/(\d{4})$/,
            "$3-$2-$1",
          )
        : payload.dateOfBirth,
      gender: payload.gender,
      address_line_1: "Customer address line 1",
      city: "Mumbai",
      state: "Maharashtra",
      pincode: "400001",
    },
    coverage_details: {
      insurance_type: payload.insuranceType,
      coverage_amount: payload.coverageAmount,
      tenure_years: payload.tenureYears,
      relation:
        payload.insuranceType === "HEALTH" &&
        (payload.insuredMembers?.length ?? 0) > 1
          ? "FAMILY"
          : "SELF",
      insured_members:
        payload.insuranceType === "HEALTH"
          ? Math.max(payload.insuredMembers?.length ?? 1, 1)
          : 1,
      sum_insured: payload.coverageAmount,
      pan_india_cover: true,
    },
    health_details:
      payload.insuranceType === "HEALTH"
        ? {
            height_cm: payload.heightCm ?? null,
            weight_kg: payload.weightKg ?? null,
            calculated_bmi: calculatedBmi,
            smoker: payload.smoker ?? false,
            diabetes: payload.healthConditions.includes("Diabetes"),
            blood_pressure: payload.healthConditions.includes("Hypertension"),
            heart_ailments: payload.healthConditions.includes("Cardiac History"),
            pre_existing_disease: payload.healthConditions.length > 0,
            other_conditions: payload.healthConditions,
          }
        : null,
    idempotency_key: crypto.randomUUID(),
  };
}

function currency(value: number | string | undefined) {
  const numericValue = Number(value ?? 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(numericValue);
}

function splitName(fullName: string) {
  const parts = fullName.trim().split(/\s+/);
  return {
    firstName: parts[0] ?? "Customer",
    lastName: parts.slice(1).join(" ") || "User",
  };
}

function createDefaultQuoteForm(mobileNumber = ""): HealthQuoteFormState {
  return {
    fullName: "",
    mobileNumber,
    email: "",
    dateOfBirth: "",
    gender: "MALE",
    addressLine1: "",
    city: "",
    state: "",
    pincode: "",
    coverageAmount: "1000000",
    tenureYears: "1",
    insuredMembers: "1",
    heightCm: "",
    weightKg: "",
    smoker: false,
    diabetes: false,
    bloodPressure: false,
    heartAilments: false,
    preExistingDisease: false,
    otherConditions: "",
  };
}

function normalizeDateOfBirth(dateOfBirth: string) {
  const trimmed = dateOfBirth.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return trimmed;
  }

  return trimmed.replace(/^(\d{2})\/(\d{2})\/(\d{4})$/, "$3-$2-$1");
}

function buildChatbotHealthQuotePayloadFromForm(
  form: HealthQuoteFormState,
  sessionId: string,
): Record<string, unknown> {
  const { firstName, lastName } = splitName(form.fullName);
  const heightCm = form.heightCm ? Number(form.heightCm) : null;
  const weightKg = form.weightKg ? Number(form.weightKg) : null;
  const calculatedBmi =
    heightCm && heightCm > 0 && weightKg && weightKg > 0
      ? Number((weightKg / ((heightCm / 100) ** 2)).toFixed(2))
      : null;
  const otherConditions = form.otherConditions
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return {
    insurance_type: "HEALTH",
    guest_identifier: `guest-${form.mobileNumber || sessionId}`,
    personal_details: {
      first_name: firstName,
      last_name: lastName,
      email: form.email,
      mobile_number: form.mobileNumber,
      date_of_birth: normalizeDateOfBirth(form.dateOfBirth),
      gender: form.gender,
      address_line_1: form.addressLine1,
      city: form.city,
      state: form.state,
      pincode: form.pincode,
      politically_exposed_person: false,
    },
    coverage_details: {
      insurance_type: "HEALTH",
      coverage_amount: Number(form.coverageAmount),
      tenure_years: Number(form.tenureYears),
      relation: Number(form.insuredMembers) > 1 ? "FAMILY" : "SELF",
      insured_members: Number(form.insuredMembers),
      sum_insured: Number(form.coverageAmount),
      pan_india_cover: true,
    },
    health_details: {
      height_cm: heightCm,
      weight_kg: weightKg,
      calculated_bmi: calculatedBmi,
      smoker: form.smoker,
      diabetes: form.diabetes,
      blood_pressure: form.bloodPressure,
      heart_ailments: form.heartAilments,
      pre_existing_disease: form.preExistingDisease,
      other_conditions: otherConditions,
    },
    idempotency_key: crypto.randomUUID(),
  };
}

function parseYesNo(answer: string, label: string) {
  const normalized = answer.trim().toLowerCase();
  if (["yes", "y"].includes(normalized)) {
    return { ok: true as const, value: true };
  }
  if (["no", "n"].includes(normalized)) {
    return { ok: true as const, value: false };
  }
  return {
    ok: false as const,
    error: `Please answer ${label} with yes or no.`,
  };
}

function parseCoverageAmount(answer: string) {
  const normalized = answer.trim().toLowerCase().replace(/\s+/g, "");
  const map: Record<string, string> = {
    "5l": "500000",
    "5lac": "500000",
    "5lakh": "500000",
    "500000": "500000",
    "10l": "1000000",
    "10lac": "1000000",
    "10lakh": "1000000",
    "1000000": "1000000",
    "25l": "2500000",
    "25lac": "2500000",
    "25lakh": "2500000",
    "2500000": "2500000",
    "50l": "5000000",
    "50lac": "5000000",
    "50lakh": "5000000",
    "5000000": "5000000",
    "1cr": "10000000",
    "1crore": "10000000",
    "10000000": "10000000",
  };
  const value = map[normalized];
  if (!value) {
    return {
      ok: false as const,
      error: "Choose coverage like 5L, 10L, 25L, 50L, or 1Cr.",
    };
  }
  return { ok: true as const, value };
}

const QUOTE_CONVERSATION_FIELDS: QuoteConversationField[] = [
  {
    keys: ["fullName", "mobileNumber"],
    question: "Sure! Please tell me your full name and mobile number.",
    parse: (answer) => {
      const mobileRegex = /\b\d{10,15}\b/;
      const match = answer.match(mobileRegex);
      if (!match) {
        return { ok: false, error: "Please make sure to include a valid 10-15 digit mobile number." };
      }
      const mobileNumber = match[0];
      const fullName = answer
        .replace(mobileNumber, "")
        .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "")
        .replace(/\s+/g, " ")
        .trim();
      if (fullName.length < 2) {
        return { ok: false, error: "Please make sure to include your full name (at least 2 characters)." };
      }
      return { ok: true, values: { fullName, mobileNumber } };
    },
  },
  {
    keys: ["email", "dateOfBirth"],
    question: "What is your email address and date of birth? (e.g. alex@example.com, 02/11/1999)",
    parse: (answer) => {
      const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
      const dobRegex = /\b(?:\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2})\b/;
      const emailMatch = answer.match(emailRegex);
      const dobMatch = answer.match(dobRegex);
      if (!emailMatch) {
        return { ok: false, error: "Please enter a valid email address." };
      }
      if (!dobMatch) {
        return { ok: false, error: "Please enter DOB as DD/MM/YYYY or YYYY-MM-DD." };
      }
      return {
        ok: true,
        values: { email: emailMatch[0].trim(), dateOfBirth: dobMatch[0].trim() },
      };
    },
  },
  {
    keys: ["gender", "addressLine1"],
    question: "What is your gender (Male/Female/Other) and your address?",
    parse: (answer) => {
      const lower = answer.toLowerCase();
      let gender: "MALE" | "FEMALE" | "OTHER" | null = null;
      let genderWord = "";
      if (/\bmale\b/.test(lower)) {
        gender = "MALE";
        genderWord = "male";
      } else if (/\bfemale\b/.test(lower)) {
        gender = "FEMALE";
        genderWord = "female";
      } else if (/\bother\b/.test(lower)) {
        gender = "OTHER";
        genderWord = "other";
      }
      if (!gender) {
        return { ok: false, error: "Please specify your gender as Male, Female, or Other." };
      }
      const addressLine1 = answer
        .replace(new RegExp(`\\b${genderWord}\\b`, "i"), "")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/^[,.\s\-]+|[,.\s\-]+$/g, "");
      if (addressLine1.length < 3) {
        return { ok: false, error: "Please enter your address line 1." };
      }
      return { ok: true, values: { gender, addressLine1 } };
    },
  },
  {
    keys: ["city", "state"],
    question: "Which city and state do you live in? (e.g. Mumbai, Maharashtra)",
    parse: (answer) => {
      const parts = answer
        .split(/,|\band\b/i)
        .map((s) => s.trim())
        .filter(Boolean);
      if (parts.length < 2) {
        const spaceParts = answer.split(/\s+/).map((s) => s.trim()).filter(Boolean);
        if (spaceParts.length >= 2) {
          return { ok: true, values: { city: spaceParts[0], state: spaceParts.slice(1).join(" ") } };
        }
        return { ok: false, error: "Please specify both your city and state, separated by a comma." };
      }
      return { ok: true, values: { city: parts[0], state: parts[1] } };
    },
  },
  {
    keys: ["pincode", "coverageAmount"],
    question: "Please enter your pincode and the coverage amount you need (5L, 10L, 25L, 50L, or 1Cr).",
    parse: (answer) => {
      const pincodeRegex = /\b\d{4,10}\b/;
      const pinMatch = answer.match(pincodeRegex);
      if (!pinMatch) {
        return { ok: false, error: "Please enter a valid pincode." };
      }
      const pincode = pinMatch[0];
      const remaining = answer.replace(pincode, "");
      const parsedCov = parseCoverageAmount(remaining);
      if (!parsedCov.ok) {
        return { ok: false, error: parsedCov.error };
      }
      return { ok: true, values: { pincode, coverageAmount: parsedCov.value } };
    },
  },
  {
    keys: ["tenureYears", "insuredMembers"],
    question: "What tenure do you want (1, 2, or 3 years) and how many members should I include? (1 to 5)",
    parse: (answer) => {
      const numbers = answer.match(/\b[1-5]\b/g);
      if (!numbers || numbers.length < 2) {
        return {
          ok: false,
          error: "Please enter numbers for both tenure (1-3) and insured members (1-5).",
        };
      }
      const tenure = numbers[0];
      const members = numbers[1];
      if (!["1", "2", "3"].includes(tenure)) {
        return { ok: false, error: "Tenure must be 1, 2, or 3 years." };
      }
      return { ok: true, values: { tenureYears: tenure, insuredMembers: members } };
    },
  },
  {
    keys: ["heightCm", "weightKg"],
    question: "What is your height in centimeters and weight in kilograms? (e.g. 175 cm, 70 kg)",
    parse: (answer) => {
      const numbers = answer.match(/\b\d+\b/g);
      if (!numbers || numbers.length < 2) {
        return { ok: false, error: "Please provide both height (in cm) and weight (in kg)." };
      }
      const h = Number(numbers[0]);
      const w = Number(numbers[1]);
      if (h < 50 || h > 250) {
        return { ok: false, error: "Please enter a valid height (50 to 250 cm)." };
      }
      if (w < 10 || w > 300) {
        return { ok: false, error: "Please enter a valid weight (10 to 300 kg)." };
      }
      return { ok: true, values: { heightCm: String(h), weightKg: String(w) } };
    },
  },
  {
    keys: ["smoker", "diabetes"],
    question: "Are you a smoker (yes/no), and do you have diabetes? (yes/no)",
    parse: (answer) => {
      const words = answer.toLowerCase().match(/\b(yes|no|y|n)\b/g);
      if (!words || words.length < 2) {
        return { ok: false, error: "Please answer yes or no for both questions." };
      }
      return {
        ok: true,
        values: {
          smoker: ["yes", "y"].includes(words[0]),
          diabetes: ["yes", "y"].includes(words[1]),
        },
      };
    },
  },
  {
    keys: ["bloodPressure", "heartAilments"],
    question: "Do you have any blood pressure history (yes/no), and do you have any heart ailments? (yes/no)",
    parse: (answer) => {
      const words = answer.toLowerCase().match(/\b(yes|no|y|n)\b/g);
      if (!words || words.length < 2) {
        return { ok: false, error: "Please answer yes or no for both questions." };
      }
      return {
        ok: true,
        values: {
          bloodPressure: ["yes", "y"].includes(words[0]),
          heartAilments: ["yes", "y"].includes(words[1]),
        },
      };
    },
  },
  {
    keys: ["preExistingDisease", "otherConditions"],
    question: "Do you have any pre-existing disease (yes/no)? If yes, list other conditions (or type none).",
    parse: (answer) => {
      const words = answer.toLowerCase().match(/\b(yes|no|y|n)\b/);
      const preExistingDisease = words ? ["yes", "y"].includes(words[0]) : false;
      const otherConditions = ["none", "no", "nil", "na"].includes(answer.trim().toLowerCase())
        ? ""
        : answer.trim();
      return { ok: true, values: { preExistingDisease, otherConditions } };
    },
  },
];

export function CustomerChatbotWidget({
  applicationPayload,
  currentScreen,
  customerMobileNumber = "",
  transactionReference,
}: CustomerChatbotWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionId, setSessionId] = useState(() => createSessionId());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draftMessage, setDraftMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [mobileNumber, setMobileNumber] = useState(customerMobileNumber);
  const [otpCode, setOtpCode] = useState("");
  const [ticketCategory, setTicketCategory] = useState("POLICY");
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketMessage, setTicketMessage] = useState("");
  const [copiedPath, setCopiedPath] = useState("");
  const [selectedQuoteAddons, setSelectedQuoteAddons] = useState<string[]>([]);
  const [quoteForm, setQuoteForm] = useState<HealthQuoteFormState>(() =>
    createDefaultQuoteForm(customerMobileNumber),
  );
  const [isCollectingQuote, setIsCollectingQuote] = useState(false);
  const [quoteFieldIndex, setQuoteFieldIndex] = useState(0);
  const messagesViewportRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!customerMobileNumber) {
      return;
    }
    setMobileNumber((current) => current || customerMobileNumber);
    setQuoteForm((current) => ({
      ...current,
      mobileNumber: current.mobileNumber || customerMobileNumber,
    }));
  }, [customerMobileNumber]);

  const resetChat = () => {
    setMessages([]);
    setError("");
    setDraftMessage("");
    setOtpCode("");
    setCopiedPath("");
    setSelectedQuoteAddons([]);
    setTicketCategory("POLICY");
    setTicketSubject("");
    setTicketMessage("");
    setIsCollectingQuote(false);
    setQuoteFieldIndex(0);
    setMobileNumber(customerMobileNumber);
    setQuoteForm(createDefaultQuoteForm(customerMobileNumber));
    setSessionId(createSessionId());
  };

  const latestAssistantMessage = useMemo(
    () => [...messages].reverse().find((message) => message.role === "assistant"),
    [messages],
  );

  useEffect(() => {
    if (!messagesViewportRef.current) {
      return;
    }
    messagesViewportRef.current.scrollTop = messagesViewportRef.current.scrollHeight;
  }, [messages, latestAssistantMessage?.data?.ui_action]);

  useEffect(() => {
    if (latestAssistantMessage?.data?.ui_action !== "SHOW_SELECTED_QUOTE") {
      return;
    }

    const payload = latestAssistantMessage.data.payload;
    if (Array.isArray(payload.selected_addons)) {
      const selectedAddons = payload.selected_addons
        .map((item) => String(item))
        .filter(Boolean);
      setSelectedQuoteAddons(selectedAddons);
    }
  }, [latestAssistantMessage]);

  const appendMessage = (message: ChatMessage) => {
    setMessages((current) => [...current, message]);
  };

  const appendAssistantText = (text: string) => {
    appendMessage({
      id: crypto.randomUUID(),
      role: "assistant",
      text,
      createdAt: new Date().toISOString(),
    });
  };

  const sendMessage = async ({
    message,
    intentHint,
    payload,
  }: {
    message: string;
    intentHint?: string;
    payload?: Record<string, unknown>;
  }) => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage && !intentHint) {
      return;
    }

    setError("");
    setIsSending(true);

    if (trimmedMessage) {
      appendMessage({
        id: crypto.randomUUID(),
        role: "user",
        text: trimmedMessage,
        createdAt: new Date().toISOString(),
      });
    }

    try {
      const response = await chatbotApi.sendMessage({
        session_id: sessionId,
        message: trimmedMessage,
        intent_hint: intentHint,
        payload,
        metadata: {
          channel: "user_frontend_widget",
          current_screen: currentScreen,
        },
      });

      appendMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        text: response.reply,
        data: response,
        createdAt: new Date().toISOString(),
      });

      if (response.ui_action === "COLLECT_QUOTE_DETAILS" && !isCollectingQuote) {
        setIsCollectingQuote(true);
        setQuoteFieldIndex(0);
        setQuoteForm(createDefaultQuoteForm(customerMobileNumber));
        window.setTimeout(() => {
          appendAssistantText(QUOTE_CONVERSATION_FIELDS[0].question);
        }, 0);
      }
      setDraftMessage("");
    } catch (requestError) {
      setError(normalizeApiError(requestError).message);
    } finally {
      setIsSending(false);
    }
  };

  const handleRequestOtp = async () => {
    await sendMessage({
      message: "Send OTP",
      intentHint: "REQUEST_CUSTOMER_OTP",
      payload: { mobile_number: mobileNumber },
    });
  };

  const handleVerifyOtp = async () => {
    await sendMessage({
      message: "Verify OTP",
      intentHint: "VERIFY_CUSTOMER_OTP",
      payload: {
        mobile_number: mobileNumber,
        otp_code: otpCode,
      },
    });
  };

  const handleGenerateQuoteFromCurrentJourney = async () => {
    if (!applicationPayload) {
      return;
    }

    await sendMessage({
      message: "Generate quote from my current details",
      intentHint: "GENERATE_QUOTE",
      payload: buildChatbotQuotePayload(applicationPayload),
    });
  };

  const handleGenerateQuoteFromChatForm = async (formToSubmit: HealthQuoteFormState) => {
    await sendMessage({
      message: "",
      intentHint: "GENERATE_QUOTE",
      payload: buildChatbotHealthQuotePayloadFromForm(formToSubmit, sessionId),
    });
  };

  const handleQuoteConversationReply = async (answer: string) => {
    const trimmedAnswer = answer.trim();
    if (!trimmedAnswer) {
      return;
    }

    const normalized = trimmedAnswer.toLowerCase();
    if (normalized === "cancel") {
      setIsCollectingQuote(false);
      setQuoteFieldIndex(0);
      appendAssistantText("Quote collection cancelled. You can tell me whenever you want to start again.");
      setDraftMessage("");
      return;
    }
    if (normalized === "start over" || normalized === "restart") {
      setQuoteForm(createDefaultQuoteForm(customerMobileNumber));
      setQuoteFieldIndex(0);
      appendAssistantText("No problem. Let's start again.");
      appendAssistantText(QUOTE_CONVERSATION_FIELDS[0].question);
      setDraftMessage("");
      return;
    }

    const currentField = QUOTE_CONVERSATION_FIELDS[quoteFieldIndex];
    const parsed = currentField.parse(trimmedAnswer);
    appendMessage({
      id: crypto.randomUUID(),
      role: "user",
      text: trimmedAnswer,
      createdAt: new Date().toISOString(),
    });
    setDraftMessage("");

    if (!parsed.ok) {
      appendAssistantText(`${parsed.error} ${currentField.question}`);
      return;
    }

    const nextForm = {
      ...quoteForm,
      ...parsed.values,
    } as HealthQuoteFormState;
    setQuoteForm(nextForm);

    const nextField = QUOTE_CONVERSATION_FIELDS[quoteFieldIndex + 1];
    if (nextField) {
      setQuoteFieldIndex((current) => current + 1);
      appendAssistantText(nextField.question);
      return;
    }

    setIsCollectingQuote(false);
    setQuoteFieldIndex(0);
    appendAssistantText("Thank you. I have everything I need. Let me generate your health insurance quotes.");
    await handleGenerateQuoteFromChatForm(nextForm);
  };

  const handleSubmit = async () => {
    if (isCollectingQuote) {
      await handleQuoteConversationReply(draftMessage);
      return;
    }

    await sendMessage({ message: draftMessage });
  };

  const handleSelectQuote = async (quoteId: string, addons: string[] = []) => {
    await sendMessage({
      message: `Select quote ${quoteId}`,
      intentHint: "SELECT_QUOTE",
      payload: {
        quote_id: quoteId,
        selected_addons: addons,
      },
    });
  };

  const handleInitiatePayment = async () => {
    const reference =
      latestAssistantMessage?.data?.session_state.transaction_reference ??
      transactionReference;

    await sendMessage({
      message: "Proceed to payment",
      intentHint: "INITIATE_PAYMENT",
      payload: reference
        ? {
            transaction_reference: reference,
          }
        : undefined,
    });
  };

  const handlePaymentStatus = async () => {
    const reference =
      latestAssistantMessage?.data?.session_state.transaction_reference ??
      transactionReference;

    await sendMessage({
      message: "Check payment status",
      intentHint: "GET_PAYMENT_STATUS",
      payload: reference
        ? {
            transaction_reference: reference,
          }
        : undefined,
    });
  };

  const handleCreateTicket = async () => {
    await sendMessage({
      message: "Create support ticket",
      intentHint: "CREATE_TICKET",
      payload: {
        category: ticketCategory,
        priority: "MEDIUM",
        subject: ticketSubject,
        message: ticketMessage,
      },
    });
  };

  const handleDownloadPolicy = async () => {
    const policyNumber =
      String(
        latestAssistantMessage?.data?.payload?.policy_number ??
          latestAssistantMessage?.data?.session_state.policy_number ??
          "",
      ).trim();

    await sendMessage({
      message: "Download policy",
      intentHint: "DOWNLOAD_POLICY",
      payload: {
        policy_number: policyNumber,
      },
    });
  };

  const handleCopy = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedPath(value);
      window.setTimeout(() => setCopiedPath(""), 2000);
    } catch {
      setCopiedPath("");
    }
  };


  return (
    <div className="if-chatbot-root">
      {isOpen ? (
        <section className="if-chatbot-panel" aria-label="InsureFlow assistant">
          <header className="if-chatbot-header">
            <div className="if-chatbot-header-title">
              <span className="if-chatbot-header-icon">
                <Bot size={18} />
              </span>
              <div>
                <strong>InsureFlow Assistant</strong>
              </div>
            </div>
            <button
              className="if-chatbot-close"
              onClick={() => setIsOpen(false)}
              type="button"
              aria-label="Close chatbot"
            >
              <X size={18} />
            </button>
          </header>

          {messages.length > 0 ? (
            <div className="if-chatbot-context">
              <button
                className="if-chatbot-context-button"
                onClick={resetChat}
                type="button"
              >
                <RotateCcw size={14} />
                New chat
              </button>
              {applicationPayload ? (
                <button
                  className="if-chatbot-context-button"
                  onClick={() => void handleGenerateQuoteFromCurrentJourney()}
                  type="button"
                >
                  Use page details
                </button>
              ) : null}
              {transactionReference ? (
                <button
                  className="if-chatbot-context-button"
                  onClick={() => void handlePaymentStatus()}
                  type="button"
                >
                  Check payment
                </button>
              ) : null}
            </div>
          ) : null}

          <div className="if-chatbot-messages" ref={messagesViewportRef}>
            {messages.map((message) => {
              const quoteSummary = Array.isArray(message.data?.payload?.quote_summary)
                ? (message.data?.payload?.quote_summary as Array<Record<string, unknown>>)
                : [];
              const paymentUrl = String(message.data?.payload?.payment_url ?? "").trim();
              const paymentMethods = Array.isArray(message.data?.payload?.available_payment_methods)
                ? (message.data?.payload?.available_payment_methods as string[])
                : [];
              const localFilePath = String(message.data?.payload?.local_file_path ?? "").trim();
              const availableAddons = Array.isArray(message.data?.payload?.available_addons)
                ? (message.data?.payload?.available_addons as ChatbotQuoteAddon[])
                : [];

              return (
                <article
                  key={message.id}
                  className={`if-chatbot-message if-chatbot-message-${message.role}`}
                >
                  <div className="if-chatbot-message-row">
                    {message.role === "assistant" ? (
                      <span className="if-chatbot-avatar">
                        <Bot size={14} />
                      </span>
                    ) : null}
                    <p>{message.text}</p>
                  </div>

                  {quoteSummary.length ? (
                    <div className="if-chatbot-card-stack">
                      {quoteSummary.map((quote) => (
                        <div className="if-chatbot-data-card" key={String(quote.quote_id)}>
                          <div>
                            <strong>{String(quote.provider_name)}</strong>
                            <span>{String(quote.plan_name)}</span>
                          </div>
                          <div className="if-chatbot-metric">
                            {currency(Number(quote.premium_amount ?? 0))}
                          </div>
                          <button
                            className="if-chatbot-inline-button"
                            onClick={() => void handleSelectQuote(String(quote.quote_id))}
                            type="button"
                          >
                            Select plan
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {paymentUrl ? (
                    <div className="if-chatbot-data-card">
                      <div>
                        <strong>Payment session ready</strong>
                        <span>{currency(Number(message.data?.payload?.amount ?? 0))}</span>
                      </div>
                      <div className="if-chatbot-chip-row">
                        {paymentMethods.map((method) => (
                          <span className="if-chatbot-chip" key={method}>
                            {method}
                          </span>
                        ))}
                      </div>
                      <div className="if-chatbot-inline-actions">
                        <a
                          className="if-chatbot-inline-button"
                          href={paymentUrl}
                          rel="noreferrer"
                          target="_blank"
                        >
                          Open payment page
                        </a>
                        <button
                          className="if-chatbot-inline-button is-secondary"
                          onClick={() => void handlePaymentStatus()}
                          type="button"
                        >
                          Check status
                        </button>
                      </div>
                    </div>
                  ) : null}

                  {message.data?.ui_action === "SHOW_POLICY" ? (
                    <div className="if-chatbot-data-card">
                      <div>
                        <strong>{String(message.data.payload.policy_number ?? "Policy")}</strong>
                        <span>{String(message.data.payload.policy_status ?? "UNKNOWN")}</span>
                      </div>
                      <div className="if-chatbot-chip-row">
                        <span className="if-chatbot-chip">
                          Coverage {currency(Number(message.data.payload.coverage_amount ?? 0))}
                        </span>
                        <span className="if-chatbot-chip">
                          Premium {currency(Number(message.data.payload.premium_amount ?? 0))}
                        </span>
                      </div>
                      <button
                        className="if-chatbot-inline-button"
                        onClick={() => void handleDownloadPolicy()}
                        type="button"
                      >
                        Download policy
                      </button>
                    </div>
                  ) : null}

                  {localFilePath ? (
                    <div className="if-chatbot-data-card">
                      <div>
                        <strong>{String(message.data?.payload?.file_name ?? "Policy file")}</strong>
                        <span>Saved by the chatbot service on the local machine</span>
                      </div>
                      <div className="if-chatbot-path-row">
                        <code>{localFilePath}</code>
                        <button
                          className="if-chatbot-icon-button"
                          onClick={() => void handleCopy(localFilePath)}
                          type="button"
                          aria-label="Copy file path"
                        >
                          {copiedPath === localFilePath ? <CheckCircle2 size={15} /> : <Copy size={15} />}
                        </button>
                      </div>
                    </div>
                  ) : null}

                  {message.data?.ui_action === "SHOW_PAYMENT_STATUS" ? (
                    <div className="if-chatbot-data-card">
                      <div>
                        <strong>Payment status</strong>
                        <span>{String(message.data.payload.payment_status ?? "UNKNOWN")}</span>
                      </div>
                      <div className="if-chatbot-chip-row">
                        <span className="if-chatbot-chip">
                          Transaction {String(message.data.payload.transaction_status ?? "UNKNOWN")}
                        </span>
                        {message.data.payload.payment_reference ? (
                          <span className="if-chatbot-chip">
                            Ref {String(message.data.payload.payment_reference)}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  ) : null}

                  {message.data?.ui_action === "SHOW_TICKET_CONFIRMATION" ? (
                    <div className="if-chatbot-data-card">
                      <div>
                        <strong>Ticket created</strong>
                        <span>{String(message.data.payload.ticket_reference ?? "")}</span>
                      </div>
                      <div className="if-chatbot-chip-row">
                        <span className="if-chatbot-chip">
                          {String(message.data.payload.status ?? "OPEN")}
                        </span>
                      </div>
                    </div>
                  ) : null}
                </article>
              );
            })}

            {!messages.length ? (
              <div className="if-chatbot-empty">
                <div className="if-chatbot-empty-shell">
                  <div className="if-chatbot-empty-card">
                    <strong>Welcome to InsureFlow.</strong>
                    <span>How may I help you with your insurance today?</span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>

          {latestAssistantMessage?.data?.ui_action === "REQUEST_OTP" ? (
            <div className="if-chatbot-form">
              <input
                className="if-chatbot-input"
                onChange={(event) => setMobileNumber(event.target.value)}
                placeholder="Mobile number"
                value={mobileNumber}
              />
              <Button
                className="if-chatbot-submit"
                loading={isSending}
                onClick={() => void handleRequestOtp()}
              >
                Send OTP
              </Button>
            </div>
          ) : null}

          {latestAssistantMessage?.data?.ui_action === "VERIFY_OTP" ? (
            <div className="if-chatbot-form if-chatbot-form-stack">
              <input
                className="if-chatbot-input"
                onChange={(event) => setMobileNumber(event.target.value)}
                placeholder="Mobile number"
                value={mobileNumber}
              />
              <input
                className="if-chatbot-input"
                onChange={(event) => setOtpCode(event.target.value)}
                placeholder="6-digit OTP"
                value={otpCode}
              />
              <Button
                className="if-chatbot-submit"
                loading={isSending}
                onClick={() => void handleVerifyOtp()}
              >
                Verify OTP
              </Button>
            </div>
          ) : null}

          {latestAssistantMessage?.data?.ui_action === "SHOW_TICKET_FORM" ? (
            <div className="if-chatbot-form if-chatbot-form-stack">
              <select
                className="if-chatbot-input"
                onChange={(event) => setTicketCategory(event.target.value)}
                value={ticketCategory}
              >
                <option value="POLICY">Policy</option>
                <option value="PAYMENT">Payment</option>
                <option value="CLAIM">Claim</option>
                <option value="OTHER">Other</option>
              </select>
              <input
                className="if-chatbot-input"
                onChange={(event) => setTicketSubject(event.target.value)}
                placeholder="Ticket subject"
                value={ticketSubject}
              />
              <textarea
                className="if-chatbot-input if-chatbot-textarea"
                onChange={(event) => setTicketMessage(event.target.value)}
                placeholder="Describe the issue"
                value={ticketMessage}
              />
              <Button
                className="if-chatbot-submit"
                loading={isSending}
                onClick={() => void handleCreateTicket()}
              >
                Create ticket
              </Button>
            </div>
          ) : null}

          {latestAssistantMessage?.data?.ui_action === "SHOW_SELECTED_QUOTE" ? (
            <div className="if-chatbot-footer-cta if-chatbot-footer-cta-stack">
              {(() => {
                const payload = latestAssistantMessage.data.payload;
                const quoteId = String(payload.quote_id ?? "").trim();
                const availableAddons = Array.isArray(payload.available_addons)
                  ? (payload.available_addons as ChatbotQuoteAddon[])
                  : [];
                const basePremium = Number(payload.total_premium ?? 0);
                const addonTotal = availableAddons
                  .filter((addon) => selectedQuoteAddons.includes(addon.addon_code))
                  .reduce((total, addon) => total + Number(addon.addon_price ?? 0), 0);

                return (
                  <>
                    <div className="if-chatbot-data-card if-chatbot-selected-quote-card">
                      <div>
                        <strong>{String(payload.plan_name ?? "Selected plan")}</strong>
                        <span>{String(payload.provider_name ?? "Provider")}</span>
                      </div>
                      <div className="if-chatbot-chip-row">
                        <span className="if-chatbot-chip">
                          Coverage {currency(Number(payload.coverage_amount ?? 0))}
                        </span>
                        <span className="if-chatbot-chip">
                          Base {currency(basePremium)}
                        </span>
                        <span className="if-chatbot-chip">
                          Add-ons {currency(addonTotal)}
                        </span>
                        <span className="if-chatbot-chip">
                          Total {currency(basePremium + addonTotal)}
                        </span>
                      </div>

                      {availableAddons.length ? (
                        <div className="if-chatbot-addon-section">
                          <div className="if-chatbot-addon-heading">
                            Available add-ons
                          </div>
                          <div className="if-chatbot-addon-list">
                            {availableAddons.map((addon) => {
                              const checked = selectedQuoteAddons.includes(addon.addon_code);
                              return (
                                <label
                                  className={`if-chatbot-addon-row${checked ? " is-active" : ""}`}
                                  key={addon.addon_code}
                                >
                                  <span className="if-chatbot-addon-copy">
                                    <strong>{addon.addon_name}</strong>
                                    <span>{addon.addon_code}</span>
                                  </span>
                                  <span className="if-chatbot-addon-action">
                                    <span className="if-chatbot-addon-price">
                                      +{currency(addon.addon_price)}
                                    </span>
                                    <input
                                      checked={checked}
                                      onChange={() => {
                                        setSelectedQuoteAddons((current) =>
                                          checked
                                            ? current.filter((item) => item !== addon.addon_code)
                                            : [...current, addon.addon_code],
                                        );
                                      }}
                                      type="checkbox"
                                    />
                                  </span>
                                </label>
                              );
                            })}
                          </div>
                          <div className="if-chatbot-inline-actions">
                            <button
                              className="if-chatbot-inline-button is-secondary"
                              onClick={() => void handleSelectQuote(quoteId, selectedQuoteAddons)}
                              type="button"
                            >
                              Apply add-ons
                            </button>
                          </div>
                        </div>
                      ) : null}
                    </div>

                    <Button
                      className="if-chatbot-submit"
                      loading={isSending}
                      onClick={() => void handleInitiatePayment()}
                    >
                      Proceed to payment
                    </Button>
                  </>
                );
              })()}
            </div>
          ) : null}

          {error ? <div className="if-chatbot-error">{error}</div> : null}

          <footer className="if-chatbot-composer">
            <input
              className="if-chatbot-input"
              onChange={(event) => setDraftMessage(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void handleSubmit();
                }
              }}
              placeholder="Ask about quotes, payment, policies, or support"
              value={draftMessage}
            />
            <button
              className="if-chatbot-send"
              onClick={() => void handleSubmit()}
              type="button"
              aria-label="Send chat message"
              disabled={isSending}
            >
              <Send size={16} />
            </button>
          </footer>
        </section>
      ) : null}

      <button
        className="if-chatbot-trigger"
        onClick={() => setIsOpen((current) => !current)}
        type="button"
        aria-label={isOpen ? "Close assistant" : "Open assistant"}
      >
        <MessageCircleMore size={20} />
        <span>Chat with InsureFlow</span>
      </button>
    </div>
  );
}
