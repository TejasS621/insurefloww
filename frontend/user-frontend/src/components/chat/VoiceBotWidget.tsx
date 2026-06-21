import {
  Bot,
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

// ─── Voice session state machine ─────────────────────────────────────────────

type VoiceStatus =
  | "idle"
  | "requesting-mic"
  | "mic-denied"
  | "connecting"
  | "connected"
  | "listening"
  | "bot-speaking"
  | "error"
  | "disconnected";

interface TranscriptLine {
  id: string;
  role: "user" | "assistant";
  text: string;
}

interface VoiceBotWidgetProps {
  /** Voice bot backend base URL (SmallWebRTC Pipecat runner). */
  voiceBotUrl?: string;
  /** Current customer screen for launcher placement adjustments. */
  currentScreen?: string;
  /** If the user has context from the chatbot (e.g., mobile), pass it here. */
  customerMobileNumber?: string;
  /** Notifies the parent when the voice panel opens or closes. */
  onOpenChange?: (isOpen: boolean) => void;
  /** Controls whether the closed launcher should be visible. */
  showLauncher?: boolean;
  /** Hides the launcher when another assistant is active. */
  suppressLauncher?: boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const VOICE_BOT_BASE = "http://localhost:7860";
const WS_OFFER_PATH = "/api/offer"; // Pipecat SmallWebRTC offer endpoint

const STATUS_LABELS: Record<VoiceStatus, string> = {
  idle: "Ready",
  "requesting-mic": "Requesting microphone…",
  "mic-denied": "Microphone denied",
  connecting: "Connecting…",
  connected: "Connected",
  listening: "Listening…",
  "bot-speaking": "Speaking…",
  error: "Connection error",
  disconnected: "Disconnected",
};

const STATUS_COLORS: Record<VoiceStatus, string> = {
  idle: "var(--if-text-2)",
  "requesting-mic": "var(--if-warning)",
  "mic-denied": "var(--if-danger)",
  connecting: "var(--if-cyan)",
  connected: "var(--if-success)",
  listening: "var(--if-violet)",
  "bot-speaking": "var(--if-cyan)",
  error: "var(--if-danger)",
  disconnected: "var(--if-text-2)",
};

// ─── Component ────────────────────────────────────────────────────────────────

export function VoiceBotWidget({
  voiceBotUrl = VOICE_BOT_BASE,
  currentScreen = "",
  customerMobileNumber = "",
  onOpenChange,
  showLauncher = true,
  suppressLauncher = false,
}: VoiceBotWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeakerMuted, setIsSpeakerMuted] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [orbPulse, setOrbPulse] = useState<"idle" | "user" | "bot">("idle");

  useEffect(() => {
    onOpenChange?.(isOpen);
  }, [isOpen, onOpenChange]);

  // WebRTC refs
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const audioOutputRef = useRef<HTMLAudioElement | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const orbAnimRef = useRef<number | null>(null);

  // ── Audio analyser for orb animation ──────────────────────────────────────
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  const startOrbAnimation = useCallback((stream: MediaStream) => {
    try {
      const ctx = new AudioContext();
      audioCtxRef.current = ctx;
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      src.connect(analyser);
      analyserRef.current = analyser;

      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        const avg = data.reduce((s, v) => s + v, 0) / data.length;
        setOrbPulse(avg > 12 ? "user" : "idle");
        orbAnimRef.current = requestAnimationFrame(tick);
      };
      orbAnimRef.current = requestAnimationFrame(tick);
    } catch {
      // non-fatal – orb just won't react to mic input
    }
  }, []);

  const stopOrbAnimation = useCallback(() => {
    if (orbAnimRef.current != null) {
      cancelAnimationFrame(orbAnimRef.current);
      orbAnimRef.current = null;
    }
    analyserRef.current?.disconnect();
    analyserRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    setOrbPulse("idle");
  }, []);

  // ── Tear-down helper ──────────────────────────────────────────────────────
  const teardown = useCallback(() => {
    stopOrbAnimation();
    dataChannelRef.current?.close();
    dataChannelRef.current = null;
    pcRef.current?.close();
    pcRef.current = null;
    localStreamRef.current?.getTracks().forEach((t) => t.stop());
    localStreamRef.current = null;
    if (audioOutputRef.current) {
      audioOutputRef.current.srcObject = null;
    }
  }, [stopOrbAnimation]);

  // ── Append transcript line ────────────────────────────────────────────────
  const appendTranscript = useCallback((role: "user" | "assistant", text: string) => {
    setTranscript((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role, text },
    ]);
  }, []);

  // ── Connect to Pipecat SmallWebRTC ────────────────────────────────────────
  const connect = useCallback(async () => {
    setErrorMessage("");
    setStatus("requesting-mic");

    // 1. Acquire mic
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    } catch {
      setStatus("mic-denied");
      setErrorMessage(
        "Microphone access was denied. Please allow microphone access in your browser settings and try again.",
      );
      return;
    }
    localStreamRef.current = stream;
    startOrbAnimation(stream);

    setStatus("connecting");

    // 2. Create peer connection
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });
    pcRef.current = pc;

    // 3. Add mic track
    stream.getAudioTracks().forEach((track) => {
      pc.addTrack(track, stream);
    });

    // 4. Handle incoming audio (bot speaking)
    const remoteStream = new MediaStream();
    pc.ontrack = (event) => {
      event.streams[0]?.getTracks().forEach((track) => {
        remoteStream.addTrack(track);
      });
      if (audioOutputRef.current) {
        audioOutputRef.current.srcObject = remoteStream;
        if (!isSpeakerMuted) {
          audioOutputRef.current.play().catch(() => {});
        }
      }
    };

    // 5. Data channel for RTVI events (transcript, VAD, bot speaking)
    const dc = pc.createDataChannel("pipecat-audio", { ordered: true });
    dataChannelRef.current = dc;
    dc.onopen = () => {
      setStatus("connected");
      setTimeout(() => setStatus("listening"), 600);
    };
    dc.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string) as {
          type?: string;
          data?: { text?: string; timestamp?: number };
        };
        if (msg.type === "transcription-user" && msg.data?.text) {
          appendTranscript("user", msg.data.text);
          setOrbPulse("user");
          setStatus("listening");
        } else if (msg.type === "transcription-bot" && msg.data?.text) {
          appendTranscript("assistant", msg.data.text);
          setOrbPulse("bot");
          setStatus("bot-speaking");
        } else if (msg.type === "bot-speaking-start") {
          setOrbPulse("bot");
          setStatus("bot-speaking");
        } else if (msg.type === "bot-speaking-stop") {
          setOrbPulse("idle");
          setStatus("listening");
        } else if (msg.type === "user-speaking-start") {
          setOrbPulse("user");
          setStatus("listening");
        } else if (msg.type === "user-speaking-stop") {
          setOrbPulse("idle");
        }
      } catch {
        // non-JSON message — ignore
      }
    };
    dc.onerror = () => {
      setStatus("error");
      setErrorMessage("Data channel error. The voice session may have dropped.");
    };

    pc.onconnectionstatechange = () => {
      const state = pc.connectionState;
      if (state === "failed" || state === "closed") {
        setStatus("disconnected");
        teardown();
      }
    };

    // 6. ICE gathering + SDP exchange with Pipecat SmallWebRTC backend
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    // Wait for ICE gathering to complete
    await new Promise<void>((resolve) => {
      if (pc.iceGatheringState === "complete") {
        resolve();
      } else {
        const check = () => {
          if (pc.iceGatheringState === "complete") {
            pc.removeEventListener("icegatheringstatechange", check);
            resolve();
          }
        };
        pc.addEventListener("icegatheringstatechange", check);
        setTimeout(resolve, 3000); // 3 s max wait
      }
    });

    try {
      const body = {
        sdp: pc.localDescription?.sdp ?? "",
        type: pc.localDescription?.type ?? "offer",
        ...(customerMobileNumber ? { metadata: { mobile_number: customerMobileNumber } } : {}),
      };
      const resp = await fetch(`${voiceBotUrl}${WS_OFFER_PATH}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!resp.ok) {
        throw new Error(`Voice bot returned ${resp.status}`);
      }
      const answer = await resp.json() as { sdp: string; type: RTCSdpType };
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus("error");
      setErrorMessage(`Could not connect to the voice bot: ${msg}`);
      teardown();
    }
  }, [voiceBotUrl, customerMobileNumber, isSpeakerMuted, startOrbAnimation, appendTranscript, teardown]);

  // ── Disconnect ────────────────────────────────────────────────────────────
  const disconnect = useCallback(() => {
    setStatus("disconnected");
    teardown();
  }, [teardown]);

  // ── Mute mic ──────────────────────────────────────────────────────────────
  const toggleMic = useCallback(() => {
    localStreamRef.current?.getAudioTracks().forEach((t) => {
      t.enabled = isMuted; // flip current muted state
    });
    setIsMuted((m) => !m);
  }, [isMuted]);

  // ── Mute speaker ─────────────────────────────────────────────────────────
  const toggleSpeaker = useCallback(() => {
    if (audioOutputRef.current) {
      audioOutputRef.current.muted = !isSpeakerMuted;
    }
    setIsSpeakerMuted((s) => !s);
  }, [isSpeakerMuted]);

  // ── Auto-scroll transcript ────────────────────────────────────────────────
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  // ── Connect when panel opens ──────────────────────────────────────────────
  useEffect(() => {
    if (isOpen && status === "idle") {
      void connect();
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Cleanup when panel closes ─────────────────────────────────────────────
  const handleClose = useCallback(() => {
    disconnect();
    setIsOpen(false);
    setStatus("idle");
    setTranscript([]);
    setOrbPulse("idle");
    setErrorMessage("");
  }, [disconnect]);

  // ── Orb class helper ──────────────────────────────────────────────────────
  const orbClass = [
    "if-voice-orb",
    orbPulse === "user" ? "is-user-speaking" : "",
    orbPulse === "bot" ? "is-bot-speaking" : "",
    (status === "connecting" || status === "requesting-mic") ? "is-connecting" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={`if-voice-root ${currentScreen === "landing" && !isOpen ? "is-landing-launcher" : ""} ${
        !showLauncher ? "is-launcher-hidden" : ""
      }`}
    >
      {/* Hidden audio output element */}
      <audio
        ref={audioOutputRef}
        autoPlay
        style={{ display: "none" }}
        aria-hidden="true"
      />

      {isOpen ? (
        <section className="if-voice-panel" aria-label="InsureFlow voice assistant">
          {/* Header */}
          <header className="if-chatbot-header">
            <div className="if-chatbot-header-title">
              <span className="if-chatbot-header-icon">
                <Bot size={18} />
              </span>
              <div>
                <strong>InsureFlow Voice Assistant</strong>
                <span
                  className="if-voice-status-badge"
                  style={{ color: STATUS_COLORS[status] }}
                >
                  <span
                    className="if-voice-status-dot"
                    style={{ background: STATUS_COLORS[status] }}
                  />
                  {STATUS_LABELS[status]}
                </span>
              </div>
            </div>
            <button
              className="if-chatbot-close"
              onClick={handleClose}
              type="button"
              aria-label="Close voice assistant"
            >
              <X size={18} />
            </button>
          </header>

          {/* Orb visualiser */}
          <div className="if-voice-orb-stage">
            <div className={orbClass}>
              <div className="if-voice-orb-ring if-voice-orb-ring-1" />
              <div className="if-voice-orb-ring if-voice-orb-ring-2" />
              <div className="if-voice-orb-ring if-voice-orb-ring-3" />
              <div className="if-voice-orb-core">
                {orbPulse === "user" ? <Mic size={28} /> : <Bot size={28} />}
              </div>
            </div>

            {/* Error or mic-denied inline message */}
            {(status === "error" || status === "mic-denied") && errorMessage ? (
              <p className="if-voice-error-inline">{errorMessage}</p>
            ) : null}
          </div>

          {/* Live transcript */}
          {transcript.length > 0 ? (
            <div className="if-voice-transcript" aria-live="polite" aria-label="Live transcript">
              {transcript.map((line) => (
                <div
                  key={line.id}
                  className={`if-voice-transcript-line if-voice-transcript-${line.role}`}
                >
                  <span className="if-voice-transcript-label">
                    {line.role === "user" ? "You" : "InsureFlow"}
                  </span>
                  <span className="if-voice-transcript-text">{line.text}</span>
                </div>
              ))}
              <div ref={transcriptEndRef} />
            </div>
          ) : (
            <div className="if-voice-transcript-hint">
              {status === "connecting" || status === "requesting-mic"
                ? "Setting up your session…"
                : status === "connected" || status === "listening"
                  ? "Start speaking — your transcript will appear here."
                  : status === "error" || status === "mic-denied"
                    ? ""
                    : "Session ended."}
            </div>
          )}

          {/* Controls */}
          <footer className="if-voice-controls">
            {/* Mic mute */}
            <button
              className={`if-voice-control-btn${isMuted ? " is-active" : ""}`}
              onClick={toggleMic}
              type="button"
              title={isMuted ? "Unmute microphone" : "Mute microphone"}
              aria-label={isMuted ? "Unmute microphone" : "Mute microphone"}
              disabled={status === "idle" || status === "requesting-mic" || status === "mic-denied" || status === "error" || status === "disconnected"}
            >
              {isMuted ? <MicOff size={18} /> : <Mic size={18} />}
            </button>

            {/* End call */}
            <button
              className="if-voice-control-btn is-end-call"
              onClick={handleClose}
              type="button"
              title="End voice session"
              aria-label="End voice session"
            >
              <PhoneOff size={20} />
            </button>

            {/* Speaker mute */}
            <button
              className={`if-voice-control-btn${isSpeakerMuted ? " is-active" : ""}`}
              onClick={toggleSpeaker}
              type="button"
              title={isSpeakerMuted ? "Unmute speaker" : "Mute speaker"}
              aria-label={isSpeakerMuted ? "Unmute speaker" : "Mute speaker"}
              disabled={status === "idle" || status === "requesting-mic" || status === "mic-denied" || status === "error" || status === "disconnected"}
            >
              {isSpeakerMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
            </button>
          </footer>
        </section>
      ) : null}

      {/* FAB trigger */}
      {!isOpen && !suppressLauncher ? (
        <button
          className="if-voice-trigger"
          onClick={() => setIsOpen(true)}
          type="button"
          aria-label="Talk to InsureFlow"
        >
          <Phone size={20} />
          <span>Talk to InsureFlow</span>
        </button>
      ) : null}
    </div>
  );
}
