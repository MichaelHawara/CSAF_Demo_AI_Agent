import type { CheckoutReceipt } from "../types";

const money = (value: number) => `$${value.toFixed(2)}`;

/** Shown under the chat after the shopper approves checkout. */
export function CheckoutReceiptPanel({ receipt }: { receipt: CheckoutReceipt }) {
  return (
    <section className="receipt" aria-label="Checkout details">
      <h3>Checkout approved</h3>
      <p className="muted">
        Order {receipt.order_id} · approved {new Date(receipt.approved_at).toLocaleString()}
      </p>
      <ul className="receipt-lines">
        {receipt.items.map((line) => (
          <li key={line.product_id}>
            <span className="receipt-name">{line.name}</span>
            <span className="muted">
              {line.quantity} × {money(line.unit_price)}
            </span>
            <strong>{money(line.line_total)}</strong>
          </li>
        ))}
      </ul>
      <dl className="receipt-totals">
        <dt>Subtotal ({receipt.item_count} items)</dt>
        <dd>{money(receipt.subtotal)}</dd>
        <dt>Tax ({Math.round(receipt.tax_rate * 100)}%)</dt>
        <dd>{money(receipt.tax)}</dd>
        <dt>Shipping</dt>
        <dd>{receipt.shipping ? money(receipt.shipping) : "Free"}</dd>
        <dt className="receipt-final">Total</dt>
        <dd className="receipt-final">{money(receipt.total)}</dd>
      </dl>
      <p className="receipt-note">{receipt.demo_notice}</p>
    </section>
  );
}
