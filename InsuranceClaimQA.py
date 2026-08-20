import unittest
from datetime import date
from InsuranceClaim import InsuranceClaim


class TestValidClaim(unittest.TestCase):
    def test_valid_claim_is_approved(self):
        ic = InsuranceClaim()
        result = ic.process_claim(
            policy_number="POL1234", customer_id="C1", policy_type="HEALTH",
            claim_amount=50000, policy_start_date=date(2024, 1, 1),
            incident_date=date(2025, 6, 1), previous_claim_count=0,
            customer_age=35, incident_type="SURGERY", documents_submitted=True,
        )
        self.assertEqual(result["decision"], "APPROVED")
        self.assertGreater(result["payout"], 0)


class TestExpiredPolicy(unittest.TestCase):
    def test_incident_after_policy_expiry_rejected(self):
        ic = InsuranceClaim()
        with self.assertRaises(ValueError):
            ic.process_claim(
                policy_number="POL1234", customer_id="C1", policy_type="AUTO",
                claim_amount=10000, policy_start_date=date(2023, 1, 1),
                incident_date=date(2025, 6, 1), previous_claim_count=0,
                customer_age=40, incident_type="COLLISION", documents_submitted=True,
                policy_end_date=date(2024, 1, 1),
            )


class TestClaimBeforePolicyStart(unittest.TestCase):
    def test_incident_before_start_date_rejected(self):
        ic = InsuranceClaim()
        with self.assertRaises(ValueError):
            ic.process_claim(
                policy_number="POL1234", customer_id="C1", policy_type="HOME",
                claim_amount=20000, policy_start_date=date(2025, 6, 1),
                incident_date=date(2025, 1, 1), previous_claim_count=0,
                customer_age=45, incident_type="FIRE", documents_submitted=True,
            )


class TestExcessiveClaimAmount(unittest.TestCase):
    def test_claim_far_exceeding_coverage_flagged(self):
        ic = InsuranceClaim()
        result = ic.process_claim(
            policy_number="POL1234", customer_id="C1", policy_type="AUTO",
            claim_amount=500000, policy_start_date=date(2020, 1, 1),
            incident_date=date(2025, 6, 1), previous_claim_count=0,
            customer_age=35, incident_type="COLLISION", documents_submitted=True,
        )
        self.assertIn("EXCESSIVE_CLAIM_AMOUNT", result["fraud_reasons"])


class TestMissingDocuments(unittest.TestCase):
    def test_missing_documents_sent_to_manual_review(self):
        ic = InsuranceClaim()
        result = ic.process_claim(
            policy_number="POL1234", customer_id="C1", policy_type="HEALTH",
            claim_amount=40000, policy_start_date=date(2020, 1, 1),
            incident_date=date(2025, 6, 1), previous_claim_count=0,
            customer_age=35, incident_type="SURGERY", documents_submitted=False,
        )
        self.assertEqual(result["decision"], "MANUAL_REVIEW")
        self.assertEqual(result["payout"], 0)


class TestMultiplePreviousClaims(unittest.TestCase):
    def test_multiple_previous_claims_increase_fraud_score(self):
        ic = InsuranceClaim()
        result = ic.process_claim(
            policy_number="POL1234", customer_id="C1", policy_type="HEALTH",
            claim_amount=40000, policy_start_date=date(2020, 1, 1),
            incident_date=date(2025, 6, 1), previous_claim_count=4,
            customer_age=35, incident_type="SURGERY", documents_submitted=True,
        )
        self.assertIn("MULTIPLE_PREVIOUS_CLAIMS", result["fraud_reasons"])


class TestFraudScenario(unittest.TestCase):
    def test_combined_fraud_indicators_trigger_fraud_suspected(self):
        ic = InsuranceClaim()
        result = ic.process_claim(
            policy_number="POL1234", customer_id="C1", policy_type="AUTO",
            claim_amount=500000, policy_start_date=date(2025, 5, 20),
            incident_date=date(2025, 6, 1), previous_claim_count=4,
            customer_age=35, incident_type="COLLISION", documents_submitted=False,
        )
        self.assertEqual(result["decision"], "FRAUD_SUSPECTED")


class TestBoundaryClaimAmount(unittest.TestCase):
    def test_claim_amount_exactly_at_coverage_limit(self):
        ic = InsuranceClaim()
        result = ic.process_claim(
            policy_number="POL1234", customer_id="C1", policy_type="AUTO",
            claim_amount=300000, policy_start_date=date(2020, 1, 1),
            incident_date=date(2025, 6, 1), previous_claim_count=0,
            customer_age=35, incident_type="COLLISION", documents_submitted=True,
        )
        self.assertEqual(result["max_payable"], 300000)
        self.assertEqual(result["decision"], "APPROVED")


class TestInvalidPolicyNumber(unittest.TestCase):
    def test_short_policy_number_rejected(self):
        ic = InsuranceClaim()
        with self.assertRaises(ValueError):
            ic.process_claim(
                policy_number="P1", customer_id="C1", policy_type="AUTO",
                claim_amount=10000, policy_start_date=date(2020, 1, 1),
                incident_date=date(2025, 6, 1), previous_claim_count=0,
                customer_age=35, incident_type="COLLISION", documents_submitted=True,
            )


class TestInvalidIncidentDate(unittest.TestCase):
    def test_future_incident_date_rejected(self):
        ic = InsuranceClaim()
        with self.assertRaises(ValueError):
            ic.process_claim(
                policy_number="POL1234", customer_id="C1", policy_type="AUTO",
                claim_amount=10000, policy_start_date=date(2020, 1, 1),
                incident_date=date(2099, 1, 1), previous_claim_count=0,
                customer_age=35, incident_type="COLLISION", documents_submitted=True,
            )


if __name__ == "__main__":
    unittest.main()
