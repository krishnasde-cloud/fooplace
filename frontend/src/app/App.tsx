import { useState } from "react";
import { AuthHeader } from "@/modules/clerk/index.ts";
import { ListingsHome } from "@/modules/listings/index.ts";
import { SignupGate } from "@/modules/signup/index.ts";
import "./App.css";

function App() {
  const [signupOpen, setSignupOpen] = useState(false);

  return (
    <>
      <AuthHeader onSignUp={() => setSignupOpen(true)} />
      <SignupGate
        requested={signupOpen}
        onFinished={() => setSignupOpen(false)}
        onCancel={() => setSignupOpen(false)}
      >
        <ListingsHome />
      </SignupGate>
    </>
  );
}

export default App;
