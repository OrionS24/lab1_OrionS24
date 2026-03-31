import csv
import os
import sys

CSV_FILE = "grades.csv"
PASS_THRESHOLD = 50.0
TOTAL_WEIGHT = 100
FORMATIVE_WEIGHT = 60
SUMMATIVE_WEIGHT = 40
GPA_SCALE = 5.0


def load_grades(filepath: str) -> list[dict]:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File '{filepath}' not found.")

    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_headers = {"assignment", "group", "score", "weight"}
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty — no headers found.")

        actual_headers = {h.strip() for h in reader.fieldnames}
        missing = required_headers - actual_headers
        if missing:
            raise ValueError(f"CSV is missing required columns: {missing}")

        for i, row in enumerate(reader, start=2):
            row = {k.strip(): v.strip() for k, v in row.items()}
            rows.append(row)

    if not rows:
        raise ValueError("CSV file contains headers but no grade data.")

    return rows


def parse_and_validate(rows: list[dict]) -> list[dict]:
    assignments = []
    errors = []

    for i, row in enumerate(rows, start=2):
        name   = row.get("assignment", f"Row {i}")
        a_type = row.get("group", "").capitalize()

        if a_type not in ("Formative", "Summative"):
            errors.append(
                f"  Row {i} ({name!r}): Type must be 'Formative' or "
                f"'Summative', got {row.get('group')!r}."
            )
            continue

        try:
            score = float(row["score"])
        except (ValueError, KeyError):
            errors.append(f"  Row {i} ({name!r}): Score is not a number.")
            continue

        if not (0 <= score <= 100):
            errors.append(
                f"  Row {i} ({name!r}): Score {score} is out of range [0, 100]."
            )
            continue

        try:
            weight = float(row["weight"])
        except (ValueError, KeyError):
            errors.append(f"  Row {i} ({name!r}): Weight is not a number.")
            continue

        if weight <= 0:
            errors.append(
                f"  Row {i} ({name!r}): Weight must be greater than 0."
            )
            continue

        assignments.append({
            "name":   name,
            "type":   a_type,
            "score":  score,
            "weight": weight,
        })

    if errors:
        print("\n[!] Validation Errors Found:")
        for e in errors:
            print(e)
        sys.exit(1)

    return assignments


def validate_weights(assignments: list[dict]) -> None:
    formative_total = sum(a["weight"] for a in assignments if a["type"] == "Formative")
    summative_total = sum(a["weight"] for a in assignments if a["type"] == "Summative")
    grand_total     = formative_total + summative_total

    weight_errors = []

    if abs(formative_total - FORMATIVE_WEIGHT) > 1e-9:
        weight_errors.append(
            f"  Formative weights sum to {formative_total}, expected {FORMATIVE_WEIGHT}."
        )
    if abs(summative_total - SUMMATIVE_WEIGHT) > 1e-9:
        weight_errors.append(
            f"  Summative weights sum to {summative_total}, expected {SUMMATIVE_WEIGHT}."
        )
    if abs(grand_total - TOTAL_WEIGHT) > 1e-9:
        weight_errors.append(
            f"  Total weights sum to {grand_total}, expected {TOTAL_WEIGHT}."
        )

    if weight_errors:
        print("\n[!] Weight Validation Failed:")
        for e in weight_errors:
            print(e)
        sys.exit(1)


def calculate_category_score(assignments: list[dict], category: str) -> float:
    category_assignments = [a for a in assignments if a["type"] == category]
    total_weight = sum(a["weight"] for a in category_assignments)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(a["score"] * a["weight"] for a in category_assignments)
    return weighted_sum / total_weight


def calculate_overall_grade(assignments: list[dict]) -> float:
    return sum(a["score"] * a["weight"] for a in assignments) / TOTAL_WEIGHT


def calculate_gpa(overall_grade: float) -> float:
    return (overall_grade / 100) * GPA_SCALE


def determine_status(formative_score: float, summative_score: float) -> str:
    if formative_score >= PASS_THRESHOLD and summative_score >= PASS_THRESHOLD:
        return "PASSED"
    return "FAILED"


def get_resubmission_candidates(assignments: list[dict]) -> list[dict]:
    failed_formatives = [
        a for a in assignments
        if a["type"] == "Formative" and a["score"] < PASS_THRESHOLD
    ]

    if not failed_formatives:
        return []

    max_weight = max(a["weight"] for a in failed_formatives)
    return [a for a in failed_formatives if a["weight"] == max_weight]


def print_report(
    assignments:      list[dict],
    formative_score:  float,
    summative_score:  float,
    overall_grade:    float,
    gpa:              float,
    status:           str,
    resubmit:         list[dict],
) -> None:
    WIDTH = 60
    SEP   = "─" * WIDTH

    print("\n" + "═" * WIDTH)
    print(" STUDENT GRADE REPORT ".center(WIDTH))
    print("═" * WIDTH)

    print(f"\n{'Assignment':<28} {'Type':<12} {'Score':>6} {'Weight':>7}")
    print(SEP)

    for a in assignments:
        print(
            f"  {a['name']:<26} {a['type']:<12} "
            f"{a['score']:>5.1f}  {a['weight']:>6.1f}"
        )

    print("\n" + SEP)
    print(f"  {'Formative Score':<30} {formative_score:>6.2f}%")
    print(f"  {'Summative Score':<30} {summative_score:>6.2f}%")
    print(SEP)
    print(f"  {'Overall Weighted Grade':<30} {overall_grade:>6.2f}%")
    print(f"  {'GPA (out of 5.0)':<30} {gpa:>6.2f}")

    print("\n" + "═" * WIDTH)
    print(f"  FINAL STATUS: {status}")
    if status == "FAILED":
        if formative_score < PASS_THRESHOLD:
            print(f"  ✗ Formative score ({formative_score:.2f}%) is below 50%.")
        if summative_score < PASS_THRESHOLD:
            print(f"  ✗ Summative score ({summative_score:.2f}%) is below 50%.")
    else:
        print("  ✓ Student meets the minimum in both categories.")
    print("═" * WIDTH)

    print()
    if resubmit:
        print("  RESUBMISSION ELIGIBLE (failed formative, highest weight):")
        for a in resubmit:
            print(
                f"    → {a['name']}  |  Score: {a['score']:.1f}  |  Weight: {a['weight']:.1f}"
            )
    else:
        print("  No formative assignments eligible for resubmission.")

    print("═" * WIDTH + "\n")


def main():
    print(f"Loading grades from '{CSV_FILE}'...")

    try:
        raw_rows = load_grades(CSV_FILE)
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("Please ensure 'grades.csv' exists in the current directory.")
        sys.exit(1)
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    assignments = parse_and_validate(raw_rows)
    validate_weights(assignments)

    formative_score = calculate_category_score(assignments, "Formative")
    summative_score = calculate_category_score(assignments, "Summative")
    overall_grade   = calculate_overall_grade(assignments)
    gpa             = calculate_gpa(overall_grade)

    status   = determine_status(formative_score, summative_score)
    resubmit = get_resubmission_candidates(assignments)

    print_report(
        assignments,
        formative_score,
        summative_score,
        overall_grade,
        gpa,
        status,
        resubmit,
    )


if __name__ == "__main__":
    main()
