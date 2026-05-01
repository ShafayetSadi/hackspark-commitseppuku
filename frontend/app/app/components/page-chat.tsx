"use client";

import { useEffect, useRef, useState } from "react";

import {
  type ChatSession,
  SUGGESTED_PROMPTS,
} from "../data";

import { Badge, Icon } from "./primitives";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  role: ChatRole;
  content: string;
};

const FALLBACK_REPLY =
  "Sorry — I couldn't reach the assistant just now. Try again in a moment.";

export function Chat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const response = await fetch("/api/chat/sessions", { cache: "no-store" });
        if (!response.ok) return;
        const payload = (await response.json()) as {
          sessions?: Array<{
            sessionId?: string;
            session_id?: string;
            name?: string;
            title?: string;
            lastMessageAt?: string;
            updated_at?: string;
            created_at?: string;
            message_count?: number;
          }>;
        };
        const next = (payload.sessions ?? [])
          .map((s) => ({
            id: s.sessionId ?? s.session_id ?? "",
            title: s.name ?? s.title ?? "Untitled chat",
            time:
              s.lastMessageAt ??
              s.updated_at ??
              s.created_at ??
              (typeof s.message_count === "number" ? `${s.message_count} messages` : "recent"),
          }))
          .filter((s) => s.id.length > 0);
        if (next.length > 0) setSessions(next);
      } catch {
        // Keep empty sessions until service is reachable.
      }
    };
    void loadSessions();
  }, []);

  useEffect(() => {
    const node = messagesEndRef.current;
    if (node?.parentElement) {
      node.parentElement.scrollTop = node.parentElement.scrollHeight;
    }
  }, [messages, loading]);

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const userMsg: ChatMessage = { role: "user", content };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: content,
          top_k: 3,
          session_id: activeSession,
        }),
      });

      let reply = FALLBACK_REPLY;
      if (response.ok) {
        const payload = (await response.json()) as {
          sessionId?: string;
          session_id?: string;
          reply?: string;
          answer?: string;
          message?: string;
        };
        const returnedSessionId = payload.session_id ?? payload.sessionId ?? null;
        if (returnedSessionId) {
          setActiveSession(returnedSessionId);
          const title = content.slice(0, 40) + (content.length > 40 ? "…" : "");
          setSessions((prev) => {
            const existing = prev.find((s) => s.id === returnedSessionId);
            if (existing) {
              return prev.map((s) =>
                s.id === returnedSessionId ? { ...s, time: "just now" } : s,
              );
            }
            const nextSession: ChatSession = {
              id: returnedSessionId,
              title,
              time: "just now",
            };
            return [nextSession, ...prev];
          });
        }
        reply =
          payload.reply ||
          payload.answer ||
          payload.message ||
          FALLBACK_REPLY;
      }
      setMessages([
        ...newMessages,
        { role: "assistant", content: reply },
      ]);
      if (!response.ok && response.status === 401) {
        setMessages([
          ...newMessages,
          {
            role: "assistant",
            content: "You are not authenticated. Please log in again and retry.",
          },
        ]);
      }
    } catch {
      setMessages([
        ...newMessages,
        { role: "assistant", content: FALLBACK_REPLY },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const newChat = () => {
    setMessages([]);
    setActiveSession(null);
    setInput("");
  };

  const loadHistory = async (sessionId: string) => {
    setActiveSession(sessionId);
    try {
      const response = await fetch(`/api/chat/${sessionId}/history`, {
        cache: "no-store",
      });
      if (!response.ok) return;
      const payload = (await response.json()) as {
        messages?: Array<{ role?: ChatRole; content?: string; message?: string }>;
      };
      const nextMessages: ChatMessage[] = (payload.messages ?? [])
        .map((m): ChatMessage => ({
          role: m.role === "assistant" ? "assistant" : "user",
          content: m.content ?? m.message ?? "",
        }))
        .filter((m) => m.content.length > 0);
      setMessages(nextMessages);
    } catch {
      // Ignore and keep current messages.
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/chat/${sessionId}`, { method: "DELETE" });
      if (!response.ok) return;
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSession === sessionId) {
        setActiveSession(null);
        setMessages([]);
      }
    } catch {
      // Ignore delete failures in UI.
    }
  };

  return (
    <div className="chat-layout">
      <div className="chat-sidebar">
        <div className="chat-sidebar-header">
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={newChat}
          >
            <Icon name="plus" size={13} /> New chat
          </button>
          <div
            className="search-input"
            style={{ background: "var(--surface-2)" }}
          >
            <Icon name="search" size={13} />
            <input placeholder="Search conversations…" />
          </div>
        </div>
        <div className="chat-sessions">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`chat-session ${
                activeSession === s.id ? "active" : ""
              }`}
              onClick={() => void loadHistory(s.id)}
            >
              <div className="chat-session-title">{s.title}</div>
              <div className="chat-session-time">
                {s.time}
                <button
                  type="button"
                  className="icon-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    void deleteSession(s.id);
                  }}
                  aria-label="Delete chat session"
                  style={{ marginLeft: 8 }}
                >
                  <Icon name="close" size={11} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="chat-main">
        <div className="chat-header">
          <div className="chat-avatar assistant" />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 600 }}>
              RentPi Assistant
            </div>
            <div style={{ fontSize: 11.5, color: "var(--text-3)" }}>
              Ask about rentals, products, availability, discounts,
              categories, and trends.
            </div>
          </div>
          <Badge variant="accent">
            <Icon name="sparkle" size={10} /> Data-focused
          </Badge>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && !loading ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                flex: 1,
                padding: "40px 20px",
                maxWidth: 720,
                margin: "0 auto",
                width: "100%",
              }}
            >
              <div
                className="chat-avatar assistant"
                style={{ width: 44, height: 44, marginBottom: 16 }}
              />
              <h2
                style={{
                  fontSize: 20,
                  fontWeight: 600,
                  letterSpacing: "-0.02em",
                  margin: "0 0 6px",
                }}
              >
                How can I help with your rental search today?
              </h2>
              <div
                style={{
                  fontSize: 13,
                  color: "var(--text-3)",
                  textAlign: "center",
                  marginBottom: 28,
                }}
              >
                Pick a starter question or type your own.
              </div>
              <div className="suggestion-grid">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    className="suggestion"
                    onClick={() => void send(p)}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {messages.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role}`}>
              <div className={`chat-avatar ${m.role}`}>
                {m.role === "user" ? "AR" : ""}
              </div>
              <div className="chat-bubble">{m.content}</div>
            </div>
          ))}

          {loading ? (
            <div className="chat-msg assistant">
              <div className="chat-avatar assistant" />
              <div className="chat-bubble">
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    color: "var(--text-3)",
                  }}
                >
                  <div className="typing-dots">
                    <span />
                    <span />
                    <span />
                  </div>
                  <span style={{ fontSize: 12 }}>
                    RentPi Assistant is checking rental data…
                  </span>
                </div>
              </div>
            </div>
          ) : null}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-wrap">
          <div
            className="chat-input"
            style={{ maxWidth: 720, margin: "0 auto" }}
          >
            <button
              type="button"
              className="icon-btn"
              tabIndex={-1}
            >
              <Icon name="paperclip" size={15} />
            </button>
            <textarea
              rows={1}
              placeholder="Ask about products, availability, trends, discounts…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
            />
            <button
              type="button"
              className="btn btn-accent btn-sm"
              onClick={() => void send()}
              disabled={!input.trim() || loading}
            >
              <Icon name="send" size={13} />
            </button>
          </div>
          <div
            style={{
              textAlign: "center",
              fontSize: 11,
              color: "var(--text-4)",
              marginTop: 8,
              fontFamily: "var(--font-mono)",
            }}
          >
            Enter to send · Shift+Enter for newline
          </div>
        </div>
      </div>
    </div>
  );
}
