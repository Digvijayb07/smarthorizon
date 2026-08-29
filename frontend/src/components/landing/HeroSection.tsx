import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Eyebrow, Mono, Reveal, RiskBadge, useCountUp, useInView } from "./shared";
import { TransactionGraph } from "./TransactionGraph";
import { demoCase, evidenceChips } from "@/data/mock-investigation";

export function HeroSection() {
  const { ref, visible } = useInView<HTMLDivElement>(0.3);
  const score = useCountUp(demoCase.risk.value, visible);

  return (
    <section id="top" className="relative overflow-hidden bg-background pt-32 pb-20 md:pt-40 md:pb-28">
      <div className="container-hz relative">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 text-center">
          <Reveal>
            <Eyebrow>Safe Flow</Eyebrow>
          </Reveal>
          <Reveal delay={80}>
            <h1 className="text-4xl leading-[1.05] font-semibold tracking-tight text-balance md:text-6xl">
              Detect. Investigate. Explain. Decide.
            </h1>
          </Reveal>
          <Reveal delay={160}>
            <p className="max-w-2xl text-base leading-relaxed text-muted-foreground md:text-lg">
              Safe Flow helps financial institutions convert suspicious activity into a disciplined,
              auditable investigation workflow with clear risk assessment and regulatory context.
            </p>
          </Reveal>
          <Reveal delay={240}>
            <div className="flex flex-col items-center gap-3 sm:flex-row">
              <Button asChild size="lg" className="rounded-xl shadow-sm">
                <Link to="/sign-in">
                  Launch Investigator <ArrowRight className="size-4" aria-hidden />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="rounded-xl border-border bg-background">
                <a href="#platform">Explore the Platform</a>
              </Button>
            </div>
          </Reveal>
          <Reveal delay={320}>
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 pt-2">
              {["RISK REVIEW", "REGULATORY CONTEXT", "AUDIT TRAIL"].map((item) => (
                <Mono key={item} className="eyebrow text-muted-foreground">
                  {item}
                </Mono>
              ))}
            </div>
          </Reveal>
        </div>

        <Reveal delay={380} className="mt-16">
          <div ref={ref} className="relative mx-auto max-w-5xl">
            <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
              <div className="flex items-center justify-between border-b border-border bg-muted px-5 py-3">
                <Mono className="text-muted-foreground">CASE {demoCase.id}</Mono>
                <Mono className="text-muted-foreground">INVESTIGATION WORKSPACE</Mono>
              </div>

              <div className="grid gap-8 p-6 md:grid-cols-[1.1fr_1fr] md:p-8">
                <div className="flex flex-col gap-6">
                  <div>
                    <Mono className="text-muted-foreground">RISK SCORE</Mono>
                    <div className="mt-2 flex items-end gap-3">
                      <span className="text-5xl font-semibold tracking-tight tabular-nums">
                        {score}
                      </span>
                      <span className="pb-1.5 text-lg text-muted-foreground">/ 100</span>
                      <RiskBadge level={demoCase.risk.level} className="mb-2" />
                    </div>
                    <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-risk-high transition-[width] duration-1000 ease-out"
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>

                  <div className="rounded-xl border border-border bg-muted p-4">
                    <Mono className="text-muted-foreground">ALERT</Mono>
                    <p className="mt-1 text-sm font-medium">{demoCase.alert}</p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {evidenceChips.map((chip) => (
                      <span
                        key={chip}
                        className="rounded-md border border-border bg-background px-2.5 py-1.5 font-mono text-[0.68rem] text-muted-foreground"
                      >
                        {chip}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-offwhite p-4">
                  <Mono className="text-muted-foreground">TRANSACTION GRAPH</Mono>
                  <TransactionGraph compact className="mt-2" />
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}