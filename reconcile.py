"""Reconcile synthetic travel declarations against the simulated ERP export."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"

def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def save(name: str, rows: list[dict]) -> None:
    if not rows:
        return
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main() -> None:
    OUT.mkdir(exist_ok=True)
    employees, projects = read("employees.csv"), read("projects.csv")
    declarations, erp = read("travel_declarations.csv"), read("erp_project_costs_simulated.csv")
    employee_map = {r["EmployeeID"]: r for r in employees}
    project_map = {r["ProjectID"]: r for r in projects}
    erp_by_ref: dict[str, list[dict]] = defaultdict(list)
    for row in erp:
        erp_by_ref[row["TravelRef"]].append(row)
    declared_key_counts = Counter((r["EmployeeID"], r["ProjectID"], r["ExpenseCategory"], r["DeclaredAmountEUR"], r["TravelStart"]) for r in declarations)
    results = []
    matched_erp = set()
    for row in declarations:
        issues = []
        if not row["EmployeeID"] or row["EmployeeID"] not in employee_map:
            issues.append("Missing or invalid employee")
        if not row["TravelStart"] or not row["TravelEnd"]:
            issues.append("Missing travel dates")
        if not row["ProjectID"] or row["ProjectID"] not in project_map:
            issues.append("Invalid project code")
        if not row["ExpenseCategory"]:
            issues.append("Missing expense category")
        if not row["ReceiptRef"]:
            issues.append("Missing receipt")
        key = (row["EmployeeID"], row["ProjectID"], row["ExpenseCategory"], row["DeclaredAmountEUR"], row["TravelStart"])
        if declared_key_counts[key] > 1:
            issues.append("Potential duplicate declaration")
        candidates = erp_by_ref.get(row["TravelRef"], [])
        if not candidates:
            status, erp_doc, variance, tx = "Unmatched declaration", "", "", None
        else:
            tx = candidates[0]
            erp_doc = tx["ERPDocumentNo"]
            matched_erp.add(tx["ERPDocumentNo"])
            variance = round(float(tx["RecordedAmountEUR"]) - float(row["DeclaredAmountEUR"]), 2)
            dims_equal = (row["ProjectID"] == tx["ProjectID"] and row["ExpenseCategory"] == tx["CostCategory"] and row["EmployeeID"] == tx["VendorOrEmployeeRef"])
            if not dims_equal:
                status = "Dimension discrepancy"
                issues.append("Project, employee or category differs from ERP")
            elif abs(variance) > 0.01:
                status = "Amount discrepancy"
                issues.append("Declared and ERP amounts differ")
            else:
                status = "Exact match"
        completeness = "Complete" if not any(x in issues for x in ["Missing or invalid employee", "Missing travel dates", "Invalid project code", "Missing expense category", "Missing receipt"]) else "Incomplete"
        results.append({"TravelRef": row["TravelRef"], "EmployeeID": row["EmployeeID"], "ProjectID": row["ProjectID"], "ExpenseCategory": row["ExpenseCategory"], "DeclaredAmountEUR": row["DeclaredAmountEUR"], "ERPDocumentNo": erp_doc, "ERPAmountEUR": "" if tx is None else tx["RecordedAmountEUR"], "VarianceEUR": variance, "ReconciliationStatus": status, "CompletenessStatus": completeness, "Issues": "; ".join(issues)})
    erp_unmatched = [{**r, "ReconciliationStatus": "Unmatched ERP transaction"} for r in erp if r["ERPDocumentNo"] not in matched_erp]
    save("reconciliation_results.csv", results)
    save("unmatched_erp_transactions.csv", erp_unmatched)

    project_summary = []
    for p in projects:
        amount = sum(float(r["RecordedAmountEUR"]) for r in erp if r["ProjectID"] == p["ProjectID"])
        project_summary.append({"ProjectID": p["ProjectID"], "ProjectName": p["ProjectName"], "Department": p["Department"], "BudgetEUR": p["BudgetEUR"], "RecordedSpendEUR": f"{amount:.2f}", "BudgetUtilization": f"{amount / float(p['BudgetEUR']):.4%}"})
    save("project_spend_summary.csv", project_summary)
    counts = Counter(r["ReconciliationStatus"] for r in results)
    incomplete = sum(r["CompletenessStatus"] == "Incomplete" for r in results)
    print("Reconciliation complete (exact TravelRef first; dimensions then amount checked).")
    print(f"Declarations: {len(results)} | exact: {counts['Exact match']} | amount differences: {counts['Amount discrepancy']} | dimension differences: {counts['Dimension discrepancy']} | unmatched declarations: {counts['Unmatched declaration']}")
    print(f"Incomplete declarations: {incomplete} | unmatched ERP lines: {len(erp_unmatched)}")
    print(f"Reports saved to: {OUT}")

if __name__ == "__main__":
    main()
