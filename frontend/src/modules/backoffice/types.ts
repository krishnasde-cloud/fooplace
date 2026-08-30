export type ReviewStatus = "pending" | "approved" | "rejected";

export type SellerReview = {
  status: ReviewStatus;
  flagged: boolean;
  removed: boolean;
  note: string;
};

export type ListingModeration = {
  flagged: boolean;
  removed: boolean;
  note: string;
};

export type OfficeSeller = {
  user_id: string;
  email: string;
  is_active: boolean;
  type: string;
  seller: {
    has_food_handler_certification: boolean;
    accepted_terms: boolean;
    facebook_marketplace_url: string;
    etransfer_email: string;
  } | null;
  review: SellerReview;
};

export type OfficeListing = {
  id: number;
  dish_name: string;
  description: string;
  price: string;
  quantity_available: number;
  neighbourhood: string;
  pickup_date: string;
  status: string;
  seller_user_id: string;
  seller_email: string;
  order_status: Record<string, number>;
  moderation: ListingModeration;
};

export type OfficeOrder = {
  id: number;
  listing_id: number;
  quantity: number;
  status: string;
  created_at: string;
  dish_name: string;
  buyer_email: string;
  seller_email: string;
};

export type OfficeSummary = {
  pending_sellers: number;
  flagged_sellers: number;
  removed_sellers: number;
  listings: number;
  flagged_listings: number;
  removed_listings: number;
  orders: number;
};

export type SellerAction = "approve" | "reject" | "flag" | "unflag" | "remove" | "restore";
export type ListingAction = "flag" | "unflag" | "remove" | "restore";

export type OfficeSource = {
  summary: () => Promise<OfficeSummary>;
  sellers: (status: string) => Promise<OfficeSeller[]>;
  actSeller: (userId: string, action: SellerAction, note: string) => Promise<OfficeSeller>;
  listings: () => Promise<OfficeListing[]>;
  actListing: (id: number, action: ListingAction, note: string) => Promise<OfficeListing>;
  orders: () => Promise<OfficeOrder[]>;
};
