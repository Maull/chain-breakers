import pandas as pd
import random
import re
import os
from astarties_data import *

# ==========================================
# 1. CONFIGURATION
# ==========================================

# Timeline
START_YEAR_ABS = 540   
END_YEAR_ABS = 1018    
REFOUNDING_YEAR = 636  
RECRUITMENT_START = 638

NEOPHYTE_INTAKE_OVERRIDE = 0 
TARGET_POPULATION = 1200

# Google Sheets Configuration
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = '1FmexJsqPIEVe4OgLWv2j1I3LUqsHhPBKEj48T8mW780'
TRANSACTION_LOG = []
DISCOVERED_RELICS_LOG = []

def log_transaction(year, marine, event, details=""):
    if marine.squad_assignment:
        c = marine.squad_assignment[0]
        s = marine.squad_assignment[1]
        k = marine.current_slot
    else:
        # Use a specific value for unassigned, not 0,0,0 which is Chapter Master's slot
        c, s, k = -2, -2, -2
    TRANSACTION_LOG.append({
        "Year": year,
        "Marine ID": marine.id,
        "Name": marine.name,
        "Event": event,
        "Rank": marine.current_rank,
        "Company": c,
        "Squad": s,
        "Slot": k,
        "Details": details
    })

def log_relic_discovery(relic):
    DISCOVERED_RELICS_LOG.append({
        "ID": relic.get('id', ''),
        "Name": relic.get('name', ''),
        "Type": relic.get('type', ''),
        "Description": relic.get('desc', ''),
        "Year Acquired": relic.get('date', '')
    })

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def get_year_str(year_abs):
    if year_abs < 1000: return f"{year_abs}.M41"
    else: return f"{year_abs - 1000:03d}.M42"

def parse_year(date_str):
    s = str(date_str).strip()
    if not s or s.lower() in ["alive", "dead", "nan", ""]: return None
    try:
        parts = s.split('.')
        y = int(parts[0])
        if len(parts) > 1 and "M42" in parts[1]: return 1000 + y
        return y
    except: return None

