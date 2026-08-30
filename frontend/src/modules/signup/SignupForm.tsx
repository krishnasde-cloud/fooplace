import { useState } from "react";
import { PickupAddressField } from "@/modules/geoapify/index.ts";
import type { AccountType, SignupPayload } from "./types.ts";
import "./SignupForm.css";

type SignupFormProps = {
  initial?: SignupPayload | null;
  submitLabel: string;
  onSubmit: (payload: SignupPayload) => Promise<void> | void;
  onCancel?: () => void;
};

function cleanText(value: string): string {
  return [...value.trim()].filter((char) => char !== "\u200b").join("");
}

export function SignupForm({ initial, submitLabel, onSubmit, onCancel }: SignupFormProps) {
  const [accountType, setAccountType] = useState<AccountType | "">(initial?.type ?? "");
  const [hasFoodHandlerCertification, setHasFoodHandlerCertification] = useState(
    initial?.has_food_handler_certification ?? false,
  );
  const [acceptedTerms, setAcceptedTerms] = useState(initial?.accepted_terms ?? false);
  const [facebookMarketplaceUrl, setFacebookMarketplaceUrl] = useState(
    initial?.facebook_marketplace_url ?? "",
  );
  const [etransferEmail, setEtransferEmail] = useState(initial?.etransfer_email ?? "");
  const [pickupAddress, setPickupAddress] = useState(initial?.pickup_address ?? "");
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
    const address = cleanText(pickupAddress);
    if (!marketplaceUrl || !payoutEmail || !address) {
      setError("Sellers must add a Marketplace URL, e-transfer email, and pickup address.");
      return null;
    }
    return {
      type: "seller",
      has_food_handler_certification: hasFoodHandlerCertification,
      accepted_terms: true,
      facebook_marketplace_url: marketplaceUrl.includes("://")
        ? marketplaceUrl
        : `https://${marketplaceUrl}`,
      etransfer_email: payoutEmail,
      pickup_address: address,
    };
  }

  return (
    <form
      className="signup-form"
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
      <h1>Create your Fooplace account</h1>
      <p className="signup-lead">Tell us how you will use Fooplace.</p>

      <fieldset className="signup-roles">
        <legend>I am a</legend>
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
      </fieldset>

      {accountType === "seller" ? (
        <fieldset className="signup-seller">
          <legend>Seller details</legend>
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
            I acknowledge the terms and conditions (we will add these later)
          </label>
          <label className="signup-field">
            Facebook Marketplace profile URL
            <input
              type="url"
              value={facebookMarketplaceUrl}
              onChange={(event) => setFacebookMarketplaceUrl(event.target.value)}
              placeholder="https://www.facebook.com/marketplace/profile/…"
              required
            />
          </label>
          <label className="signup-field">
            E-transfer email
            <input
              type="email"
              value={etransferEmail}
              onChange={(event) => setEtransferEmail(event.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>
          <PickupAddressField value={pickupAddress} onChange={setPickupAddress} />
        </fieldset>
      ) : null}

      {error ? <p className="signup-error">{error}</p> : null}

      <div className="signup-actions">
        <button type="submit" className="signup-submit" disabled={pending}>
          {pending ? "Saving…" : submitLabel}
        </button>
        {onCancel ? (
          <button type="button" className="signup-cancel" onClick={onCancel} disabled={pending}>
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}
