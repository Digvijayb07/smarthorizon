import { Network, Route } from "lucide-react";
import { TransactionGraph } from "@/components/landing/TransactionGraph";
import type { GraphEdge, GraphNode } from "@/types/investigation";

export interface InvestigationGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function InvestigationGraph({ nodes, edges }: InvestigationGraphProps) {
  const suspiciousNodes = nodes.filter((node) => node.suspicious).length;

  return (
    <section className="rounded-2xl border border-border bg-card p-5 sm:p-6" aria-labelledby="transaction-graph-title">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-muted-foreground uppercase">Evidence</p>
          <h2 id="transaction-graph-title" className="mt-1 text-lg font-semibold text-foreground">Transaction Graph</h2>
        </div>
        <Network className="size-5 text-violet" aria-hidden="true" />
      </div>
      <div className="mt-5 rounded-xl border border-border bg-background/60 p-3 sm:p-5">
        <TransactionGraph />
      </div>
      <div className="mt-5 grid grid-cols-3 divide-x divide-border rounded-lg border border-border bg-muted/30">
        <div className="p-3"><p className="text-xl font-semibold">{nodes.length}</p><p className="text-[11px] text-muted-foreground uppercase">Accounts</p></div>
        <div className="p-3"><p className="text-xl font-semibold">{edges.length}</p><p className="text-[11px] text-muted-foreground uppercase">Transfers</p></div>
        <div className="p-3"><p className="text-xl font-semibold text-risk-high">{suspiciousNodes}</p><p className="text-[11px] text-muted-foreground uppercase">Flagged</p></div>
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground"><Route className="size-3.5 text-violet" aria-hidden="true" />Solid links show the transaction relationships in this case.</div>
    </section>
  );
}
