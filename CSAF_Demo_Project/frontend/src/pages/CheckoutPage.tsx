import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckoutReceiptPanel } from "../components/CheckoutReceiptPanel";
import { useDemo } from "../demoContext";
import { api } from "../services/api";

export function CheckoutPage() {
  const demo = useDemo();
  const [message, setMessage] = useState("");
  const [working, setWorking] = useState(false);
  const cart = demo.cart;
  const empty = !cart || cart.items.length === 0;

  async function decide(approve: boolean) {
    if (!demo.agent) return;
    setMessage("");
    setWorking(true);
    try {
      if (approve) {
        await api.approveCheckout(demo.agent.customer_id, demo.agent.id);
      } else {
        setMessage((await api.rejectCheckout(demo.agent.customer_id, demo.agent.id)).message);
      }
      await demo.refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="page">
      <h1>Checkout</h1>
      <p className="muted">
        No payment provider is connected. Approving checkout records an order in this local demonstration only.
      </p>
      {!empty ? (
        <div className="card">
          <ul className="receipt-lines">
            {cart!.items.map((item) => (
              <li key={item.id}>
                <span className="receipt-name">{item.product_name}</span>
                <span className="muted">
                  {item.quantity} × ${item.unit_price.toFixed(2)}
                </span>
                <strong>${item.line_total.toFixed(2)}</strong>
              </li>
            ))}
          </ul>
          <p>
            Subtotal ({cart!.quantity} items): <strong>${cart!.total.toFixed(2)}</strong>
          </p>
          <div className="row">
            <button className="btn" type="button" onClick={() => decide(true)} disabled={working}>
              Approve checkout
            </button>
            <button className="btn secondary" type="button" onClick={() => decide(false)} disabled={working}>
              Not now
            </button>
            <Link className="btn ghost" to="/cart">
              Edit cart
            </Link>
          </div>
        </div>
      ) : (
        <p>
          Your cart is empty. <Link to="/">Continue shopping</Link>
        </p>
      )}
      {message ? <p className="muted">{message}</p> : null}
      {demo.checkoutReceipt ? <CheckoutReceiptPanel receipt={demo.checkoutReceipt} /> : null}
      <p className="footer-note">Demo mode: synthetic data only. No real purchase occurs.</p>
    </div>
  );
}
