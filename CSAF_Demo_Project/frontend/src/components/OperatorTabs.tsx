import { NavLink } from "react-router-dom";

export function OperatorTabs() {
    return (
        <nav className="operator-tabs" aria-label="Operator pages">
            <NavLink to="/monitor">Monitor</NavLink>
            <NavLink to="/control">Control</NavLink>
        </nav>
    );
}
