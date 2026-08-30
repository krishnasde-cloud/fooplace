import { useState } from "react";
import type { AccountType, SignupPayload } from "./types.ts";
import "./SignupForm.css";

type SignupFormProps = {
  initial?: SignupPayload | null;
  onSubmit: (payload: SignupPayload) => Promise<void> | void;
};

function cleanText(value: string): string {
  return [...value.trim()].filter((char) => char !== "\u200b").join("");
}

export function SignupForm({ initial, onSubmit }: SignupFormProps) {
  const [accountType, setAccountType] = useState<AccountType | "">(initial?.type ?? "");
  const [hasFoodHandlerCertification, setHasFoodHandlerCertification] = useState(
    initial?.has_food_handler_certification ?? false,
  );
  const [acceptedTerms, setAcceptedTerms] = useState(initial?.accepted_terms ?? false);
  const [facebookMarketplaceUrl, setFacebookMarketplaceUrl] = useState(
    initial?.facebook_marketplace_url ?? "",
  );
  const [etransferEmail, setEtransferEmail] = useState(initial?.etransfer_email ?? "");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function buildPayload(): SignupPayload | null {
    if (accountType !== "buyer" && accountType !== "seller") {
      setError("Choose whether you are a buyer or a seller.");
      return null;
    }
    if (accountType === "buyer") {
      return { type: "buyer" };
    }
    if (!acceptedTerms) {
      setError("Sellers must acknowledge the terms and conditions.");
      return null;
    }
    const marketplaceUrl = cleanText(facebookMarketplaceUrl);
    const payoutEmail = cleanText(etransferEmail);
    return {
      type: "seller",
      has_food_handler_certification: hasFoodHandlerCertification,
      accepted_terms: true,
      facebook_marketplace_url: marketplaceUrl
        ? marketplaceUrl.includes("://")
          ? marketplaceUrl
          : `https://${marketplaceUrl}`
        : "",
      etransfer_email: payoutEmail,
    };
  }

  return (
    <section className="signup-card">
      <h1>Welcome</h1>
      <p className="signup-lead">Are you buying or selling on Fooplace?</p>
      <form
        className="signup-profile"
        onSubmit={(event) => {
          event.preventDefault();
          const payload = buildPayload();
          if (!payload) {
            return;
          }
          setError(null);
          setPending(true);
          Promise.resolve(onSubmit(payload))
            .catch((submitError: unknown) => {
              setError(submitError instanceof Error ? submitError.message : "Signup failed.");
            })
            .finally(() => setPending(false));
        }}
      >
        <div className="signup-roles" role="radiogroup" aria-label="Account type">
          <label className={accountType === "buyer" ? "selected" : undefined}>
            <input
              type="radio"
              name="account-type"
              value="buyer"
              checked={accountType === "buyer"}
              onChange={() => setAccountType("buyer")}
            />
            Buyer
          </label>
          <label className={accountType === "seller" ? "selected" : undefined}>
            <input
              type="radio"
              name="account-type"
              value="seller"
              checked={accountType === "seller"}
              onChange={() => setAccountType("seller")}
            />
            Seller
          </label>
        </div>

        {accountType === "seller" ? (
          <div className="signup-seller">
            <label className="signup-check">
              <input
                type="checkbox"
                checked={hasFoodHandlerCertification}
                onChange={(event) => setHasFoodHandlerCertification(event.target.checked)}
              />
              I have a food handler certification
            </label>
            <label className="signup-check">
              <input
                type="checkbox"
                checked={acceptedTerms}
                onChange={(event) => setAcceptedTerms(event.target.checked)}
              />
              I acknowledge the terms and conditions
            </label>
            <label className="signup-field">
              Facebook Marketplace URL <span>optional</span>
              <input
                type="url"
                value={facebookMarketplaceUrl}
                onChange={(event) => setFacebookMarketplaceUrl(event.target.value)}
                placeholder="https://facebook.com/marketplace/…"
              />
            </label>
            <label className="signup-field">
              E-transfer email <span>optional</span>
              <input
                type="email"
                value={etransferEmail}
                onChange={(event) => setEtransferEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </label>
          </div>
        ) : null}

        {error ? <p className="signup-error">{error}</p> : null}
        <button type="submit" className="signup-submit" disabled={pending}>
          {pending ? "Saving…" : "Continue"}
        </button>
      </form>
    </section>
  );
}
