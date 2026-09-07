import { Bot, MessageSquare, Send, Sparkles, User, X, Loader2, RefreshCw, Cpu, Activity } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { sendAIChatMessage } from "../services/aiService";

function parseInlineBold(text) {
  if (!text) return "";
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-bold text-emerald-300">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

function FormattedChatMessage({ text }) {
  if (!text) return null;

  const lines = text.split("\n");

  return (
    <div className="space-y-1.5 text-xs sm:text-sm leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-0.5" />;

        // Check if line is a bullet point: - or • or *
        if (trimmed.startsWith("- ") || trimmed.startsWith("• ") || (trimmed.startsWith("* ") && !trimmed.endsWith("*"))) {
          const content = trimmed.replace(/^[-•*]\s+/, "");
          return (
            <div key={idx} className="flex items-start gap-2 pl-0.5 mt-1">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.8)]" />
              <span className="flex-1">{parseInlineBold(content)}</span>
            </div>
          );
        }

        // Check if line is a numbered list: 1. or 2.
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
        if (numMatch) {
          return (
            <div key={idx} className="flex items-start gap-2 pl-0.5 mt-1">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 border border-emerald-500/40 text-[9px] font-mono font-bold text-emerald-400 mt-0.5">
                {numMatch[1]}
              </span>
              <span className="flex-1">{parseInlineBold(numMatch[2])}</span>
            </div>
          );
        }

        // Section headers or regular text
        return <p key={idx}>{parseInlineBold(line)}</p>;
      })}
    </div>
  );
}

const SUGGESTIONS = [
  "Best sunscreen for oily acne skin?",
  "Can I use Niacinamide with Salicylic Acid?",
  "How to layer my skincare routine?",
  "Ingredients to fade dark spots?",
];

