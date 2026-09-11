import { Link } from "react-router-dom";
import { useDemo } from "../demoContext";
import { api } from "../services/api";

export function CartPage() {
  const demo = useDemo();
  const cart = demo.cart;

  async function remove(id: string) {
    if (!demo.agent) return;
    await api.removeCartItem(demo.agent.customer_id, id);
    await demo.refresh();
  }

  return (
    <div className="page">
      <h1>Shopping cart</h1>
      {!cart || cart.items.length === 0 ? <p>Your Nozama cart is empty.</p> : null}
      {cart?.items.map((item) => (
        <div key={item.id} className="card row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
          <div>
            <Link to={`/product/${item.product_id}`}>{item.product_name}</Link>
            <div className="muted">
              Qty {item.quantity} · ${item.unit_price.toFixed(2)} each
            </div>
          </div>
          <div>
            <strong>${item.line_total.toFixed(2)}</strong>
            <div>
              <button className="btn danger" type="button" onClick={() => remove(item.id)}>
                Remove
              </button>
            </div>
          </div>
        </div>
      ))}
      {cart ? <p className="price">Subtotal ({cart.quantity} items): ${cart.total.toFixed(2)}</p> : null}
      <Link className="btn" to="/checkout">
        Proceed to checkout
      </Link>
      <p className="footer-note">Demo transaction only—no real purchase occurred.</p>
    </div>
  );
}
