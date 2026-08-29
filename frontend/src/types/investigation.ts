export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface RiskFactor {
  label: string;
  contribution: number;
}

export interface RiskScore {
  value: number;
  max: number;
  level: RiskLevel;
  factors: RiskFactor[];
}

export interface Evidence {
  label: string;
  kind: "supporting" | "counter";
}

export interface Case {
  id: string;
  alert: string;
  openedAt: string;
  risk: RiskScore;
  evidence: Evidence[];
  recommendation: "ALLOW" | "VERIFY" | "ESCALATE";
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  tier: "orchestrator" | "collection" | "reasoning" | "human";
}

export interface RegulatorySource {
  code: string;
  name: string;
}

export interface InvestigationReportSection {
  title: string;
  summary: string;
}

export interface InvestigationReport {
  caseId: string;
  risk: RiskLevel;
  recommendation: string;
  sections: InvestigationReportSection[];
}

export interface ThreatItem {
  id: string;
  category: "Fraud Pattern" | "Regulatory Update" | "Threat Intelligence";
  headline: string;
  date: string;
  description: string;
}

export interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
  suspicious?: boolean;
}

export interface GraphEdge {
  from: string;
  to: string;
  amount: string;
  time: string;
}