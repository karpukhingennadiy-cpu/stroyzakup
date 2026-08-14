"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send } from "lucide-react";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

const QUICK_QUESTIONS = [
  "Как создать закупку?",
  "Что такое статусы заявки?",
  "Как поставщики попадают в список?",
  "Как работает публичная страница КП?",
];

export function AssistantWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;
    setInput("");
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content }]);
    setLoading(true);
    try {
      const res = await fetch(
        (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api") + "/assistant/chat/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content, history }),
        }
      );
      const data = await res.json();
      if (data.reply) {
        setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: data.error || "Ошибка сервера" }]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Не удалось связаться с ассистентом. Попробуйте ещё раз." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        aria-label="Помощник"
        className="fixed bottom-6 right-6 z-[1000] flex h-12 w-12 items-center justify-center rounded-full bg-[var(--accent)] text-white shadow-[var(--shadow-medium)] hover:bg-[var(--accent-hover)]"
      >
        {open ? <X className="h-5 w-5" /> : <MessageSquare className="h-5 w-5" />}
      </button>

      {open && (
        <div className="fixed bottom-20 right-6 z-[1000] flex h-[480px] w-[360px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-[var(--radius-xl)] border border-[var(--separator)] bg-[var(--bg-tertiary)] shadow-[var(--shadow-large)]">
          <div className="flex items-center justify-between border-b border-[var(--separator)] px-4 py-3">
            <div>
              <p className="text-sm font-semibold tracking-tight text-[var(--label-primary)]">Ассистент Минитендера</p>
              <p className="text-xs text-[var(--label-tertiary)]">DeepSeek v4 · отвечает мгновенно</p>
            </div>
            <button onClick={() => setOpen(false)} className="text-[var(--label-tertiary)] hover:text-[var(--label-primary)]" aria-label="Закрыть">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.length === 0 && (
              <div className="space-y-2">
                <p className="text-sm text-[var(--label-secondary)] leading-relaxed">
                  Здравствуйте. Помогу разобраться в платформе: создание закупок, статусы, поставщики, КП.
                </p>
                {QUICK_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => send(q)}
                    className="block w-full rounded-[var(--radius-md)] border border-[var(--separator)] bg-[var(--fill-1)] px-3 py-2 text-left text-xs text-[var(--label-secondary)] hover:bg-[var(--fill-2)]"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={"max-w-[85%] rounded-[var(--radius-lg)] px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap " + (m.role === "user" ? "ml-auto bg-[var(--label-primary)] text-[var(--bg-primary)]" : "bg-[var(--fill-1)] text-[var(--label-primary)]")}>
                {m.content}
              </div>
            ))}
            {loading && (
              <div className="max-w-[85%] rounded-[var(--radius-lg)] bg-[var(--fill-1)] px-3 py-2 text-sm text-[var(--label-tertiary)]">
                Печатает...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-[var(--separator)] p-3">
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Спросите о платформе..."
                className="flex-1 rounded-[var(--radius-md)] border border-[var(--separator)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--label-primary)] placeholder:text-[var(--label-quaternary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/25"
              />
              <button
                onClick={() => send()}
                disabled={!input.trim() || loading}
                className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] disabled:opacity-40"
                aria-label="Отправить"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}