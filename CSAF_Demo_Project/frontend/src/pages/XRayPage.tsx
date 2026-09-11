import { XRayBoard } from "../components/XRayBoard";
import { useDemo } from "../demoContext";

export function XRayPage() {
  const demo = useDemo();
  return (
    <div className="page">
      <h1>Agent X-Ray</h1>
      <p className="muted">
        Presenter view. Column 1 is the shopper. Column 2 is assembled model input — not hidden
        chain-of-thought. Column 3 is what the application actually did.
      </p>
      <XRayBoard xray={demo.xray} attackResult={demo.attackResult} />
    </div>
  );
}
