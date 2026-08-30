export type AccountType = "buyer" | "seller";

export type SocialProvider = "google" | "facebook";

export type SellerSignup = {
  has_food_handler_certification: boolean;
  accepted_terms: boolean;
  facebook_marketplace_url: string;
  etransfer_email: string;
};

export type SignupPayload = {
  type: AccountType;
} & Partial<SellerSignup>;
