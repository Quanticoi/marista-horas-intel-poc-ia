"""Synthetic only; gaps stay gaps and the last series is a new course."""
import math
import random
import uuid
from datetime import date

NAMESPACE = uuid.UUID("8de1899d-047b-48d9-8ee5-b481d4e04b8f")


def identity(value):
    return uuid.uuid5(NAMESPACE, value)


def generate(seed=42, semesters=12, start_year=2020):
    rng = random.Random(seed)
    records = []
    for campus in range(1, 4):
        for course in range(1, 6):
            for period in range(1, 3):
                key = f"C{campus}-CR{course}-P{period}"
                for step in range(semesters):
                    if key == "C3-CR5-P2" and step < semesters - 3:
                        continue
                    if key == "C2-CR2-P1" and step == 4:
                        continue
                    regular = max(0, round(35 + campus * 8 + course * 3 + step * 1.7 +
                                           8 * math.cos(step * math.pi) + rng.gauss(0, 4)))
                    records.append(dict(model_key=key, campus_id=str(identity(f"C{campus}")),
                        course_id=str(identity(f"C{campus}-CR{course}")),
                        period_id=str(identity(key)), reference_year=start_year + step // 2,
                        reference_semester=step % 2 + 1, regular_students=regular,
                        dependency_students=rng.randint(0, 8), elective_students=rng.randint(0, 5)))
    return records


def validate(records, as_of_date):
    seen = set()
    previous = {}
    for row in records:
        if row["reference_semester"] not in (1, 2):
            raise ValueError("Invalid semester")
        campus, course, period = row["model_key"].split("-")
        expected = {"campus_id": identity(campus), "course_id": identity(f"{campus}-{course}"),
                    "period_id": identity(row["model_key"])}
        if any(str(row[k]) != str(v) for k, v in expected.items()):
            raise ValueError("Inconsistent series references")
        key = (row["model_key"], row["reference_year"], row["reference_semester"])
        if key in seen:
            raise ValueError("Duplicate series/time")
        seen.add(key)
        end = date(row["reference_year"], 6 if row["reference_semester"] == 1 else 12,
                   30 if row["reference_semester"] == 1 else 31)
        if end > as_of_date:
            raise ValueError("Future data leakage")
        if any(row[c] < 0 for c in ("regular_students", "dependency_students", "elective_students")):
            raise ValueError("Negative enrollment")
        if previous.get(row["model_key"], date.min) >= end:
            raise ValueError("Unsorted series")
        previous[row["model_key"]] = end
    return len(seen)
