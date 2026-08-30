import type { SellerCard } from "@/modules/reviews/types.ts";

export type ListingStatus = "active" | "sold_out";

export type OrderStatusCounts = {
  pending: number;
  confirmed: number;
  ready_for_pickup: number;
  completed: number;
  expired: number;
  picked_up: number;
  cancelled: number;
};

export type Listing = {
  id: number;
  dish_name: string;
  description: string;
  price: string;
  quantity_available: number;
  neighbourhood: string;
  pickup_date: string;
  pickup_window_start: string;
  pickup_window_end: string;
  status: ListingStatus;
  photo: string;
  expires_at: string;
  expired: boolean;
  created_at: string;
  updated_at: string;
  order_status: OrderStatusCounts;
  seller?: SellerCard;
  cuisine: string;
  photos: string[];
  sold_out: boolean;
  seller_name: string;
  pickup_start: string;
  pickup_end: string;
};

export type ListingCatalog = {
  listings: Listing[];
  filters: {
    neighbourhoods: string[];
    cuisines: string[];
  };
};

export type ListingInput = {
  photo: string;
  dish_name: string;
  description: string;
  price: string;
  quantity_available: number;
  neighbourhood: string;
  pickup_date: string;
  pickup_window_start: string;
  pickup_window_end: string;
  status?: ListingStatus;
  cuisine?: string;
};

export type ListingSource = {
  listMine: () => Promise<Listing[]>;
  listActive: () => Promise<Listing[]>;
  create: (input: ListingInput) => Promise<Listing>;
  update: (id: number, input: Partial<ListingInput>) => Promise<Listing>;
  relist: (id: number) => Promise<Listing>;
  remove: (id: number) => Promise<void>;
};
