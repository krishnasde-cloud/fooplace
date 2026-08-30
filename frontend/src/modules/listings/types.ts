export type Listing = {
  id: number;
  dish_name: string;
  description: string;
  cuisine: string;
  neighbourhood: string;
  price: string;
  quantity_available: number;
  photos: string[];
  pickup_start: string;
  pickup_end: string;
  sold_out: boolean;
  seller_name: string;
};

export type ListingCatalog = {
  listings: Listing[];
  filters: {
    neighbourhoods: string[];
    cuisines: string[];
  };
};
