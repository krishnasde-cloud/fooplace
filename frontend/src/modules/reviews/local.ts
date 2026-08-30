import { loadPendingSignup } from "@/modules/signup/pending.ts";
import type { BuyerOrder, Review, ReviewsSource, SellerCard, SellerProfile } from "./types.ts";

const ORDERS_KEY = "fooplace.buyerOrders";
const REVIEWS_KEY = "fooplace.sellerReviews";

function loadOrders(): BuyerOrder[] {
  const raw = localStorage.getItem(ORDERS_KEY);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw) as BuyerOrder[];
  } catch {
    return [];
  }
}

function saveOrders(orders: BuyerOrder[]) {
  localStorage.setItem(ORDERS_KEY, JSON.stringify(orders));
}

function loadReviews(): Review[] {
  const raw = localStorage.getItem(REVIEWS_KEY);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw) as Review[];
  } catch {
    return [];
  }
}

function saveReviews(reviews: Review[]) {
  localStorage.setItem(REVIEWS_KEY, JSON.stringify(reviews));
}

export function localSellerCard(): SellerCard {
  const pending = loadPendingSignup();
  const reviews = loadReviews();
  const orders = loadOrders();
  const completed = orders.filter((order) => order.status === "picked_up").length;
  const average =
    reviews.length === 0
      ? null
      : Math.round((reviews.reduce((sum, review) => sum + review.stars, 0) / reviews.length) * 100) /
        100;
  return {
    id: 1,
    name: pending?.name || "Seller",
    neighbourhood: pending?.neighbourhood || "",
    has_food_handler_certification: pending?.has_food_handler_certification ?? false,
    joined_at: new Date().toISOString(),
    completed_orders: completed,
    average_rating: average,
    review_count: reviews.length,
  };
}

export function localReviews(): ReviewsSource {
  return {
    async sellerProfile() {
      return {
        ...localSellerCard(),
        reviews: loadReviews(),
      } satisfies SellerProfile;
    },
    async myOrders() {
      return loadOrders();
    },
    async completeOrder(id) {
      const orders = loadOrders().map((order) =>
        order.id === id ? { ...order, status: "picked_up" as const } : order,
      );
      saveOrders(orders);
      const found = orders.find((order) => order.id === id);
      if (!found) {
        throw new Error("Order not found");
      }
      return found;
    },
    async leaveReview(orderId, stars, comment) {
      const review: Review = {
        id: Date.now(),
        stars,
        comment,
        created_at: new Date().toISOString(),
        buyer_name: loadPendingSignup()?.name || "Buyer",
      };
      saveReviews([review, ...loadReviews()]);
      saveOrders(
        loadOrders().map((order) => (order.id === orderId ? { ...order, review } : order)),
      );
      return review;
    },
    async placeOrder(listingId, quantity = 1, dishName = "Local dish") {
      const seller = localSellerCard();
      const order: BuyerOrder = {
        id: Date.now(),
        listing_id: listingId,
        dish_name: dishName,
        quantity,
        status: "pending",
        created_at: new Date().toISOString(),
        seller,
        review: null,
      };
      saveOrders([order, ...loadOrders()]);
      return order;
    },
  };
}
