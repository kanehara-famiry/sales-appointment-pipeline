#!/usr/bin/env python3
"""
スプレッドシート操作用ユーティリティ
"""
import json, os, sys
from pathlib import Path

SPREADSHEET_PATH = os.environ.get("APPOINTMENT_SHEET_PATH",
    "/opt/data/sales_appointment_prep_package.xlsx")

# openpyxl from venv
BASEDIR = Path(__file__).resolve().parent.parent.parent
VENV_PYTHON = BASEDIR / ".venv_sales" / "bin" / "python"


def with_openpyxl(func):
    """Decorator that runs the function in a subprocess with openpyxl available."""
    import subprocess
    code = json.dumps(func.__code__.co_code.hex())
    # We'll implement this differently - direct import via sys.path manipulation
    # Actually, let's just use a wrapper script approach
    pass


def read_appointments():
    """Read all appointment rows from sheet1 (入力管理)."""
    import subprocess
    result = subprocess.run(
        [str(VENV_PYTHON), str(Path(__file__).parent / "_read_sheet.py")],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"ERROR reading spreadsheet: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"ERROR parsing output: {e}", file=sys.stderr)
        return []


def write_appointment_cell(apo_id, column_letter, value):
    """Write a single cell value back to the spreadsheet by apo_id."""
    import subprocess
    data = json.dumps({"apo_id": apo_id, "col": column_letter, "value": value})
    result = subprocess.run(
        [str(VENV_PYTHON), str(Path(__file__).parent / "_write_cell.py"), data],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"ERROR writing cell: {result.stderr}", file=sys.stderr)
        return False
    return True


def update_status(apo_id, new_status):
    """Update the status column (H) for an appointment."""
    return write_appointment_cell(apo_id, "H", new_status)


def update_confirm_count(apo_id, count):
    """Update the 要確認数 column (K)."""
    return write_appointment_cell(apo_id, "K", str(count))


def update_proposal_url(apo_id, url):
    """Update the 提案資料URL column (AB)."""
    return write_appointment_cell(apo_id, "AB", url)


def update_timestamp(apo_id):
    """Update the 最終更新日時 column (AJ)."""
    from datetime import datetime
    return write_appointment_cell(apo_id, "AJ", datetime.now().strftime("%Y/%m/%d %H:%M"))


def get_status_counts():
    """Get count of appointments by status."""
    apps = read_appointments()
    counts = {}
    for app in apps:
        s = app.get("status", "未着手")
        counts[s] = counts.get(s, 0) + 1
    return counts


def find_pending_appointments():
    """Find appointments that are '未着手'."""
    apps = read_appointments()
    return [a for a in apps if a.get("status", "") == "未着手"]


def read_agent_assignments():
    """Read agent assignment table from sheet2."""
    import subprocess
    result = subprocess.run(
        [str(VENV_PYTHON), str(Path(__file__).parent / "_read_sheet2.py")],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"ERROR reading sheet2: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Spreadsheet utility for appointment pipeline")
    parser.add_argument("command", choices=["list", "pending", "status", "write", "agents"],
                        help="Command to run")
    parser.add_argument("--id", help="Appointment ID")
    parser.add_argument("--col", help="Column letter")
    parser.add_argument("--value", help="Value to write")
    args = parser.parse_args()

    if args.command == "list":
        apps = read_appointments()
        print(json.dumps(apps, ensure_ascii=False, indent=2))
    elif args.command == "pending":
        apps = find_pending_appointments()
        print(json.dumps(apps, ensure_ascii=False, indent=2))
    elif args.command == "status":
        counts = get_status_counts()
        print(json.dumps(counts, ensure_ascii=False, indent=2))
    elif args.command == "write":
        if not all([args.id, args.col, args.value]):
            print("ERROR: --id, --col, --value required", file=sys.stderr)
            sys.exit(1)
        ok = write_appointment_cell(args.id, args.col, args.value)
        print(json.dumps({"success": ok}))
    elif args.command == "agents":
        agents = read_agent_assignments()
        print(json.dumps(agents, ensure_ascii=False, indent=2))
