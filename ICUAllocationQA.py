import unittest
from ICUAllocation import ICUAllocation


class TestCriticalPatient(unittest.TestCase):
    def test_critical_patient_classified_and_admitted(self):
        icu = ICUAllocation(total_beds=5)
        patient = icu.admit_patient("P1", age=70, oxygen_level=85, heart_rate=145,
                                     blood_pressure_systolic=185, temperature=40.5,
                                     conditions=["diabetes", "hypertension"])
        self.assertEqual(patient["priority"], "CRITICAL")
        self.assertEqual(patient["status"], "ADMITTED")


class TestNormalPatient(unittest.TestCase):
    def test_low_priority_patient_admitted_when_beds_free(self):
        icu = ICUAllocation(total_beds=5)
        patient = icu.admit_patient("P1", age=30, oxygen_level=98, heart_rate=75,
                                     blood_pressure_systolic=118, temperature=37.0, conditions=[])
        self.assertEqual(patient["priority"], "LOW")
        self.assertEqual(patient["status"], "ADMITTED")


class TestEmergencyCase(unittest.TestCase):
    def test_emergency_bumps_lower_priority_patient(self):
        icu = ICUAllocation(total_beds=1)
        icu.admit_patient("P1", age=25, oxygen_level=98, heart_rate=70,
                           blood_pressure_systolic=115, temperature=37.0)
        emergency_patient = icu.admit_patient("P2", age=40, oxygen_level=96, heart_rate=80,
                                               blood_pressure_systolic=120, temperature=37.0,
                                               emergency=True)
        self.assertEqual(emergency_patient["status"], "ADMITTED")
        self.assertEqual(icu.get_patient("P1")["status"], "WAITING")


class TestNoICUBeds(unittest.TestCase):
    def test_low_priority_patient_waits_when_full(self):
        icu = ICUAllocation(total_beds=1)
        icu.admit_patient("P1", age=25, oxygen_level=98, heart_rate=70,
                           blood_pressure_systolic=115, temperature=37.0)
        patient = icu.admit_patient("P2", age=30, oxygen_level=97, heart_rate=72,
                                     blood_pressure_systolic=118, temperature=37.0)
        self.assertEqual(patient["status"], "WAITING")
        self.assertIn("P2", icu.waiting_list)


class TestDuplicatePatient(unittest.TestCase):
    def test_duplicate_patient_id_rejected(self):
        icu = ICUAllocation(total_beds=5)
        icu.admit_patient("P1", age=30, oxygen_level=98, heart_rate=75,
                           blood_pressure_systolic=118, temperature=37.0)
        with self.assertRaises(ValueError):
            icu.admit_patient("P1", age=40, oxygen_level=95, heart_rate=80,
                               blood_pressure_systolic=120, temperature=37.0)


class TestInvalidOxygenLevel(unittest.TestCase):
    def test_oxygen_level_out_of_range(self):
        icu = ICUAllocation(total_beds=5)
        with self.assertRaises(ValueError):
            icu.admit_patient("P1", age=30, oxygen_level=150, heart_rate=75,
                               blood_pressure_systolic=118, temperature=37.0)


class TestInvalidHeartRate(unittest.TestCase):
    def test_heart_rate_out_of_range(self):
        icu = ICUAllocation(total_beds=5)
        with self.assertRaises(ValueError):
            icu.admit_patient("P1", age=30, oxygen_level=98, heart_rate=0,
                               blood_pressure_systolic=118, temperature=37.0)


class TestPriorityBoundaryValues(unittest.TestCase):
    def test_score_boundary_between_medium_and_high(self):
        icu = ICUAllocation(total_beds=5)
        patient = icu.admit_patient("P1", age=30, oxygen_level=93, heart_rate=115,
                                     blood_pressure_systolic=170, temperature=37.0, conditions=[])
        self.assertEqual(patient["score"], 25 + 15 + 10)
        self.assertEqual(patient["priority"], "HIGH")

    def test_score_boundary_between_low_and_medium(self):
        icu = ICUAllocation(total_beds=5)
        patient = icu.admit_patient("P1", age=30, oxygen_level=96, heart_rate=75,
                                     blood_pressure_systolic=118, temperature=37.0, conditions=[])
        self.assertEqual(patient["score"], 10)
        self.assertEqual(patient["priority"], "LOW")


class TestMultiplePatientsCompeting(unittest.TestCase):
    def test_highest_priority_wins_last_bed(self):
        icu = ICUAllocation(total_beds=2)
        icu.admit_patient("P1", age=30, oxygen_level=97, heart_rate=75,
                           blood_pressure_systolic=118, temperature=37.0)
        icu.admit_patient("P2", age=35, oxygen_level=96, heart_rate=78,
                           blood_pressure_systolic=120, temperature=37.0)
        critical_patient = icu.admit_patient("P3", age=72, oxygen_level=85, heart_rate=145,
                                              blood_pressure_systolic=185, temperature=40.5,
                                              conditions=["heart disease"])
        self.assertEqual(critical_patient["status"], "ADMITTED")
        waiting_statuses = [icu.get_patient("P1")["status"], icu.get_patient("P2")["status"]]
        self.assertIn("WAITING", waiting_statuses)

    def test_discharge_admits_next_from_waiting_list(self):
        icu = ICUAllocation(total_beds=1)
        icu.admit_patient("P1", age=30, oxygen_level=97, heart_rate=75,
                           blood_pressure_systolic=118, temperature=37.0)
        icu.admit_patient("P2", age=72, oxygen_level=85, heart_rate=145,
                           blood_pressure_systolic=185, temperature=40.5,
                           conditions=["heart disease"], emergency=True)
        icu.discharge_patient("P2")
        self.assertEqual(icu.get_patient("P1")["status"], "ADMITTED")


if __name__ == "__main__":
    unittest.main()
