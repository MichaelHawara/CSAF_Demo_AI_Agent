import { FormEvent, useEffect, useState } from "react";
import { useDemo, useLiveSync } from "../demoContext";
import { api } from "../services/api";
import type {
  Agent,
  Cart,
  ConversationMessage,
  XRayState,
} from "../types";
import { CheckoutReceiptPanel } from "./CheckoutReceiptPanel";
import { ChatProductCard } from "./ChatProductCard";

// The shopper-facing panel never shows security events. What the monitor
// recorded is operator information (X-Ray / Monitor / Control).

interface Props {
  agent: Agent | null;
  cart: Cart | null;
  messages: ConversationMessage[];
  xray?: XRayState | null;
  busy: boolean;
  onRefresh: () => Promise<void>;
  onSent: () => Promise<void>;
}

export function NoziPanel({
  agent,
  cart,
  messages,
  xray,
  busy,
  onRefresh,
  onSent,
}: Props) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [notice, setNotice] = useState("");
  const { checkoutReceipt, selectAgent } = useDemo();
  const [agents, setAgents] = useState<Agent[]>([]);
  // Keep this panel on the agent chosen in any tab, and show changes made on Control.
  useLiveSync(4000);

  useEffect(() => {
    api.agents().then(setAgents).catch(() => undefined);
  }, [agent?.id, agent?.mode, agent?.provider]);
  const reading = xray?.shopper?.product_being_read as
    | { name?: string }
    | null
    | undefined;

  useEffect(() => {
    if (!text) {
      setText("");
    }
  }, [agent?.id]);

  // Picks a random request generated from the product catalog. The one
  // currently in the box is excluded so the button never repeats itself.
  async function loadDemoRequest() {
    setError("");
    setLoadingDemo(true);
    try {
      const demo = await api.loadDemo(text.trim() || undefined);
      setText(demo.demo_request);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load a demo request");
    } finally {
      setLoadingDemo(false);
    }
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

  // Approve = the shopper's own click. The backend validates the current cart,
  // prices it from the catalog, and only then records the receipt and empties
  // the cart. Reject leaves the cart untouched.
  async function decideCheckout(approve: boolean) {
    if (!agent) return;
    setError("");
    setNotice("");
    setDeciding(true);
    try {
      if (approve) {
        await api.approveCheckout(agent.customer_id, agent.id);
      } else {
        const result = await api.rejectCheckout(agent.customer_id, agent.id);
        setNotice(result.message);
      }
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setDeciding(false);
    }
  }

  const cartEmpty = !cart || cart.items.length === 0;

  return (
    <aside className="nozi">
      <div className="nozi-head">
        <div className="nozi-heading-row">
          <h2>Alex - Your Shopping Assistant</h2>
          <a
            className="nozi-tools-button"
            href="/control"
            target="nozama-control-monitor"
            title="Open Control and Monitor"
          >
            Tools
          </a>
        </div>
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
        <div className="agent-picker">
          <label htmlFor="agent-select">Agent in use</label>
          <select
            id="agent-select"
            value={agent?.id || ""}
            disabled={!agent || sending}
            onChange={(e) => selectAgent(e.target.value).catch((err) => setError(String(err)))}
          >
            {agents.map((row) => (
              <option key={row.id} value={row.id}>
                {row.display_name} · {row.mode} · {row.provider}
              </option>
            ))}
          </select>
        </div>
        <div className="row">
          <span className="status-line">
            Status:{" "}
            {busy || sending ? "Alex is working…" : agent?.status || "idle"}
          </span>
        </div>
        {reading?.name ? (
          <div className="muted">Reading listing: {reading.name}</div>
        ) : null}
        <div className="chat-log" aria-live="polite">
          {messages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => (
              <div key={m.id} className={`bubble ${m.role}`}>
                <strong>{m.role === "user" ? "You" : "Alex"}:</strong>{" "}
                {m.content}
                {m.attachments?.products?.length ? (
                  <div className="chat-cards">
                    {m.attachments.products.map((product) => (
                      <ChatProductCard
                        key={product.id}
                        product={product}
                        defaultQuantity={m.attachments?.quantity || 1}
                        agent={agent}
                        onAdded={onRefresh}
                      />
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
        </div>
        <form onSubmit={send}>
          <textarea
            className="prompt"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Tell Alex what you're looking for, how many, and your budget…"
          />
          <div className="row" style={{ marginTop: 8 }}>
            <button
              type="button"
              className="btn secondary"
              onClick={loadDemoRequest}
              disabled={loadingDemo || sending}
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
            disabled={!agent || cartEmpty || deciding}
            title={cartEmpty ? "Your cart is empty" : undefined}
          >
            Approve checkout
          </button>
          <button
            type="button"
            className="btn danger"
            onClick={() => decideCheckout(false)}
            disabled={!agent || cartEmpty || deciding}
          >
            Reject checkout
          </button>
        </div>
        {cartEmpty && !checkoutReceipt ? (
          <p className="muted">Add something to your cart to check out.</p>
        ) : null}
        {notice ? <p className="muted">{notice}</p> : null}
        {checkoutReceipt ? <CheckoutReceiptPanel receipt={checkoutReceipt} /> : null}
        <p className="muted">
          Use this panel to test out the AI Shopping assistant! Load a random
          request built from our catalog, or write your own. Say how many you
          want and your budget in the message.
        </p>
        {/* <p className="muted">
          Alex can propose actions. The Nozama backend decides whether they are allowed.
          Demo transaction only—no real purchase occurred.
        </p> */}
      </div>
    </aside>
  );
}
