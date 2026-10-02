import { FormEvent, useEffect, useState } from "react";
import { AttackBanner } from "./AttackBanner";
import { api } from "../services/api";
import type {
  Agent,
  AttackResult,
  Cart,
  ConversationMessage,
  XRayState,
} from "../types";

interface Props {
  agent: Agent | null;
  cart: Cart | null;
  messages: ConversationMessage[];
  attackResult?: AttackResult | null;
  xray?: XRayState | null;
  busy: boolean;
  onRefresh: () => Promise<void>;
  onSent: () => Promise<void>;
}

export function NoziPanel({
  agent,
  cart,
  messages,
  attackResult,
  xray,
  busy,
  onRefresh,
  onSent,
}: Props) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const reading = xray?.shopper?.product_being_read as
    | { name?: string }
    | null
    | undefined;

  useEffect(() => {
    if (!text) {
      setText("");
    }
  }, [agent?.id]);

  async function loadDemoRequest() {
    setError("");
    const demo = await api.loadDemo();
    setText(demo.demo_request);
    await onRefresh();
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    if (!agent || !text.trim()) return;
    setError("");
    setSending(true);
    try {
      await api.sendMessage(agent.id, text.trim());
      await onSent();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed");
    } finally {
      setSending(false);
    }
  }

  async function decideCheckout(approve: boolean) {
    if (!agent) return;
    const pending = (xray?.system?.checkout_requests || []).find(
      (row) => row.pending_id,
    );
    if (!approve) {
      await api.resetAgent(agent.id);
      await onRefresh();
      return;
    }
    if (!pending?.pending_id || !pending.snapshot) {
      await api.requestCheckout(agent.customer_id, agent.id);
      await onRefresh();
      return;
    }
    const snapshot = pending.snapshot as Record<string, unknown>;
    await api.confirmCheckout({
      pending_id: pending.pending_id,
      customer_id: agent.customer_id,
      product_id: snapshot.product_id,
      seller_id: snapshot.seller_id,
      quantity: snapshot.quantity,
      unit_price: snapshot.unit_price,
      total: snapshot.total,
    });
    await onRefresh();
  }

  const mock =
    !agent?.gemini_available ||
    agent.provider === "mock" ||
    agent.provider_note.includes("mock");

  return (
    <aside className="nozi">
      <div className="nozi-head">
        <h2>Nozi - Your Shopping Assistant</h2>
        {/* {mock ? (
          <div className="demo-mode">Deterministic Demo Mode</div>
        ) : (
          <div className="demo-mode">Gemini provider</div>
        )} */}
        {agent && !agent.gemini_available && agent.provider === "gemini" ? (
          <div className="muted">
            GEMINI_API_KEY is missing, so mock mode is active.
          </div>
        ) : null}
      </div>
      <div className="nozi-body">
        <div className="restrictions">
          <strong>Active restrictions</strong>
          Budget: ${Number(agent?.budget ?? 80).toFixed(0)}
          <br />
          Maximum quantity: {agent?.max_quantity ?? 1}
          <br />
          Checkout confirmation: Required
        </div>
        <div className="row">
          <span
            className={`mode-pill ${agent?.mode === "patched" ? "patched" : ""}`}
          >
            {agent?.mode || "vulnerable"} mode
          </span>
          <span className="status-line">
            Status:{" "}
            {busy || sending ? "Nozi is working…" : agent?.status || "idle"}
          </span>
        </div>
        {reading?.name ? (
          <div className="muted">Reading listing: {reading.name}</div>
        ) : null}
        <AttackBanner result={attackResult} />
        <div className="chat-log" aria-live="polite">
          {messages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => (
              <div key={m.id} className={`bubble ${m.role}`}>
                <strong>{m.role === "user" ? "You" : "Nozi"}:</strong>{" "}
                {m.content}
              </div>
            ))}
          {cart && cart.quantity > 0 ? (
            <div className="bubble">
              Cart now has {cart.quantity} item(s) totaling $
              {cart.total.toFixed(2)}.
            </div>
          ) : null}
        </div>
        <form onSubmit={send}>
          <textarea
            className="prompt"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ask Nozi to find a product…"
          />
          <div className="row" style={{ marginTop: 8 }}>
            <button
              type="button"
              className="btn secondary"
              onClick={loadDemoRequest}
            >
              Load Demo Request
            </button>
            <button
              className="btn"
              type="submit"
              disabled={busy || sending || !agent}
            >
              Send
            </button>
          </div>
        </form>
        {error ? <div className="muted">{error}</div> : null}
        <div className="row">
          <button
            type="button"
            className="btn"
            onClick={() => decideCheckout(true)}
            disabled={!agent}
          >
            Approve checkout
          </button>
          <button
            type="button"
            className="btn danger"
            onClick={() => decideCheckout(false)}
            disabled={!agent}
          >
            Reject checkout
          </button>
        </div>
        <p className="muted">
          Use this panel to test out the AI Shopping assistant! You can load a
          prewritten request or curate your own.
        </p>
        {/* <p className="muted">
          Nozi can propose actions. The Nozama backend decides whether they are allowed.
          Demo transaction only—no real purchase occurred.
        </p> */}
      </div>
    </aside>
  );
}
