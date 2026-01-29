import csv
import random

# ==========================================
# CONFIGURATION
# ==========================================

# Placeholder lists - Replace these with the lists provided by your AI
FIRST_NAMES = [
    'Dayved', 'Syman', 'Jawn', 'Mykal', 'Jaymz', 'Tommas', 'Robart', 'Wyllam', 
    'Rychard', 'Jozeff', 'Krystofer', 'Charlz', 'Danyal', 'Mathyu', 'Antny', 
    'Marck', 'Donnald', 'Stevan', 'Pawl', 'Andru', 'Joshwa', 'Kennth', 
    'Kevyn', 'Bryan', 'Jorj', 'Edwad', 'Ronnald', 'Tymothy', 'Jayson', 
    'Jeffry', 'Rian', 'Gari', 'Jakub', 'Nycolas', 'Eryk', 'Stefan', 
    'Jonathun', 'Lary', 'Justyn', 'Skott', 'Brandun', 'Franck', 'Benjamyn', 
    'Gregry', 'Samual', 'Raymund', 'Patryck', 'Alyxander', 'Jak', 'Denys', 
    'Jery', 'Tylor', 'Aron', 'Henree', 'Duglas', 'Peeter', 'Joze', 'Adum', 
    'Zakary', 'Waltar', 'Nathun', 'Harald', 'Kile', 'Karl', 'Artur', 'Jerald', 
    'Rojer', 'Keeth', 'Jeramy', 'Tery', 'Lawrense', 'Shawn', 'Krystian', 
    'Albar', 'Jo', 'Jwan', 'Ostin', 'Jesee', 'Wyllie', 'Byllee', 'Broose', 
    'Haree', 'Fredd', 'Wayn', 'Steev', 'Luwis', 'Ugene', 'Russal', 'Bobbee', 
    'Vyctor', 'Martyn', 'Erny', 'Filyp', 'Tadd', 'Kraig', 'Alun', 'Klarenz', 
    'Krys', 'Jawnnee', 'Erl', 'Jymee', 'Antunio', 'Dannee', 'Tonee', 'Myk', 
    'Stanlee', 'Lennd', 'Dayl', 'Manwel', 'Rodnee', 'Kurtys', 'Norman', 
    'Alen', 'Marvyn', 'Vinsent', 'Glen', 'Jeff', 'Travys', 'Jakub', 'Lee', 
    'Melvyn', 'Alfrad', 'Fransys', 'Herbar', 'Fredryk', 'Ray', 'Joal', 'Edwyn', 
    'Don', 'Eddee', 'Rykee', 'Troy', 'Randul', 'Baree', 'Bernad', 'Maryo', 
    'Leeroy', 'Fransysko', 'Markuz', 'Theodor', 'Clyford', 'Mygwel', 'Oskah', 
    'Jay', 'Jym', 'Tom', 'Kalvyn', 'Alyx', 'Jon', 'Ronnee', 'Byl', 'Loyd', 
    'Leon', 'Deryk', 'Warren', 'Darel', 'Jerom', 'Floyd', 'Alvyn', 'Tym', 
    'Weslee', 'Gordan', 'Deen', 'Greg', 'Jorjay', 'Dustyn', 'Dan', 'Herman', 
    'Shayn', 'Ryk', 'Brent', 'Ramun', 'Sam', 'Trystun', 'Zayn', 'Bo', 
    'Drayk', 'Kayn', 'Grant', 'Blak', 'Kol', 'Zander', 'Sylas', 'Tytus', 
    'Syrus', 'Feelyks', 'Dexxtar', 'Jaspur', 'Fyn', 'Mylo', 'Arlo', 'Otys', 
    'Remee', 'Enzok', 'Nyko', 'Hugo', 'Otto', 'Rokko', 'Dantay', 'Vans', 
    'Kayd', 'Reed', 'Seth', 'Gayj', 'Kwyn', 'Reez', 'Noxx', 'Nash', 
    'Wyldar', 'Archur', 'Soyar', 'Rykar', 'Bekket', 'Holdun', 'Atlass', 
    'Oryon', 'Soren', 'Kallum', 'Bodee', 'Kaspyan', 'Attykus', 'Kyllyan', 
    'Magnuz', 'Awrelyus', 'Kassyan', 'Evandur', 'Leandur', 'Thatchur', 
    'Fetchur', 'Graysun'
]

