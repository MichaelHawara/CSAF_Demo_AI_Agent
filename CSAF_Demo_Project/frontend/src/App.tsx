import { Navigate, Route, Routes } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import { DemoProvider, useDemo } from "./demoContext";
import { CartPage } from "./pages/CartPage";
import { CheckoutPage } from "./pages/CheckoutPage";
import { ControlPage } from "./pages/ControlPage";
import { MonitorPage } from "./pages/MonitorPage";
import { ProductPage } from "./pages/ProductPage";
import { ShopPage } from "./pages/ShopPage";
import { XRayPage } from "./pages/XRayPage";

function Shell() {
  const demo = useDemo();
  return (
    <>
      <NavBar cartCount={demo.cart?.quantity || 0} />
      <Routes>
        <Route path="/" element={<ShopPage />} />
        <Route path="/product/:productId" element={<ProductPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/xray" element={<XRayPage />} />
        <Route path="/control" element={<ControlPage />} />
        <Route path="/monitor" element={<MonitorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <DemoProvider>
      <Shell />
    </DemoProvider>
  );
}
