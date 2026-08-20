from datetime import date

POLICY_TYPES = {
    "HEALTH": {"coverage": 500000, "deductible_rate": 0.10},
    "AUTO": {"coverage": 300000, "deductible_rate": 0.15},
    "HOME": {"coverage": 1000000, "deductible_rate": 0.05},
    "LIFE": {"coverage": 2000000, "deductible_rate": 0.0},
}

FRAUD_SUSPECTED_THRESHOLD = 60
MANUAL_REVIEW_THRESHOLD = 30
SHORT_ACTIVATION_WINDOW_DAYS = 15
EXCESSIVE_CLAIM_MULTIPLIER = 1.5
RECENT_CLAIMS_WINDOW_DAYS = 30
RECENT_CLAIMS_LIMIT = 2
PREVIOUS_CLAIMS_LIMIT = 3


class InsuranceClaim:
    def __init__(self):
        self.claims = {}
        self.customer_claim_dates = {}

    def process_claim(self, policy_number, customer_id, policy_type, claim_amount,
                       policy_start_date, incident_date, previous_claim_count, customer_age,
                       incident_type, documents_submitted, policy_end_date=None):
        if policy_type not in POLICY_TYPES:
            raise ValueError("Invalid policy type")
        if not policy_number or len(str(policy_number)) < 6:
            raise ValueError("Invalid policy number")
        if not isinstance(incident_date, date) or not isinstance(policy_start_date, date):
            raise ValueError("Invalid incident date")
        if incident_date > date.today():
            raise ValueError("Invalid incident date")
        if incident_date < policy_start_date:
            raise ValueError("Claim incident occurred before policy start date")
        if policy_end_date is not None and incident_date > policy_end_date:
            raise ValueError("Policy expired before incident date")
        if claim_amount <= 0:
            raise ValueError("Claim amount must be positive")
        if customer_age < 0:
            raise ValueError("Invalid customer age")

        policy = POLICY_TYPES[policy_type]
        coverage = policy["coverage"]
        max_payable = min(claim_amount, coverage)
        deductible = round(max_payable * policy["deductible_rate"], 2)
        customer_contribution = deductible
        potential_payout = round(max_payable - deductible, 2)

        fraud_score = 0
        reasons = []

        days_since_start = (incident_date - policy_start_date).days
        if days_since_start <= SHORT_ACTIVATION_WINDOW_DAYS:
            fraud_score += 30
            reasons.append("INCIDENT_IMMEDIATELY_AFTER_ACTIVATION")

        if claim_amount > coverage * EXCESSIVE_CLAIM_MULTIPLIER:
            fraud_score += 30
            reasons.append("EXCESSIVE_CLAIM_AMOUNT")

        if not documents_submitted:
            fraud_score += 20
            reasons.append("MISSING_DOCUMENTATION")

        if previous_claim_count >= PREVIOUS_CLAIMS_LIMIT:
            fraud_score += 20
            reasons.append("MULTIPLE_PREVIOUS_CLAIMS")

        recent_dates = self.customer_claim_dates.get(customer_id, [])
        recent_count = sum(1 for d in recent_dates if (incident_date - d).days <= RECENT_CLAIMS_WINDOW_DAYS)
        if recent_count >= RECENT_CLAIMS_LIMIT:
            fraud_score += 25
            reasons.append("MULTIPLE_CLAIMS_SHORT_PERIOD")

        if fraud_score >= FRAUD_SUSPECTED_THRESHOLD:
            decision = "FRAUD_SUSPECTED"
        elif not documents_submitted:
            decision = "MANUAL_REVIEW"
        elif fraud_score >= MANUAL_REVIEW_THRESHOLD:
            decision = "MANUAL_REVIEW"
        elif claim_amount > coverage:
            decision = "MANUAL_REVIEW"
        else:
            decision = "APPROVED"

        payout = potential_payout if decision == "APPROVED" else 0

        claim_id = f"{policy_number}-{len(self.claims) + 1}"
        result = {
            "claim_id": claim_id,
            "policy_number": policy_number,
            "customer_id": customer_id,
            "policy_type": policy_type,
            "claim_amount": claim_amount,
            "max_payable": max_payable,
            "deductible": deductible,
            "customer_contribution": customer_contribution,
            "payout": payout,
            "fraud_score": fraud_score,
            "fraud_reasons": reasons,
            "decision": decision,
        }
        self.claims[claim_id] = result
        self.customer_claim_dates.setdefault(customer_id, []).append(incident_date)
        return result

    def get_claim(self, claim_id):
        if claim_id not in self.claims:
            raise ValueError("Claim not found")
        return self.claims[claim_id]
