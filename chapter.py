from config import (
    DREADNOUGHT_PRIORITY,
    SPECIALIST_PATHS,
    TENURE_REQS,
    TIERS,
    log_transaction,
)


class Chapter:
    def __init__(self):
        self.grid = {
            c: {s: {k: None for k in range(12)} for s in range(0, 11)}
            for c in range(0, 11)
        }
        # 20th Company (Special Process)
        self.grid[20] = {
            1: {k: None for k in range(3)},      # 3 Slots for Bond-Keepers
            2: {k: None for k in range(500)}     # Unlimited (500) for Iron Calculus + Counters
        }
        self.reserve = []

    def remove_from_grid(self, marine):
        if marine.squad_assignment:
            c, s = marine.squad_assignment
            if c in self.grid and s in self.grid[c]:
                for k in self.grid[c][s]:
                    if self.grid[c][s][k] == marine:
                        self.grid[c][s][k] = None
            marine.squad_assignment = None

    def add_to_reserve(self, marine, year):
        if marine in self.reserve:
            return

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
            if slot == 9:
                return "Dreadnought"

        # COMPANY 0 (Chapter High Command & Support)
        if company == 0:
            if squad == 0:  # Chapter Command
                if slot == 0:
                    return "Chapter Master"
                if slot in [1, 2]:
                    return "Lieutenant"  # Honor Guard / Chapter Lts
                if slot < 11:
                    return "Veteran Battle Brother"
                return None
            if squad == 1:  # Apothecarion
                if slot < 4:
                    return "Apothecary"
                if slot < 6:
                    return "Veteran Battle Brother"
                return None
            if squad == 2:  # Reclusiam
                if slot < 4:
                    return "Chaplain"
                if slot < 8:
                    return "Veteran Battle Brother"
                return None
            if squad == 3:  # Libarius
                if slot < 4:
                    return "Null-Warden"
                if slot < 8:
                    return "Veteran Battle Brother"
                return None
            if squad == 4:  # Armory
                if slot == 0:
                    return "Techmarine"
                if slot < 5:
                    return "Artificer Brother"
                if slot < 9:
                    return "Veteran Battle Brother"
                return None
            return None

        # COMPANY 1 (Veterans)
        if company == 1:
            # Squad 0: Command
            if squad == 0:
                roles = {
                    0: "Captain",
                    1: "Standard Bearer",
                    2: "Apothecary",
                    3: "Chaplain",
                    4: "Null-Warden",
                    5: "Lieutenant",
                    6: "Lieutenant",
                }
                return roles.get(slot, None)

            # Squads 1-10: Veteran Battle Squads
            if slot == 0:
                return "Veteran Sergeant"
            if slot == 1:
                return "Bond-Keeper"
            if slot < 10:
                return "Veteran Battle Brother"
            return None

        # COMPANY 5 (5th Chapter - Armory/Tech)
        if company == 5:
            # Squad 0: Command Squad
            if squad == 0:
                roles = {
                    0: "Captain",
                    1: "Standard Bearer",
                    2: "Apothecary",
                    3: "Chaplain",
                    4: "Null-Warden",
                    5: "Techmarine",
                    6: "Lieutenant",
                    7: "Lieutenant",
                }
                return roles.get(slot, None)

            # Squad 10: 5th Chapter, 10th Squad (Runt)
            if squad == 10:
                if slot == 0:
                    return "Sergeant (Runt)"
                if slot == 1:
                    return "Bond-Keeper"
                if slot < 10:
                    return "Battle Brother (Runt)"
                return None

            # Squads 1-9: Standard Tech Squads
            if slot == 0:
                return "Sergeant"
            if slot == 1:
                return "Bond-Keeper"
            if slot in [2, 3]:
                return "Artificer Brother"
            if slot < 10:
                return "Battle Brother"
            return None

        # COMPANY 10 (Scouts)
        if company == 10:
            if squad == 0:
                roles = {
                    0: "Captain",
                    1: "Standard Bearer",
                    2: "Apothecary",
                    3: "Chaplain",
                    4: "Null-Warden",
                    5: "Lieutenant",
                    6: "Lieutenant",
                }
                return roles.get(slot, None)

            # Squads 1-5: Chaplain as Trainer in slot 0
            if 1 <= squad <= 5 and slot == 0:
                return "Chaplain"

            # Squads 6-10: Sergeant in slot 0 (Standard Scout Squads)
            if slot == 0:
                return "Sergeant"
            if slot < 10:
                return "Neophyte"
            return None

        # COMPANIES 2-4, 6-10 (Standard Battle Companies)

        # Special 10th Squads for 3rd and 4th (Runt Logic - Mapped from old Squad 11)
        if squad == 10:
            if company == 3:
                if slot == 0:
                    return "Sergeant (Runt)"
                if slot == 1:
                    return "Bond-Keeper"
                if slot < 7:
                    return "Battle Brother (Runt)"
                if slot < 10:
                    return "Battle Brother"
                return None
            if company == 4:
                if slot == 0:
                    return "Sergeant"
                if slot == 1:
                    return "Bond-Keeper"
                if slot < 6:
                    return "Battle Brother"
                if slot < 10:
                    return "Battle Brother (Runt)"
                return None

        # Squad 0: Command Squad
        if squad == 0:
            roles = {
                0: "Captain",
                1: "Standard Bearer",
                2: "Apothecary",
                3: "Chaplain",
                4: "Null-Warden",
                5: "Lieutenant",
                6: "Lieutenant",
            }
            return roles.get(slot, None)

        # Squads 1-10: Standard Battle Squads
        if slot == 0:
            return "Sergeant"
        if slot == 1:
            return "Bond-Keeper"
        if slot < 10:
            return "Battle Brother"
        return None

    def find_best_candidate(self, target_role, all_marines, moved_ids, target_company):
        target_tier = TIERS.get(target_role, 1)

        def is_valid(m):
            return m.status == "Alive" and m.id not in moved_ids

        # 1. INTER-CHAPTER MOVE CHECK (40 Years Rule)
        def check_inter_chapter(m):
            # Dreadnoughts go where they are needed, ignoring tenure
            if m.current_rank == "Dreadnought":
                return True

            # 20th Company Lockdown
            if m.squad_assignment and m.squad_assignment[0] == 20:
                return True

            if m.squad_assignment:
                sc, ss = m.squad_assignment
                if sc != 0 and sc != 1 and sc != -1 and sc != target_company:
                    if m.years_in_assignment < 40:
                        return False
            return True

        allowed_sources = SPECIALIST_PATHS.get(target_role, None)

        # 2. LATERAL (Exact Rank)
        reserves = [m for m in self.reserve if is_valid(m)]
        reserves.sort(key=lambda x: x.years_in_service, reverse=True)
        for m in reserves:
            if target_company == 1 and m.current_tier < 2:
                continue
            if not check_inter_chapter(m):
                continue

            # Strict Specialist Matching
            if allowed_sources and m.current_rank not in allowed_sources:
                # Exception: Tier 1 to Tier 1 lateral (BB <-> BB Runt)
                if target_tier == 1 and m.current_tier == 1:
                    pass
                elif m.current_rank == target_role:
                    pass
                else:
                    continue

            if m.current_tier == target_tier:
                return m

        # 3. PROMOTION / DOWN-FILLING
        # Dreadnoughts are only created via Mortality events, never promoted to fill a slot.
        if target_role == "Dreadnought":
            return None

        start_search = target_tier - 1
        if start_search < 1:
            start_search = 1

        search_range = list(range(start_search, 0, -1))

        for search_tier in search_range:
            required_tenure = TENURE_REQS.get(search_tier, 0)
            candidates = []

            # Check Reserve
            res_candidates = [
                m
                for m in self.reserve
                if m.current_tier == search_tier
                and is_valid(m)
                and check_inter_chapter(m)
            ]
            if search_tier < target_tier:
                res_candidates = [
                    m for m in res_candidates if m.years_in_rank >= required_tenure
                ]
            candidates.extend(res_candidates)

            # Check Active Duty (Only for Promotions, not for lateral/down fill)
            if search_tier < target_tier:
                actives = [
                    m
                    for m in all_marines
                    if m.squad_assignment
                    and m.current_tier == search_tier
                    and is_valid(m)
                    and check_inter_chapter(m)
                ]
                eligible_actives = [
                    m for m in actives if m.years_in_rank >= required_tenure
                ]
                if eligible_actives:
                    candidates.extend(eligible_actives)

            # Garrick (101) cannot be promoted via standard logic
            if search_tier < target_tier:
                candidates = [m for m in candidates if m.id != "101"]

            # Filter
            if allowed_sources:
                # If target is Tier 1, allow any Tier 1 source (Cross-Training)
                if target_tier == 1:
                    candidates = [
                        m
                        for m in candidates
                        if m.current_tier == 1 or m.current_rank in allowed_sources
                    ]
                else:
                    candidates = [
                        m for m in candidates if m.current_rank in allowed_sources
                    ]

            if target_company == 1:
                candidates = [m for m in candidates if m.current_tier >= 1]

            if candidates:
                if target_role == "Bond-Keeper":
                    candidates = [m for m in candidates if not any(r.get("type") == "Echo" for r in m.active_relics)]

                candidates.sort(
                    key=lambda x: (x.years_in_rank, x.years_in_service), reverse=True
                )
                return candidates[0]

        return None

    def assign_relics(self, all_marines, reliquary, year):
        if not reliquary:
            return

        # --- PASS 1: ECHO RELICS (Top-Down, Ignore Relic Count) ---
        echo_relics = [r for r in reliquary if r.get("type") == "Echo"]
        # Remove Echoes from main reliquary for now
        reliquary[:] = [r for r in reliquary if r.get("type") != "Echo"]

        if echo_relics:
            eligible_ranks_echo = [
                "Chapter Master", "Captain", "Lieutenant", "Chaplain", "Techmarine",
                "Standard Bearer", "Veteran Sergeant", "Veteran Battle Brother", "Battle Brother"
            ]
            
            # Filter candidates for Echoes
            echo_candidates = [
                m for m in all_marines
                if m.status == "Alive"
                and m.current_rank in eligible_ranks_echo
                and m.id != "101"
                # Specific Echo restrictions
                and int(m.id) > 500 
                and m.current_rank != "Bond-Keeper"
                # Must not already have an Echo
                and not any(r["type"] == "Echo" for r in m.active_relics)
            ]

            # Sort by Rank Priority (High to Low), then Tenure
            rank_priority_echo = {r: i for i, r in enumerate(eligible_ranks_echo)}
            echo_candidates.sort(
                key=lambda m: (
                    rank_priority_echo.get(m.current_rank, 99),
                    m.years_in_rank * -1
                )
            )

            # Assign Echoes
            for cand in echo_candidates:
                if not echo_relics:
                    break
                
                relic = echo_relics.pop(0)
                cand.receive_relic(relic, year)
                cand.name = f"{cand.name} (Echo)"
                log_transaction(year, cand, "Relic", f"Received {relic['name']}")

            # Put back any unassigned Echoes (if any remain)
            if echo_relics:
                reliquary.extend(echo_relics)

        # --- PASS 2: STANDARD RELICS (Spread Out) ---
        if not reliquary:
            return

        # Eligibility: Tier 4+ (Officers/Veterans) + Chapter Master, excluding Garrick (101)
        eligible_ranks = [
            "Chapter Master",
            "Captain",
            "Lieutenant",
            "Chaplain",
            "Techmarine",
            "Standard Bearer",
            "Veteran Sergeant",
            "Veteran Battle Brother",
            "Battle Brother",
        ]
        eligible_marines = [
            m
            for m in all_marines
            if m.status == "Alive"
            and m.current_rank in eligible_ranks
            and m.id != "101"
        ]

        # Sort by Rank Priority (High to Low)
        rank_priority = {r: i for i, r in enumerate(eligible_ranks)}

        # Distribute
        while reliquary:
            # Sort: Fewest relics first, then Rank Priority, then Tenure
            eligible_marines.sort(
                key=lambda m: (
                    len(m.active_relics),
                    rank_priority.get(m.current_rank, 99),
                    m.years_in_rank * -1,
                )
            )

            assigned = False
            for candidate in eligible_marines:
                # Find first compatible relic in reliquary
                for i, relic in enumerate(reliquary):
                    # Battle Brothers can only take Echoes
                    if candidate.current_rank == "Battle Brother" and relic.get("type") != "Echo":
                        continue

                    # Echo Relic Restrictions
                    if relic.get("type") == "Echo":
                        if int(candidate.id) <= 500 or candidate.current_rank == "Bond-Keeper":
                            continue

                    # Check for duplicate type
                    if not any(r["type"] == relic["type"] for r in candidate.active_relics):
                        candidate.receive_relic(relic, year)
                        if relic.get("type") == "Echo":
                            candidate.name = f"{candidate.name} (Echo)"
                        log_transaction(
                            year, candidate, "Relic", f"Received {relic['name']}"
                        )
                        reliquary.pop(i)
                        assigned = True
                        break
                if assigned:
                    break

            if not assigned:
                break
