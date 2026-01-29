import pandas as pd
import re
import argparse

# ==========================================
# CONFIGURATION
# ==========================================
ROSTER_FILE = 'OUTPUT Auto-Roster.csv'

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def parse_year(date_str):
    """Parses XXX.M41 or XXX.M42 into an integer year. Handles 'Current'."""
    s = str(date_str).strip()
    if not s or s.lower() in ["alive", "dead", "nan", "", "current"]: return 99999 # Future/Present
    try:
        parts = s.split('.')
        y = int(parts[0])
        if len(parts) > 1 and "M42" in parts[1]: return 1000 + y
        return y
    except: return None

def get_ordinal(n):
    """Matches the ordinal logic from astarties.py"""
    if 11 <= (n % 100) <= 13: suffix = 'th'
    else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def get_location_string(company, squad):
    """Reconstructs the location string used in Deployment History logs."""
    if company == -1: return "Chapter Reserve"
    if company == 0:
        if squad == 0: return "Chapter Command"
        if squad == 1: return "Apothecarion"
        if squad == 2: return "Reclusiam"
        if squad == 3: return "Libarius"
        if squad == 4: return "Armory"
        return "Chapter HQ Support"
    
    # Companies 1-10
    comp_str = f"{get_ordinal(company)} Chapter"
    if squad == 0:
        return f"{comp_str}, Command Squad"
    else:
        return f"{comp_str}, {get_ordinal(squad)} Squad"

def find_rank_at_time(rank_history_text, target_year):
    """Parses Rank History to find the rank held at a specific year."""
    # Regex matches: "Rank Name (Start.MXX - End.MXX)"
    lines = rank_history_text.split('\n')
    for line in lines:
        if not line.strip(): continue
        # Capture: Group 1 (Rank), Group 2 (Start), Group 3 (End)
        match = re.search(r"^(.*?) \((.*?\.M4[12]) - (.*?)\)", line)
        if match:
            rank = match.group(1)
            start_year = parse_year(match.group(2))
            end_year = parse_year(match.group(3))
            
            if start_year is not None and start_year <= target_year <= end_year:
                return rank
    return "Unknown Rank"

def run_query(target_year_str, company, squad):
    target_year = parse_year(target_year_str)
    if target_year is None:
        print(f"Invalid year format: {target_year_str}")
        return

    target_location = get_location_string(company, squad)
    print(f"Querying Codex for: {target_location} in {target_year_str} (Abs: {target_year})")

    try:
        df = pd.read_csv(ROSTER_FILE).fillna("")
    except FileNotFoundError:
        print(f"Error: Could not find {ROSTER_FILE}. Run astarties.py first.")
        return

    found_members = []

    for _, row in df.iterrows():
        dep_hist = str(row['Deployment History'])
        
        # Check if marine was at location at time
        if target_location in dep_hist:
            lines = dep_hist.split('\n')
            for line in lines:
                if target_location in line:
                    match = re.search(r"\((.*?\.M4[12]) - (.*?)\)", line)
                    if match:
                        start = parse_year(match.group(1))
                        end = parse_year(match.group(2))
                        if start is not None and start <= target_year <= end:
                            rank = find_rank_at_time(str(row['Rank History']), target_year)
                            found_members.append((row['Chapter ID Number'], row['Name'], rank))
                            break

    print(f"\nFound {len(found_members)} members active in {target_location}:")
    print(f"{'ID':<6} | {'Name':<25} | {'Rank'}")
    print("-" * 50)
    for mid, name, rank in found_members:
        print(f"{mid:<6} | {name:<25} | {rank}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Codex Astartes Roster.")
    parser.add_argument("year", help="Year to query (e.g. 850.M41)")
    parser.add_argument("company", type=int, help="Company Number")
    parser.add_argument("squad", type=int, help="Squad Number")
    
    args = parser.parse_args()
    run_query(args.year, args.company, args.squad)
