"""Build the Excel management workbook from the generated CSV source and reports."""
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import xlsxwriter

ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "outputs"
OUT.mkdir(exist_ok=True)

SHEETS = [
    ("Employees", DATA / "employees.csv"), ("Projects", DATA / "projects.csv"),
    ("Declarations", DATA / "travel_declarations.csv"),
    ("ERP Simulated", DATA / "erp_project_costs_simulated.csv"),
    ("Reconciliation", OUT / "reconciliation_results.csv"),
    ("Follow-ups", DATA / "follow_up_tracker.csv"),
    ("Unmatched ERP", OUT / "unmatched_erp_transactions.csv"),
    ("Project Spend", OUT / "project_spend_summary.csv"),
]

def read_csv(file):
    with file.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

def as_value(header, value):
    if value == "":
        return None
    if header == "BudgetUtilization":
        try:
            return float(value.rstrip("%")) / (100 if value.endswith("%") else 1)
        except ValueError:
            return value
    if "EUR" in header or header == "BudgetEUR":
        try:
            return float(value)
        except ValueError:
            return value
    if header.endswith("Date") or header in ("TravelStart", "TravelEnd", "PostingDate"):
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return value
    return value

def main():
    if not (OUT / "reconciliation_results.csv").exists():
        raise SystemExit("Run generate_data.py and reconcile.py first.")
    workbook = xlsxwriter.Workbook(str(OUT / "expense_control_workbook.xlsx"))
    workbook.set_properties({"title": "Nexora Expense Control & Project Reporting", "subject": "Synthetic administrative expense control training project", "author": "Nexora Technologies GmbH (fictional training company)"})
    navy = "#17365D"
    header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": navy, "align": "center", "valign": "vcenter", "text_wrap": True, "border": 0})
    title = workbook.add_format({"bold": True, "font_size": 16, "font_color": navy})
    note = workbook.add_format({"italic": True, "font_color": "#526579", "font_size": 9})
    money = workbook.add_format({"num_format": '€#,##0.00;[Red]-€#,##0.00'})
    datefmt = workbook.add_format({"num_format": "dd-mmm-yyyy"})
    percent = workbook.add_format({"num_format": "0.0%"})
    warning = workbook.add_format({"bg_color": "#FCE4D6", "font_color": "#9C0006"})

    all_data = {}
    for name, file in SHEETS:
        cols, rows = read_csv(file)
        all_data[name] = (cols, rows)

    overview = workbook.add_worksheet("Overview")
    overview.hide_gridlines(2)
    overview.set_tab_color(navy)
    overview.set_column("A:A", 40)
    overview.set_column("B:B", 21)
    overview.set_column("C:C", 3)
    overview.set_column("D:D", 24)
    overview.set_column("E:E", 21)
    overview.write("A1", "Nexora | Expense control & project reporting", title)
    overview.write("A2", "Synthetic training data • EUR • ERP-style source is simulated, not connected to SAP", note)
    overview.write_row("A4", ["Control measure", "Current result"], header)

    recs = all_data["Reconciliation"][1]
    erp = all_data["ERP Simulated"][1]
    projects = all_data["Projects"][1]
    followups = all_data["Follow-ups"][1]
    counts = Counter(r["ReconciliationStatus"] for r in recs)
    incomplete = sum(r["CompletenessStatus"] == "Incomplete" for r in recs)
    open_followups = sum(r["Status"] != "Resolved" for r in followups)
    spend = sum(float(r["RecordedAmountEUR"]) for r in erp)
    budgets = sum(float(r["BudgetEUR"]) for r in projects)
    metrics = [
        ("ERP recorded spend", spend, money), ("Total project budgets", budgets, money),
        ("Exact matches", counts["Exact match"], None), ("Amount discrepancies", counts["Amount discrepancy"], None),
        ("Dimension discrepancies", counts["Dimension discrepancy"], None), ("Unmatched declarations", counts["Unmatched declaration"], None),
        ("Incomplete declarations", incomplete, None), ("Open follow-ups", open_followups, None),
    ]
    for rownum, (label, val, fmt) in enumerate(metrics, 4):
        overview.write(rownum, 0, label)
        overview.write(rownum, 1, val, fmt)
    dept_for_project = {r["ProjectID"]: r["Department"] for r in projects}
    dept_spend = defaultdict(float)
    for r in erp:
        dept_spend[dept_for_project.get(r["ProjectID"], "Unknown")] += float(r["RecordedAmountEUR"])
    overview.write_row("D4", ["Department", "ERP spend (EUR)"], header)
    for n, (dept, total) in enumerate(sorted(dept_spend.items()), 4):
        overview.write(n, 3, dept)
        overview.write(n, 4, total, money)
    overview.write("A15", "Review sequence", workbook.add_format({"bold": True, "font_color": navy, "font_size": 11}))
    steps = [
        "1  Filter incomplete declarations; resolve the issue listed on each row.",
        "2  Review amount and dimension discrepancies against supporting evidence.",
        "3  Investigate potential duplicates individually; flags are not automatic rejections.",
        "4  Review ERP-only transactions and follow-up due dates with the responsible employee.",
        "5  Validate budget utilization against approved project records before management use.",
    ]
    for i, step in enumerate(steps, 15):
        overview.write(i, 0, step)
    overview.set_column("A:A", 54)
    chart = workbook.add_chart({"type": "bar"})
    chart.add_series({"name": "ERP spend", "categories": ["Overview", 4, 3, 4 + len(dept_spend) - 1, 3], "values": ["Overview", 4, 4, 4 + len(dept_spend) - 1, 4], "fill": {"color": "#4472C4"}})
    chart.set_title({"name": "Recorded spend by department"})
    chart.set_legend({"none": True})
    chart.set_y_axis({"reverse": True})
    chart.set_x_axis({"num_format": '€#,##0'})
    chart.set_size({"width": 520, "height": 280})
    overview.insert_chart("G4", chart)
    overview.freeze_panes(3, 0)

    for name, _ in SHEETS:
        cols, rows = all_data[name]
        ws = workbook.add_worksheet(name)
        ws.hide_gridlines(2)
        ws.freeze_panes(1, 0)
        ws.set_row(0, 32, header)
        ws.add_table(0, 0, len(rows), len(cols) - 1, {
            "name": "T" + "".join(ch for ch in name.title() if ch.isalnum()),
            "style": "Table Style Medium 2",
            "columns": [{"header": c} for c in cols],
            "data": [[as_value(c, r[c]) for c in cols] for r in rows],
            "autofilter": True,
        })
        for i, col in enumerate(cols):
            width = min(max(len(col) + 2, 14), 31)
            if col in ("Description", "Issues", "MissingDocumentOrQuestion"):
                width = 38
            fmt = money if ("EUR" in col or col == "BudgetEUR") else datefmt if (col.endswith("Date") or col in ("TravelStart", "TravelEnd", "PostingDate")) else None
            ws.set_column(i, i, width, fmt)
        if name == "Reconciliation":
            status_col = cols.index("ReconciliationStatus")
            ws.conditional_format(1, status_col, len(rows), status_col, {"type": "text", "criteria": "containing", "value": "discrepancy", "format": warning})
            ws.conditional_format(1, status_col, len(rows), status_col, {"type": "text", "criteria": "containing", "value": "Unmatched", "format": warning})
        if name == "Project Spend":
            pct_col = cols.index("BudgetUtilization")
            ws.set_column(pct_col, pct_col, 19, percent)
    workbook.close()
    print(f"Workbook built: {OUT / 'expense_control_workbook.xlsx'}")

if __name__ == "__main__":
    main()