LAST_NAMES = [
    # --- The -sons (Patronymic & Foundry-born) ---
    'Noxson', 'Sumpson', 'Dayvdson', 'Symanson', 'Jawnson', 'Mykalson', 'Jaymzson', 'Tommasson', 
    'Robartson', 'Wyllamson', 'Forgeson', 'Ironson', 'Ashson', 'Dustson', 'Weldson', 'Steelson', 
    'Gearson', 'Rivetson', 'Pistonson', 'Cinderson', 'Blastson', 'Slagson', 'Alloyson', 'Sledgeson', 
    'Pyreson', 'Kilnson', 'Valveson', 'Pipeson', 'Cableson', 'Wireson', 'Grilleson', 'Dregson', 
    'Shaleson', 'Cobaltson', 'Nickelson', 'Copperson', 'Brasson', 'Bronzeson', 'Carbonson', 'Cokeson', 
    'Peatson', 'Pitson', 'Mineson', 'Quarryson', 'Claspson', 'Braceson', 'Anchorson', 'Linkson', 
    'Chainson', 'Boltson', 'Gasketson', 'Shaftson', 'Beamborn', 'Plateborn', 'Sunderborn', 'Hearthson',
    
    # --- The -ers (Functional/Locational) ---
    'Sumper', 'Forger', 'Welder', 'Riveter', 'Driller', 'Grinder', 'Smelter', 'Burner', 'Caster', 
    'Shaper', 'Binder', 'Hewer', 'Cutter', 'Joiner', 'Anchorer', 'Gager', 'Tanker', 'Pumper', 
    'Shoveler', 'Leverer', 'Fluxer', 'Grater', 'Kilner', 'Drillerson', 'Hewerson', 'Cutterson', 
    'Shaperson', 'Joinerson', 'Binderson', 'Claspson', 'Braceson', 'Anchorson', 'Sunderer', 
    'Slaggur', 'Foundrer', 'Pistoner', 'Gasketer', 'Rivettar', 'Turbiner', 'Blastur', 'Meltar', 
    'Vatman', 'Boiler', 'Steamer', 'Railer', 'Trencher', 'Sifter', 'Grappler', 'Hauler', 'Lifter',
    
    # --- Warped Terran-Son & -er Drift ---
    'Smythson', 'Milyrson', 'Tailorson', 'Bakerson', 'Kukson', 'Fisherer', 'Huntarson', 'Waldson', 
    'Karterson', 'Wryghtson', 'Taylerson', 'Glovson', 'Tannerson', 'Mayson', 'Parsoner', 'Abbotson', 
    'Clarkson', 'Wybson', 'Dixoner', 'Hudsoner', 'Wattson', 'Richudson', 'Wilkson', 'Robson', 
    'Nellson', 'Gibbson', 'Haryson', 'Jamesson', 'Andruson', 'Stephensur', 'Michaelson', 'Matthewsur',
    
    # --- Industrial Compounds (The Warped -er/-son) ---
    'Steel-er', 'Iron-er', 'Ash-er', 'Dust-er', 'Soot-er', 'Stone-er', 'Rock-er', 'Deep-er', 
    'Lux-son', 'Anvil-er', 'Hearth-er', 'Verdi-son', 'Gris-son', 'Rust-son', 'Oxyd-er', 'Melt-er', 
    'Fuse-son', 'Bond-er', 'Chain-er', 'Lock-son', 'Key-er', 'Gate-son', 'Wall-er', 'Keep-er',
    
    # --- Noxian Specialized Suffixes ---
    'Ironson-Vex', 'Sumpman-Thrac', 'Noxson-Grey', 'Forgeson-Vorn', 'Weldman-Krell', 'Asherson-Gaunt',
    'Steel-Sunderer', 'Iron-Hewer', 'Dust-Binder', 'Rock-Crusher', 'Void-Linker', 'Terminus-son',
    'Anvil-son', 'Lux-born', 'Nox-born', 'Sump-born', 'Forge-born', 'Steel-born', 'Iron-born',
    'Steam-son', 'Smoke-son', 'Coal-son', 'Oil-son', 'Acid-son', 'Sludge-son', 'Filth-son',
    'Grit-son', 'Sand-son', 'Clay-son', 'Mud-son', 'Earth-son', 'World-son', 'Star-son',
    'Sun-son', 'Moon-son', 'Void-son', 'Hell-son', 'Death-son', 'Life-son', 'War-son',
    'Blood-son', 'Bone-son', 'Flesh-son', 'Mind-son', 'Soul-son', 'Will-son', 'Power-son',
    'Might-son', 'Strength-son', 'Honor-son', 'Glory-son', 'Duty-son', 'Faith-son', 'Oath-son',
    'Word-son', 'Law-son', 'Rule-son', 'King-son', 'Lord-son', 'Prince-son', 'Duke-son',
    'Baron-son', 'Count-son', 'Knight-son', 'Squire-son', 'Page-son', 'Serf-son', 'Slave-son',
    'Master-son', 'Boss-son', 'Chief-son', 'Head-son', 'Eye-son', 'Hand-son', 'Foot-son',
    'Arm-son', 'Leg-son', 'Back-son', 'Chest-son', 'Heart-son', 'Liver-son', 'Lung-son'
]

OUTPUT_FILE = 'unique_names.csv'
MAX_NAMES = 5430  # Set to None for no limit

# ==========================================
# GENERATOR
# ==========================================

def main():
    print("Generating unique names...")
    
    # Generate all possible unique combinations (Cartesian Product)
    combinations = []
    for first in FIRST_NAMES:
        for last in LAST_NAMES:
            combinations.append(f"{first} {last}")
    
    # Shuffle to randomize the order
    random.shuffle(combinations)
    
    print(f"Total unique combinations found: {len(combinations)}")
    
    final_list = combinations
    if MAX_NAMES is not None:
        final_list = combinations[:MAX_NAMES]
        print(f"Limiting output to {len(final_list)} names.")
    
    # Write to CSV
    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name']) # Header
            for name in final_list:
                writer.writerow([name])
        print(f"Successfully wrote to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    main()
