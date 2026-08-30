import { Show, SignInButton, UserButton } from "@clerk/react";
import "./AuthHeader.css";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

type AuthHeaderProps = {
  onSignUp?: () => void;
};

export function AuthHeader({ onSignUp }: AuthHeaderProps) {
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
            <button type="button" className="auth-signup" onClick={onSignUp}>
              Sign up
            </button>
          </Show>
          <Show when="signed-in">
            <UserButton />
          </Show>
        </>
      ) : (
        <>
          <button type="button" className="auth-signup" onClick={onSignUp}>
            Sign up
          </button>
          <span className="auth-hint">Set VITE_CLERK_PUBLISHABLE_KEY to enable sign-in</span>
        </>
      )}
    </header>
  );
}
