import { useState } from "react";
import { AuthHeader } from "@/modules/clerk/index.ts";
import { BrowseListings, ListingDetail, ListingsHome } from "@/modules/listings/index.ts";
import { BuyerOrders, OrderStatus } from "@/modules/orders/index.ts";
import { SellerProfilePage, localReviews, publicSellerProfile } from "@/modules/reviews/index.ts";
import { SignupGate } from "@/modules/signup/index.ts";
import { useHashRoute } from "./route.ts";
import "./App.css";

function App() {
  const [signupOpen, setSignupOpen] = useState(false);
  const route = useHashRoute();

  return (
    <>
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
        <AuthHeader onSignUp={() => setSignupOpen(true)} />
      </div>
      <SignupGate
        requested={signupOpen}
        onFinished={() => setSignupOpen(false)}
        onCancel={() => setSignupOpen(false)}
      >
        {route.page === "listing" ? <ListingDetail id={route.id} /> : null}
        {route.page === "seller" ? (
          <SellerProfilePage
            sellerId={route.id === "local" ? 1 : route.id}
            source={route.id === "local" ? localReviews() : { sellerProfile: publicSellerProfile }}
            onBack={() => {
              window.location.hash = "#/";
            }}
          />
        ) : null}
        {route.page === "orders" ? <BuyerOrders /> : null}
        {route.page === "order" ? <OrderStatus id={route.id} /> : null}
        {route.page === "sell" ? <ListingsHome /> : null}
        {route.page === "browse" ? <BrowseListings /> : null}
      </SignupGate>
    </>
  );
}

export default App;
