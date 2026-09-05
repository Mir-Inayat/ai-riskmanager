export type Alert = {
  transactionId: string;
  timestamp: number;
  amount: number;
  riskScore: number;             // calibrated probability
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
    severity: string;
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
