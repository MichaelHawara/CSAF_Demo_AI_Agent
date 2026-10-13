import { useState } from "react";
import { Link } from "react-router-dom";
import { ProductThumb } from "../components/ProductCard";
import { useDemo } from "../demoContext";
import { api } from "../services/api";

export function CartPage() {
  const demo = useDemo();
  const cart = demo.cart;
  const [error, setError] = useState("");

  async function run(action: () => Promise<unknown>) {
    setError("");
    try {
      await action();
      await demo.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the cart");
    }
  }

  const setQuantity = (itemId: string, quantity: number) =>
    demo.agent && quantity >= 1 && run(() => api.updateCartItem(demo.agent!.customer_id, itemId, quantity));
  const remove = (itemId: string) => demo.agent && run(() => api.removeCartItem(demo.agent!.customer_id, itemId));

  const empty = !cart || cart.items.length === 0;

  return (
    <div className="page">
      <h1>Shopping cart</h1>
      {empty ? (
        <p>
          Your Nozama cart is empty. <Link to="/">Continue shopping</Link>
        </p>
      ) : (
        <div className="cart-layout">
          <ul className="cart-list">
            {cart!.items.map((item) => (
              <li key={item.id} className="cart-row">
                <div className="cart-image">
                  <Link to={`/product/${item.product_id}`}>
                    <ProductThumb
                      product={{ name: item.product_name, accent: "#888", url: item.image_url || "" }}
                    />
                  </Link>
                </div>
                <div className="cart-info">
                  <Link to={`/product/${item.product_id}`} className="cart-name">
                    {item.product_name}
                  </Link>
                  <div className="muted">${item.unit_price.toFixed(2)} each</div>
                  <div className="cart-controls">
                    <div className="stepper" role="group" aria-label={`Quantity of ${item.product_name}`}>
                      <button
                        type="button"
                        aria-label="Decrease quantity"
                        disabled={item.quantity <= 1}
                        onClick={() => setQuantity(item.id, item.quantity - 1)}
                      >
                        −
                      </button>
                      <span aria-live="polite">{item.quantity}</span>
                      <button
                        type="button"
                        aria-label="Increase quantity"
                        disabled={item.quantity >= 99}
                        onClick={() => setQuantity(item.id, item.quantity + 1)}
                      >
                        +
                      </button>
                    </div>
                    <button type="button" className="link-button" onClick={() => remove(item.id)}>
                      Remove
                    </button>
                  </div>
                </div>
                <div className="cart-subtotal">
                  <span className="muted">Subtotal</span>
                  <strong>${item.line_total.toFixed(2)}</strong>
                </div>
              </li>
            ))}
          </ul>
          <aside className="card cart-summary">
            <h3>Order summary</h3>
            <p>
              Subtotal ({cart!.quantity} items): <strong>${cart!.total.toFixed(2)}</strong>
            </p>
            <p className="muted">Tax and shipping are calculated when checkout is approved.</p>
            <Link className="btn" to="/checkout">
              Proceed to checkout
            </Link>
          </aside>
        </div>
      )}
      {error ? <p className="muted">{error}</p> : null}
      <p className="footer-note">Demo mode: synthetic data only. No real purchase occurs.</p>
    </div>
  );
}
