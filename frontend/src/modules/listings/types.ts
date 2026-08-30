export type ListingStatus = "active" | "sold_out";

export type OrderStatusCounts = {
  pending: number;
  confirmed: number;
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
  created_at: string;
  updated_at: string;
  order_status: OrderStatusCounts;
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
};

export type ListingSource = {
  listMine: () => Promise<Listing[]>;
  listActive: () => Promise<Listing[]>;
  create: (input: ListingInput) => Promise<Listing>;
  update: (id: number, input: Partial<ListingInput>) => Promise<Listing>;
  remove: (id: number) => Promise<void>;
};
