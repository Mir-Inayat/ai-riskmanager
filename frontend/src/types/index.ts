export type Alert = {
  transactionId: string;
  timestamp: number;
  amount: number;
  riskScore: number;             // calibrated probability [0, 1]
  decision: "ALLOW" | "REVIEW" | "SIMULATED_HOLD";
  reasonCodes: string[];
  expectedCost: number;
  linkedEntityCount: number;
  modelVersion: string;
};

export type CaseEvidence = {
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
};

export type GraphNode = {
  id: string;
  group: "transaction" | "device" | "email" | "transaction_prior_fraud" | "card" | "ip";
  val: number;
};

export type GraphLink = {
  source: string;
  target: string;
};

export type GraphData = {
  nodes: GraphNode[];
  links: GraphLink[];
};

export type SystemMetrics = {
  precision: number;
  recall: number;
  prAuc: number;
  recallAtBudget: number;
  preventableExposureCaptured: number;
  falsePositiveCost: number;
  f1Score?: number;
  totalScored?: number;
  fraudDetected?: number;
  reviewQueueSize?: number;
};

export type CostMetrics = {
  expectedCost: number;
  netPreventedExposure: number;
  falsePositiveCost: number;
  manualReviewCost: number;
  missedFraudCost: number;
  totalExposure: number;
  costReductionPct: number;
};

