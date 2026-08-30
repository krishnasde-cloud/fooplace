export type ReviewStatus = "pending" | "approved" | "rejected";

export type SellerReview = {
  status: ReviewStatus;
  flagged: boolean;
  removed: boolean;
  note: string;
};
