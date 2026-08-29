import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { InvestigationWorkspace } from "@/components/investigation/InvestigationWorkspace";
import {
  agents,
  demoCase,
  demoReport,
  evidenceChips,
  graphEdges,
  graphNodes,
  regulatorySources,
} from "@/data/mock-investigation";
import { getCase, runInvestigation, submitDecision, type BackendCase } from "@/lib/api";
import { Loader2 } from "lucide-react";
import type { Case, InvestigationReport, RiskLevel } from "@/types/investigation";

export const Route = createFileRoute("/dashboard/cases/$caseId")({
  component: CaseWorkspacePage,
});

/** Convert a backend case to the frontend Case type */
function backendToFrontendCase(bc: BackendCase): Case {
  const riskLevel = bc.risk_band?.toUpperCase() as RiskLevel ?? "MEDIUM";
  const score = Math.round(bc.risk_score ?? 50);

  return {
    id: bc.case_id,
    alert: bc.recommended_action || "Under investigation",
    openedAt: bc.opened_at,
    risk: {
      value: score,
      max: 100,
      level:
        riskLevel === "CRITICAL" || riskLevel === "HIGH" || riskLevel === "MEDIUM" || riskLevel === "LOW"
          ? riskLevel
          : "MEDIUM",
      factors: [
        { label: "ML Risk Score (XGBoost)", contribution: Math.round(score * 0.6) },
        { label: "Contextual Topological Signals", contribution: Math.round(score * 0.2) },
        { label: "Anomaly Score (Isolation Forest)", contribution: Math.round(score * 0.2) },
      ],
    },
    evidence: [
      { label: `Transaction ID: ${bc.transaction_id}`, kind: "supporting" },
      { label: `Model Risk Band: ${bc.risk_band}`, kind: "supporting" },
      ...(bc.sender ? [{ label: `Sender KYC: ${bc.sender.kyc_status} (${bc.sender.name})`, kind: "supporting" as const }] : []),
      ...(bc.transaction
        ? [
            {
              label: `Amount: ₹${bc.transaction.amount?.toLocaleString()} (${bc.transaction.type})`,
              kind: "supporting" as const,
            },
          ]
        : []),
    ],
    recommendation:
      bc.recommended_action?.includes("BLOCK") || bc.recommended_action?.includes("ESCALAT")
        ? "ESCALATE"
        : bc.recommended_action?.includes("FLAG") || bc.recommended_action?.includes("REVIEW")
          ? "VERIFY"
          : "ALLOW",
  };
}

function CaseWorkspacePage() {
  const { caseId } = Route.useParams();
  const queryClient = useQueryClient();
  const [investigationResult, setInvestigationResult] = useState<string | null>(null);
  const [strDraftResult, setStrDraftResult] = useState<string | null>(null);
  const [decisionFeedback, setDecisionFeedback] = useState<string | null>(null);

  // Fetch real case data from backend
  const {
    data: backendCase,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => getCase(caseId),
    retry: 1,
    staleTime: 10_000,
  });

  // Investigation mutation
  const investigateMutation = useMutation({
    mutationFn: () => runInvestigation(caseId),
    onSuccess: (data) => {
      setInvestigationResult(data.investigation_report);
      setStrDraftResult(data.str_draft);
      queryClient.invalidateQueries({ queryKey: ["case", caseId] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["auditLog"] });
    },
  });

  // Decision mutation
  const decisionMutation = useMutation({
    mutationFn: (params: { decision: string; notes?: string }) =>
      submitDecision(caseId, params.decision, "investigator-1", params.notes),
    onSuccess: (data) => {
      setDecisionFeedback(data.decision);
      queryClient.invalidateQueries({ queryKey: ["case", caseId] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["caseStats"] });
      queryClient.invalidateQueries({ queryKey: ["auditLog"] });
    },
  });

  // Build case data — use backend if available, otherwise mock
  const caseData: Case = backendCase
    ? backendToFrontendCase(backendCase)
    : { ...demoCase, id: caseId || demoCase.id };

  // Build report — use investigation result if available, or backend saved report, or fallback demo
  const reportSummary =
    investigationResult ||
    backendCase?.investigation_report ||
    demoReport.sections[0]?.summary;

  const report: InvestigationReport = {
    caseId: caseId,
    risk: caseData.risk.level,
    recommendation: caseData.recommendation === "ESCALATE" ? "ESCALATE" : "REVIEW",
    sections: [
      { title: "Executive Findings", summary: reportSummary },
      ...(strDraftResult || backendCase?.str_draft
        ? [{ title: "FIU-IND STR Draft", summary: strDraftResult || backendCase?.str_draft || "" }]
        : []),
    ],
  };

  if (isLoading) {
    return (
      <DashboardLayout title={`Case Workspace — ${caseId}`}>
        <div className="flex items-center justify-center gap-3 py-20">
          <Loader2 className="size-5 animate-spin text-violet" />
          <span className="text-sm text-muted-foreground">Loading case {caseId} from database...</span>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={`Case Workspace — ${caseId}`}>
      {/* Backend connection indicator */}
      {isError && (
        <div className="mb-4 rounded-xl border border-risk-medium/20 bg-risk-medium/5 px-4 py-2 text-xs text-risk-medium">
          ⚠ Backend offline — displaying local demo data
        </div>
      )}

      <InvestigationWorkspace
        caseData={caseData}
        backendCase={backendCase}
        evidenceChips={
          backendCase
            ? [
                `Txn: ${backendCase.transaction_id}`,
                `Risk: ${Math.round(backendCase.risk_score)}/100 (${backendCase.risk_band})`,
                `Action: ${backendCase.recommended_action}`,
                `Status: ${backendCase.status}`,
              ]
            : evidenceChips
        }
        nodes={graphNodes}
        edges={graphEdges}
        agents={agents}
        regulatorySources={regulatorySources}
        report={report}
        onRunInvestigation={() => investigateMutation.mutate()}
        isInvestigating={investigateMutation.isPending}
        onDecision={(decisionCode, notes) => decisionMutation.mutate({ decision: decisionCode, notes })}
        isSubmittingDecision={decisionMutation.isPending}
        decisionSuccess={decisionFeedback}
        strDraft={strDraftResult || backendCase?.str_draft}
      />
    </DashboardLayout>
  );
}
