import { Link } from "react-router-dom";
import type { Product } from "../types";


/*
export function ProductThumb({ product, tall }: { product: Pick<Product, "name" | "accent">; tall?: boolean }) {
  return (
    <div
      className="thumb"
      style={{
        background: `linear-gradient(145deg, ${product.accent}, #111)`,
        height: tall ? 240 : undefined,
      }}
    >
      {product.name.split(" ")[0]}
    </div>
  );
}
  */

export function ProductThumb({
  product,
  tall,
}: {
  product: Pick<Product, "name" | "accent" | "url" >;
  tall?: boolean;
}) {
  if (product.url) {
    return (
      <img
        className="thumb"
        src={product.url}
        alt={product.name}
        style={{ height: tall ? 240 : undefined, objectFit: "contain", background: "#fff" }}
      />
    );
  }
  return (
    <div
      className="thumb"
      style={{
        background: `linear-gradient(145deg, ${product.accent}, #111)`,
        height: tall ? 240 : undefined,
      }}
    >
      {product.name.split(" ")[0]}
    </div>
  );
}

export function ProductCard({ product }: { product: Product }) {
  return (
    <article className="card product-card">
      <ProductThumb product={product} />
      <Link to={`/product/${product.id}`}>
        <strong>{product.name}</strong>
      </Link>
      <div className="muted">
        {product.seller_name}{" "}
        <span className={`badge ${product.trusted_seller ? "trusted" : "untrusted"}`}>
          {product.trusted_seller ? "Trusted seller" : "Marketplace seller"}
        </span>
      </div>
      <div>★ {product.rating.toFixed(1)} ({product.review_count})</div>
      <div className="price">${product.price.toFixed(2)}</div>
      <Link className="btn" to={`/product/${product.id}`}>
        View
      </Link>
    </article>
  );
}
