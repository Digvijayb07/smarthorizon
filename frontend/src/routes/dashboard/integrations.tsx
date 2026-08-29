import { createFileRoute } from "@tanstack/react-router";
import { Sliders, CheckCircle2, RefreshCw } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";

export const Route = createFileRoute("/dashboard/integrations")({
  component: IntegrationsPage,
});

const integrationsList = [
  { name: "Core Banking Ledger API", category: "Core Banking", status: "Connected", latency: "14ms" },
  { name: "OFAC & UN Sanctions Feed", category: "Sanctions Telemetry", status: "Connected", latency: "8ms" },
  { name: "FinCEN E-Filing Portal Gateway", category: "Regulatory", status: "Connected", latency: "32ms" },
  { name: "Blockchain Transaction Monitor", category: "Crypto Analytics", status: "Connected", latency: "25ms" },
];

function IntegrationsPage() {
  return (
    <DashboardLayout title="Data Integrations & Connectors">
      <div className="space-y-6 max-w-4xl">
        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-violet/10 text-violet">
              <Sliders className="size-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Data Ingestion Pipeline Connectors</h2>
              <p className="text-xs text-muted-foreground">Manage real-time transactional feeds, sanctions watchlists, and core banking gateways.</p>
            </div>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {integrationsList.map((item) => (
            <div key={item.name} className="rounded-2xl border border-border bg-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground uppercase">{item.category}</span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal bg-teal/10 px-2.5 py-0.5 rounded-full">
                  <CheckCircle2 className="size-3" />
                  {item.status}
                </span>
              </div>
              <h3 className="font-semibold text-foreground text-sm">{item.name}</h3>
              <p className="text-xs text-muted-foreground">Response latency: {item.latency}</p>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
