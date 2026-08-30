import { useState } from "react";
import { AuthHeader } from "@/modules/clerk/index.ts";
import { BrowseListings, ListingDetail, ListingsHome } from "@/modules/listings/index.ts";
import { BuyerOrders, OrderStatus } from "@/modules/orders/index.ts";
import { SellerProfilePage, localReviews, publicSellerProfile } from "@/modules/reviews/index.ts";
import { PageSeo } from "@/modules/seo/index.ts";
import { SignupGate } from "@/modules/signup/index.ts";
import { paths, useRoute } from "./route.ts";
import "./App.css";

function App() {
  const [signupOpen, setSignupOpen] = useState(false);
  const route = useRoute();

  return (
    <>
      <PageSeo route={route} />
      <div className="app-top">
        <nav className="app-nav">
          <a href={paths.browse} className={route.page === "browse" || route.page === "listing" ? "active" : undefined}>
            Browse
          </a>
          <a href={paths.sell} className={route.page === "sell" ? "active" : undefined}>
            Sell
          </a>
          <a href={paths.orders} className={route.page === "orders" || route.page === "order" ? "active" : undefined}>
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
            indexable={route.id !== "local"}
            onBack={() => {
              window.location.assign(paths.browse);
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
