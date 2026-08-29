import { Show, SignInButton, SignUpButton, UserButton } from "@clerk/react";
import "./AuthHeader.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

export function AuthHeader() {
  return (
    <header className="auth-bar">
      {publishableKey ? (
        <>
          <Show when="signed-out">
            <SignInButton>
              <button type="button" className="auth-signin">
                Sign in
              </button>
            </SignInButton>
            <SignUpButton>
              <button type="button" className="auth-signup">
                Sign up
              </button>
            </SignUpButton>
          </Show>
          <Show when="signed-in">
            <UserButton />
          </Show>
        </>
      ) : (
        <span className="auth-hint">Set VITE_CLERK_PUBLISHABLE_KEY to enable sign-in</span>
      )}
    </header>
  );
}