def get_ordinal(n):
    if 11 <= (n % 100) <= 13: suffix = 'th'
    else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def to_roman(n):
    if n <= 0: return ""
    num_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
               (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    roman = ''
    for i, r in num_map:
        while n >= i:
            roman += r
            n -= i
    return roman

# ==========================================
# 3. CLASS DEFINITIONS
# ==========================================

class Marine:
    def __init__(self, data_row=None, procedural_id=None, birth_year=None, name=None):
        self.moved_this_turn = False 
        self.is_old_guard = False
        self.current_slot = 0

        if data_row is not None:
            # --- OLD GUARD ---
            self.id = str(data_row['Chapter ID Number'])
            self.is_old_guard = True if int(self.id) < 1000 else False
            self.name = data_row['Name']
            self.cognomen = str(data_row['Cognomen / Earned Name'])
            self.born_str = str(data_row['Born'])
            self.geneseed_str = str(data_row['Date of Geneseed Implantation'])
            self.death_str = str(data_row['Date of Death'])
            self.death_year_abs = parse_year(self.death_str)
            
            if self.death_str and self.death_str.lower() != "alive":
                if self.death_year_abs and self.death_year_abs >= START_YEAR_ABS:
                    self.status = "Alive"
                else:
                    self.status = "Dead"
            else:
                self.status = "Alive"

            self.is_protected = True if self.death_str.lower() == "alive" else False
            self.deployment_history = str(data_row['Deployment History']) if pd.notna(data_row['Deployment History']) else ""
            self.personality = str(data_row['Personality / Psy-Profile'])
            self.notes = str(data_row['Notes'])
            self.implantation_year = parse_year(self.geneseed_str)
            if not self.implantation_year: self.implantation_year = 550
            
            self.rank_history = str(data_row['Rank History']) if pd.notna(data_row['Rank History']) else ""
            self.current_rank = self.rank_history.split('(')[0].strip() if self.rank_history else "Veteran Battle Brother"
            if not self.rank_history:
                self.rank_history = f"{self.current_rank} ({get_year_str(self.implantation_year)} - Current) (Unknown age)\n"
            self.current_tier = TIERS.get(self.current_rank, 2)
            
            # LORE OVERRIDE: Garrick (ID 101) starts as Sergeant
            # LORE OVERRIDE: Garrick (ID 101) starts as Battle Brother
            # LORE OVERRIDE: Garrick (ID 101) starts as a Battle Brother.
            if self.id == "101":
                self.current_rank = "Sergeant"
                self.current_tier = TIERS.get(self.current_rank, 3)
                self.rank_history = f"Sergeant ({get_year_str(self.implantation_year)} - Current)\n"
                self.current_rank = "Battle Brother"
                self.current_tier = TIERS.get(self.current_rank, 1)
                self.rank_history = f"Battle Brother ({get_year_str(self.implantation_year)} - Current)\n"

            # LORE OVERRIDE: Ferren Vrox (ID 200) must survive to 771.M41
            if self.id == "200":
                self.status = "Alive"
                self.death_str = "Alive"
                self.death_year_abs = None
                self.is_protected = True
                if "Commander" in self.current_rank:
                    self.current_rank = "Captain"
                    self.rank_history = self.rank_history.replace("Commander", "Captain")
                    self.current_tier = TIERS.get(self.current_rank, 5)
        else:
            # --- PROCEDURAL ---
            self.id = str(procedural_id)
            self.is_old_guard = False
            if name:
                self.name = name
            else:
                self.name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            self.cognomen = ""
            self.born_str = get_year_str(birth_year)
            self.geneseed_str = get_year_str(birth_year + 12)
            self.death_str = "Alive"
            self.status = "Alive"
            self.death_year_abs = None
            self.is_protected = False
            self.deployment_history = ""
            self.personality = ""
            self.notes = "Standard Indoctrination"
            self.implantation_year = birth_year + 12
            self.current_rank = "Neophyte"
            self.current_tier = 0
            self.rank_history = f"Neophyte ({get_year_str(self.implantation_year)} - Current) (12 Years old on date of promotion)\n"

        self.squad_assignment = None
        self.years_in_rank = 0
        self.years_in_service = 0
        self.years_in_assignment = 0
        self.deathwatch_service_start = None
        self.deathwatch_terms = 0
        self.last_deathwatch_return = 0
        self.active_relics = []
        self.relic_history = []

    def reset_turn_flag(self):
        self.moved_this_turn = False

    def update_age(self, current_year):
        if self.status == "Alive":
            self.years_in_service = current_year - self.implantation_year
            self.years_in_rank += 1
            if self.squad_assignment:
                self.years_in_assignment += 1

    def _get_origin_stamp(self, year):
        """Gets the origin chapter stamp for pre-Refounding marines."""
        if year < 638:
            try:
                mid = int(self.id)
                if 100 <= mid <= 199: return " [Doom Eagles]"
                if 200 <= mid <= 299: return " [Storm Giants]"
            except (ValueError, TypeError):
                pass
        return ""

    def close_history_string(self, text_block, end_year):
        match = re.search(r'\((\d{3})\.M4([12]) - Current\)', text_block)
        if match:
            start_y_part = int(match.group(1))
            era = match.group(2)
            start_abs = start_y_part + (1000 if era == '2' else 0)
            duration = end_year - start_abs
            dur_str = f"{duration} Years" if duration > 0 else "<1 Year"
            old_str = match.group(0)
            new_str = f"({get_year_str(start_abs)} - {get_year_str(end_year)}) ({dur_str})"
            return text_block.replace(old_str, new_str, 1)
        return text_block

    def promote(self, new_rank, year, display_rank=None):
        if display_rank is None: display_rank = new_rank

        age = year - (self.implantation_year - 12)
        new_tier = TIERS.get(new_rank, 1)

        if new_tier < self.current_tier:
            note = f"Demoted on {get_year_str(year)} (from {self.current_rank} to {new_rank}) Aged {age}"
            if self.notes == "Standard Indoctrination" or not self.notes:
                self.notes = note
            else:
                self.notes += f"\n{note}"

        if "Runt" in new_rank and self.notes == "Standard Indoctrination":
            self.notes = "Ossmodula Shunt Applied"
        elif new_rank == "Bond-Keeper" and self.notes == "Standard Indoctrination":
            self.notes = "Hollow High-Capacity Identified"

        origin_stamp = ""
        if year < 638:
            try:
                mid = int(self.id)
                if 100 <= mid <= 199: origin_stamp = " [Doom Eagles]"
                elif 200 <= mid <= 299: origin_stamp = " [Storm Giants]"
            except: pass

        self.rank_history = self.close_history_string(self.rank_history, year)
        new_entry = f"{display_rank} ({get_year_str(year)} - Current) ({age} Years old on date of promotion){origin_stamp}\n"
        new_entry = f"{display_rank} ({get_year_str(year)} - Current) ({age} Years old on date of promotion){self._get_origin_stamp(year)}\n"
        self.rank_history = new_entry + self.rank_history
        self.current_rank = new_rank
        self.current_tier = TIERS.get(new_rank, 1)
        self.years_in_rank = 0
        self.moved_this_turn = True
        log_transaction(year, self, "Promotion", f"Promoted to {display_rank}")

    def receive_relic(self, relic, year):
        self.active_relics.append(relic)
        self.relic_history.append({'relic': relic, 'start': year, 'end': None})

    def return_relics(self, year, reliquary):
        for r in self.active_relics:
            for h in self.relic_history:
                if h['relic'] == r and h['end'] is None:
                    h['end'] = year
            reliquary.append(r)
        self.active_relics = []

    def deploy(self, company, squad, year, slot=0):
        if self.squad_assignment == (company, squad) and self.current_slot == slot: return
        self.deployment_history = self.close_history_string(self.deployment_history, year)
        
        origin_stamp = ""
        if year < 638:
            try:
                mid = int(self.id)
                if 100 <= mid <= 199: origin_stamp = " [Doom Eagles]"
                elif 200 <= mid <= 299: origin_stamp = " [Storm Giants]"
            except: pass
        origin_stamp = self._get_origin_stamp(year)

        if company == -1:
            new_entry = f"Chapter Reserve ({get_year_str(year)} - Current)\n"
        elif company == 0:
            if squad == 0: new_entry = f"Chapter Command ({get_year_str(year)} - Current)\n"
            elif squad == 1: new_entry = f"Apothecarion ({get_year_str(year)} - Current)\n"
            elif squad == 2: new_entry = f"Reclusiam ({get_year_str(year)} - Current)\n"
            elif squad == 3: new_entry = f"Libarius ({get_year_str(year)} - Current)\n"
            elif squad == 4: new_entry = f"Armory ({get_year_str(year)} - Current)\n"
            else: new_entry = f"Chapter HQ Support ({get_year_str(year)} - Current)\n"
        elif company == 1:
            squad_str = "Command Squad" if squad == 0 else f"{get_ordinal(squad)} Squad"
            new_entry = f"1st Chapter, {squad_str} ({get_year_str(year)} - Current)\n"
        else:
            squad_str = "Command Squad" if squad == 0 else f"{get_ordinal(squad)} Squad"
            new_entry = f"{get_ordinal(company)} Chapter, {squad_str} ({get_year_str(year)} - Current)\n"
            
        if origin_stamp:
            new_entry = new_entry.strip() + origin_stamp + "\n"

        self.deployment_history = new_entry + self.deployment_history
        self.squad_assignment = (company, squad)
        self.current_slot = slot
        self.years_in_assignment = 0
        self.moved_this_turn = True
        log_transaction(year, self, "Transfer", f"Deployed to {company}-{squad}-{slot}")

    def kill(self, year):
        self.status = "Dead"
        self.death_str = get_year_str(year)
        self.rank_history = self.close_history_string(self.rank_history, year)
        self.deployment_history = self.close_history_string(self.deployment_history, year)
        age = year - (self.implantation_year - 12)
        kia_entry = f"KIA ({self.current_rank}) ({get_year_str(year)}) ({age} Years old)\n"
        self.rank_history = kia_entry + self.rank_history
        self.moved_this_turn = True
        log_transaction(year, self, "Death", "Killed in Action")

    def to_dict(self, current_year):
        if self.status == "Alive":
            age = current_year - (self.implantation_year - 12)
        else:
            d_year = parse_year(self.death_str)
            age = (d_year - (self.implantation_year - 12)) if d_year else "Unknown"

        r_hist = self.rank_history
        d_hist = self.deployment_history
        if len(r_hist) > 45000: r_hist = r_hist[:45000] + "\n[...ARCHIVE TRUNCATED...]"
        if len(d_hist) > 45000: d_hist = d_hist[:45000] + "\n[...ARCHIVE TRUNCATED...]"

        wargear_lines = []
        for h in self.relic_history:
            r_name = h['relic']['name']
            r_type = h['relic']['type']
            start = get_year_str(h['start'])
            end = get_year_str(h['end']) if h['end'] else "Current"
            wargear_lines.append(f"{r_type} ({r_name}) ({start} - {end})")
        wargear_str = "\n".join(wargear_lines)

        return {
            'Chapter ID Number': self.id,
            'Name': self.name,
            'Cognomen / Earned Name': self.cognomen,
            'Born': self.born_str,
            'Date of Geneseed Implantation': self.geneseed_str,
            'Date of Death': self.death_str,
            'Age (Or Age at Death)': age,
            'Wargear': wargear_str,
            'Rank History': r_hist,
            'Deployment History': d_hist,
            'Personality / Psy-Profile': self.personality,
            'Notes': self.notes
        }

# ==========================================
# 4. LOGIC CORE
# ==========================================

def generate_assignment_priority_list():
    """Generates the squad filling order based on command hierarchy."""
    priority_list = []

    # 1. Chapter Command (Company 0, Squads 0-4)
    for s in range(5):
        priority_list.append((0, s))

    # 2. "First" Squads (Squad 1 of Companies 1-9)
    for c in range(1, 10):
        priority_list.append((c, 1))

    # 3. Command Squads (Squad 0 of Companies 1-9)
    for c in range(1, 10):
        priority_list.append((c, 0))

    # 4. The Rest (Squads 2-10 for Companies 1-9)
    for s in range(2, 11):
        for c in range(1, 10):
            priority_list.append((c, s))
    
    # 5. 10th Company Command
    priority_list.append((10, 0))

    # 6. 10th Company Squads (Officers)
    for s in range(1, 11):
        priority_list.append((10, s))

    return priority_list

class Chapter:
    def __init__(self):
        self.grid = {c: {s: {k: None for k in range(12)} for s in range(0, 11)} for c in range(0, 11)}
        self.reserve = [] 

    def remove_from_grid(self, marine):
        if marine.squad_assignment:
            c, s = marine.squad_assignment
            if c in self.grid:
                for k in range(12):
                    if self.grid[c][s][k] == marine:
                        self.grid[c][s][k] = None
            marine.squad_assignment = None

    def add_to_reserve(self, marine, year):
        if marine in self.reserve: return
        
        # Find lowest available slot
        used_slots = {m.current_slot for m in self.reserve}
        slot = 0
        while slot in used_slots:
            slot += 1
            
        self.reserve.append(marine)
        marine.deploy(-1, 0, year, slot)

    def get_role_rule(self, company, squad, slot, active_dreadnoughts=0):
        # Check Dreadnought Priority
        dread_index = -1
        try:
            dread_index = DREADNOUGHT_PRIORITY.index((company, squad))
        except ValueError:
            pass
        
        if dread_index != -1 and dread_index < active_dreadnoughts:
            if slot == 9: return "Dreadnought"

        # COMPANY 0 (Chapter High Command & Support)
        if company == 0:
            if squad == 0: # Chapter Command
                if slot == 0: return "Chapter Master"
                if slot in [1, 2]: return "Lieutenant" # Honor Guard / Chapter Lts
                if slot < 11: return "Veteran Battle Brother"
                return None
            if squad == 1: # Apothecarion
                if slot < 4: return "Apothecary"
                if slot < 6: return "Veteran Battle Brother"
                return None
            if squad == 2: # Reclusiam
                if slot < 4: return "Chaplain"
                if slot < 8: return "Veteran Battle Brother"
                return None
            if squad == 3: # Libarius
                if slot < 4: return "Null-Warden"
                if slot < 8: return "Veteran Battle Brother"
                return None
            if squad == 4: # Armory
                if slot == 0: return "Techmarine"
                if slot < 5: return "Artificer Brother"
                if slot < 9: return "Veteran Battle Brother"
                return None
            return None

        # COMPANY 1 (Veterans)
        if company == 1:
            # Squad 0: Command
            if squad == 0:
                roles = {0: "Captain", 1: "Standard Bearer", 2: "Apothecary", 3: "Chaplain", 4: "Null-Warden", 5: "Lieutenant", 6: "Lieutenant"}
                return roles.get(slot, None)
            
            # Squads 1-10: Veteran Battle Squads
            if slot == 0: return "Veteran Sergeant"
            if slot == 1: return "Bond-Keeper"
            if slot < 10: return "Veteran Battle Brother"
            return None

        # COMPANY 5 (5th Chapter - Armory/Tech)
        if company == 5:
            # Squad 0: Command Squad
            if squad == 0:
                roles = {0: "Captain", 1: "Standard Bearer", 2: "Apothecary", 3: "Chaplain", 4: "Null-Warden", 5: "Techmarine", 6: "Lieutenant", 7: "Lieutenant"}
                return roles.get(slot, None)
            
            # Squad 10: 5th Chapter, 10th Squad (Runt)
            if squad == 10:
                if slot == 0: return "Sergeant (Runt)"
                if slot == 1: return "Bond-Keeper"
                if slot < 10: return "Battle Brother (Runt)"
                return None

            # Squads 1-9: Standard Tech Squads
            if slot == 0: return "Sergeant"
            if slot == 1: return "Bond-Keeper"
            if slot in [2, 3]: return "Artificer Brother"
            if slot < 10: return "Battle Brother"
            return None

        # COMPANY 10 (Scouts)
        if company == 10:
            if squad == 0:
                roles = {0: "Captain", 1: "Standard Bearer", 2: "Apothecary", 3: "Chaplain", 4: "Null-Warden", 5: "Lieutenant", 6: "Lieutenant"}
                return roles.get(slot, None)
            
            # Squads 1-5: Chaplain as Trainer in slot 0
            if 1 <= squad <= 5 and slot == 0:
                return "Chaplain"

            # Squads 6-10: Sergeant in slot 0 (Standard Scout Squads)
            if slot == 0: return "Sergeant"
            if slot < 10: return "Neophyte"
            return None

        # COMPANIES 2-4, 6-10 (Standard Battle Companies)
        
        # Special 10th Squads for 3rd and 4th (Runt Logic - Mapped from old Squad 11)
        if squad == 10:
            if company == 3:
                if slot == 0: return "Sergeant (Runt)"
                if slot == 1: return "Bond-Keeper"
                if slot < 7: return "Battle Brother (Runt)"
                if slot < 10: return "Battle Brother"
                return None
            if company == 4:
                if slot == 0: return "Sergeant"
                if slot == 1: return "Bond-Keeper"
                if slot < 6: return "Battle Brother"
                if slot < 10: return "Battle Brother (Runt)"
                return None

        # Squad 0: Command Squad
        if squad == 0:
            roles = {0: "Captain", 1: "Standard Bearer", 2: "Apothecary", 3: "Chaplain", 4: "Null-Warden", 5: "Lieutenant", 6: "Lieutenant"}
            return roles.get(slot, None)
        
        # Squads 1-10: Standard Battle Squads
        if slot == 0: return "Sergeant"
        if slot == 1: return "Bond-Keeper"
        if slot < 10: return "Battle Brother"
        return None

    def find_best_candidate(self, target_role, all_marines, moved_ids, target_company):
        target_tier = TIERS.get(target_role, 1)
        
        def is_valid(m):
            return m.status == "Alive" and m.id not in moved_ids

        # 1. INTER-CHAPTER MOVE CHECK (40 Years Rule)
        def check_inter_chapter(m):
            # Dreadnoughts go where they are needed, ignoring tenure
            if m.current_rank == "Dreadnought": return True

            if m.squad_assignment:
                sc, ss = m.squad_assignment
                if sc != 0 and sc != 1 and sc != -1 and sc != target_company:
                    if m.years_in_assignment < 40: return False
            return True

        allowed_sources = SPECIALIST_PATHS.get(target_role, None)
        
        # 2. LATERAL (Exact Rank)
        reserves = [m for m in self.reserve if is_valid(m)]
        reserves.sort(key=lambda x: x.years_in_service, reverse=True)
        for m in reserves:
            if target_company == 1 and m.current_tier < 2: continue
            if not check_inter_chapter(m): continue
            
            # Strict Specialist Matching
            if allowed_sources and m.current_rank not in allowed_sources:
                # Exception: Tier 1 to Tier 1 lateral (BB <-> BB Runt)
                if target_tier == 1 and m.current_tier == 1: pass
                elif m.current_rank == target_role: pass
                else: 
                    continue
            
            if m.current_tier == target_tier: return m
        
        # 3. PROMOTION / DOWN-FILLING
        # Dreadnoughts are only created via Mortality events, never promoted to fill a slot.
        if target_role == "Dreadnought": return None

        start_search = target_tier - 1
        if start_search < 1: start_search = 1
        
        search_range = list(range(start_search, 0, -1))
        
        for search_tier in search_range:
            required_tenure = TENURE_REQS.get(search_tier, 0)
            candidates = []
            
            # Check Reserve
            res_candidates = [m for m in self.reserve if m.current_tier == search_tier and is_valid(m) and check_inter_chapter(m)]
            if search_tier < target_tier:
                res_candidates = [m for m in res_candidates if m.years_in_rank >= required_tenure]
            candidates.extend(res_candidates)
            
            # Check Active Duty (Only for Promotions, not for lateral/down fill)
            if search_tier < target_tier:
                actives = [m for m in all_marines if m.squad_assignment and m.current_tier == search_tier and is_valid(m) and check_inter_chapter(m)]
                eligible_actives = [m for m in actives if m.years_in_rank >= required_tenure]
                if eligible_actives: candidates.extend(eligible_actives)
            
            # Garrick (101) cannot be promoted via standard logic
            if search_tier < target_tier:
                candidates = [m for m in candidates if m.id != "101"]

            # Filter
            if allowed_sources:
                # If target is Tier 1, allow any Tier 1 source (Cross-Training)
                if target_tier == 1:
                    candidates = [m for m in candidates if m.current_tier == 1 or m.current_rank in allowed_sources]
                else:
                    candidates = [m for m in candidates if m.current_rank in allowed_sources]

            if target_company == 1:
                candidates = [m for m in candidates if m.current_tier >= 1]

            if candidates:
                candidates.sort(key=lambda x: (x.years_in_rank, x.years_in_service), reverse=True)
                return candidates[0]

        return None

    def assign_relics(self, all_marines, reliquary, year):
        if not reliquary: return

        # Eligibility: Tier 4+ (Officers/Veterans) + Chapter Master, excluding Garrick (101)
        eligible_ranks = ["Chapter Master", "Captain", "Lieutenant", "Chaplain", "Techmarine", "Standard Bearer", "Veteran Sergeant", "Veteran Battle Brother"]
        eligible_marines = [m for m in all_marines if m.status == "Alive" and m.current_rank in eligible_ranks and m.id != "101"]
        
        # Sort by Rank Priority (High to Low)
        rank_priority = {r: i for i, r in enumerate(eligible_ranks)}

        # Distribute
        while reliquary:
            # Sort: Fewest relics first, then Rank Priority, then Tenure
            eligible_marines.sort(key=lambda m: (len(m.active_relics), rank_priority.get(m.current_rank, 99), m.years_in_rank * -1))
            
            assigned = False
            for candidate in eligible_marines:
                # Find first compatible relic in reliquary
                for i, relic in enumerate(reliquary):
                    # Check for duplicate type
                    if not any(r['type'] == relic['type'] for r in candidate.active_relics):
                        candidate.receive_relic(relic, year)
                        log_transaction(year, candidate, "Relic", f"Received {relic['name']}")
                        reliquary.pop(i)
                        assigned = True
                        break
                if assigned: break
            
            if not assigned: break

def upload_to_google_sheets():
    print("Initiating Uplink to Codex Datasheet...")
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Error: '{SERVICE_ACCOUNT_FILE}' not found. Upload skipped.")
        return

    try:
        import gspread
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        sh = gc.open_by_key(SPREADSHEET_ID)
        
        def _upload_sheet(sheet_name, csv_file):
            try:
                ws = sh.worksheet(sheet_name)
                df = pd.read_csv(csv_file).fillna("")
                ws.clear()
                data = [df.columns.values.tolist()] + df.values.tolist()
                ws.update(range_name='A1', values=data)
                print(f"{sheet_name} uploaded.")
            except Exception as e:
                print(f"Error uploading {sheet_name}: {e}")

        _upload_sheet('Logbook', 'Logbook.csv')
        _upload_sheet('Relics', 'Relics.csv')
        _upload_sheet('Roster', 'OUTPUT Auto-Roster.csv')
            
    except ImportError:
        print("Error: gspread library not installed. Run: pip install gspread")
    except Exception as e:
        print(f"Google Sheets API Error: {e}")

def update_human_officers():
    print("Synchronizing Human High Command (Noxian PDF)...")
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Error: '{SERVICE_ACCOUNT_FILE}' not found. Human Officer update skipped.")
        return

    try:
        import gspread
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        sh = gc.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet('Offices')
        
        # Download current data
        raw_values = ws.get_all_values()
        
        raw_formulas = ws.get(value_render_option='FORMULA')
        
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
        officer_state = {role: {"Name": None, "RetireYear": 0} for role in HUMAN_OFFICES}
        
        # Process Rows (Timeline)
        updated_data = [row[:] for row in raw_formulas] # Deep copy of formulas
        
        for r_idx in range(header_row_idx + 1, len(updated_data)):
            row_form = updated_data[r_idx]
            if r_idx >= len(raw_values): break
            row_val = raw_values[r_idx]
            
            # Get Year
            # Assuming Year is in column 1 (index 1) based on provided CSV structure: ",638.M41,..."
            # If headers are shifted, we might need to find "Year" column, but CSV context shows it at index 1.
            if len(row_val) < 2: continue
            year_str = row_val[1] 
            current_year = parse_year(year_str)
            
            if not current_year or current_year < 638: continue

            # Update Officers
            for role, config in HUMAN_OFFICES.items():
                if role not in col_map: continue
                col_idx = col_map[role]
                
                # Check Start Year
                if current_year < config.get("StartYear", 0): continue
                
                # Handle Linked Roles (Arrow of Terminus follows Master of Fleet)
                if config.get("IsLinked"):
                    # Find the master role
                    master_role = next((k for k, v in HUMAN_OFFICES.items() if v.get("Linked") == role), None)
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
                    if end_age <= start_age: end_age = start_age + 5
                    
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
        ws.update(range_name='A1', values=updated_data, value_input_option='USER_ENTERED')
        
        # Save local copy
        pd.DataFrame(updated_data).to_csv('Codex Datasheet - Offices.csv', index=False, header=False)
        print("Human Officers synchronized.")

    except Exception as e:
        print(f"Error updating Human Officers: {e}")

# ==========================================
# 5. EXECUTION
# ==========================================

def run_simulation():
    global TRANSACTION_LOG
    TRANSACTION_LOG = []
    global DISCOVERED_RELICS_LOG
    DISCOVERED_RELICS_LOG = []
    print("Initiating Chain Breakers Auto-Roster Protocol v17.0...")
    assignment_order = generate_assignment_priority_list()
    
    try:
        # Load from CSV, filling NaNs with empty strings to match previous behavior
        raw_data = pd.read_csv('INPUT Auto-Roster.csv').fillna("").to_dict('records')
    except FileNotFoundError:
        print("Error: 'INPUT Auto-Roster.csv' not found.")
        return

    all_marines = []
    seen_ids = set()
    existing_names = set()
    chapter = Chapter()
    
    reliquary = []
    
    print("Ingesting Old Guard...")
    for row in raw_data:
        try:
            mid = int(row['Chapter ID Number'])
            if mid in seen_ids: continue
            seen_ids.add(mid)
            if mid < 1000:
                d_str = str(row['Date of Death'])
                if d_str and d_str.lower() != "alive":
                    d_year = parse_year(d_str)
                    if d_year and d_year < START_YEAR_ABS: continue 
                m = Marine(data_row=row)
                all_marines.append(m)
                log_transaction(START_YEAR_ABS, m, "Ingested", "Initial Roster Import")
                existing_names.add(m.name)
                # Old Guard Initialization
                if m.is_old_guard and m.implantation_year < START_YEAR_ABS:
                    if not m.squad_assignment:
                        chapter.add_to_reserve(m, START_YEAR_ABS)
        except (ValueError, KeyError): continue
            
    next_id = 1000
    
    # DREADNOUGHT SCHEDULE GENERATION
    dread_arrival_years = [661, 694, 716, 739, 761, 824, 856, 899, 921, 934, 956, 1005]
    dread_name_index = 0
    dread_id_counter = 1

    # --- TIME LOOP ---
    for year in range(START_YEAR_ABS, END_YEAR_ABS + 1):
        moved_ids = set() 

        # RELIC DISCOVERY (Fixed Dates)
        for relic in FOUND_RELICS:
            if relic['date'] == year:
                log_relic_discovery(relic)
                if relic['id'] in ["R9001", "R9002", "R9003"]:
                    garrick = next((m for m in all_marines if m.id == "101"), None)
                    if garrick:
                        garrick.receive_relic(relic, year)
                        log_transaction(year, garrick, "Relic", f"Received {relic['name']}")
                        continue
                reliquary.append(relic)

        # DEATHWATCH LOGIC
        # 1. Manage Returns
        dw_marines = [m for m in all_marines if m.status == "Alive" and m.squad_assignment == (0, 5)]
        for m in dw_marines:
            if m.deathwatch_service_start is not None and (year - m.deathwatch_service_start) >= 15:
                chapter.remove_from_grid(m)
                chapter.add_to_reserve(m, year)
                # Override the default Reserve string to add flavor
                lines = m.deployment_history.split('\n')
                if lines:
                    lines[0] = f"Chapter Reserve (Returned from Long Vigil) ({get_year_str(year)} - Current)\n"
                    m.deployment_history = '\n'.join(lines)
                log_transaction(year, m, "Transfer", "Returned from Long Vigil")
                m.deathwatch_service_start = None
                m.deathwatch_terms += 1
                m.last_deathwatch_return = year
                
                # Deathwatch Relic Discovery Chance (25%)
                if DEATHWATCH_RELICS and random.random() < 0.25:
                    found_relic = DEATHWATCH_RELICS.pop(random.randint(0, len(DEATHWATCH_RELICS)-1))
                    found_relic['date'] = year # Set discovery date
                    log_relic_discovery(found_relic)
                    reliquary.append(found_relic)
                    log_transaction(year, m, "Relic Found", f"Recovered {found_relic['name']} from Deathwatch")

        # 2. Manage Recruitment
        # Count Strength: Companies 1-10, Squads 1-10, Slots 0-9 (Max 1000)
        fighting_strength = 0
        for c in range(1, 11):
            for s in range(1, 11):
                for k in range(10):
                    if chapter.grid[c][s][k] is not None:
                        fighting_strength += 1
        
        if fighting_strength >= 900:
            dw_count = len([m for m in all_marines if m.status == "Alive" and m.squad_assignment == (0, 5)])
            if dw_count < 3:
                slots_needed = 3 - dw_count
                for _ in range(slots_needed):
                    def check_dw_eligibility(m):
                        if m.status != "Alive": return False
                        if m.current_rank != "Veteran Battle Brother": return False
                        if m.deathwatch_terms >= 2: return False
                        if m.deathwatch_terms > 0 and (year - m.last_deathwatch_return) < 30: return False
                        return True

                    candidate = None
                    # Priority 1: Reserve Veterans
                    res_cands = [m for m in chapter.reserve if check_dw_eligibility(m)]
                    res_cands.sort(key=lambda x: x.years_in_rank, reverse=True)
                    if res_cands: candidate = res_cands[0]
                    # Priority 2: 1st Company Veterans
                    if not candidate:
                        c1_cands = [m for m in all_marines if m.status == "Alive" and m.squad_assignment and m.squad_assignment[0] == 1 and check_dw_eligibility(m)]
                        c1_cands.sort(key=lambda x: x.years_in_rank, reverse=True)
                        if c1_cands: candidate = c1_cands[0]
                    
                    if candidate:
                        if candidate.squad_assignment: chapter.remove_from_grid(candidate)
                        if candidate in chapter.reserve: chapter.reserve.remove(candidate)
                        target_slot = next(k for k in range(3) if chapter.grid[0][5][k] is None)
                        chapter.grid[0][5][target_slot] = candidate
                        candidate.deploy(0, 5, year, target_slot)
                        candidate.deathwatch_service_start = year
                        # Override history string
                        lines = candidate.deployment_history.split('\n')
                        if lines:
                            lines[0] = f"Seconded to Deathwatch ({get_year_str(year)} - Current)\n"
                            candidate.deployment_history = '\n'.join(lines)
                        log_transaction(year, candidate, "Transfer", "Seconded to Deathwatch")
                        moved_ids.add(candidate.id)

        # LORE EVENTS
        if year == 619:
            # Garrick (101) Promotion to Sergeant
            garrick = next((m for m in all_marines if m.id == "101"), None)
            if garrick and garrick.status == "Alive":
                if garrick.squad_assignment: chapter.remove_from_grid(garrick)
                if garrick in chapter.reserve: chapter.reserve.remove(garrick)
                garrick.promote("Sergeant", year)
                chapter.add_to_reserve(garrick, year)
                moved_ids.add(garrick.id)

        if year == 634:
            # Garrick (101) Promotion to Chapter Master
            garrick = next((m for m in all_marines if m.id == "101"), None)
            if garrick and garrick.status == "Alive":
                if garrick.squad_assignment: chapter.remove_from_grid(garrick)
                if garrick in chapter.reserve: chapter.reserve.remove(garrick)
                garrick.promote("Chapter Master", year)
                garrick.deploy(0, 0, year)
                chapter.grid[0][0][0] = garrick
                moved_ids.add(garrick.id)

        if year == 638:
            # Garrick (101) enters Stasis
            garrick = next((m for m in all_marines if m.id == "101"), None)
            if garrick:
                chapter.remove_from_grid(garrick)
                if garrick in chapter.reserve: chapter.reserve.remove(garrick)
                garrick.status = "Stasis"
                garrick.rank_history = garrick.close_history_string(garrick.rank_history, year)
                garrick.rank_history = f"In Stasis (No Rank) ({get_year_str(year)} - Current)\n" + garrick.rank_history
                garrick.deployment_history = garrick.close_history_string(garrick.deployment_history, year)
                garrick.deployment_history = f"In Stasis ({get_year_str(year)} - Current)\n" + garrick.deployment_history
                garrick.squad_assignment = None
                log_transaction(year, garrick, "Stasis", "Entered Stasis")
            
            # Ferren Vrox (200) becomes Chapter Master
            vrox = next((m for m in all_marines if m.id == "200"), None)
            if vrox and vrox.status == "Alive":
                # Ensure slot is empty
                current_cm = chapter.grid[0][0][0]
                if current_cm and current_cm != vrox:
                    chapter.remove_from_grid(current_cm)
                    chapter.add_to_reserve(current_cm, year)
                
                if vrox.squad_assignment: chapter.remove_from_grid(vrox)
                if vrox in chapter.reserve: chapter.reserve.remove(vrox)
                
                vrox.promote("Chapter Master", year)
                vrox.deploy(0, 0, year)
                chapter.grid[0][0][0] = vrox
                moved_ids.add(vrox.id)

        if year == 771:
            # Garrick (101) returns from Stasis
            garrick = next((m for m in all_marines if m.id == "101"), None)
            if garrick:
                # Handle Vrox (Current CM) -> Demote to Captain of 1st Company
                current_cm = chapter.grid[0][0][0]
                if current_cm and current_cm.id == "200": # Vrox
                    vrox = current_cm
                    chapter.remove_from_grid(vrox)
                    vrox.promote("Captain", year)
                    
                    # Displace existing 1st Company Captain
                    c1_capt = chapter.grid[1][0][0]
                    if c1_capt:
                        chapter.remove_from_grid(c1_capt)
                        # Find free Captain slot
                        placed = False
                        for co in range(2, 11):
                            if chapter.grid[co][0][0] is None:
                                chapter.grid[co][0][0] = c1_capt
                                c1_capt.deploy(co, 0, year)
                                placed = True
                                break
                        if not placed:
                            chapter.add_to_reserve(c1_capt, year)
                    
                    # Place Vrox
                    chapter.grid[1][0][0] = vrox
                    vrox.deploy(1, 0, year)
                    moved_ids.add(vrox.id)

                # Ensure slot is clear for Garrick
                current_cm = chapter.grid[0][0][0]
                if current_cm and current_cm != garrick:
                    chapter.remove_from_grid(current_cm)
                    chapter.add_to_reserve(current_cm, year)

                garrick.status = "Alive"
                # History strings are closed automatically by promote/deploy calls below
                log_transaction(year, garrick, "Stasis", "Returned from Stasis")
                garrick.promote("Chapter Master", year)
                garrick.deploy(0, 0, year)
                chapter.grid[0][0][0] = garrick
                moved_ids.add(garrick.id)

        for m in all_marines:
            if m.status == "Alive":
                if m.implantation_year == year or (year == REFOUNDING_YEAR and m.implantation_year < year):
                     if m not in chapter.reserve and not m.squad_assignment:
                         chapter.add_to_reserve(m, year)
                if m.implantation_year <= year:
                    m.update_age(year)

        # DREADNOUGHT CAPACITY (Randomized Schedule)
        dread_cap = 0
        if year >= 661:
            dread_cap = sum(1 for y in dread_arrival_years if year >= y)
            if dread_cap > 12: dread_cap = 12
        
        active_dreadnoughts = sum(1 for m in all_marines if m.status == "Alive" and m.current_rank == "Dreadnought")
        active_pop = sum(1 for m in all_marines if m.status == "Alive" and m.squad_assignment)
        reserve_pop = len(chapter.reserve)
        total_pop = active_pop + reserve_pop
        
        # GRADUATION (Before Recruitment)
        for s in range(1, 11): # 10th Company Squads 1-10 are Scouts
            for k in range(10):
                m = chapter.grid[10][s][k]
                if m and m.status == "Alive" and m.current_rank == "Neophyte":
                    if m.years_in_service >= 7:
                        chapter.grid[10][s][k] = None
                        m.squad_assignment = None
                        m.promote("Battle Brother", year)
                        chapter.add_to_reserve(m, year)

        # MORTALITY
        base_risk = 0.002 # Peace < 800
        if active_pop >= 1300: base_risk = 0.020 # War
        elif active_pop >= 900: base_risk = 0.010 # Building
        
        # Boros (103) Dreadnought Event - Processed first to guarantee D001
        if year == 661:
            boros = next((m for m in all_marines if m.id == "103" and m.status == "Alive"), None)
            if boros:
                if boros.squad_assignment: chapter.remove_from_grid(boros)
                if boros in chapter.reserve: chapter.reserve.remove(boros)
                boros.return_relics(year, reliquary)
                boros.promote("Dreadnought", year, display_rank="Dreadnought : D-I")
                dread_id_counter = 2
                chapter.add_to_reserve(boros, year)
                active_dreadnoughts += 1

        for m in [x for x in all_marines if x.status == "Alive"]:
            if m.current_rank == "Dreadnought": continue
            if m.squad_assignment == (0, 5):
                if random.random() < 0.002:
                    chapter.remove_from_grid(m)
                    m.return_relics(year, reliquary)
                    m.kill(year)
                continue

            # Hardcoded Death
            if m.death_year_abs and m.death_year_abs == year:
                if m in chapter.reserve: chapter.reserve.remove(m)
                chapter.remove_from_grid(m)
                m.return_relics(year, reliquary)
                m.kill(year)
                continue
            
            # Random Death
            if not m.death_year_abs and not m.is_protected and m.implantation_year < year:
                if m.is_old_guard:
                    risk = OLD_GUARD_MORTALITY_RISK
                else:
                    risk = base_risk
                    if m.current_tier == 0: risk += 0.02 
                    if m.current_tier >= 4: risk *= 0.05 # -90%
                
                if random.random() < risk:
                    # DREADNOUGHT INTERVENTION
                    if m.current_rank in ["Veteran Battle Brother", "Veteran Sergeant"] and active_dreadnoughts < dread_cap:
                        if m.id != "103" and dread_name_index < len(DREADNOUGHT_NAMES):
                            new_name = DREADNOUGHT_NAMES[dread_name_index]
                            dread_name_index += 1
                            m.name = new_name
                            existing_names.add(new_name)
                            # Retroactive Log Update
                            for log_entry in TRANSACTION_LOG:
                                if log_entry["Marine ID"] == m.id:
                                    log_entry["Name"] = new_name

                        if m.squad_assignment: chapter.remove_from_grid(m)
                        if m in chapter.reserve: chapter.reserve.remove(m)
                        m.return_relics(year, reliquary)
                        m.promote("Dreadnought", year, display_rank=f"Dreadnought : D-{to_roman(dread_id_counter)}")
                        dread_id_counter += 1
                        chapter.add_to_reserve(m, year)
                        active_dreadnoughts += 1
                        continue

                    if m in chapter.reserve: chapter.reserve.remove(m)
                    chapter.remove_from_grid(m)
                    m.return_relics(year, reliquary)
                    m.kill(year)

        # FORCED INTERMENT PROTOCOL
        if active_dreadnoughts < dread_cap:
            candidate = None
            
            def get_forced_candidate(rank_filter):
                candidates = [m for m in all_marines if m.status == "Alive" and m.current_rank == rank_filter]
                candidates.sort(key=lambda x: x.years_in_service, reverse=True)
                if not candidates: return None
                # Take 4th oldest (index 3), or the last available if fewer than 4
                idx = min(3, len(candidates) - 1)
                return candidates[idx]

            candidate = get_forced_candidate("Veteran Battle Brother")
            if not candidate: candidate = get_forced_candidate("Veteran Sergeant")
            if not candidate: candidate = get_forced_candidate("Battle Brother")
            
            if candidate:
                if candidate.id != "103" and dread_name_index < len(DREADNOUGHT_NAMES):
                    new_name = DREADNOUGHT_NAMES[dread_name_index]
                    dread_name_index += 1
                    candidate.name = new_name
                    existing_names.add(new_name)
                    for log_entry in TRANSACTION_LOG:
                        if log_entry["Marine ID"] == candidate.id:
                            log_entry["Name"] = new_name

                if candidate.squad_assignment: chapter.remove_from_grid(candidate)
                if candidate in chapter.reserve: chapter.reserve.remove(candidate)
                candidate.return_relics(year, reliquary)
                candidate.promote("Dreadnought", year, display_rank=f"Dreadnought : D-{to_roman(dread_id_counter)}")
                dread_id_counter += 1
                chapter.add_to_reserve(candidate, year)
                active_dreadnoughts += 1
            else:
                print(f"ERROR - DREADNOUGHT PROTOCOL FAILED in {year}")

        # RECRUITMENT (Proportional Filling)
        empty_neo_slots = []
        for s in range(1, 11): # 10th Company Squads 1-10
            # Start from 1 to reserve slot 0 for Officer (Chaplain/Sergeant)
            for k in range(1, 10):
                if chapter.grid[10][s][k] is None:
                    empty_neo_slots.append((10, s, k))
        
        if NEOPHYTE_INTAKE_OVERRIDE > 0: intake = NEOPHYTE_INTAKE_OVERRIDE
        else:
            # Ramp Up Curve
            if year < RECRUITMENT_START: intake = 0
            else:
                intake = 5 + (year - RECRUITMENT_START) * 10
        
        real_intake = min(intake, len(empty_neo_slots))
        
        if real_intake > 0:
            for _ in range(real_intake):
                loc = empty_neo_slots.pop(0)
                
                # Generate unique name
                new_name = ""
                attempts = 0
                while True:
                    new_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                    if new_name not in existing_names:
                        existing_names.add(new_name)
                        break
                    attempts += 1
                    if attempts > 500: new_name = f"{new_name} {next_id}"; existing_names.add(new_name); break

                new_m = Marine(procedural_id=next_id, birth_year=year-12, name=new_name)
                next_id += 1
                all_marines.append(new_m)
                log_transaction(year, new_m, "Recruitment", "New Initiate")
                c, s, k = loc
                chapter.grid[c][s][k] = new_m
                new_m.deploy(c, s, year, k)
                moved_ids.add(new_m.id)

        # DEMOTION
        for m in [x for x in all_marines if x.status=="Alive" and x.squad_assignment]:
            if m.id == "101": continue

            if m.current_tier in [2, 3] and "Bond-Keeper" not in m.current_rank and random.random() < 0.002:
                chapter.remove_from_grid(m)

                demoted_rank = "Battle Brother (Runt)" if m.current_rank == "Sergeant (Runt)" else "Battle Brother"

                m.promote(demoted_rank, year)
                chapter.add_to_reserve(m, year)
                moved_ids.add(m.id)

        # DREADNOUGHT SLOT CLEARING
        # Ensure slots designated for Dreadnoughts are not occupied by non-Dreadnoughts
        for idx, (dc, ds) in enumerate(DREADNOUGHT_PRIORITY):
            if idx < active_dreadnoughts:
                occupant = chapter.grid[dc][ds][9]
                if occupant and occupant.current_rank != "Dreadnought":
                    chapter.remove_from_grid(occupant)
                    chapter.add_to_reserve(occupant, year)

        # RELIC ASSIGNMENT
        chapter.assign_relics(all_marines, reliquary, year)

        # ASSIGNMENTS
        for c, s in assignment_order:
            for k in range(12):
                if chapter.grid[c][s][k] is None:
                    # Prevent Chapter Master assignment before 634.M41
                    if c == 0 and s == 0 and k == 0 and year < 634: continue

                    target_role = chapter.get_role_rule(c, s, k, active_dreadnoughts)
                    if not target_role: continue
                    candidate = chapter.find_best_candidate(target_role, all_marines, moved_ids, c)
                    if candidate:
                        if candidate.squad_assignment: chapter.remove_from_grid(candidate)
                        if candidate in chapter.reserve: chapter.reserve.remove(candidate)
                        chapter.grid[c][s][k] = candidate
                        candidate.deploy(c, s, year, k)
                        moved_ids.add(candidate.id)
                        if candidate.current_tier < TIERS.get(target_role, 1) or (target_role == "Battle Brother (Runt)" and candidate.current_rank == "Battle Brother"):
                            candidate.promote(target_role, year)

        if year % 5 == 0:
            current_active = sum(1 for m in all_marines if m.status == "Alive" and m.squad_assignment and m.squad_assignment[0] != -1)
            current_reserve = len([m for m in chapter.reserve if m.status == "Alive"])
            current_neophytes = sum(1 for m in all_marines if m.status == "Alive" and m.current_rank == "Neophyte")
            print(f"Year {get_year_str(year)} | Active: {current_active} / 1112 | Reserve: {current_reserve} | Recruits: {current_neophytes}")

        if year % 10 == 0 and all_marines:
            data_out = [m.to_dict(year) for m in all_marines]
            df_out = pd.DataFrame(data_out)
            df_out['SortID'] = df_out['Chapter ID Number'].astype(int)
            df_out = df_out.sort_values('SortID').drop('SortID', axis=1)
            df_out.to_csv('OUTPUT Auto-Roster.csv', index=False, mode='w')

    final_dread_count = sum(1 for m in all_marines if m.status == "Alive" and m.current_rank == "Dreadnought")
    if final_dread_count < 12:
        print(f"ERROR - ONLY {final_dread_count}/12 DREADNAUGHTS CREATED")

    # STORY CHARACTER INJECTION
    print("Integrating Story Characters...")
    success_count = 0
    failed_chars = []

    for char_req in STORY_CHARACTERS:
        target_rank = char_req.get("Rank")
        target_company = char_req.get("Company")
        target_squad = char_req.get("Squad")
        
        candidate = None
        # Find a match in the current roster (alive at end of sim)
        candidates = [m for m in all_marines if m.status == "Alive" and m.current_rank == target_rank]
        
        if target_company is not None:
            candidates = [m for m in candidates if m.squad_assignment and m.squad_assignment[0] == target_company]
        if target_squad is not None:
            candidates = [m for m in candidates if m.squad_assignment and m.squad_assignment[1] == target_squad]
            
        if candidates:
            candidate = candidates[0] # Take the first match
            print(f"  Found candidate for {char_req['Name']}: {candidate.name} (ID: {candidate.id})")
            candidate.name = char_req["Name"]
            candidate.cognomen = char_req.get("Cognomen", "")
            # Retroactive Log Update
            for log_entry in TRANSACTION_LOG:
                if log_entry["Marine ID"] == candidate.id:
                    log_entry["Name"] = candidate.name
            success_count += 1
        else:
            print(f"  Warning: No suitable candidate found for {char_req['Name']} ({target_rank} in Co {target_company} Sq {target_squad})")
            failed_chars.append(char_req['Name'])

    print(f"{success_count}/{len(STORY_CHARACTERS)} Story Characters successfully added.")
    if failed_chars:
        print(f"Unable to add: {', '.join(failed_chars)}")

    print("Formatting Codex & Compressing Logs...")
    if all_marines:
        data_out = [m.to_dict(END_YEAR_ABS) for m in all_marines]
        df_out = pd.DataFrame(data_out)
        
        df_out['SortID'] = df_out['Chapter ID Number'].astype(int)
        df_out = df_out.sort_values('SortID').drop('SortID', axis=1)
        
        print("Uploading to Holy Archives...")
        df_out.to_csv('OUTPUT Auto-Roster.csv', index=False, mode='w')
        
        print("Compiling Logbook...")
        pd.DataFrame(TRANSACTION_LOG).to_csv('Logbook.csv', index=False)
        
        print("Compiling Relic Index...")
        pd.DataFrame(DISCOVERED_RELICS_LOG).to_csv('Relics.csv', index=False)
        
        update_human_officers()
        upload_to_google_sheets()
    else:
        print("Warning: No marines found. Output generation skipped.")
    print("Process Finished.")

if __name__ == "__main__":
    run_simulation()