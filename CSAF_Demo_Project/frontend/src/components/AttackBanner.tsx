import type { AttackResult } from "../types";

export function AttackBanner({ result }: { result?: AttackResult | null }) {
  if (!result?.banner || result.banner === "NO PREPARED ATTACK RESULT") {
    return null;
  }
  const succeeded = result.banner === "ATTACK SUCCEEDED";
  return (
    <div className={`banner ${succeeded ? "success" : "blocked"}`}>
      <div>{result.banner}</div>
      {succeeded ? (
        <p>
          Requested quantity: {result.requested_quantity}
          <br />
          Cart quantity: {result.cart_quantity}
          <br />
          Budget: ${Number(result.budget).toFixed(2)}
          <br />
          Cart total: ${Number(result.cart_total).toFixed(2)}
          <br />
          Confirmation received: {result.confirmation_received ? "Yes" : "No"}
        </p>
      ) : (
        <p>
          Agent attempted quantity: {result.attempted_quantity}
          <br />
          Allowed quantity: {result.allowed_quantity}
          <br />
          Attempted total: ${Number(result.attempted_total).toFixed(2)}
          <br />
          Maximum budget: ${Number(result.budget).toFixed(2)}
          <br />
          Checkout confirmation: {result.confirmation_received ? "Received" : "Missing"}
        </p>
      )}
      <p>{result.demo_notice}</p>
    </div>
  );
}
