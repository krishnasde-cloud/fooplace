import { useState } from "react";
import type { SocialProvider } from "./types.ts";
import "./SignupForm.css";

type SignupAuthProps = {
  onSocial: (provider: SocialProvider) => Promise<void> | void;
  onCancel?: () => void;
};

export function SignupAuth({ onSocial, onCancel }: SignupAuthProps) {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<SocialProvider | null>(null);

  function start(provider: SocialProvider) {
    setError(null);
    setPending(provider);
    Promise.resolve(onSocial(provider))
      .catch((socialError: unknown) => {
        setError(socialError instanceof Error ? socialError.message : "Signup failed.");
      })
      .finally(() => setPending(null));
  }

  return (
    <section className="signup-card">
      <h1>Sign up</h1>
      <p className="signup-lead">Continue with Google or Facebook.</p>
      <button
        type="button"
        className="signup-social-btn"
        disabled={pending !== null}
        onClick={() => start("google")}
      >
        <GoogleMark />
        {pending === "google" ? "Continuing…" : "Continue with Google"}
      </button>
      <button
        type="button"
        className="signup-social-btn"
        disabled={pending !== null}
        onClick={() => start("facebook")}
      >
        <FacebookMark />
        {pending === "facebook" ? "Continuing…" : "Continue with Facebook"}
      </button>
      {error ? <p className="signup-error">{error}</p> : null}
      {onCancel ? (
        <button type="button" className="signup-text-btn" onClick={onCancel} disabled={pending !== null}>
          Cancel
        </button>
      ) : null}
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
