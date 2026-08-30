export type AccountType = "buyer" | "seller";

export type SellerSignup = {
  neighbourhood: string;
  has_food_handler_certification: boolean;
  accepted_terms: boolean;
  facebook_marketplace_url: string;
  etransfer_email: string;
};

export type SignupPayload = {
  type: AccountType;
  name: string;
  phone?: string;
} & Partial<SellerSignup>;
