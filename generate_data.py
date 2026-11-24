"""Create deterministic, synthetic Nexora travel and ERP practice data."""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
SEED = 20261124
random.seed(SEED)

FIRST = ["Ava", "Milan", "Sofia", "Noah", "Lea", "Jonas", "Mia", "Elias", "Lina", "Theo", "Emma", "Luca", "Nina", "Felix", "Sara", "Oskar", "Maya", "Leon", "Eva", "Finn"]
LAST = ["Weber", "Fischer", "Schmidt", "Meyer", "Wagner", "Becker", "Hoffmann", "Schulz", "Koch", "Richter", "Klein", "Wolf", "Neumann", "Braun", "Zimmermann", "Hartmann", "Kruger", "Lange", "Schmitt", "Werner"]
DEPTS = ["Engineering", "Sales", "Customer Success", "Operations", "Finance", "People", "Product", "IT"]
CATEGORIES = ["Accommodation", "Air travel", "Rail travel", "Meals", "Local transport", "Parking", "Conference", "Other"]
PROJECT_TYPES = ["Customer delivery", "Platform modernization", "Network planning", "Digital workplace", "Security uplift", "Service transition", "Data migration", "Field operations"]
VENDORS = ["Lufthansa", "Deutsche Bahn", "City Hotel Berlin", "Motel One", "Sixt", "DB Vertrieb", "Taxi Berlin", "Event Services GmbH", "Employee reimbursement"]

def write(name: str, rows: list[dict]) -> None:
    DATA.mkdir(exist_ok=True)
    with (DATA / name).open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def main() -> None:
    today = date(2026, 11, 24)
    employees = []
    for i in range(1, 601):
        dept = DEPTS[(i - 1) % len(DEPTS)]
        employees.append({"EmployeeID": f"E{i:04d}", "EmployeeName": f"{FIRST[(i-1)%len(FIRST)]} {LAST[((i-1)//len(FIRST)+i)%len(LAST)]}", "Department": dept, "Manager": f"{FIRST[(i+3)%len(FIRST)]} {LAST[(i+7)%len(LAST)]}", "CostCentre": f"CC-{100+(i-1)%48:03d}", "Email": f"employee{i:04d}@nexora.example"})
    projects = []
    for i in range(1, 601):
        dept = DEPTS[(i - 1) % len(DEPTS)]
        projects.append({"ProjectID": f"NX-{i:04d}", "ProjectName": f"{PROJECT_TYPES[(i-1)%len(PROJECT_TYPES)]} {i:03d}", "ProjectManager": f"{FIRST[(i+5)%len(FIRST)]} {LAST[(i+11)%len(LAST)]}", "CostCentre": f"CC-{100+(i-1)%48:03d}", "Department": dept, "BudgetEUR": f"{random.randrange(80000, 650001, 5000):.2f}", "Status": "Active" if i % 17 else "Closed"})

    declarations, erp = [], []
    start = today - timedelta(days=330)
    # 800 normal submissions pair to an ERP row. Additional rows intentionally model common control exceptions.
    for i in range(1, 1001):
        emp = employees[(i * 7) % 600]
        proj = projects[(i * 11) % 600]
        category = CATEGORIES[(i * 3) % len(CATEGORIES)]
        trip_start = start + timedelta(days=(i * 3) % 320)
        trip_end = trip_start + timedelta(days=(i % 5) + 1)
        amount = round(random.uniform(24, 1450), 2)
        receipt = f"RCPT-{i:05d}" if i % 23 else ""
        if i % 41 == 0:  # deliberately wrong project
            proj_id = "NX-9999"
        else:
            proj_id = proj["ProjectID"]
        if i % 53 == 0:  # deliberately incomplete dates
            start_text, end_text = "", ""
        else:
            start_text, end_text = trip_start.isoformat(), trip_end.isoformat()
        travel_id = f"TR-{i:05d}"
        declarations.append({"TravelRef": travel_id, "EmployeeID": "" if i % 67 == 0 else emp["EmployeeID"], "TravelStart": start_text, "TravelEnd": end_text, "ProjectID": proj_id, "ExpenseCategory": "" if i % 71 == 0 else category, "DeclaredAmountEUR": f"{amount:.2f}", "ReceiptRef": receipt, "SubmissionDate": (trip_end + timedelta(days=(i % 12) + 1)).isoformat()})
        if i <= 800:
            erp_amount = amount if i % 9 else round(amount + random.choice([-17.25, 12.40, 31.00]), 2)
            erp_project = proj_id if i % 41 else proj["ProjectID"]
            erp.append({"ERPDocumentNo": f"50{2026}{i:06d}", "PostingDate": (trip_end + timedelta(days=(i % 18) + 2)).isoformat(), "ProjectID": erp_project, "CostCategory": category, "RecordedAmountEUR": f"{erp_amount:.2f}", "VendorOrEmployeeRef": emp["EmployeeID"], "Description": f"Travel expense - {category.lower()} - {travel_id}", "TravelRef": travel_id})
    # 200 unmatched ERP records, including plausible duplicates and independent spend.
    for j in range(801, 1001):
        emp = employees[(j * 13) % 600]
        proj = projects[(j * 17) % 600]
        category = CATEGORIES[(j * 5) % len(CATEGORIES)]
        day = start + timedelta(days=(j * 2) % 320)
        erp.append({"ERPDocumentNo": f"50{2026}{j:06d}", "PostingDate": day.isoformat(), "ProjectID": proj["ProjectID"], "CostCategory": category, "RecordedAmountEUR": f"{random.uniform(30, 1900):.2f}", "VendorOrEmployeeRef": emp["EmployeeID"] if j % 3 else random.choice(VENDORS), "Description": "Travel expense - unmatched ERP item" if j % 2 else "Potential duplicate travel posting", "TravelRef": f"ERP-ONLY-{j:05d}"})
    # Add 12 explicit duplicate declarations to teach duplicate detection.
    for i in range(12):
        duplicate = declarations[99 + i].copy()
        duplicate["TravelRef"] = f"TR-DUP-{i+1:03d}"
        duplicate["SubmissionDate"] = (today - timedelta(days=i+2)).isoformat()
        declarations.append(duplicate)

    followups = []
    reasons = ["Receipt missing", "Travel dates incomplete", "Project code clarification", "Amount discrepancy", "Employee details missing", "Expense category missing"]
    statuses = ["Open", "Requested", "Awaiting employee", "Resolved"]
    for i in range(1, 701):
        travel = declarations[(i * 19) % len(declarations)]
        request = today - timedelta(days=(i * 7) % 45)
        due = request + timedelta(days=7)
        status = statuses[i % len(statuses)]
        followups.append({"FollowUpID": f"FU-{i:05d}", "TravelRef": travel["TravelRef"], "EmployeeID": travel["EmployeeID"], "MissingDocumentOrQuestion": reasons[(i * 3) % len(reasons)], "RequestDate": request.isoformat(), "DueDate": due.isoformat(), "Status": status, "ResolutionDate": (due + timedelta(days=1)).isoformat() if status == "Resolved" else "", "Owner": "Administrative Operations"})

    write("employees.csv", employees)
    write("projects.csv", projects)
    write("travel_declarations.csv", declarations)
    write("erp_project_costs_simulated.csv", erp)
    write("follow_up_tracker.csv", followups)
    print("Created: 600 employees, 600 projects, 1,012 declarations, 1,000 simulated ERP lines, 700 follow-ups")
    print(f"Seed: {SEED}; data directory: {DATA}")

if __name__ == "__main__":
    main()
