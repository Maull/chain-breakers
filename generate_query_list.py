DREADNOUGHT_PRIORITY = [
    (5, 3), (5, 4), (5, 5), (5, 6), # 5th Chapter: Old Squads 4-7 -> New Squads 3-6
    (1, 1), (2, 3), (3, 3),         # 1st (Sq 1), 2nd & 3rd (Old Sq 4 -> New Sq 3)
    (6, 1), (7, 1), (8, 1),         # 6th, 7th, 8th: Old Sq 2 -> New Sq 1
    (9, 3), (9, 4)                  # 9th Chapter: Old Sq 4-5 -> New Sq 3-4
]

def get_role_rule(company, squad, slot, active_dreadnoughts=0):
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
        # Squads 1-10 are Neophytes (Handled by recruitment logic, but defined here for safety)
        if slot == 0: return "Sergeant" # Scout Sergeant
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

def main():
    # --- RESERVE ---
    for i in range(50):
        print(f"Chapter Reserve - Reserve {i+1} - Squad 0 - Slot {i+1}, -1, 0, {i}")

    # --- COMPANY 0 (Special Squads) ---
    # Squads 0-4, Slots 0-11 (12 slots total per squad in astarties.py)
    for squad in range(5):
        for slot in range(12):
            # Format: Company X - Rank - Squad Y - Slot Z, C, S, K
            # Display Slot is 1-based (Slot 1 = internal 0)
            # C, S, K are the internal numbers used in the logbook (0-indexed)
            rank = get_role_rule(0, squad, slot, 20) or "UNUSED"
            print(f"Company 0 - {rank} - Squad {squad} - Slot {slot + 1}, 0, {squad}, {slot}")

    # --- COMPANIES 1-10 ---
    # Squads 0-10, Slots 0-11 (12 slots total per squad in astarties.py)
    for company in range(1, 11):
        for squad in range(11):
            for slot in range(12):
                rank = get_role_rule(company, squad, slot, 20) or "UNUSED"
                print(f"Company {company} - {rank} - Squad {squad} - Slot {slot + 1}, {company}, {squad}, {slot}")

if __name__ == "__main__":
    main()
