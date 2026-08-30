import { useAuth } from "@clerk/react";
import { useSignUp } from "@clerk/react/legacy";
import { type ReactNode, useEffect, useState } from "react";
import { completeSignup } from "./api.ts";
import { clearPendingSignup, loadPendingSignup, savePendingSignup } from "./pending.ts";
import { SignupForm, type SocialProvider } from "./SignupForm.tsx";
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
  if (!requested) {
    return children;
  }
  return (
    <SignupForm
      initial={loadPendingSignup()}
      submitLabel="Create account"
      showSocial
      onCancel={onCancel}
      onSocial={() => {
        throw new Error("Set VITE_CLERK_PUBLISHABLE_KEY to enable Google and Facebook sign-up.");
      }}
      onSubmit={(payload) => {
        savePendingSignup(payload);
        onFinished();
      }}
    />
  );
}

function ClerkSignupGate({ requested, onFinished, onCancel, children }: SignupGateProps) {
  const { isSignedIn, getToken } = useAuth();
  const { isLoaded, signUp, setActive } = useSignUp();
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
  const showForm = (requested && !alreadyJoined) || incomplete;

  useEffect(() => {
    if (requested && alreadyJoined) {
      onFinished();
    }
  }, [alreadyJoined, onFinished, requested]);

  if (!showForm) {
    return children;
  }

  async function submit(payload: SignupPayload, login?: { email: string; password: string }) {
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
    if (!login) {
      throw new Error("Enter an email and password, or continue with Google or Facebook.");
    }
    if (!isLoaded || !signUp) {
      throw new Error("Clerk is still loading.");
    }
    const created = await signUp.create({
      emailAddress: login.email,
      password: login.password,
    });
    if (created.status === "complete" && created.createdSessionId) {
      await setActive({ session: created.createdSessionId });
      return;
    }
    if (created.unverifiedFields?.includes("email_address")) {
      await created.prepareEmailAddressVerification({ strategy: "email_code" });
    }
    throw new Error("Check your email to verify this account, then sign in.");
  }

  async function social(provider: SocialProvider, payload: SignupPayload | null) {
    if (payload) {
      savePendingSignup(payload);
    }
    if (!isLoaded || !signUp) {
      throw new Error("Clerk is still loading.");
    }
    await signUp.authenticateWithRedirect({
      strategy: provider === "google" ? "oauth_google" : "oauth_facebook",
      redirectUrl: `${window.location.origin}/`,
      redirectUrlComplete: `${window.location.origin}/#/signup`,
    });
  }

  return (
    <section>
      {loadError ? <p className="signup-error">{loadError}</p> : null}
      <SignupForm
        initial={loadPendingSignup() ?? undefined}
        submitLabel={isSignedIn ? "Complete signup" : "Create account"}
        showSocial={!isSignedIn}
        showEmail={!isSignedIn}
        showSubmit
        onCancel={incomplete ? undefined : onCancel}
        onSocial={social}
        onSubmit={submit}
      />
    </section>
  );
}