export default function AIChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      sender: "ai",
      text: "👋 Hi! Main hoon DermaBot AI Skincare Assistant.\nAap mujhse kisi bhi skin issue, skincare routine, ya active ingredients ke baare mein pooch sakte hain!",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (textToSend) => {
    const query = typeof textToSend === "string" ? textToSend : input;
    if (!query.trim() || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: "user",
      text: query.trim(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({ sender: m.sender, text: m.text }));

      const res = await sendAIChatMessage(query.trim(), history);
      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: res.response || "I am here to help! Could you please clarify your skincare question?",
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          text: "⚠️ I encountered a temporary connection issue. Please check your backend connection or try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const resetChat = () => {
    setMessages([
      {
        id: "welcome",
        sender: "ai",
        text: "👋 Hi! I am DermaBot AI 3D Biometric Assistant. Ask me anything about skincare routines, clinical ingredients, or product layering formulation!",
      },
    ]);
  };

  return (
    <aside aria-label="AI Skincare Assistant" className="fixed bottom-6 right-6 z-50">
      {/* 3D Holographic Floating Toggle Orb */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group relative flex h-16 w-16 items-center justify-center rounded-full bg-slate-950 p-1 shadow-[0_0_35px_rgba(16,185,129,0.4)] transition-all duration-500 hover:scale-110 hover:shadow-[0_0_50px_rgba(6,182,212,0.6)] focus:outline-none focus:ring-4 focus:ring-emerald-500/50"
          aria-label="Open AI Skincare Chatbot"
        >
          {/* Orbital Neon Ring 1 */}
          <div className="absolute inset-0 rounded-full border border-dashed border-emerald-400/60 animate-[spin_8s_linear_infinite]" />
          
          {/* Orbital Neon Ring 2 */}
          <div className="absolute -inset-1 rounded-full border border-cyan-400/40 animate-[spin_12s_linear_infinite_reverse]" />
          
          {/* Glowing Inner Core */}
          <div className="relative flex h-full w-full items-center justify-center rounded-full bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-500 text-white shadow-inner">
            <Sparkles className="absolute -top-1 -right-1 h-5 w-5 animate-bounce text-amber-300 drop-shadow-[0_0_8px_rgba(251,191,36,0.8)]" />
            <Bot className="h-7 w-7 transition-transform group-hover:rotate-12 duration-300" />
          </div>

          {/* Holographic Status Pill */}
          <span className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full border border-emerald-500/40 bg-slate-950/90 px-2 py-0.5 text-[9px] font-mono font-bold uppercase tracking-wider text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.3)] backdrop-blur-md">
            ● AI LIVE
          </span>
        </button>
      )}

      {/* 3D Cybernetic Glass Chat Window */}
      {isOpen && (
        <div className="flex h-[560px] w-[360px] sm:w-[410px] flex-col overflow-hidden rounded-3xl border border-emerald-500/30 bg-slate-950/95 backdrop-blur-2xl shadow-[0_25px_60px_-15px_rgba(16,185,129,0.35)] transition-all duration-300 animate-in fade-in zoom-in-95">
          {/* Cybernetic HUD Header */}
          <div className="relative flex items-center justify-between border-b border-white/10 bg-gradient-to-r from-slate-900 via-slate-900/90 to-emerald-950/60 px-5 py-4 text-white">
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#10b98110_1px,transparent_1px),linear-gradient(to_bottom,#10b98110_1px,transparent_1px)] bg-[size:14px_14px] pointer-events-none opacity-40" />

            <div className="relative flex items-center gap-3">
              <div className="relative flex h-10 w-10 items-center justify-center rounded-2xl border border-emerald-500/40 bg-emerald-500/10 backdrop-blur-md shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                <Bot className="h-5 w-5 text-emerald-400" />
                <span className="absolute -bottom-0.5 -right-0.5 flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-extrabold tracking-wide text-white">DermaBot AI</h2>
                  <span className="rounded border border-emerald-500/30 bg-emerald-500/10 px-1.5 py-0.2 text-[9px] font-mono font-bold text-emerald-400">
                    v2.4 3D
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
                  <Activity className="h-3 w-3 text-cyan-400 animate-pulse" />
                  <span>Gemini 2.5 Flash Engine</span>
                </p>
              </div>
            </div>

            <div className="relative flex items-center gap-1.5">
              <button
                type="button"
                onClick={resetChat}
                title="Restart chat session"
                className="rounded-xl border border-white/5 bg-white/5 p-2 text-slate-300 hover:bg-emerald-500/20 hover:text-emerald-300 hover:border-emerald-500/40 transition"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Close chat"
                className="rounded-xl border border-white/5 bg-white/5 p-2 text-slate-300 hover:bg-rose-500/20 hover:text-rose-300 hover:border-rose-500/40 transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-950/60 backdrop-blur-md">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.sender === "ai" && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-950/70 text-emerald-400 text-xs font-bold shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div
                  className={`max-w-[84%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed ${
                    msg.sender === "user"
                      ? "border border-cyan-500/30 bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-br-none shadow-[0_4px_15px_rgba(6,182,212,0.25)] font-medium"
                      : "border border-white/10 bg-slate-900/95 text-slate-100 rounded-bl-none shadow-sm backdrop-blur-lg"
                  }`}
                >
                  <FormattedChatMessage text={msg.text} />
                </div>
                {msg.sender === "user" && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-cyan-500/30 bg-cyan-950/70 text-cyan-300 text-xs font-bold">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2.5 rounded-2xl border border-emerald-500/20 bg-slate-900/60 p-3 text-emerald-400 text-xs">
                <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
                <span className="font-mono text-[11px] tracking-wider uppercase">DermaBot Neural Synthesis...</span>
                <div className="flex gap-1 ml-auto">
                  <span className="h-2 w-1 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="h-3 w-1 rounded-full bg-cyan-400 animate-pulse [animation-delay:0.2s]" />
                  <span className="h-2 w-1 rounded-full bg-emerald-400 animate-pulse [animation-delay:0.4s]" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Starter Chips */}
          {messages.length <= 2 && !loading && (
            <div className="border-t border-white/10 bg-slate-900/80 px-4 py-2.5">
              <p className="mb-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                ⚡ Quick Prompts:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => handleSend(s)}
                    className="rounded-xl border border-emerald-500/20 bg-emerald-950/40 px-2.5 py-1 text-[11px] text-emerald-300 hover:border-emerald-400/50 hover:bg-emerald-900/50 transition text-left"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Box */}
          <div className="border-t border-white/10 bg-slate-900/90 p-3.5">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about ingredients, acne, barrier repair..."
                className="flex-1 rounded-xl border border-white/10 bg-slate-950/80 px-4 py-2.5 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:border-emerald-500/60 focus:bg-slate-950 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)] transition hover:scale-105 disabled:opacity-30 disabled:hover:scale-100"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
            <p className="mt-2 text-center text-[10px] text-slate-500 font-mono">
              🔒 AI Guidance Only · Consult certified dermatologist for medical treatment.
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}
