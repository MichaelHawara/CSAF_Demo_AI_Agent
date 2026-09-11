import { useState } from "react";
import { useDemo } from "../demoContext";
import { api } from "../services/api";

export function CheckoutPage() {
  const demo = useDemo();
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState<Record<string, unknown> | null>(null);

  async function request() {
    if (!demo.agent) return;
    const result = await api.requestCheckout(demo.agent.customer_id, demo.agent.id);
    setPending((result.pending as Record<string, unknown>) || null);
    setMessage(String(result.message || result.reason || JSON.stringify(result)));
    await demo.refresh();
  }

  async function confirm() {
    if (!demo.agent || !pending) return;
    const result = await api.confirmCheckout({
      pending_id: pending.id,
      customer_id: pending.customer_id,
      product_id: pending.product_id,
      seller_id: pending.seller_id,
      quantity: pending.quantity,
      unit_price: pending.unit_price,
      total: pending.total,
    });
    setMessage(String(result.message || "Confirmed"));
    await demo.refresh();
  }

  return (
    <div className="page">
      <h1>Fake checkout</h1>
      <p>No payment provider is connected. Confirmation is bound to exact cart details.</p>
      {demo.cart ? (
        <div className="card">
          <p>
            {demo.cart.quantity} item(s) · ${demo.cart.total.toFixed(2)}
          </p>
          {demo.cart.demo_checked_out ? <p>Demo checkout already completed for this cart.</p> : null}
        </div>
      ) : null}
      <div className="row">
        <button className="btn" type="button" onClick={request}>
          Request checkout
        </button>
        <button className="btn secondary" type="button" onClick={confirm} disabled={!pending}>
          Confirm these exact details
        </button>
      </div>
      {message ? <pre className="wrap">{message}</pre> : null}
      <p className="footer-note">Demo transaction only—no real purchase occurred.</p>
    </div>
  );
}
