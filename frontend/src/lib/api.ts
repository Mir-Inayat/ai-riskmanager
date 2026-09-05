import { Alert, CaseEvidence, CostMetrics, SystemMetrics } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AlertDetailResponse extends Alert {
  status?: "pending" | "reviewed" | "dismissed" | string;
  shapContributions: {
    feature: string;
    contribution: number;
  }[];
  ruleTriggers: {
    ruleId: string;
    severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | string;
    explanation: string;
  }[];
  graphContext: {
    clusterId?: string;
    sharedAttributes: string[];
    clusterSize: number;
  };
  costBreakdown: {
    expectedFraudLoss: number;
    frictionCostIfFP: number;
    reviewCost: number;
    netExposure: number;
  };
  auditHash: string;
  transactionDetails?: Record<string, any>;
  auditTrail?: {
    step: string;
    timestamp: number;
    action: string;
    hash: string;
  }[];
}

export interface AnalystDecisionResponse {
  success: boolean;
  transactionId: string;
  decision: string;
  status: string;
  auditHash: string;
  timestamp: number;
  message: string;
}

/**
 * Fetch list of transaction alerts.
 * Endpoint: GET /api/alerts
 */
export async function fetchAlerts(): Promise<Alert[]> {
  const res = await fetch(`${API_BASE_URL}/api/alerts`, {
    headers: {
      Accept: "application/json",
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch alerts: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch case evidence & details for a specific alert.
 * Endpoint: GET /api/alerts/${id}
 */
export async function fetchAlertById(id: string): Promise<AlertDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/alerts/${encodeURIComponent(id)}`, {
    headers: {
      Accept: "application/json",
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch alert details for ${id}: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch held-out test detection performance metrics.
 * Endpoint: GET /api/metrics/detection
 */
export async function fetchMetrics(): Promise<SystemMetrics> {
  const res = await fetch(`${API_BASE_URL}/api/metrics/detection`, {
    headers: {
      Accept: "application/json",
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch detection metrics: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * Fetch aggregate financial risk & cost metrics.
 * Endpoint: GET /api/metrics/cost
 */
export async function fetchCostMetrics(): Promise<CostMetrics> {
  const res = await fetch(`${API_BASE_URL}/api/metrics/cost`, {
    headers: {
      Accept: "application/json",
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch cost metrics: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * Record an analyst's review decision for a transaction alert.
 * Endpoint: POST /api/alerts/${id}/decision
 */
export async function submitDecision(
  id: string,
  decision: string,
  reviewer: string = "analyst_1",
  notes?: string
): Promise<AnalystDecisionResponse> {
  const res = await fetch(`${API_BASE_URL}/api/alerts/${encodeURIComponent(id)}/decision`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      decision,
      reviewer,
      notes,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit decision: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
