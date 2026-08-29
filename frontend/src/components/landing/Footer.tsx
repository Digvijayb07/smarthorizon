import { Mono } from "./shared";

const platformLinks = [
  { label: "Investigator", href: "#investigation" },
  { label: "Risk Intelligence", href: "#intelligence" },
  { label: "Graph Analysis", href: "#graph" },
  { label: "Compliance", href: "#compliance" },
  { label: "Reports", href: "#reports" },
];

const resourcesLinks = [
  { label: "Documentation", href: "#faq" },
  { label: "Architecture", href: "#intelligence" },
  { label: "Research", href: "#threat-watch" },
  { label: "FAQ", href: "#faq" },
];

const companyLinks = [
  { label: "About", href: "#about" },
  { label: "Contact", href: "#launch" },
];

const legalLinks = [
  { label: "Privacy", href: "#faq" },
  { label: "Security", href: "#launch" },
  { label: "Terms", href: "#launch" },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-muted">
      <div className="container-hz py-12 md:py-16">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr_1fr_1fr]">
          <div>
            <img
              src="/public/main_logo.png"
              alt="Logo"
              className="h-10 w-auto object-contain"
            />

            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              Digital Investigator for Financial Crime Intelligence
            </p>
          </div>

          <div>
            <Mono className="text-muted-foreground">PLATFORM</Mono>
            <ul className="mt-4 space-y-2 text-sm text-foreground/80">
              {platformLinks.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.href}
                    className="transition-colors hover:text-foreground"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <Mono className="text-muted-foreground">RESOURCES</Mono>
            <ul className="mt-4 space-y-2 text-sm text-foreground/80">
              {resourcesLinks.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.href}
                    className="transition-colors hover:text-foreground"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <Mono className="text-muted-foreground">COMPANY</Mono>
            <ul className="mt-4 space-y-2 text-sm text-foreground/80">
              {companyLinks.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.href}
                    className="transition-colors hover:text-foreground"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <Mono className="text-muted-foreground">LEGAL</Mono>
            <ul className="mt-4 space-y-2 text-sm text-foreground/80">
              {legalLinks.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.href}
                    className="transition-colors hover:text-foreground"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-border pt-6 text-sm text-muted-foreground">
          © 2026 Safe Flow 
        </div>
      </div>
    </footer>
  );
}