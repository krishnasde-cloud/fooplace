export type SellerCard = {
  id: number;
  name: string;
  neighbourhood: string;
  has_food_handler_certification: boolean;
  joined_at: string;
  completed_orders: number;
  average_rating: number | null;
  review_count: number;
};

export type Review = {
  id: number;
  stars: number;
  comment: string;
  created_at: string;
  buyer_name: string;
};

export type SellerProfile = SellerCard & {
  reviews: Review[];
};

export type BuyerOrder = {
  id: number;
  listing_id: number;
  dish_name: string;
  quantity: number;
  status: "pending" | "confirmed" | "ready_for_pickup" | "completed" | "expired" | "picked_up" | "cancelled";
  created_at: string;
  seller: SellerCard;
  review: Review | null;
};

export type ReviewsSource = {
  sellerProfile: (id: number) => Promise<SellerProfile>;
  myOrders: () => Promise<BuyerOrder[]>;
  completeOrder: (id: number) => Promise<BuyerOrder>;
  leaveReview: (orderId: number, stars: number, comment: string) => Promise<Review>;
  placeOrder: (listingId: number, quantity?: number, dishName?: string) => Promise<unknown>;
};
