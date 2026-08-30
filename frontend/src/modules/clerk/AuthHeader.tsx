import { Show, SignInButton, useAuth, UserButton } from "@clerk/react";
import { useEffect, useState } from "react";
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
            <AdminLink />
            <UserButton />
          </Show>
        </>
      ) : (
        <>
          <a className="auth-admin" href="/admin/">
            Admin
          </a>
          <button type="button" className="auth-signup" onClick={onSignUp}>
            Sign up
          </button>
          <span className="auth-hint">Set VITE_CLERK_PUBLISHABLE_KEY to enable sign-in</span>
        </>
      )}
    </header>
  );
}

function AdminLink() {
  const { isSignedIn, getToken } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (!isSignedIn) {
      setIsAdmin(false);
      return;
    }
    const controller = new AbortController();
    getToken()
      .then(async (token) => {
        if (!token) {
          return;
        }
        const response = await fetch("/api/me/", {
          signal: controller.signal,
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          return;
        }
        const body = (await response.json()) as { type?: string };
        setIsAdmin(body.type === "admin");
      })
      .catch(() => {
        setIsAdmin(false);
      });
    return () => controller.abort();
  }, [getToken, isSignedIn]);

  if (!isAdmin) {
    return null;
  }
  return (
    <a className="auth-admin" href="/admin/">
      Admin
    </a>
  );
}
