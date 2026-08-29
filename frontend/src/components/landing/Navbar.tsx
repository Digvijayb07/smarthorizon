import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";

const navItems = [
  { label: "Platform", href: "#platform" },
  { label: "Investigation", href: "#investigation" },
  { label: "Intelligence", href: "#intelligence" },
  { label: "Compliance", href: "#compliance" },
  { label: "About", href: "#about" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 border-b transition-all duration-300",
        scrolled
          ? "border-border bg-background/85 backdrop-blur-md"
          : "border-transparent bg-background",
      )}
    >
      <div
        className={cn(
          "container-hz flex items-center justify-between transition-all duration-300",
          scrolled ? "h-14" : "h-18",
        )}
      >
        <a
          href="#top"
          className="rounded-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        >
          <img
            src="/public/main_logo.png"
            alt="Logo"
            className="h-9 w-auto object-contain"
          />
        </a>

        <nav aria-label="Primary" className="hidden items-center gap-8 lg:flex">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="rounded text-sm font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <ThemeToggle compact />

          <a
            href="#faq"
            className="rounded px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            FAQ
          </a>

          <Link
            to="/sign-in"
            className="rounded px-3 py-2 text-sm font-medium text-foreground transition-colors hover:text-primary focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            Sign In
          </Link>

          <Button asChild size="sm" className="rounded-xl">
            <Link to="/sign-in">Launch Investigator</Link>
          </Button>
        </div>

        <div className="flex items-center gap-2 lg:hidden">
          <ThemeToggle compact />

          <Button asChild size="sm" className="rounded-xl">
            <Link to="/sign-in">Launch</Link>
          </Button>

          <button
            id="mobile-nav-button"
            type="button"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((v) => !v)}
            className="flex size-9 items-center justify-center rounded-lg border border-border text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          >
            {open ? <X className="size-4" /> : <Menu className="size-4" />}
          </button>
        </div>
      </div>

      <div
        id="mobile-nav"
        className={cn(
          "overflow-hidden border-t border-border bg-background transition-[max-height,opacity] duration-300 lg:hidden",
          open ? "max-h-96 opacity-100" : "max-h-0 opacity-0",
        )}
      >
        <nav
          aria-label="Mobile"
          className="container-hz flex flex-col gap-1 py-4"
        >
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              onClick={() => setOpen(false)}
              className="rounded-lg px-2 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              {item.label}
            </a>
          ))}

          <a
            href="#faq"
            onClick={() => setOpen(false)}
            className="rounded-lg px-2 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            FAQ
          </a>

          <Link
            to="/sign-in"
            onClick={() => setOpen(false)}
            className="rounded-lg px-2 py-2.5 text-sm font-semibold text-primary transition-colors hover:bg-muted"
          >
            Sign In / Launch
          </Link>
        </nav>
      </div>
    </header>
  );
}