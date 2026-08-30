import { AuthHeader, ClerkRedirect } from "@/modules/clerk/index.ts";
import { BrowseListings, ListingDetail, ListingsHome } from "@/modules/listings/index.ts";
import { BuyerOrders, OrderStatus } from "@/modules/orders/index.ts";
import { SignupGate } from "@/modules/signup/index.ts";
import { useHashRoute } from "./route.ts";
import "./App.css";

function goHome() {
  if (window.location.hash !== "#/" && window.location.hash !== "") {
    window.location.hash = "#/";
  }
}

function App() {
  const route = useHashRoute();

  return (
    <>
      <ClerkRedirect />
      <div className="app-top">
        <nav className="app-nav">
          <a href="#/" className={route.page === "browse" || route.page === "listing" ? "active" : undefined}>
            Browse
          </a>
          <a href="#/sell" className={route.page === "sell" ? "active" : undefined}>
            Sell
          </a>
          <a href="#/orders" className={route.page === "orders" || route.page === "order" ? "active" : undefined}>
            My orders
          </a>
        </nav>
        <AuthHeader />
      </div>
      <SignupGate requested={route.page === "signup"} onFinished={goHome} onCancel={goHome}>
        {route.page === "listing" ? <ListingDetail id={route.id} /> : null}
        {route.page === "orders" ? <BuyerOrders /> : null}
        {route.page === "order" ? <OrderStatus id={route.id} /> : null}
        {route.page === "sell" ? <ListingsHome /> : null}
        {route.page === "browse" ? <BrowseListings /> : null}
      </SignupGate>
    </>
  );
}

export default App;
