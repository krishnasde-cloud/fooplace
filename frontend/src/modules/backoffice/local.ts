import type {
  ListingAction,
  OfficeListing,
  OfficeOrder,
  OfficeSeller,
  OfficeSource,
  SellerAction,
} from "./types.ts";

function seedSellers(): OfficeSeller[] {
  return [
    {
      user_id: "user_pending",
      email: "newcook@example.com",
      is_active: true,
      type: "seller",
      seller: {
        has_food_handler_certification: true,
        accepted_terms: true,
        facebook_marketplace_url: "https://facebook.com/marketplace/profile/1",
        etransfer_email: "newcook@example.com",
      },
      review: { status: "pending", flagged: false, removed: false, note: "" },
    },
    {
      user_id: "user_live",
      email: "seller@example.com",
      is_active: true,
      type: "seller",
      seller: {
        has_food_handler_certification: false,
        accepted_terms: true,
        facebook_marketplace_url: "https://facebook.com/marketplace/profile/2",
        etransfer_email: "payouts@example.com",
      },
      review: { status: "approved", flagged: false, removed: false, note: "" },
    },
  ];
}

function seedListings(): OfficeListing[] {
  return [
    {
      id: 1,
      dish_name: "Butter chicken",
      description: "Homemade, mild spice, includes rice.",
      price: "14.00",
      quantity_available: 4,
      neighbourhood: "Kensington",
      pickup_date: "2026-09-02",
      status: "active",
      seller_user_id: "user_live",
      seller_email: "seller@example.com",
      order_status: { pending: 1, confirmed: 0, picked_up: 0, cancelled: 0 },
      moderation: { flagged: false, removed: false, note: "" },
    },
  ];
}

function seedOrders(): OfficeOrder[] {
  return [
    {
      id: 11,
      listing_id: 1,
      quantity: 1,
      status: "pending",
      created_at: "2026-08-30T12:00:00Z",
      dish_name: "Butter chicken",
      buyer_email: "buyer@example.com",
      seller_email: "seller@example.com",
    },
  ];
}

function applySeller(seller: OfficeSeller, action: SellerAction, note: string): OfficeSeller {
  const review = { ...seller.review, note: note || seller.review.note };
  if (action === "approve") {
    return { ...seller, is_active: true, review: { ...review, status: "approved", removed: false } };
  }
  if (action === "reject") {
    return { ...seller, review: { ...review, status: "rejected", removed: false } };
  }
  if (action === "flag") {
    return { ...seller, review: { ...review, flagged: true } };
  }
  if (action === "unflag") {
    return { ...seller, review: { ...review, flagged: false } };
  }
  if (action === "remove") {
    return {
      ...seller,
      is_active: false,
      review: { ...review, removed: true, flagged: true },
    };
  }
  return {
    ...seller,
    is_active: true,
    review: {
      ...review,
      removed: false,
      flagged: false,
      status: review.status === "rejected" ? "approved" : review.status,
    },
  };
}

function applyListing(listing: OfficeListing, action: ListingAction, note: string): OfficeListing {
  const moderation = { ...listing.moderation, note: note || listing.moderation.note };
  if (action === "flag") {
    return { ...listing, moderation: { ...moderation, flagged: true } };
  }
  if (action === "unflag") {
    return { ...listing, moderation: { ...moderation, flagged: false } };
  }
  if (action === "remove") {
    return { ...listing, moderation: { ...moderation, removed: true, flagged: true } };
  }
  return { ...listing, moderation: { ...moderation, removed: false, flagged: false } };
}

export function localOffice(): OfficeSource {
  let sellers = seedSellers();
  let listings = seedListings();
  const orders = seedOrders();

  return {
    async summary() {
      return {
        pending_sellers: sellers.filter((item) => item.review.status === "pending").length,
        flagged_sellers: sellers.filter((item) => item.review.flagged).length,
        removed_sellers: sellers.filter((item) => item.review.removed || !item.is_active).length,
        listings: listings.length,
        flagged_listings: listings.filter((item) => item.moderation.flagged).length,
        removed_listings: listings.filter((item) => item.moderation.removed).length,
        orders: orders.length,
      };
    },
    async sellers(status) {
      if (status === "pending") {
        return sellers.filter((item) => item.review.status === "pending");
      }
      if (status === "approved") {
        return sellers.filter((item) => item.review.status === "approved");
      }
      if (status === "rejected") {
        return sellers.filter((item) => item.review.status === "rejected");
      }
      if (status === "flagged") {
        return sellers.filter((item) => item.review.flagged);
      }
      if (status === "removed") {
        return sellers.filter((item) => item.review.removed || !item.is_active);
      }
      return sellers;
    },
    async actSeller(userId, action, note) {
      sellers = sellers.map((item) =>
        item.user_id === userId ? applySeller(item, action, note) : item,
      );
      const next = sellers.find((item) => item.user_id === userId);
      if (!next) {
        throw new Error("Seller not found");
      }
      return next;
    },
    async listings() {
      return listings;
    },
    async actListing(listingId, action, note) {
      listings = listings.map((item) =>
        item.id === listingId ? applyListing(item, action, note) : item,
      );
      const next = listings.find((item) => item.id === listingId);
      if (!next) {
        throw new Error("Listing not found");
      }
      return next;
    },
    async orders() {
      return orders;
    },
  };
}
