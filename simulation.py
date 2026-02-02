import pandas as pd
import random

from chapter import Chapter
from config import (
    DEATHWATCH_RELICS,
    DREADNOUGHT_NAMES,
    DREADNOUGHT_PRIORITY,
    END_YEAR_ABS,
    FIRST_NAMES,
    FOUND_RELICS,
    LAST_NAMES,
    NEOPHYTE_INTAKE_OVERRIDE,
    OLD_GUARD_MORTALITY_RISK,
    RECRUITMENT_START,
    START_YEAR_ABS,
    STORY_CHARACTERS,
    TIERS,
    TRANSACTION_LOG,
    log_relic_discovery,
    log_transaction,
    REFOUNDING_YEAR,
    DISCOVERED_RELICS_LOG,
)
from gsuite import upload_to_google_sheets, update_human_officers
from marine import Marine
from utils import get_year_str, parse_year, to_roman


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


def run_simulation():
    TRANSACTION_LOG.clear()
    DISCOVERED_RELICS_LOG.clear()
    print("Initiating Chain Breakers Auto-Roster Protocol v17.0...")
    assignment_order = generate_assignment_priority_list()

    try:
        # Load from CSV, filling NaNs with empty strings to match previous behavior
        raw_data = pd.read_csv("INPUT Auto-Roster.csv").fillna("").to_dict("records")
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
            mid = int(row["Chapter ID Number"])
            if mid in seen_ids:
                continue
            seen_ids.add(mid)
            if mid < 1000:
                d_str = str(row["Date of Death"])
                if d_str and d_str.lower() != "alive":
                    d_year = parse_year(d_str)
                    if d_year and d_year < START_YEAR_ABS:
                        continue
                m = Marine(data_row=row)
                all_marines.append(m)
                log_transaction(START_YEAR_ABS, m, "Ingested", "Initial Roster Import")
                existing_names.add(m.name)
                # Old Guard Initialization
                if m.is_old_guard and m.implantation_year < START_YEAR_ABS:
                    if not m.squad_assignment:
                        chapter.add_to_reserve(m, START_YEAR_ABS)
        except (ValueError, KeyError):
            continue

    next_id = 1000

    # DREADNOUGHT SCHEDULE GENERATION
    dread_arrival_years = [
        661,
        694,
        716,
        739,
        761,
        824,
        856,
        899,
        921,
        934,
        956,
        1005,
    ]
    dread_name_index = 0
    dread_id_counter = 1

    dead_iron_calculus_count = 0
    # --- TIME LOOP ---
    for year in range(START_YEAR_ABS, END_YEAR_ABS + 1):
        moved_ids = set()

        # RELIC DISCOVERY (Fixed Dates)
        for relic in FOUND_RELICS:
            if relic["date"] == year:
                log_relic_discovery(relic)
                if relic["id"] in ["R9001", "R9002", "R9003"]:
                    garrick = next((m for m in all_marines if m.id == "101"), None)
                    if garrick:
                        garrick.receive_relic(relic, year)
                        log_transaction(
                            year, garrick, "Relic", f"Received {relic['name']}"
                        )
                        continue
                reliquary.append(relic)

        # DEATHWATCH LOGIC
        # 1. Manage Returns
        dw_marines = [
            m
            for m in all_marines
            if m.status == "Alive" and m.squad_assignment == (0, 5)
        ]
        for m in dw_marines:
            if m.deathwatch_service_start is not None and (
                year - m.deathwatch_service_start
            ) >= 15:
                chapter.remove_from_grid(m)
                chapter.add_to_reserve(m, year)
                # Override the default Reserve string to add flavor
                lines = m.deployment_history.split("\n")
                if lines:
                    lines[
                        0
                    ] = f"Chapter Reserve (Returned from Long Vigil) ({get_year_str(year)} - Current)\n"
                    m.deployment_history = "\n".join(lines)
                log_transaction(year, m, "Transfer", "Returned from Long Vigil")
                m.deathwatch_service_start = None
                m.deathwatch_terms += 1
                m.last_deathwatch_return = year

                # Deathwatch Relic Discovery Chance (25%)
                if DEATHWATCH_RELICS and random.random() < 0.25:
                    found_relic = DEATHWATCH_RELICS.pop(
                        random.randint(0, len(DEATHWATCH_RELICS) - 1)
                    )
                    found_relic["date"] = year  # Set discovery date
                    log_relic_discovery(found_relic)
                    reliquary.append(found_relic)
                    log_transaction(
                        year,
                        m,
                        "Relic Found",
                        f"Recovered {found_relic['name']} from Deathwatch",
                    )

        # 2. Manage Recruitment
        # Count Strength: Companies 1-10, Squads 1-10, Slots 0-9 (Max 1000)
        fighting_strength = 0
        for c in range(1, 11):
            for s in range(1, 11):
                for k in range(10):
                    if chapter.grid[c][s][k] is not None:
                        fighting_strength += 1

        if fighting_strength >= 900:
            dw_count = len(
                [
                    m
                    for m in all_marines
                    if m.status == "Alive" and m.squad_assignment == (0, 5)
                ]
            )
            if dw_count < 3:
                slots_needed = 3 - dw_count
                for _ in range(slots_needed):

                    def check_dw_eligibility(m):
                        if m.status != "Alive":
                            return False
                        if m.current_rank != "Veteran Battle Brother":
                            return False
                        if m.deathwatch_terms >= 2:
                            return False
                        if m.deathwatch_terms > 0 and (
                            year - m.last_deathwatch_return
                        ) < 30:
                            return False
                        if not any(r.get("type") == "Echo" for r in m.active_relics):
                            return False
                        return True

                    candidate = None
                    # Priority 1: Reserve Veterans
                    res_cands = [
                        m for m in chapter.reserve if check_dw_eligibility(m)
                    ]
                    res_cands.sort(key=lambda x: x.years_in_rank, reverse=True)
                    if res_cands:
                        candidate = res_cands[0]
                    # Priority 2: 1st Company Veterans
                    if not candidate:
                        c1_cands = [
                            m
                            for m in all_marines
                            if m.status == "Alive"
                            and m.squad_assignment
                            and m.squad_assignment[0] == 1
                            and check_dw_eligibility(m)
                        ]
                        c1_cands.sort(key=lambda x: x.years_in_rank, reverse=True)
                        if c1_cands:
                            candidate = c1_cands[0]

                    if candidate:
                        if candidate.squad_assignment:
                            chapter.remove_from_grid(candidate)
                        if candidate in chapter.reserve:
                            chapter.reserve.remove(candidate)
                        target_slot = next(
                            k for k in range(3) if chapter.grid[0][5][k] is None
                        )
                        chapter.grid[0][5][target_slot] = candidate
                        candidate.deploy(0, 5, year, target_slot)
                        candidate.deathwatch_service_start = year
                        # Override history string
                        lines = candidate.deployment_history.split("\n")
                        if lines:
                            lines[
                                0
                            ] = f"Seconded to Deathwatch ({get_year_str(year)} - Current)\n"
                            candidate.deployment_history = "\n".join(lines)
                        log_transaction(
                            year, candidate, "Transfer", "Seconded to Deathwatch"
                        )
                        moved_ids.add(candidate.id)

        # LORE EVENTS
        if year == 619:
            # Garrick (101) Promotion to Sergeant
            garrick = next((m for m in all_marines if m.id == "101"), None)
            if garrick and garrick.status == "Alive":
                if garrick.squad_assignment:
                    chapter.remove_from_grid(garrick)
                if garrick in chapter.reserve:
                    chapter.reserve.remove(garrick)
                garrick.promote("Sergeant", year)
                chapter.add_to_reserve(garrick, year)
                moved_ids.add(garrick.id)

        if year == 634:
            # Garrick (101) Promotion to Chapter Master
            garrick = next((m for m in all_marines if m.id == "101"), None)
            if garrick and garrick.status == "Alive":
                if garrick.squad_assignment:
                    chapter.remove_from_grid(garrick)
                if garrick in chapter.reserve:
                    chapter.reserve.remove(garrick)
                garrick.promote("Chapter Master", year)
                garrick.deploy(0, 0, year)
                chapter.grid[0][0][0] = garrick
                moved_ids.add(garrick.id)

        if year == 638:
            # Garrick (101) enters Stasis
            garrick = next((m for m in all_marines if m.id == "101"), None)
            if garrick:
                chapter.remove_from_grid(garrick)
                if garrick in chapter.reserve:
                    chapter.reserve.remove(garrick)
                garrick.status = "Stasis"
                garrick.rank_history = garrick.close_history_string(
                    garrick.rank_history, year
                )
                garrick.rank_history = (
                    f"In Stasis (No Rank) ({get_year_str(year)} - Current)\n"
                    + garrick.rank_history
                )
                garrick.deployment_history = garrick.close_history_string(
                    garrick.deployment_history, year
                )
                garrick.deployment_history = (
                    f"In Stasis ({get_year_str(year)} - Current)\n"
                    + garrick.deployment_history
                )
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

                if vrox.squad_assignment:
                    chapter.remove_from_grid(vrox)
                if vrox in chapter.reserve:
                    chapter.reserve.remove(vrox)

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
                if current_cm and current_cm.id == "200":  # Vrox
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
                if m.implantation_year == year or (
                    year == REFOUNDING_YEAR and m.implantation_year < year
                ):
                    if m not in chapter.reserve and not m.squad_assignment:
                        chapter.add_to_reserve(m, year)
                if m.implantation_year <= year:
                    m.update_age(year)

        # DREADNOUGHT CAPACITY (Randomized Schedule)
        dread_cap = 0
        if year >= 661:
            dread_cap = sum(1 for y in dread_arrival_years if year >= y)
            if dread_cap > 12:
                dread_cap = 12

        active_dreadnoughts = sum(
            1
            for m in all_marines
            if m.status == "Alive" and m.current_rank == "Dreadnought"
        )
        active_pop = sum(
            1
            for m in all_marines
            if m.status == "Alive" and m.squad_assignment
        )
        reserve_pop = len(chapter.reserve)
        total_pop = active_pop + reserve_pop

        # GRADUATION (Before Recruitment)
        for s in range(1, 11):  # 10th Company Squads 1-10 are Scouts
            for k in range(10):
                m = chapter.grid[10][s][k]
                if m and m.status == "Alive" and m.current_rank == "Neophyte":
                    if m.years_in_service >= 7:
                        chapter.grid[10][s][k] = None
                        m.squad_assignment = None
                        m.promote("Battle Brother", year)
                        chapter.add_to_reserve(m, year)

        # MORTALITY
        base_risk = 0.002  # Peace < 800
        if active_pop >= 1300:
            base_risk = 0.020  # War
        elif active_pop >= 900:
            base_risk = 0.010  # Building

        # Boros (103) Dreadnought Event - Processed first to guarantee D001
        if year == 661:
            boros = next(
                (m for m in all_marines if m.id == "103" and m.status == "Alive"),
                None,
            )
            if boros:
                if boros.squad_assignment:
                    chapter.remove_from_grid(boros)
                if boros in chapter.reserve:
                    chapter.reserve.remove(boros)
                boros.return_relics(year, reliquary)
                boros.promote("Dreadnought", year, display_rank="Dreadnought : D-I")
                dread_id_counter = 2
                chapter.add_to_reserve(boros, year)
                active_dreadnoughts += 1

        for m in [x for x in all_marines if x.status == "Alive"]:
            if m.current_rank == "Dreadnought":
                continue
            if m.current_rank == "Iron Calculus": continue
            if m.squad_assignment == (0, 5):
                if random.random() < 0.002:
                    chapter.remove_from_grid(m)
                    m.return_relics(year, reliquary)
                    m.kill(year)
                continue

            # Hardcoded Death
            if m.death_year_abs and m.death_year_abs == year:
                if m in chapter.reserve:
                    chapter.reserve.remove(m)
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
                    if m.current_tier == 0:
                        risk += 0.02
                    if m.current_tier >= 4:
                        risk *= 0.05  # -90%

                if random.random() < risk:
                    # DREADNOUGHT INTERVENTION
                    if (
                        m.current_rank in ["Veteran Battle Brother", "Veteran Sergeant"]
                        and active_dreadnoughts < dread_cap
                    ):
                        if m.id != "103" and dread_name_index < len(DREADNOUGHT_NAMES):
                            new_name = DREADNOUGHT_NAMES[dread_name_index]
                            dread_name_index += 1
                            m.name = new_name
                            existing_names.add(new_name)
                            # Retroactive Log Update
                            for log_entry in TRANSACTION_LOG:
                                if log_entry["Marine ID"] == m.id:
                                    log_entry["Name"] = new_name

                        if m.squad_assignment:
                            chapter.remove_from_grid(m)
                        if m in chapter.reserve:
                            chapter.reserve.remove(m)
                        m.return_relics(year, reliquary)
                        m.promote(
                            "Dreadnought",
                            year,
                            display_rank=f"Dreadnought : D-{to_roman(dread_id_counter)}",
                        )
                        dread_id_counter += 1
                        chapter.add_to_reserve(m, year)
                        active_dreadnoughts += 1
                        continue

                    if m in chapter.reserve:
                        chapter.reserve.remove(m)
                    chapter.remove_from_grid(m)
                    m.return_relics(year, reliquary)
                    m.kill(year)

        # 20th COMPANY LOGIC (Starts 792.M41)
        if year >= 792:
            # 1. Iron Calculus Mortality (0.1%)
            ic_squad = chapter.grid[20][2]
            for k in range(2, 500):
                m = ic_squad[k]
                if m and m.status == "Alive":
                    if random.random() < 0.001:
                        chapter.remove_from_grid(m)
                        m.return_relics(year, reliquary)
                        m.kill(year)
                        dead_iron_calculus_count += 1

            # 2. Transformation (Bond-Keeper -> Iron Calculus)
            bk_squad = chapter.grid[20][1]
            for k in range(3):
                m = bk_squad[k]
                if m and m.status == "Alive" and m.current_rank == "Bond-Keeper":
                    # Promote after 2-4 years
                    should_promote = False
                    if m.years_in_assignment >= 4:
                        should_promote = True
                    elif m.years_in_assignment >= 2 and random.random() < 0.3:
                        should_promote = True

                    if should_promote:
                        chapter.remove_from_grid(m)
                        m.promote("Iron Calculus", year)
                        
                        # Move to Co 20 Sq 2 (First empty slot >= 2)
                        target_slot = next((ts for ts in range(2, 500) if chapter.grid[20][2][ts] is None), -1)
                        if target_slot != -1:
                            chapter.grid[20][2][target_slot] = m
                            m.deploy(20, 2, year, target_slot)
                            
                            # Create Echo Relic(s)
                            echo_roll = random.random()
                            if echo_roll < 0.40:
                                num_echoes = 1
                            elif echo_roll < 0.60:
                                num_echoes = 2
                            else:
                                num_echoes = 3

                            for i in range(1, num_echoes + 1):
                                if num_echoes == 1:
                                    r_name = f"{m.name}'s Echo"
                                    r_id = f"E-{m.id}"
                                else:
                                    roman = to_roman(i)
                                    r_name = f"{m.name}'s Echo Shard {roman}"
                                    r_id = f"E-{m.id}-{roman}"

                                new_relic = {
                                    "id": r_id,
                                    "name": r_name,
                                    "type": "Echo",
                                    "desc": f"An Echo implant, donated by {m.name}",
                                    "date": year
                                }
                                reliquary.append(new_relic)
                                log_relic_discovery(new_relic)
                                log_transaction(year, m, "Relic Created", f"Manifested {new_relic['name']}")

            # 3. Recruitment (Fill Co 20 Sq 1)
            open_slots = [k for k in range(3) if chapter.grid[20][1][k] is None]
            if open_slots:
                candidates = [
                    x for x in all_marines 
                    if x.status == "Alive" 
                    and x.current_rank == "Battle Brother"
                    and x.years_in_rank >= 5
                    and (year - (x.implantation_year - 12)) < 40
                    and x.squad_assignment != (20, 1)
                    and x.squad_assignment != (0, 5)
                ]
                candidates.sort(key=lambda x: x.years_in_rank, reverse=True)
                
                for _ in range(len(open_slots)):
                    if not candidates: break
                    cand = candidates.pop(0)
                    slot = open_slots.pop(0)
                    if cand.squad_assignment: chapter.remove_from_grid(cand)
                    if cand in chapter.reserve: chapter.reserve.remove(cand)
                    cand.promote("Bond-Keeper", year)
                    chapter.grid[20][1][slot] = cand
                    cand.deploy(20, 1, year, slot)

            # 4. Update Counters (Co 20 Sq 2 Slots 0 & 1)
            living_ic = sum(1 for k in range(2, 500) if chapter.grid[20][2][k] is not None)
            
            cnt1 = Marine(procedural_id=f"{living_ic}", birth_year=year, name="Iron Calculus (Alive)")
            chapter.grid[20][2][0] = cnt1
            cnt1.deploy(20, 2, year, 0)

            cnt2 = Marine(procedural_id=f"{dead_iron_calculus_count}", birth_year=year, name="Iron Calculus (Dead)")
            chapter.grid[20][2][1] = cnt2
            cnt2.deploy(20, 2, year, 1)

        # FORCED INTERMENT PROTOCOL
        if active_dreadnoughts < dread_cap:
            candidate = None

            def get_forced_candidate(rank_filter):
                candidates = [
                    m
                    for m in all_marines
                    if m.status == "Alive" and m.current_rank == rank_filter
                ]
                candidates.sort(key=lambda x: x.years_in_service, reverse=True)
                if not candidates:
                    return None
                # Take 4th oldest (index 3), or the last available if fewer than 4
                idx = min(3, len(candidates) - 1)
                return candidates[idx]

            candidate = get_forced_candidate("Veteran Battle Brother")
            if not candidate:
                candidate = get_forced_candidate("Veteran Sergeant")
            if not candidate:
                candidate = get_forced_candidate("Battle Brother")

            if candidate:
                if candidate.id != "103" and dread_name_index < len(DREADNOUGHT_NAMES):
                    new_name = DREADNOUGHT_NAMES[dread_name_index]
                    dread_name_index += 1
                    candidate.name = new_name
                    existing_names.add(new_name)
                    for log_entry in TRANSACTION_LOG:
                        if log_entry["Marine ID"] == candidate.id:
                            log_entry["Name"] = candidate.name

                if candidate.squad_assignment:
                    chapter.remove_from_grid(candidate)
                if candidate in chapter.reserve:
                    chapter.reserve.remove(candidate)
                candidate.return_relics(year, reliquary)
                candidate.promote(
                    "Dreadnought",
                    year,
                    display_rank=f"Dreadnought : D-{to_roman(dread_id_counter)}",
                )
                dread_id_counter += 1
                chapter.add_to_reserve(candidate, year)
                active_dreadnoughts += 1
            else:
                print(f"ERROR - DREADNOUGHT PROTOCOL FAILED in {year}")

        # RECRUITMENT (Proportional Filling)
        empty_neo_slots = []
        for s in range(1, 11):  # 10th Company Squads 1-10
            # Start from 1 to reserve slot 0 for Officer (Chaplain/Sergeant)
            for k in range(1, 10):
                if chapter.grid[10][s][k] is None:
                    empty_neo_slots.append((10, s, k))

        if NEOPHYTE_INTAKE_OVERRIDE > 0:
            intake = NEOPHYTE_INTAKE_OVERRIDE
        else:
            # Ramp Up Curve
            if year < RECRUITMENT_START:
                intake = 0
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
                    if attempts > 500:
                        new_name = f"{new_name} {next_id}"
                        existing_names.add(new_name)
                        break

                new_m = Marine(procedural_id=next_id, birth_year=year - 12, name=new_name)
                next_id += 1
                all_marines.append(new_m)
                log_transaction(year, new_m, "Recruitment", "New Initiate")
                c, s, k = loc
                chapter.grid[c][s][k] = new_m
                new_m.deploy(c, s, year, k)
                moved_ids.add(new_m.id)

        # DEMOTION
        for m in [
            x
            for x in all_marines
            if x.status == "Alive" and x.squad_assignment
        ]:
            if m.id == "101":
                continue

            if (
                m.current_tier in [2, 3]
                and "Bond-Keeper" not in m.current_rank
                and random.random() < 0.002
            ):
                chapter.remove_from_grid(m)

                demoted_rank = (
                    "Battle Brother (Runt)"
                    if m.current_rank == "Sergeant (Runt)"
                    else "Battle Brother"
                )

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
                    if c == 0 and s == 0 and k == 0 and year < 634:
                        continue

                    target_role = chapter.get_role_rule(c, s, k, active_dreadnoughts)
                    if not target_role:
                        continue
                    candidate = chapter.find_best_candidate(
                        target_role, all_marines, moved_ids, c
                    )
                    if candidate:
                        if candidate.squad_assignment:
                            chapter.remove_from_grid(candidate)
                        if candidate in chapter.reserve:
                            chapter.reserve.remove(candidate)
                        chapter.grid[c][s][k] = candidate
                        candidate.deploy(c, s, year, k)
                        moved_ids.add(candidate.id)
                        if candidate.current_tier < TIERS.get(
                            target_role, 1
                        ) or (
                            target_role == "Battle Brother (Runt)"
                            and candidate.current_rank == "Battle Brother"
                        ):
                            candidate.promote(target_role, year)

        if year % 5 == 0:
            current_active = sum(
                1
                for m in all_marines
                if m.status == "Alive"
                and m.squad_assignment
                and m.squad_assignment[0] != -1
            )
            current_reserve = len([m for m in chapter.reserve if m.status == "Alive"])
            current_neophytes = sum(
                1
                for m in all_marines
                if m.status == "Alive" and m.current_rank == "Neophyte"
            )
            print(
                f"Year {get_year_str(year)} | Active: {current_active} / 1112 | Reserve: {current_reserve} | Recruits: {current_neophytes}"
            )

        if year % 10 == 0 and all_marines:
            data_out = [m.to_dict(year) for m in all_marines]
            df_out = pd.DataFrame(data_out)
            df_out["SortID"] = df_out["Chapter ID Number"].astype(int)
            df_out = df_out.sort_values("SortID").drop("SortID", axis=1)
            df_out.to_csv("OUTPUT Auto-Roster.csv", index=False, mode="w")

    final_dread_count = sum(
        1
        for m in all_marines
        if m.status == "Alive" and m.current_rank == "Dreadnought"
    )
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
        candidates = [
            m
            for m in all_marines
            if m.status == "Alive" and m.current_rank == target_rank
        ]

        if target_company is not None:
            candidates = [
                m
                for m in candidates
                if m.squad_assignment and m.squad_assignment[0] == target_company
            ]
        if target_squad is not None:
            candidates = [
                m
                for m in candidates
                if m.squad_assignment and m.squad_assignment[1] == target_squad
            ]

        if candidates:
            candidate = candidates[0]  # Take the first match
            print(
                f"  Found candidate for {char_req['Name']}: {candidate.name} (ID: {candidate.id})"
            )
            candidate.name = char_req["Name"]
            candidate.cognomen = char_req.get("Cognomen", "")
            # Retroactive Log Update
            for log_entry in TRANSACTION_LOG:
                if log_entry["Marine ID"] == candidate.id:
                    log_entry["Name"] = candidate.name
            success_count += 1
        else:
            print(
                f"  Warning: No suitable candidate found for {char_req['Name']} ({target_rank} in Co {target_company} Sq {target_squad})"
            )
            failed_chars.append(char_req["Name"])

    print(f"{success_count}/{len(STORY_CHARACTERS)} Story Characters successfully added.")
    if failed_chars:
        print(f"Unable to add: {', '.join(failed_chars)}")

    print("Formatting Codex & Compressing Logs...")
    if all_marines:
        data_out = [m.to_dict(END_YEAR_ABS) for m in all_marines]
        df_out = pd.DataFrame(data_out)

        df_out["SortID"] = df_out["Chapter ID Number"].astype(int)
        df_out = df_out.sort_values("SortID").drop("SortID", axis=1)

        print("Uploading to Holy Archives...")
        df_out.to_csv("OUTPUT Auto-Roster.csv", index=False, mode="w")

        update_human_officers()
        upload_to_google_sheets(TRANSACTION_LOG, DISCOVERED_RELICS_LOG)
    else:
        print("Warning: No marines found. Output generation skipped.")
    print("Process Finished.")
