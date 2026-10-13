import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { Agent, Product } from "../types";
import { ProductThumb } from "./ProductCard";

/**
 * A product Alex found, shown inside the chat. The shopper picks the quantity
 * and clicks "Add to cart" themselves.
 */
export function ChatProductCard({
  product,
  defaultQuantity,
  agent,
  onAdded,
}: {
  product: Product;
  defaultQuantity: number;
  agent: Agent | null;
  onAdded: () => Promise<void>;
}) {
  const [quantity, setQuantity] = useState(Math.max(1, defaultQuantity));
  const [status, setStatus] = useState("");
  const [working, setWorking] = useState(false);

  async function add() {
    if (!agent) return;
    setWorking(true);
    setStatus("");
    try {
      await api.addCartItem(agent.customer_id, product.id, quantity, agent.id);
      setStatus(`Added ${quantity} to cart`);
      await onAdded();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Could not add to cart");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="chat-card">
      <div className="chat-card-image">
        <ProductThumb product={product} />
      </div>
      <div className="chat-card-body">
        <Link to={`/product/${product.id}`} className="chat-card-name">
          {product.name}
        </Link>
        <div className="price">${product.price.toFixed(2)}</div>
        <div className="chat-card-controls">
          <label>
            Qty{" "}
            <input
              type="number"
              min={1}
              max={99}
              value={quantity}
              aria-label={`Quantity of ${product.name}`}
              onChange={(e) => setQuantity(Math.min(99, Math.max(1, Number(e.target.value) || 1)))}
            />
          </label>
          <button type="button" className="btn" onClick={add} disabled={!agent || working}>
            Add to cart
          </button>
        </div>
        {status ? <div className="muted">{status}</div> : null}
      </div>
    </div>
  );
}
