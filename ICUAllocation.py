PRIORITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


class ICUAllocation:
    def __init__(self, total_beds=10):
        if total_beds <= 0:
            raise ValueError("total_beds must be positive")
        self.total_beds = total_beds
        self.occupied_beds = 0
        self.patients = {}
        self.waiting_list = []

    def _priority_score(self, age, oxygen_level, heart_rate, blood_pressure_systolic, temperature, conditions):
        score = 0
        if oxygen_level < 90:
            score += 40
        elif oxygen_level < 94:
            score += 25
        elif oxygen_level < 97:
            score += 10

        if heart_rate < 40 or heart_rate > 130:
            score += 25
        elif heart_rate < 50 or heart_rate > 110:
            score += 15

        if blood_pressure_systolic < 90 or blood_pressure_systolic > 180:
            score += 20
        elif blood_pressure_systolic < 100 or blood_pressure_systolic > 160:
            score += 10

        if temperature >= 40 or temperature <= 35:
            score += 15
        elif temperature >= 39:
            score += 8

        if age >= 65 or age <= 5:
            score += 10

        score += min(len(conditions) * 5, 20)
        return score

    def _classify(self, score):
        if score >= 70:
            return "CRITICAL"
        if score >= 45:
            return "HIGH"
        if score >= 20:
            return "MEDIUM"
        return "LOW"

    def admit_patient(self, patient_id, age, oxygen_level, heart_rate, blood_pressure_systolic,
                       temperature, conditions=None, emergency=False):
        if patient_id in self.patients:
            raise ValueError("Duplicate patient ID")
        if not (0 <= oxygen_level <= 100):
            raise ValueError("Invalid oxygen level")
        if not (0 < heart_rate <= 300):
            raise ValueError("Invalid heart rate")
        if age < 0:
            raise ValueError("Invalid age")

        conditions = conditions or []
        score = self._priority_score(age, oxygen_level, heart_rate, blood_pressure_systolic, temperature, conditions)
        priority = self._classify(score)

        patient = {
            "patient_id": patient_id,
            "age": age,
            "oxygen_level": oxygen_level,
            "heart_rate": heart_rate,
            "blood_pressure_systolic": blood_pressure_systolic,
            "temperature": temperature,
            "conditions": conditions,
            "priority": priority,
            "score": score,
            "emergency": emergency,
            "status": None,
        }
        self.patients[patient_id] = patient
        self._allocate(patient)
        return patient

    def _allocate(self, patient):
        if self.occupied_beds < self.total_beds:
            self.occupied_beds += 1
            patient["status"] = "ADMITTED"
        elif patient["emergency"] or patient["priority"] == "CRITICAL":
            bumped_id = self._find_bump_candidate(patient)
            if bumped_id:
                self._bump(bumped_id)
                self.occupied_beds += 1
                patient["status"] = "ADMITTED"
            else:
                self.waiting_list.append(patient["patient_id"])
                patient["status"] = "WAITING"
        else:
            self.waiting_list.append(patient["patient_id"])
            patient["status"] = "WAITING"
        return patient["status"]

    def _find_bump_candidate(self, incoming):
        admitted = [p for pid, p in self.patients.items() if p["status"] == "ADMITTED" and pid != incoming["patient_id"]]
        if not admitted:
            return None
        lowest = min(admitted, key=lambda p: PRIORITY_ORDER[p["priority"]])
        if incoming["emergency"]:
            if PRIORITY_ORDER[lowest["priority"]] <= PRIORITY_ORDER[incoming["priority"]]:
                return lowest["patient_id"]
            return None
        if PRIORITY_ORDER[lowest["priority"]] < PRIORITY_ORDER[incoming["priority"]]:
            return lowest["patient_id"]
        return None

    def _bump(self, patient_id):
        patient = self.patients[patient_id]
        patient["status"] = "WAITING"
        self.occupied_beds -= 1
        self.waiting_list.insert(0, patient_id)

    def discharge_patient(self, patient_id):
        if patient_id not in self.patients:
            raise ValueError("Patient not found")
        patient = self.patients[patient_id]
        if patient["status"] != "ADMITTED":
            raise ValueError("Patient is not currently admitted")
        patient["status"] = "DISCHARGED"
        self.occupied_beds -= 1
        self._process_waiting_list()

    def _process_waiting_list(self):
        if not self.waiting_list:
            return
        self.waiting_list.sort(key=lambda pid: -PRIORITY_ORDER[self.patients[pid]["priority"]])
        next_id = self.waiting_list.pop(0)
        patient = self.patients[next_id]
        self.occupied_beds += 1
        patient["status"] = "ADMITTED"

    def get_patient(self, patient_id):
        if patient_id not in self.patients:
            raise ValueError("Patient not found")
        return self.patients[patient_id]

    def available_beds(self):
        return self.total_beds - self.occupied_beds
