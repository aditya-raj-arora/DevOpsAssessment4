import unittest
from CourseRegistration import CourseRegistration


class TestValidRegistration(unittest.TestCase):
    def test_register_course_with_met_prerequisite(self):
        reg = CourseRegistration()
        reg.set_completed_courses("S1", ["Programming"])
        credits = reg.register_course("S1", "MIS", 4, "DBMS")
        self.assertEqual(credits, 4)
        self.assertIn("DBMS", reg.get_registered_courses("S1"))


class TestMissingPrerequisite(unittest.TestCase):
    def test_register_without_prerequisite_fails(self):
        reg = CourseRegistration()
        with self.assertRaises(ValueError):
            reg.register_course("S1", "MIS", 4, "DBMS")


class TestCreditLimitViolation(unittest.TestCase):
    def test_exceeding_max_credits_rejected(self):
        reg = CourseRegistration(max_credits=6)
        reg.set_completed_courses("S1", ["Programming"])
        reg.register_course("S1", "MIS", 4, "DBMS")
        with self.assertRaises(ValueError):
            reg.register_course("S1", "MIS", 4, "Cloud")


class TestTimetableConflict(unittest.TestCase):
    def test_overlapping_timetable_rejected(self):
        reg = CourseRegistration()
        reg.set_completed_courses("S1", ["Programming", "Statistics"])
        reg.register_course("S1", "MIS", 5, "DBMS")
        with self.assertRaises(ValueError):
            reg.register_course("S1", "MIS", 5, "ML")


class TestFullCourse(unittest.TestCase):
    def test_course_full_rejects_further_registration(self):
        reg = CourseRegistration()
        reg.set_completed_courses("S1", ["Networking"])
        reg.set_completed_courses("S2", ["Networking"])
        reg.set_completed_courses("S3", ["Networking"])
        reg.register_course("S1", "MIS", 4, "Cloud")
        reg.register_course("S2", "MIS", 4, "Cloud")
        with self.assertRaises(ValueError):
            reg.register_course("S3", "MIS", 4, "Cloud")


class TestDuplicateRegistration(unittest.TestCase):
    def test_duplicate_registration_rejected(self):
        reg = CourseRegistration()
        reg.set_completed_courses("S1", ["Programming"])
        reg.register_course("S1", "MIS", 4, "DBMS")
        with self.assertRaises(ValueError):
            reg.register_course("S1", "MIS", 4, "DBMS")


class TestInvalidCourse(unittest.TestCase):
    def test_unknown_course_rejected(self):
        reg = CourseRegistration()
        with self.assertRaises(ValueError):
            reg.register_course("S1", "MIS", 4, "Quantum")


class TestSemesterRestriction(unittest.TestCase):
    def test_course_not_offered_in_semester_rejected(self):
        reg = CourseRegistration()
        reg.set_completed_courses("S1", ["Programming"])
        with self.assertRaises(ValueError):
            reg.register_course("S1", "MIS", 1, "DBMS")


class TestBoundaryCreditValues(unittest.TestCase):
    def test_registration_exactly_at_credit_limit_succeeds(self):
        reg = CourseRegistration(max_credits=4)
        reg.set_completed_courses("S1", ["Programming"])
        credits = reg.register_course("S1", "MIS", 4, "DBMS")
        self.assertEqual(credits, 4)

    def test_registration_one_credit_over_limit_fails(self):
        reg = CourseRegistration(max_credits=3)
        reg.set_completed_courses("S1", ["Programming"])
        with self.assertRaises(ValueError):
            reg.register_course("S1", "MIS", 4, "DBMS")


if __name__ == "__main__":
    unittest.main()
