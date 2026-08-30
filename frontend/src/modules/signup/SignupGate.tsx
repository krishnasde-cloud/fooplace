import { useAuth } from "@clerk/react";
import { useSignUp } from "@clerk/react/legacy";
import { type ReactNode, useEffect, useState } from "react";
import { completeSignup } from "./api.ts";
import { clearPendingSignup, loadPendingSignup, savePendingSignup } from "./pending.ts";
import { SignupAuth } from "./SignupAuth.tsx";
import { SignupForm } from "./SignupForm.tsx";
import type { SignupPayload, SocialProvider } from "./types.ts";

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
  const [pickedAccount, setPickedAccount] = useState(false);

  useEffect(() => {
    if (!requested) {
      setPickedAccount(false);
    }
  }, [requested]);

  if (!requested) {
    return children;
  }
  if (!pickedAccount) {
    return (
      <SignupAuth
        onCancel={onCancel}
        onSocial={() => {
          setPickedAccount(true);
        }}
      />
    );
  }
  return (
    <SignupForm
      initial={loadPendingSignup()}
      onSubmit={(payload) => {
        savePendingSignup(payload);
        onFinished();
      }}
    />
  );
}

function ClerkSignupGate({ requested, onFinished, onCancel, children }: SignupGateProps) {
  const { isSignedIn, getToken } = useAuth();
  const { isLoaded, signUp } = useSignUp();
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
  const alreadyJoined = Boolean(profile?.type);
  const incomplete = Boolean(profile && !profile.type);

  useEffect(() => {
    if (requested && alreadyJoined) {
      onFinished();
    }
  }, [alreadyJoined, onFinished, requested]);

  async function social(provider: SocialProvider) {
    if (!isLoaded || !signUp) {
      throw new Error("Clerk is still loading.");
    }
    await signUp.authenticateWithRedirect({
      strategy: provider === "google" ? "oauth_google" : "oauth_facebook",
      redirectUrl: `${window.location.origin}/`,
      redirectUrlComplete: `${window.location.origin}/#/signup`,
    });
  }

  async function submit(payload: SignupPayload) {
    const token = await getToken();
    if (!token) {
      throw new Error("Clerk session token missing");
    }
    await completeSignup(token, payload);
    clearPendingSignup();
    setMe({ type: payload.type });
    onFinished();
  }

  if (incomplete) {
    return (
      <section>
        {loadError ? <p className="signup-error">{loadError}</p> : null}
        <SignupForm initial={loadPendingSignup() ?? undefined} onSubmit={submit} />
      </section>
    );
  }

  if (requested && !isSignedIn) {
    return (
      <section>
        {loadError ? <p className="signup-error">{loadError}</p> : null}
        <SignupAuth onCancel={onCancel} onSocial={social} />
      </section>
    );
  }

  return children;
}
