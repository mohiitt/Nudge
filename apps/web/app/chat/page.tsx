"use client";

import { FormEvent, useState } from "react";
import { sendChat } from "../../lib/api";

type Msg = { role: "user" | "agent"; text: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "agent",
      text: "I'm Nudge. Ask what needs attention, or name an account for a plan.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setBusy(true);
    const res = await sendChat(text);
    setMessages((m) => [...m, { role: "agent", text: res.reply }]);
    setBusy(false);
  }

  return (
    <main className="page">
      <h1>Chat</h1>
      <p className="sub">Personal agent loop — actions that matter still go through approvals.</p>
      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.text}
          </div>
        ))}
      </div>
      <form className="chat-form" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What needs attention today?"
          disabled={busy}
        />
        <button className="btn" type="submit" disabled={busy}>
          Send
        </button>
      </form>
    </main>
  );
}
