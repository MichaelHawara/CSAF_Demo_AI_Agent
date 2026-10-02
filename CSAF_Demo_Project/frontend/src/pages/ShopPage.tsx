import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { NoziPanel } from "../components/NoziPanel";
import { ProductCard } from "../components/ProductCard";
import { api } from "../services/api";
import type { Product } from "../types";
import { useDemo } from "../demoContext";

export function ShopPage() {
  const demo = useDemo();
  const [params] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const q = params.get("q") || "";

  useEffect(() => {
    const load = q ? api.searchProducts(q) : api.products();
    load.then(setProducts).catch(() => setProducts([]));
  }, [q]);

  return (
    <div className="page shop-layout">
      <div>
        <section className="hero">
          <h1>Find it on Nozama </h1>
          <p>
            Fictional marketplace for a cybersecurity fair. Nozi can search and
            recommend. Secure application code decides whether cart and checkout
            actions are allowed.
          </p>
        </section>
        <div className="grid">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </div>
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
