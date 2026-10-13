import type { RequestSummary } from "../types";

const money = (value?: number | null) => (value == null ? "not stated" : `$${Number(value).toFixed(2)}`);

/**
 * Operator-only. Lists what the monitor recorded for the latest request in
 * plain, neutral language. It never labels the outcome; the reader pieces it
 * together from the facts. The shopper-facing Alex panel does not render this.
 */
export function SecuritySummary({ result }: { result?: RequestSummary | null }) {
  const lines = result?.security_summary || [];
  if (!result || result.mode == null) {
    return null;
  }
  return (
    <div className="summary-panel">
      <h4>{lines.length ? "Security events recorded" : "No security events recorded"}</h4>
      {lines.length ? (
        <ul>
          {lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : null}
      <p className="muted">
        Customer asked for {result.requested_quantity ?? "an unstated number of"} item(s), budget{" "}
        {money(result.budget)}. Cart received {result.added_quantity ?? 0} item(s),{" "}
        {money(result.added_total)}, in this request.
      </p>
      {result.demo_notice ? <p className="muted">{result.demo_notice}</p> : null}
    </div>
  );
}
