import { type ReactNode, useState } from "react";
import type { AccountType, SignupPayload } from "./types.ts";
import "./SignupForm.css";

export type SocialProvider = "google" | "facebook";

type SignupFormProps = {
  initial?: SignupPayload | null;
  submitLabel: string;
  showSocial?: boolean;
  showEmail?: boolean;
  showSubmit?: boolean;
  children?: ReactNode;
  onSubmit: (payload: SignupPayload, login?: { email: string; password: string }) => Promise<void> | void;
  onSocial?: (provider: SocialProvider, payload: SignupPayload | null) => Promise<void> | void;
  onCancel?: () => void;
};

function cleanText(value: string): string {
  return [...value.trim()].filter((char) => char !== "\u200b").join("");
}

export function SignupForm({
  initial,
  submitLabel,
  showSocial = false,
  showEmail = false,
  showSubmit = true,
  children,
  onSubmit,
  onSocial,
  onCancel,
}: SignupFormProps) {
  const [accountType, setAccountType] = useState<AccountType | "">(initial?.type ?? "");
  const [hasFoodHandlerCertification, setHasFoodHandlerCertification] = useState(
    initial?.has_food_handler_certification ?? false,
  );
  const [acceptedTerms, setAcceptedTerms] = useState(initial?.accepted_terms ?? false);
  const [facebookMarketplaceUrl, setFacebookMarketplaceUrl] = useState(
    initial?.facebook_marketplace_url ?? "",
  );
  const [etransferEmail, setEtransferEmail] = useState(initial?.etransfer_email ?? "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function peekPayload(): SignupPayload | null {
    if (accountType === "buyer") {
      return { type: "buyer" };
    }
    if (accountType !== "seller" || !acceptedTerms) {
      return null;
    }
    const marketplaceUrl = cleanText(facebookMarketplaceUrl);
    const payoutEmail = cleanText(etransferEmail);
    if (!marketplaceUrl || !payoutEmail) {
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
    };
  }

  function buildPayload(): SignupPayload | null {
    if (accountType !== "buyer" && accountType !== "seller") {
      setError("Choose whether you are a buyer or a seller.");
      return null;
    }
    const payload = peekPayload();
    if (payload) {
      return payload;
    }
    if (!acceptedTerms) {
      setError("Sellers must acknowledge the terms and conditions.");
      return null;
    }
    setError("Sellers must add a Facebook Marketplace URL and an e-transfer email.");
    return null;
  }

  function run(action: () => Promise<void> | void) {
    setError(null);
    setPending(true);
    Promise.resolve(action())
      .catch((submitError: unknown) => {
        setError(submitError instanceof Error ? submitError.message : "Signup failed.");
      })
      .finally(() => setPending(false));
  }

  return (
    <section className="signup-form">
      <h1>Create your Fooplace account</h1>
      <p className="signup-lead">
        {showSocial
          ? "Continue with Google or Facebook, or create an account with email."
          : "Tell us how you will use Fooplace."}
      </p>

      {showSocial ? (
        <div className="signup-social">
          <button
            type="button"
            className="signup-social-btn"
            disabled={pending}
            onClick={() => run(() => onSocial?.("google", peekPayload()))}
          >
            <GoogleMark />
            Continue with Google
          </button>
          <button
            type="button"
            className="signup-social-btn"
            disabled={pending}
            onClick={() => run(() => onSocial?.("facebook", peekPayload()))}
          >
            <FacebookMark />
            Continue with Facebook
          </button>
        </div>
      ) : null}

      <form
        onSubmit={(event) => {
          event.preventDefault();
          const payload = buildPayload();
          if (!payload) {
            return;
          }
          const loginEmail = cleanText(email);
          const loginPassword = password;
          run(() =>
            onSubmit(
              payload,
              loginEmail && loginPassword ? { email: loginEmail, password: loginPassword } : undefined,
            ),
          );
        }}
      >
        {showSocial && !showEmail ? (
          <p className="signup-divider">or choose your account type</p>
        ) : null}
        {showEmail ? <p className="signup-divider">or use email</p> : null}

        {showEmail ? (
          <>
            <label className="signup-field">
              Email
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </label>
            <label className="signup-field">
              Password
              <input
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Create a password"
              />
            </label>
          </>
        ) : null}

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
          </fieldset>
        ) : null}

        {error ? <p className="signup-error">{error}</p> : null}

        {showSubmit || onCancel ? (
          <div className="signup-actions">
            {showSubmit ? (
              <button type="submit" className="signup-submit" disabled={pending}>
                {pending ? "Saving…" : submitLabel}
              </button>
            ) : null}
            {onCancel ? (
              <button type="button" className="signup-cancel" onClick={onCancel} disabled={pending}>
                Cancel
              </button>
            ) : null}
          </div>
        ) : null}
      </form>
      {children}
    </section>
  );
}

function GoogleMark() {
  return (
    <svg className="signup-social-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h6.5c-.3 1.5-1.2 2.8-2.5 3.7v3h4c2.4-2.2 3.5-5.5 3.5-8.8z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.2 0 5.9-1.1 7.9-2.9l-4-3c-1.1.8-2.5 1.2-3.9 1.2-3 0-5.6-2-6.5-4.8H1.4v3.1C3.4 21.4 7.4 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.5 14.5c-.2-.7-.4-1.4-.4-2.1s.1-1.4.4-2.1V7.2H1.4C.5 9 0 10.9 0 12.4s.5 3.4 1.4 5.2l4.1-3.1z"
      />
      <path
        fill="#EA4335"
        d="M12 4.8c1.7 0 3.3.6 4.5 1.8l3.4-3.4C17.9 1.2 15.2 0 12 0 7.4 0 3.4 2.6 1.4 6.4l4.1 3.1C6.4 6.8 9 4.8 12 4.8z"
      />
    </svg>
  );
}

function FacebookMark() {
  return (
    <svg className="signup-social-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#1877F2"
        d="M24 12.1C24 5.4 18.6 0 12 0S0 5.4 0 12.1C0 18.1 4.4 23.1 10.1 24v-8.4H7.1v-3.5h3V9.4c0-3 1.8-4.6 4.5-4.6 1.3 0 2.6.2 2.6.2v2.9h-1.5c-1.5 0-1.9.9-1.9 1.8v2.2h3.3l-.5 3.5h-2.8V24C19.6 23.1 24 18.1 24 12.1z"
      />
    </svg>
  );
}
