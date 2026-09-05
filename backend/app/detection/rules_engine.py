from typing import List, Tuple
from app.models.schemas import RuleTrigger, TransactionInput


class RulesEngine:
    """
    Layer 1: Deterministic rule-based gating.
    Evaluates incoming payment transaction features against hardened fraud rules.
    Yields structured rule triggers and human-readable reason codes.
    """

    def __init__(
        self,
        high_amount_threshold: float = 10000.0,
        elevated_amount_threshold: float = 2000.0,
    ):
        self.high_amount_threshold = high_amount_threshold
        self.elevated_amount_threshold = elevated_amount_threshold
        self.disposable_email_keywords = {
            "temp", "xyz", "top", "disposable", "mailinator", 
            "trashmail", "guerrillamail", "10minutemail", "yopmail", "sharklasers"
        }
        self.suspicious_device_keywords = {
            "unknown", "proxy", "tor", "emulator", "vpn", "rooted", "jailbreak", "headless"
        }

    def evaluate(self, txn: TransactionInput) -> Tuple[List[RuleTrigger], List[str]]:
        triggers: List[RuleTrigger] = []
        reason_codes: List[str] = []

        amount = float(txn.amount)

        # Rule 1: High Value Amount
        if amount >= self.high_amount_threshold:
            triggers.append(RuleTrigger(
                ruleId="RULE-001",
                severity="HIGH",
                explanation=f"Transaction amount (₹{amount:,.2f}) is >99th percentile for typical customer profile."
            ))
            reason_codes.append("HIGH_VALUE_TRANSACTION")
        elif amount >= self.elevated_amount_threshold:
            triggers.append(RuleTrigger(
                ruleId="RULE-002",
                severity="MEDIUM",
                explanation=f"Transaction amount (₹{amount:,.2f}) significantly deviates from baseline."
            ))
            reason_codes.append("ELEVATED_AMOUNT")

        # Rule 2: Disposable / Suspicious Email Domain
        if txn.P_emaildomain:
            domain_str = str(txn.P_emaildomain).lower()
            if any(k in domain_str for k in self.disposable_email_keywords):
                triggers.append(RuleTrigger(
                    ruleId="RULE-045",
                    severity="MEDIUM",
                    explanation=f"Transaction uses disposable or high-risk email domain '{txn.P_emaildomain}'."
                ))
                reason_codes.append("NEW_EMAIL_DOMAIN")

        # Rule 3: Anomalous Device / Proxy / Emulator Fingerprint
        device_type_str = str(txn.DeviceType).lower() if txn.DeviceType else ""
        device_info_str = str(txn.DeviceInfo).lower() if txn.DeviceInfo else ""
        if any(k in device_type_str or k in device_info_str for k in self.suspicious_device_keywords):
            triggers.append(RuleTrigger(
                ruleId="RULE-089",
                severity="HIGH",
                explanation="Transaction originated from an unrecognized or anomalous device fingerprint."
            ))
            reason_codes.append("UNUSUAL_DEVICE")

        # Rule 4: Velocity Spike Indicators
        c1 = getattr(txn, "C1", None)
        c2 = getattr(txn, "C2", None)
        try:
            c1_val = float(c1) if c1 is not None else 0.0
            c2_val = float(c2) if c2 is not None else 0.0
            if c1_val >= 5.0 or c2_val >= 5.0:
                triggers.append(RuleTrigger(
                    ruleId="RULE-012",
                    severity="MEDIUM",
                    explanation=f"High transaction count velocity detected across card cluster (C1={c1_val}, C2={c2_val})."
                ))
                reason_codes.append("VELOCITY_SPIKE")
        except (ValueError, TypeError):
            pass

        # Rule 5: Geographic Distance Anomaly
        dist1 = txn.dist1
        dist2 = txn.dist2
        try:
            if (dist1 is not None and float(dist1) > 500.0) or (dist2 is not None and float(dist2) > 500.0):
                triggers.append(RuleTrigger(
                    ruleId="RULE-023",
                    severity="LOW",
                    explanation="Elevated distance detected between billing address and transaction point."
                ))
                reason_codes.append("DISTANCE_ANOMALY")
        except (ValueError, TypeError):
            pass

        # Rule 6: High Risk Merchant / ProductCD Category
        if txn.ProductCD in ["C", "R"] and amount >= 500.0:
            triggers.append(RuleTrigger(
                ruleId="RULE-031",
                severity="MEDIUM",
                explanation=f"High-risk product code category '{txn.ProductCD}' with elevated amount."
            ))
            if "HIGH_RISK_MERCHANT_CATEGORY" not in reason_codes:
                reason_codes.append("HIGH_RISK_MERCHANT_CATEGORY")

        # Deduplicate reason codes maintaining order
        deduped_reason_codes: List[str] = []
        for rc in reason_codes:
            if rc not in deduped_reason_codes:
                deduped_reason_codes.append(rc)

        return triggers, deduped_reason_codes

