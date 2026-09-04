import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RiskScore } from "@/types/investigation";

const levelStyle = {
  LOW: "text-risk-low bg-risk-low/10",
  MEDIUM: "text-risk-medium bg-risk-medium/10",
  HIGH: "text-risk-high bg-risk-high/10",
  CRITICAL: "text-risk-critical bg-risk-critical/10",
};

export function RiskIntelligencePanel({
  risk,
  networkRisk,
  networkRiskSummary,
}: {
  risk: RiskScore;
  networkRisk?: string;
  networkRiskSummary?: string;
}) {
  const maxContribution = Math.max(...risk.factors.map((factor) => factor.contribution));
  const majorFactors = risk.factors.slice(0, 4);

  const netRiskLevel = (networkRisk || "LOW").toUpperCase();
  const netStyle =
    netRiskLevel === "CRITICAL"
      ? "text-risk-high bg-risk-high/15 border-risk-high/40"
      : netRiskLevel === "HIGH"
      ? "text-amber-400 bg-amber-500/15 border-amber-500/40"
      : netRiskLevel === "MEDIUM"
      ? "text-yellow-400 bg-yellow-500/15 border-yellow-500/40"
      : "text-teal bg-teal/15 border-teal/40";

  return (
    <aside className="rounded-2xl border border-border bg-card p-5 sm:p-6" aria-labelledby="risk-intelligence-title">
      <div className="flex items-start justify-between gap-3 border-b border-border pb-4">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.16em] text-muted-foreground uppercase font-mono">
            Dual Risk Intelligence
          </p>
          <h2 id="risk-intelligence-title" className="mt-1 text-lg font-semibold text-foreground">
            Risk Assessment
          </h2>
        </div>
        <AlertTriangle className="size-5 text-risk-high" aria-hidden="true" />
      </div>

      {/* Dual Risk Side-by-Side: ML Transaction Risk + NetworkX Graph Risk */}
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {/* ML Transaction Risk */}
        <div className="rounded-xl border border-border bg-muted/40 p-3.5">
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            ML Transaction Risk
          </span>
          <div className="mt-1.5 flex items-end justify-between">
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-bold tabular-nums text-foreground">{risk.value}</span>
              <span className="text-xs text-muted-foreground">/ {risk.max}</span>
            </div>
            <span className={cn("rounded-md border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider font-mono", levelStyle[risk.level])}>
              {risk.level}
            </span>
          </div>
          <span className="mt-1.5 block text-[10px] text-muted-foreground font-mono">XGBoost Feature Attribution</span>
        </div>

        {/* NetworkX Relational Risk */}
        <div className="rounded-xl border border-border bg-muted/40 p-3.5">
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            Network Topology Risk
          </span>
          <div className="mt-1.5 flex items-end justify-between">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-bold font-mono tracking-tight text-foreground">{netRiskLevel}</span>
            </div>
            <span className={cn("rounded-md border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider font-mono", netStyle)}>
              NetworkX
            </span>
          </div>
          <span className="mt-1.5 block text-[10px] text-muted-foreground truncate" title={networkRiskSummary || "Multi-hop Graph Analysis"}>
            {networkRiskSummary || "Multi-hop Relational Analysis"}
          </span>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground font-mono">
          Key Factors
        </h3>
        <div className="mt-3 space-y-2.5">
          {majorFactors.map((factor) => (
            <div key={factor.label} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background px-3 py-2.5">
              <span className="text-xs text-foreground">{factor.label}</span>
              <span className="font-mono text-[11px] font-semibold text-risk-high">+{factor.contribution}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 border-t border-border pt-5">
        <h3 className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground font-mono">
          Contribution profile
        </h3>
        <ul className="mt-4 space-y-3">
          {risk.factors.map((factor) => (
            <li key={factor.label}>
              <div className="flex justify-between gap-3 text-xs">
                <span className="text-foreground">{factor.label}</span>
                <span className="font-mono text-muted-foreground">+{factor.contribution}</span>
              </div>
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
                <div className="h-full rounded-full bg-violet" style={{ width: `${(factor.contribution / maxContribution) * 100}%` }} />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
