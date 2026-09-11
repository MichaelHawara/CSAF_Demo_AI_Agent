import { NavLink, useNavigate } from "react-router-dom";
import { FormEvent, useState } from "react";

export function NavBar({ cartCount }: { cartCount: number }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  function onSearch(event: FormEvent) {
    event.preventDefault();
    navigate(`/?q=${encodeURIComponent(query)}`);
  }

  return (
    <header className="nav">
      <NavLink to="/" className="brand">
        Noz<span>ama</span>
      </NavLink>
      <form className="nav-search" onSubmit={onSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search Nozama"
          aria-label="Search products"
        />
        <button type="submit">Search</button>
      </form>
      <NavLink to="/" end>
        Shop
      </NavLink>
      <NavLink to="/xray">X-Ray</NavLink>
      <NavLink to="/control">Control</NavLink>
      <NavLink to="/monitor">Monitor</NavLink>
      <NavLink to="/cart" className="cart-link">
        Cart ({cartCount})
      </NavLink>
    </header>
  );
}
