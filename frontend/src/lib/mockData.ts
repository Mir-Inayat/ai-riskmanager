import rawAlerts from "../fixtures/alerts.json";
import rawEvidence from "../fixtures/case-evidence.json";
import rawGraph from "../fixtures/graph-data.json";
import rawMetrics from "../fixtures/metrics.json";
import { Alert, CaseEvidence, GraphData, SystemMetrics } from "../types";

export const mockAlerts: Alert[] = rawAlerts as Alert[];
export const mockCaseEvidence: CaseEvidence = rawEvidence as CaseEvidence;
export const mockGraphData: GraphData = rawGraph as GraphData;
export const mockMetrics: SystemMetrics = rawMetrics as SystemMetrics;

// Additional simulated historical alerts for rich queue demonstrations
const extendedAlerts: Alert[] = [
  ...mockAlerts,
  {
    transactionId: "TXN-77412-D",
    timestamp: 1693566300000,
    amount: 18450.00,
    riskScore: 0.82,
    decision: "SIMULATED_HOLD",
    reasonCodes: ["HIGH_VALUE_TRANSACTION", "CARD_VELOCITY_24H"],
    expectedCost: 15129.00,
    linkedEntityCount: 3,
    modelVersion: "lgbm-v1.0"
  },
  {
    transactionId: "TXN-65901-E",
    timestamp: 1693566720000,
    amount: 3200.75,
    riskScore: 0.58,
    decision: "REVIEW",
    reasonCodes: ["UNUSUAL_DEVICE_FINGERPRINT"],
    expectedCost: 1856.43,
    linkedEntityCount: 1,
    modelVersion: "lgbm-v1.0"
  },
  {
    transactionId: "TXN-54319-F",
    timestamp: 1693567100000,
    amount: 450.00,
    riskScore: 0.08,
    decision: "ALLOW",
    reasonCodes: [],
    expectedCost: 36.00,
    linkedEntityCount: 0,
    modelVersion: "lgbm-v1.0"
  },
  {
    transactionId: "TXN-43210-G",
    timestamp: 1693567540000,
    amount: 78900.00,
    riskScore: 0.94,
    decision: "SIMULATED_HOLD",
    reasonCodes: ["HIGH_VALUE_TRANSACTION", "CLUSTER_PRIOR_FRAUD", "NEW_EMAIL_DOMAIN"],
    expectedCost: 74166.00,
    linkedEntityCount: 5,
    modelVersion: "lgbm-v1.0"
  },
  {
    transactionId: "TXN-32109-H",
    timestamp: 1693567890000,
    amount: 1950.00,
    riskScore: 0.49,
    decision: "REVIEW",
    reasonCodes: ["CROSS_BORDER_GEO_MISMATCH"],
    expectedCost: 955.50,
    linkedEntityCount: 2,
    modelVersion: "lgbm-v1.0"
  }
];

export function getAllAlerts(): Alert[] {
  return extendedAlerts;
}

export function getAlertById(id: string): Alert | undefined {
  const match = extendedAlerts.find((a) => a.transactionId === id);
  if (match) return match;
  // Fallback default for any random ID in demo
  return {
    transactionId: id,
    timestamp: Date.now() - 3600000,
    amount: 45000.50,
    riskScore: 0.89,
    decision: "SIMULATED_HOLD",
    reasonCodes: ["HIGH_VALUE_TRANSACTION", "NEW_EMAIL_DOMAIN"],
    expectedCost: 40050.44,
    linkedEntityCount: 4,
    modelVersion: "lgbm-v1.0"
  };
}

export function getCaseEvidence(transactionId: string): CaseEvidence {
  const alert = getAlertById(transactionId);
  const base = mockCaseEvidence;
  if (!alert) return base;

  // Dynamically adapt cost breakdown to match transaction amount if different
  const expectedFraudLoss = alert.amount * alert.riskScore;
  const netExposure = Math.max(0, expectedFraudLoss - base.costBreakdown.frictionCostIfFP);

  return {
    ...base,
    costBreakdown: {
      expectedFraudLoss,
      frictionCostIfFP: 150.00,
      reviewCost: 25.00,
      netExposure
    }
  };
}

export function getSystemMetrics(): SystemMetrics {
  return mockMetrics;
}

export function getGraphData(): GraphData {
  return mockGraphData;
}

// Benford Law Reference Distribution
export const benfordExpected = [
  { digit: 1, expected: 30.1, observed: 29.4 },
  { digit: 2, expected: 17.6, observed: 18.1 },
  { digit: 3, expected: 12.5, observed: 12.0 },
  { digit: 4, expected: 9.7, observed: 9.9 },
  { digit: 5, expected: 7.9, observed: 8.2 },
  { digit: 6, expected: 6.7, observed: 6.5 },
  { digit: 7, expected: 5.8, observed: 6.1 },
  { digit: 8, expected: 5.1, observed: 5.0 },
  { digit: 9, expected: 4.6, observed: 4.8 }
];

export const modelComparisonData = [
  {
    model: "Heuristic Rules Engine",
    type: "Baseline Gates",
    precision: 0.61,
    recall: 0.54,
    f1: 0.57,
    prAuc: 0.59,
    preventedExposure: 0.52,
    latencyMs: "0.4ms",
    status: "Active (Layer 1)"
  },
  {
    model: "Logistic Regression (Balanced)",
    type: "Linear ML",
    precision: 0.74,
    recall: 0.65,
    f1: 0.69,
    prAuc: 0.71,
    preventedExposure: 0.64,
    latencyMs: "1.2ms",
    status: "Shadow"
  },
  {
    model: "Calibrated LightGBM (v1.0)",
    type: "Ensemble GBDT",
    precision: 0.85,
    recall: 0.72,
    f1: 0.78,
    prAuc: 0.81,
    preventedExposure: 0.76,
    latencyMs: "3.1ms",
    status: "Champion (Active)"
  }
];

export const driftMetrics = [
  { feature: "TransactionAmt", ksPValue: 0.42, status: "HEALTHY", driftType: "Online Input Drift" },
  { feature: "card1_velocity_24h", ksPValue: 0.28, status: "HEALTHY", driftType: "Online Input Drift" },
  { feature: "P_emaildomain_dist", ksPValue: 0.08, status: "MONITOR", driftType: "Online Input Drift" },
  { feature: "RiskScore_Distribution", ksPValue: 0.35, status: "HEALTHY", driftType: "Online Score Drift" },
  { feature: "Confirmed_Fraud_Precision", ksPValue: null, value: "85.2%", status: "STABLE", driftType: "Delayed Outcome (T+30d)" },
  { feature: "Confirmed_Fraud_Recall", ksPValue: null, value: "72.4%", status: "STABLE", driftType: "Delayed Outcome (T+30d)" }
];
