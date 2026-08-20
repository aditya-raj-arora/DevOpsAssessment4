DEFAULT_CATALOG = {
    "DBMS": {"credits": 4, "prerequisites": ["Programming"], "capacity": 2, "timetable": "MON_10_12", "semesters": [3, 4, 5]},
    "AI": {"credits": 4, "prerequisites": ["Data Structures"], "capacity": 2, "timetable": "TUE_10_12", "semesters": [5, 6, 7]},
    "ML": {"credits": 3, "prerequisites": ["Statistics"], "capacity": 2, "timetable": "MON_10_12", "semesters": [5, 6, 7]},
    "Cloud": {"credits": 3, "prerequisites": ["Networking"], "capacity": 2, "timetable": "WED_14_16", "semesters": [4, 5, 6]},
}


class CourseRegistration:
    def __init__(self, catalog=None, max_credits=18):
        self.catalog = catalog if catalog is not None else DEFAULT_CATALOG
        self.max_credits = max_credits
        self.enrollments = {}
        self.students = {}

    def _new_student_record(self):
        return {"courses": [], "credits": 0, "completed": set(), "program": None, "semester": None}

    def set_completed_courses(self, student_id, completed):
        self.students.setdefault(student_id, self._new_student_record())
        self.students[student_id]["completed"] = set(completed)

    def register_course(self, student_id, program, semester, course_id):
        if course_id not in self.catalog:
            raise ValueError("Invalid course")

        record = self.students.setdefault(student_id, self._new_student_record())
        record["program"] = program
        record["semester"] = semester
        course = self.catalog[course_id]

        if course_id in record["courses"]:
            raise ValueError("Duplicate registration")

        if "semesters" in course and semester not in course["semesters"]:
            raise ValueError("Course not offered in this semester")

        missing = [p for p in course["prerequisites"] if p not in record["completed"]]
        if missing:
            raise ValueError(f"Missing prerequisite: {', '.join(missing)}")

        projected_credits = record["credits"] + course["credits"]
        if projected_credits > self.max_credits:
            raise ValueError("Credit limit exceeded")

        for existing_id in record["courses"]:
            if self.catalog[existing_id]["timetable"] == course["timetable"]:
                raise ValueError("Timetable conflict")

        enrolled = self.enrollments.setdefault(course_id, set())
        if len(enrolled) >= course["capacity"]:
            raise ValueError("Course is full")

        enrolled.add(student_id)
        record["courses"].append(course_id)
        record["credits"] = projected_credits
        return record["credits"]

    def get_total_credits(self, student_id):
        return self.students.get(student_id, self._new_student_record())["credits"]

    def get_registered_courses(self, student_id):
        return list(self.students.get(student_id, self._new_student_record())["courses"])

    def get_seats_remaining(self, course_id):
        if course_id not in self.catalog:
            raise ValueError("Invalid course")
        enrolled = len(self.enrollments.get(course_id, set()))
        return self.catalog[course_id]["capacity"] - enrolled
