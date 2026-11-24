# Administrative Operations, Expense Reconciliation & Management Reporting

A small, repeatable administrative control workflow based on the supplied project brief. It checks employee travel declarations against a clearly **simulated SAP-style ERP export**, flags missing information and likely duplicate claims, and prepares project spend and follow-up reports.

> **Training data only:** Nexora Technologies GmbH and every person, project, supplier, amount, reference and transaction in this project are fictional. The ERP export is synthetic and was not accessed from SAP or any real company system. Amounts are in EUR.

## Start here (Windows)

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). During setup, select **Add Python to PATH**.
2. Open this folder in File Explorer. Click the address bar, type `powershell`, and press Enter.
3. Install the workbook dependency, then run these commands:

   ```powershell
   python -m pip install -r requirements.txt
   python generate_data.py
   python reconcile.py
   python build_workbook.py
   ```

4. Open `outputs/reconciliation_results.csv` or `outputs/project_spend_summary.csv` in Excel. The other output, `outputs/unmatched_erp_transactions.csv`, lists ERP-side items without a declaration.

Only Excel workbook creation needs XlsxWriter; data generation and reconciliation use the Python standard library. Running `generate_data.py` recreates the same records from a fixed seed. Run it before `reconcile.py` whenever you want a clean refresh. Run `build_workbook.py` after refreshing the reports. The `data` folder is the source layer; files in `outputs` are generated reports.

## Included workbook

Open `outputs/expense_control_workbook.xlsx` in Microsoft Excel. Start on **Overview**, then use the filterable tables to review employee and project masters, declarations, ERP source lines, reconciliation results and follow-ups. It contains the same generated snapshot as the CSV files. Run the commands above to rebuild the complete project outputs.

## Dataset sizes

| File | Records (excluding header) | Use |
|---|---:|---|
| `data/employees.csv` | 600 | Employee, department, manager and cost centre master |
| `data/projects.csv` | 600 | Project, manager, cost centre, department and budget master |
| `data/travel_declarations.csv` | 1,012 | Employee travel and expense submissions |
| `data/erp_project_costs_simulated.csv` | 1,000 | Simulated ERP project cost export |
| `data/follow_up_tracker.csv` | 700 | Document and clarification follow-up queue |
| `outputs/reconciliation_results.csv` | 1,012 | Declaration-level status, variance and completeness results |
| `outputs/unmatched_erp_transactions.csv` | 200 | ERP transactions without a declaration reference |
| `outputs/project_spend_summary.csv` | 600 | Recorded spend and budget utilization by project |

The generated data deliberately includes realistic practice exceptions: blank receipts and fields, invalid project references, possible duplicate declarations, amount variances, dimension mismatches, and unmatched rows on both sides.

## Reconciliation control logic

The workflow first pairs rows by the unique travel reference, then checks project, employee/reference and expense category. It labels a row **Exact match** only when those dimensions agree and the amount difference is no more than EUR 0.01. It separately reports amount discrepancies, dimension discrepancies and unmatched declarations. A repeated combination of employee, project, category, amount and travel start date is flagged as a **Potential duplicate declaration**; that is a review prompt, not an automatic rejection. Completeness checks cover employee ID, travel dates, project code, category and receipt reference. ERP-only rows are listed separately.

## Project files

- `generate_data.py` — deterministic synthetic source-data generator.
- `reconcile.py` — standard-library reconciliation and report generator.
- `build_workbook.py` — creates the Excel workbook with filterable tables, exception highlighting and a department spend chart.
- `docs/administrative_control_procedure.md` — step-by-step review and exception handling procedure.
- `docs/email_templates.md` — employee follow-up email templates.
- `data/` — source CSV datasets.
- `outputs/` — generated CSV reports and workbook.

## Refresh or adapt

To refresh after changing the generator, run `generate_data.py`, `reconcile.py` and `build_workbook.py` in that order. Keep the CSV column names stable, since the scripts expect those headers. To use real company data, replace synthetic files only when authorized, preserve access controls, validate identifiers and currency, and confirm the matching rules with the process owner. Never treat a same-value amount as a verified match by itself.

## Suggested review sequence

1. Filter the reconciliation report to **Incomplete** and address each issue listed in `Issues`.
2. Review **Amount discrepancy**, **Dimension discrepancy** and **Unmatched declaration** rows against source documents.
3. Review potential duplicates individually; the flag can identify legitimate repeat expenses as well as duplicate submissions.
4. Check unmatched ERP items and follow-up due dates with the responsible employee.
5. Use project spend and budget utilization as a management view, then validate material items against authorized source records.

This is a training workflow, not an SAP integration, an accounting system, or an automated approval decision.
