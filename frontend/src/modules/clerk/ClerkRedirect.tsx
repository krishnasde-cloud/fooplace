import { AuthenticateWithRedirectCallback } from "@clerk/react";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

export function ClerkRedirect() {
  if (!publishableKey || !/__clerk/i.test(window.location.search)) {
    return null;
  }
  return (
    <AuthenticateWithRedirectCallback
      continueSignUpUrl="/#/signup"
      signInForceRedirectUrl="/#/signup"
      signUpForceRedirectUrl="/#/signup"
    />
  );
}
