import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import {ArrowRight, LockKeyhole, ShieldCheck, AlertCircle, Info} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Mono, Reveal } from "@/components/landing/shared";
import { RoleSelector, type RoleId } from "@/components/auth/RoleSelector";
import { useRole } from "@/context/RoleContext";
import { Logo } from "@/components/Logo";

const roleTargetMap: Record<RoleId, string> = {
  investigator: "/dashboard",
  manager: "/dashboard",
  administrator: "/dashboard",
};

export const Route = createFileRoute("/sign-in")({
  component: SignInPage,
});

function SignInPage() {
  const { setRole } = useRole();
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] =
    useState<RoleId>("investigator");

  const [email, setEmail] = useState(
    "marcus.johnson@smarthorizon.ai"
  );

  const [password, setPassword] = useState("demo-password");

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [infoNotice, setInfoNotice] = useState("");

  const handleRoleSelect = (role: RoleId) => {
    setSelectedRole(role);

    setGeneralError("");
    setEmailError("");
    setPasswordError("");
    setInfoNotice("");
  };

  const handleSignIn = (roleToSet: RoleId = selectedRole) => {
    setRole(roleToSet);
    navigate({
      to: roleTargetMap[roleToSet],
    });
  };

  const handleSubmit = (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setEmailError("");
    setPasswordError("");
    setGeneralError("");
    setInfoNotice("");

    let hasError = false;

    if (!email.trim()) {
      setEmailError("Work email is required.");
      hasError = true;
    } else if (!/\S+@\S+\.\S+/.test(email.trim())) {
      setEmailError(
        "Please enter a valid work email address."
      );
      hasError = true;
    }

    if (!password.trim()) {
      setPasswordError("Password is required.");
      hasError = true;
    }

    if (!selectedRole) {
      setGeneralError(
        "Please select a user role to continue."
      );
      hasError = true;
    }

    if (hasError) return;

    handleSignIn(selectedRole);
  };

  const handleForgotPassword = (
    event: React.MouseEvent
  ) => {
    event.preventDefault();

    setInfoNotice(
      `Password reset instructions sent to ${
        email || "your registered email"
      }.`
    );
  };

  const handleSSOClick = () => {
    setInfoNotice(
      "SSO authentication verified. Logging in with corporate credentials..."
    );

    setTimeout(() => {
      handleSignIn(selectedRole);
    }, 600);
  };

  return (
    <div className="min-h-screen bg-offwhite p-3 md:p-8">
      <div className="mx-auto max-w-6xl overflow-hidden rounded-[32px] border border-border bg-background shadow-[var(--shadow-float)]">
        <div className="grid min-h-[calc(100vh-2rem)] lg:grid-cols-[1.08fr_0.92fr]">
          
          {/* LEFT IMAGE PANEL */}
          <Reveal>
            <div className="relative hidden h-full min-h-[calc(100vh-2rem)] overflow-hidden lg:block">
              <img
                src="/public/login.png"
                alt="Safe Flow Digital Investigator"
                className="absolute inset-0 h-full w-full object-cover"
              />
            </div>
          </Reveal>

          {/* RIGHT SIGN-IN PANEL */}
          <Reveal delay={80}>
            <div className="flex flex-col justify-center bg-background px-4 py-8 sm:px-6 lg:px-10 xl:px-14">
              <div className="mx-auto w-full max-w-md">

                {/* Mobile Header */}
                <div className="mb-6 flex items-center justify-between gap-3 lg:hidden">
                  <Logo size="md" rounded="lg" />

                  <Link
                    to="/"
                    className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Back to home
                  </Link>
                </div>

                {/* Desktop Header */}
                <div className="hidden items-center justify-between gap-3 border-b border-border pb-5 lg:flex">
                  <div>
                    <p className="text-sm font-semibold tracking-[0.16em] text-foreground">
                      Safe Flow
                    </p>

                    <Mono className="mt-1 text-muted-foreground">
                      Digital Investigator
                    </Mono>
                  </div>

                  <Link
                    to="/"
                    className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Back to home
                  </Link>
                </div>

                {/* Heading */}
                <div className="mt-8">
                  <h2 className="text-3xl font-semibold tracking-tight text-foreground">
                    Welcome back.
                  </h2>

                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    Sign in to your Safe Flow workspace.
                  </p>
                </div>

                {/* General Error */}
                {generalError && (
                  <div className="mt-4 flex items-center gap-2 rounded-xl border border-risk-high/30 bg-risk-high/10 p-3 text-xs text-risk-high">
                    <AlertCircle
                      className="size-4 flex-shrink-0"
                      aria-hidden
                    />

                    <span>{generalError}</span>
                  </div>
                )}

                {/* Info Notice */}
                {infoNotice && (
                  <div className="mt-4 flex items-center gap-2 rounded-xl border border-violet/30 bg-violet/10 p-3 text-xs text-violet">
                    <Info
                      className="size-4 flex-shrink-0"
                      aria-hidden
                    />

                    <span>{infoNotice}</span>
                  </div>
                )}

                {/* Role Selector */}
                <div className="mt-6">
                  <RoleSelector
                    selectedRole={selectedRole}
                    onRoleSelect={handleRoleSelect}
                    onContinue={() =>
                      handleSignIn(selectedRole)
                    }
                  />
                </div>

                {/* Sign In Form */}
                <form
                  className="mt-6 space-y-5"
                  onSubmit={handleSubmit}
                  noValidate
                >
                  {/* Email */}
                  <div className="space-y-1.5">
                    <label
                      htmlFor="email"
                      className="text-sm font-medium text-foreground"
                    >
                      Work Email
                    </label>

                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(event) => {
                        setEmail(event.target.value);

                        if (emailError) {
                          setEmailError("");
                        }
                      }}
                      placeholder="name@company.com"
                      className={`w-full rounded-xl border bg-background px-3.5 py-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:ring-2 focus:ring-violet/20 ${
                        emailError
                          ? "border-risk-high focus:border-risk-high"
                          : "border-border focus:border-violet/50"
                      }`}
                    />

                    {emailError && (
                      <p className="text-xs text-risk-high">
                        {emailError}
                      </p>
                    )}
                  </div>

                  {/* Password */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-3">
                      <label
                        htmlFor="password"
                        className="text-sm font-medium text-foreground"
                      >
                        Password
                      </label>

                      <button
                        type="button"
                        onClick={handleForgotPassword}
                        className="text-sm font-medium text-gov transition-colors hover:text-violet focus:outline-none"
                      >
                        Forgot password?
                      </button>
                    </div>

                    <div className="relative">
                      <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(event) => {
                          setPassword(event.target.value);

                          if (passwordError) {
                            setPasswordError("");
                          }
                        }}
                        placeholder="Enter your password"
                        className={`w-full rounded-xl border bg-background px-3.5 py-3 pr-10 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:ring-2 focus:ring-violet/20 ${
                          passwordError
                            ? "border-risk-high focus:border-risk-high"
                            : "border-border focus:border-violet/50"
                        }`}
                      />

                      <LockKeyhole
                        className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted-foreground"
                        aria-hidden
                      />
                    </div>

                    {passwordError && (
                      <p className="text-xs text-risk-high">
                        {passwordError}
                      </p>
                    )}
                  </div>

                  {/* Sign In Button */}
                  <Button
                    type="submit"
                    className="w-full rounded-xl"
                    size="lg"
                  >
                    Sign In

                    <ArrowRight
                      className="size-4"
                      aria-hidden
                    />
                  </Button>
                </form>

                {/* Divider */}
                <div className="my-6 flex items-center gap-4">
                  <div
                    className="h-px flex-1 bg-border"
                    aria-hidden
                  />

                  <span className="text-xs font-medium tracking-[0.16em] text-muted-foreground uppercase">
                    OR
                  </span>

                  <div
                    className="h-px flex-1 bg-border"
                    aria-hidden
                  />
                </div>

                {/* SSO */}
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleSSOClick}
                  className="w-full rounded-xl border-border bg-background"
                >
                  Continue with organization SSO
                </Button>

                {/* Security Notice */}
                <div className="mt-6 rounded-2xl border border-border bg-offwhite p-4">
                  <div className="flex items-start gap-3">
                    <ShieldCheck
                      className="mt-0.5 size-4 text-violet"
                      aria-hidden
                    />

                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Protected investigation environment
                      </p>

                      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                        Session activity is monitored and audit-ready.
                      </p>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </div>
  );
}