import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { NoziPanel } from "../components/NoziPanel";
import { ProductThumb } from "../components/ProductCard";
import { api } from "../services/api";
import type { ProductDetail } from "../types";
import { useDemo } from "../demoContext";

export function ProductPage() {
  const { productId } = useParams();
  const demo = useDemo();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!productId) return;
    api.product(productId).then(setProduct);
  }, [productId]);

  async function addOne() {
    if (!product || !demo.agent) return;
    try {
      await api.addCartItem(demo.agent.customer_id, product.id, 1, demo.agent.id);
      setNotice("Added to cart.");
      await demo.refresh();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Could not add to cart");
    }
  }

  if (!product) {
    return <div className="page">Loading listing…</div>;
  }

  return (
    <div className="page shop-layout">
      <article className="detail">
        <ProductThumb product={product} tall />
        <div>
          <h1>{product.name}</h1>
          <p className="muted">
            {product.seller_name}{" "}
            <span className={`badge ${product.trusted_seller ? "trusted" : "untrusted"}`}>
              {product.trusted_seller ? "Trusted seller: Yes" : "Trusted seller: No"}
            </span>
          </p>
          <p>★ {product.rating.toFixed(1)} · {product.review_count} ratings</p>
          <p className="price">${product.price.toFixed(2)}</p>
          <p>{product.description}</p>
          <p className="muted">{product.image_alt_text_public}</p>
          <button className="btn" type="button" onClick={addOne}>
            Add to cart
          </button>
          {notice ? <p>{notice}</p> : null}
          <h3>Customer reviews</h3>
          {product.reviews.map((review) => (
            <div key={review.id} className="card">
              <strong>{review.author}</strong> ★ {review.rating}
              <p>{review.body}</p>
            </div>
          ))}
        </div>
      </article>
      <NoziPanel
        agent={demo.agent}
        cart={demo.cart}
        messages={demo.messages}
        attackResult={demo.attackResult}
        xray={demo.xray}
        busy={demo.busy}
        onRefresh={demo.refresh}
        onSent={demo.refresh}
      />
    </div>
  );
}
