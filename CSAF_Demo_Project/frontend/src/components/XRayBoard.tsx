import { useMemo, useState } from "react";
import { AttackBanner } from "./AttackBanner";
import { ProductCard } from "./ProductCard";
import type { AttackResult, Product, XRayState } from "../types";

const STEPS = [
  "1. Customer asks",
  "2. Agent searches",
  "3. Listing is read",
  "4. Hidden content enters context",
  "5. Agent proposes tool calls",
  "6. Backend allows or blocks the action",
];

export function XRayBoard({
  xray,
  attackResult,
}: {
  xray: XRayState | null;
  attackResult?: AttackResult | null;
}) {
  const [step, setStep] = useState(xray?.current_step || 1);
  const [reveal, setReveal] = useState(false);
  const visibleStep = step;

  const searchResults = (xray?.shopper?.search_results || []) as Product[];
  const sections = useMemo(() => {
    const all = xray?.ai_context || [];
    if (visibleStep < 2) return all.filter((s) => s.label !== "TOOL RESULT" && s.label !== "UNTRUSTED SELLER CONTENT" && s.label !== "TRUSTED PRODUCT DATA");
    if (visibleStep < 4) return all.filter((s) => s.label !== "UNTRUSTED SELLER CONTENT");
    return all;
  }, [xray, visibleStep]);

  return (
    <div>
      <AttackBanner result={attackResult} />
      <div className="steps">
        {STEPS.map((label, index) => (
          <button
            key={label}
            className={`btn ${visibleStep === index + 1 ? "" : "secondary"}`}
            onClick={() => setStep(index + 1)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>
      <div className="xray">
        <section className="xray-col">
          <h3>What the shopper sees</h3>
          <p className="muted">{xray?.shopper?.request || "No request yet."}</p>
          {visibleStep >= 2 ? (
            <div className="grid">
              {searchResults.slice(0, 3).map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : null}
          {visibleStep >= 3 && xray?.shopper?.product_being_read ? (
            <div className="card">
              <strong>Product being read</strong>
              <pre className="wrap">{JSON.stringify(xray.shopper.product_being_read, null, 2)}</pre>
              <p>{xray.shopper.visible_description}</p>
            </div>
          ) : null}
          {visibleStep >= 6 && xray?.shopper?.cart ? (
            <div className="card">
              <strong>Cart result</strong>
              <pre className="wrap">{JSON.stringify(xray.shopper.cart, null, 2)}</pre>
            </div>
          ) : null}
          <button type="button" className="btn danger" onClick={() => setReveal((v) => !v)}>
            Reveal hidden listing content
          </button>
          {reveal ? (
            <div className="hidden-reveal">
              {JSON.stringify(xray?.hidden_content || { note: "No hidden content captured yet." }, null, 2)}
            </div>
          ) : (
            <p className="muted">Hidden seller fields stay invisible in the normal Nozama UI.</p>
          )}
        </section>
        <section className="xray-col">
          <h3>What the AI receives</h3>
          {sections.map((section, index) => (
            <div
              key={`${section.label}-${index}`}
              className={`section ${section.trusted ? "" : "untrusted"} ${section.highlight ? "highlight" : ""}`}
            >
              <strong>{section.label}</strong>
              <div>{section.text}</div>
            </div>
          ))}
        </section>
        <section className="xray-col">
          <h3>What the system does</h3>
          <p className="muted">The model proposes. The backend allows or blocks.</p>
          <pre className="wrap">{JSON.stringify(xray?.system || {}, null, 2)}</pre>
        </section>
      </div>
    </div>
  );
}
