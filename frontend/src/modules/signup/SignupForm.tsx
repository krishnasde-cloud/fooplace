import { useState } from "react";
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
  const [name, setName] = useState(initial?.name ?? "");
  const [phone, setPhone] = useState(initial?.phone ?? "");
  const [neighbourhood, setNeighbourhood] = useState(initial?.neighbourhood ?? "");
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
    const displayName = cleanText(name);
    const phoneNumber = cleanText(phone);
    if (!displayName) {
      setError("Add your name so people know who they are meeting.");
      return null;
    }
    if (accountType === "buyer") {
      return { type: "buyer", name: displayName, phone: phoneNumber || undefined };
    }
    if (!acceptedTerms) {
      setError("Sellers must acknowledge the terms and conditions.");
      return null;
    }
    const area = cleanText(neighbourhood);
    if (!area) {
      setError("Sellers must add a neighbourhood, not a street address.");
      return null;
    }
    const marketplaceUrl = cleanText(facebookMarketplaceUrl);
    const payoutEmail = cleanText(etransferEmail);
    if (!marketplaceUrl || !payoutEmail) {
      setError("Sellers must add a Facebook Marketplace URL and an e-transfer email.");
      return null;
    }
    return {
      type: "seller",
      name: displayName,
      phone: phoneNumber || undefined,
      neighbourhood: area,
      has_food_handler_certification: hasFoodHandlerCertification,
      accepted_terms: true,
      facebook_marketplace_url: marketplaceUrl.includes("://")
        ? marketplaceUrl
        : `https://${marketplaceUrl}`,
      etransfer_email: payoutEmail,
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

      {accountType ? (
        <fieldset>
          <legend>Your details</legend>
          <label className="signup-field">
            Name
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Asha Patel"
              required
            />
          </label>
          <label className="signup-field">
            Phone
            <input
              type="tel"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              placeholder="Optional if you use email"
            />
          </label>
          <p className="signup-lead">No verification for now — name plus phone or email is enough.</p>
        </fieldset>
      ) : null}

      {accountType === "seller" ? (
        <fieldset className="signup-seller">
          <legend>Seller details</legend>
          <label className="signup-field">
            Neighbourhood
            <input
              type="text"
              value={neighbourhood}
              onChange={(event) => setNeighbourhood(event.target.value)}
              placeholder="Kensington"
              required
            />
          </label>
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
