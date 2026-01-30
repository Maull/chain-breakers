import pandas as pd
import random
import re

from config import (
    FIRST_NAMES,
    LAST_NAMES,
    log_transaction,
    START_YEAR_ABS,
    TIERS,
)
from utils import get_year_str, parse_year, get_ordinal


class Marine:
    def __init__(self, data_row=None, procedural_id=None, birth_year=None, name=None):
        self.moved_this_turn = False
        self.is_old_guard = False
        self.current_slot = 0

        if data_row is not None:
            # --- OLD GUARD ---
            self.id = str(data_row["Chapter ID Number"])
            self.is_old_guard = True if int(self.id) < 1000 else False
            self.name = data_row["Name"]
            self.cognomen = str(data_row["Cognomen / Earned Name"])
            self.born_str = str(data_row["Born"])
            self.geneseed_str = str(data_row["Date of Geneseed Implantation"])
            self.death_str = str(data_row["Date of Death"])
            self.death_year_abs = parse_year(self.death_str)

            if self.death_str and self.death_str.lower() != "alive":
                if self.death_year_abs and self.death_year_abs >= START_YEAR_ABS:
                    self.status = "Alive"
                else:
                    self.status = "Dead"
            else:
                self.status = "Alive"

            self.is_protected = True if self.death_str.lower() == "alive" else False
            self.deployment_history = (
                str(data_row["Deployment History"]) 
                if pd.notna(data_row["Deployment History"]) 
                else ""
            )
            self.personality = str(data_row["Personality / Psy-Profile"])
            self.notes = str(data_row["Notes"])
            self.implantation_year = parse_year(self.geneseed_str)
            if not self.implantation_year:
                self.implantation_year = 550

            self.rank_history = (
                str(data_row["Rank History"]) 
                if pd.notna(data_row["Rank History"]) 
                else ""
            )
            self.current_rank = (
                self.rank_history.split("(")[0].strip() 
                if self.rank_history 
                else "Veteran Battle Brother"
            )
            if not self.rank_history:
                self.rank_history = f"{self.current_rank} ({get_year_str(self.implantation_year)} - Current) (Unknown age)\n"
            self.current_tier = TIERS.get(self.current_rank, 2)

            # LORE OVERRIDE: Garrick (ID 101) starts as Sergeant
            # LORE OVERRIDE: Garrick (ID 101) starts as Battle Brother
            # LORE OVERRIDE: Garrick (ID 101) starts as a Battle Brother.
            if self.id == "101":
                self.current_rank = "Sergeant"
                self.current_tier = TIERS.get(self.current_rank, 3)
                self.rank_history = (
                    f"Sergeant ({get_year_str(self.implantation_year)} - Current)\n"
                )
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
                if 100 <= mid <= 199:
                    return " [Doom Eagles]"
                if 200 <= mid <= 299:
                    return " [Storm Giants]"
            except (ValueError, TypeError):
                pass
        return ""

    def close_history_string(self, text_block, end_year):
        match = re.search(r"\((\d{3})\.M4([12]) - Current\)", text_block)
        if match:
            start_y_part = int(match.group(1))
            era = match.group(2)
            start_abs = start_y_part + (1000 if era == "2" else 0)
            duration = end_year - start_abs
            dur_str = f"{duration} Years" if duration > 0 else "<1 Year"
            old_str = match.group(0)
            new_str = (
                f"({get_year_str(start_abs)} - {get_year_str(end_year)}) ({dur_str})"
            )
            return text_block.replace(old_str, new_str, 1)
        return text_block

    def promote(self, new_rank, year, display_rank=None):
        if display_rank is None:
            display_rank = new_rank

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
                if 100 <= mid <= 199:
                    origin_stamp = " [Doom Eagles]"
                elif 200 <= mid <= 299:
                    origin_stamp = " [Storm Giants]"
            except:
                pass

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
        self.relic_history.append({"relic": relic, "start": year, "end": None})

    def return_relics(self, year, reliquary):
        for r in self.active_relics:
            for h in self.relic_history:
                if h["relic"] == r and h["end"] is None:
                    h["end"] = year
            reliquary.append(r)
        self.active_relics = []

    def deploy(self, company, squad, year, slot=0):
        if self.squad_assignment == (company, squad) and self.current_slot == slot:
            return
        self.deployment_history = self.close_history_string(
            self.deployment_history, year
        )

        origin_stamp = ""
        if year < 638:
            try:
                mid = int(self.id)
                if 100 <= mid <= 199:
                    origin_stamp = " [Doom Eagles]"
                elif 200 <= mid <= 299:
                    origin_stamp = " [Storm Giants]"
            except:
                pass
        origin_stamp = self._get_origin_stamp(year)

        if company == -1:
            new_entry = f"Chapter Reserve ({get_year_str(year)} - Current)\n"
        elif company == 0:
            if squad == 0:
                new_entry = f"Chapter Command ({get_year_str(year)} - Current)\n"
            elif squad == 1:
                new_entry = f"Apothecarion ({get_year_str(year)} - Current)\n"
            elif squad == 2:
                new_entry = f"Reclusiam ({get_year_str(year)} - Current)\n"
            elif squad == 3:
                new_entry = f"Libarius ({get_year_str(year)} - Current)\n"
            elif squad == 4:
                new_entry = f"Armory ({get_year_str(year)} - Current)\n"
            else:
                new_entry = f"Chapter HQ Support ({get_year_str(year)} - Current)\n"
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
        self.deployment_history = self.close_history_string(
            self.deployment_history, year
        )
        age = year - (self.implantation_year - 12)
        kia_entry = (
            f"KIA ({self.current_rank}) ({get_year_str(year)}) ({age} Years old)\n"
        )
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
        if len(r_hist) > 45000:
            r_hist = r_hist[:45000] + "\n[...ARCHIVE TRUNCATED...]"
        if len(d_hist) > 45000:
            d_hist = d_hist[:45000] + "\n[...ARCHIVE TRUNCATED...]"

        wargear_lines = []
        for h in self.relic_history:
            r_name = h["relic"]["name"]
            r_type = h["relic"]["type"]
            start = get_year_str(h["start"])
            end = get_year_str(h["end"]) if h["end"] else "Current"
            wargear_lines.append(f"{r_type} ({r_name}) ({start} - {end})")
        wargear_str = "\n".join(wargear_lines)

        return {
            "Chapter ID Number": self.id,
            "Name": self.name,
            "Cognomen / Earned Name": self.cognomen,
            "Born": self.born_str,
            "Date of Geneseed Implantation": self.geneseed_str,
            "Date of Death": self.death_str,
            "Age (Or Age at Death)": age,
            "Wargear": wargear_str,
            "Rank History": r_hist,
            "Deployment History": d_hist,
            "Personality / Psy-Profile": self.personality,
            "Notes": self.notes,
        }
