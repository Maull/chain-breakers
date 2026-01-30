import os
import random
import pandas as pd

try:
    import gspread
except ImportError:
    print("Error: gspread library not installed. Run: pip install gspread")
    gspread = None

from config import (
    FIRST_NAMES,
    LAST_NAMES,
    SERVICE_ACCOUNT_FILE,
    SCOPES,
    SPREADSHEET_ID,
    HUMAN_OFFICES,
)
from utils import parse_year


def upload_to_google_sheets(transaction_log, relics_log):
    print("Initiating Uplink to Codex Datasheet...")

    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Error: '{SERVICE_ACCOUNT_FILE}' not found. Upload skipped.")
        return

    if not gspread:
        return

    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        sh = gc.open_by_key(SPREADSHEET_ID)

        def _upload_sheet(sheet_name, df):
            try:
                ws = sh.worksheet(sheet_name)
                ws.clear()
                data = [df.columns.values.tolist()] + df.values.tolist()
                ws.update(range_name="A1", values=data)
                print(f"{sheet_name} uploaded.")
            except Exception as e:
                print(f"Error uploading {sheet_name}: {e}")

        _upload_sheet("Logbook", pd.DataFrame(transaction_log))
        _upload_sheet("Relics", pd.DataFrame(relics_log))
        
        # Roster is still read from CSV
        try:
            roster_df = pd.read_csv("OUTPUT Auto-Roster.csv").fillna("")
            _upload_sheet("Roster", roster_df)
        except Exception as e:
            print(f"Error uploading Roster: {e}")

    except Exception as e:
        print(f"Google Sheets API Error: {e}")


def update_human_officers():
    print("Synchronizing Human High Command (Noxian PDF)...")

    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Error: '{SERVICE_ACCOUNT_FILE}' not found. Human Officer update skipped.")
        return

    if not gspread:
        return

    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        sh = gc.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet("Offices")

        # Download current data
        raw_values = ws.get_all_values()

        raw_formulas = ws.get(value_render_option="FORMULA")

        # Find Header Row
        header_row_idx = -1
        headers = []
        for i, row in enumerate(raw_values):
            if "High Marshal of Nox (Human Commander)" in row:
                header_row_idx = i
                headers = row
                break

        if header_row_idx == -1:
            print("Error: Could not find header row in 'Offices' tab.")
            return

        # Map column names to indices
        col_map = {name: idx for idx, name in enumerate(headers) if name}

        # Initialize State for Officers
        # Format: "Role": {"Name": "Rank Name", "RetireYear": int}
        officer_state = {
            role: {"Name": None, "RetireYear": 0} for role in HUMAN_OFFICES
        }

        # Process Rows (Timeline)
        updated_data = [row[:] for row in raw_formulas]  # Deep copy of formulas

        for r_idx in range(header_row_idx + 1, len(updated_data)):
            row_form = updated_data[r_idx]
            if r_idx >= len(raw_values):
                break
            row_val = raw_values[r_idx]

            # Get Year
            # Assuming Year is in column 1 (index 1) based on provided CSV structure: ",638.M41,..."
            # If headers are shifted, we might need to find "Year" column, but CSV context shows it at index 1.
            if len(row_val) < 2:
                continue
            year_str = row_val[1]
            current_year = parse_year(year_str)

            if not current_year or current_year < 638:
                continue

            # Update Officers
            for role, config in HUMAN_OFFICES.items():
                if role not in col_map:
                    continue
                col_idx = col_map[role]

                # Check Start Year
                if current_year < config.get("StartYear", 0):
                    continue

                # Handle Linked Roles (Arrow of Terminus follows Master of Fleet)
                if config.get("IsLinked"):
                    # Find the master role
                    master_role = next(
                        (
                            k
                            for k, v in HUMAN_OFFICES.items()
                            if v.get("Linked") == role
                        ),
                        None,
                    )
                    if master_role and officer_state[master_role]["Name"]:
                        while len(row_form) <= col_idx:
                            row_form.append("")
                        row_form[col_idx] = officer_state[master_role]["Name"]
                    continue

                # Check if we need a new officer
                state = officer_state[role]

                if state["Name"] is None or current_year >= state["RetireYear"]:
                    # Generate New Officer
                    # Tenure: Min Age + (0-5) to start. Serve until Max Age +/- 5.
                    start_age = config["MinAge"] + random.randint(0, 5)
                    end_age = config["MaxAge"] + random.randint(-5, 5)
                    if end_age <= start_age:
                        end_age = start_age + 5

                    tenure = end_age - start_age
                    state["RetireYear"] = current_year + tenure

                    # Generate Name
                    first = random.choice(FIRST_NAMES)
                    last = random.choice(LAST_NAMES)
                    rank = config["Rank"]
                    state["Name"] = f"{rank} {first} {last}"

                # Write to Row
                while len(row_form) <= col_idx:
                    row_form.append("")
                row_form[col_idx] = state["Name"]

        # Upload back to Sheets
        print("Uploading updated Human Officers to 'Offices' tab...")
        ws.update(
            range_name="A1", values=updated_data, value_input_option="USER_ENTERED"
        )

        # Save local copy
        pd.DataFrame(updated_data).to_csv(
            "Codex Datasheet - Offices.csv", index=False, header=False
        )
        print("Human Officers synchronized.")

    except Exception as e:
        print(f"Error updating Human Officers: {e}")
