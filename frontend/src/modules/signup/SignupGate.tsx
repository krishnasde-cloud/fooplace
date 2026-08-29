import { useAuth, useClerk } from "@clerk/react";
import { type ReactNode, useEffect, useState } from "react";
import { completeSignup } from "./api.ts";
import { clearPendingSignup, loadPendingSignup, savePendingSignup } from "./pending.ts";
import { SignupForm } from "./SignupForm.tsx";
import type { SignupPayload } from "./types.ts";

type MeResponse = {
  type: "buyer" | "seller" | "admin" | "";
};

type SignupGateProps = {
  requested: boolean;
  onFinished: () => void;
  onCancel: () => void;
  children: ReactNode;
};

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

export function SignupGate(props: SignupGateProps) {
  if (publishableKey) {
    return <ClerkSignupGate {...props} />;
  }
  return <LocalSignupGate {...props} />;
}

function LocalSignupGate({ requested, onFinished, onCancel, children }: SignupGateProps) {
  const [saved, setSaved] = useState<SignupPayload | null>(null);

  if (!requested) {
    return children;
  }
  if (saved) {
    return (
      <section className="signup-form">
        <h1>Thanks — we saved your signup details</h1>
        <p className="signup-lead">
          {saved.type === "seller"
            ? "You chose a seller account. We will ask you to create a login next."
            : "You chose a buyer account. We will ask you to create a login next."}
        </p>
        <div className="signup-actions">
          <button type="button" className="signup-submit" onClick={onFinished}>
            Back home
          </button>
        </div>
      </section>
    );
  }
  return (
    <SignupForm
      initial={loadPendingSignup()}
      submitLabel="Continue"
      onCancel={onCancel}
      onSubmit={(payload) => {
        savePendingSignup(payload);
        setSaved(payload);
      }}
    />
  );
}

function ClerkSignupGate({ requested, onFinished, onCancel, children }: SignupGateProps) {
  const { isSignedIn, getToken } = useAuth();
  const { openSignUp } = useClerk();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSignedIn) {
      return;
    }

    const controller = new AbortController();
    getToken()
      .then((token) => {
        if (!token) {
          throw new Error("Clerk session token missing");
        }
        return fetch("/api/me/", {
          signal: controller.signal,
          headers: { Authorization: `Bearer ${token}` },
        });
      })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Backend returned HTTP ${response.status}`);
        }
        return (await response.json()) as MeResponse;
      })
      .then((payload) => {
        setMe(payload);
        setLoadError(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setLoadError(error instanceof Error ? error.message : "Unknown error");
      });

    return () => controller.abort();
  }, [getToken, isSignedIn]);

  useEffect(() => {
    if (!isSignedIn || !me || me.type) {
      return;
    }
    const pending = loadPendingSignup();
    if (!pending) {
      return;
    }

    const controller = new AbortController();
    getToken()
      .then((token) => {
        if (!token) {
          throw new Error("Clerk session token missing");
        }
        return completeSignup(token, pending, controller.signal);
      })
      .then(() => {
        clearPendingSignup();
        setMe({ type: pending.type });
        onFinished();
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setLoadError(error instanceof Error ? error.message : "Could not finish signup.");
      });

    return () => controller.abort();
  }, [getToken, isSignedIn, me, onFinished]);

  const profile = isSignedIn ? me : null;
  const incomplete = Boolean(profile && !profile.type);
  const showForm = requested || incomplete;

  if (!showForm) {
    return children;
  }

  async function submit(payload: SignupPayload) {
    if (isSignedIn) {
      const token = await getToken();
      if (!token) {
        throw new Error("Clerk session token missing");
      }
      await completeSignup(token, payload);
      clearPendingSignup();
      setMe({ type: payload.type });
      onFinished();
      return;
    }
    savePendingSignup(payload);
    onFinished();
    openSignUp();
  }

  return (
    <section>
      {loadError ? <p className="signup-error">{loadError}</p> : null}
      <SignupForm
        initial={loadPendingSignup() ?? undefined}
        submitLabel={isSignedIn ? "Complete signup" : "Continue to create account"}
        onCancel={incomplete ? undefined : onCancel}
        onSubmit={submit}
      />
    </section>
  );
}
