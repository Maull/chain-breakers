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

# Tenure Requirements (Years in rank required for promotion)
TENURE_REQS = {0: 8, 1: 5, 2: 10, 3: 15, 4: 20, 5: 30}
OLD_GUARD_MORTALITY_RISK = 0.00005 # 0.05% chance per year

# Nomenclature
FIRST_NAMES = [
    "Cato", "Alaric", "Tibalt", "Hektor", "Silas", "Cassiel", "Varro", "Kardan", "Mordecai", 
    "Jago", "Bram", "Valerius", "Zephon", "Ortan", "Garviel", "Tarik", "Iacton", "Saul", 
    "Sigismund", "Alexis", "Fafnir", "Nassir", "Azkaellon", "Raldoron", "Amit", "Sevatarion", 
    "Shang", "Gendor", "Malcharion", "Talos", "Xarl", "Cyrion", "Uzas", "Mercutian", "Variel", 
    "Lucoryphus", "Zso", "Skraivok", "Hecaton", "Atharva", "Phosis", "Hathor", "Khalophis", 
    "Auramagma", "Uthizzar", "Ahriman", "Ohrmuzd", "Sanakht", "Ignis", "Gaumata", "Menes", 
    "Arvida", "Iezekyle", "Falkus", "Kayfal", "Kalus", "Luc", "Devram", "Maloghurst", "Serghar", 
    "Geraddon", "Argis", "Berossus", "Forrix", "Kroeger", "Honsou", "Barban", "Soltarn", 
    "Golg", "Narik", "Nykona", "Sabik", "Branthan", "Atreus", "Castus", "Decimus", "Justinian", 
    "Messinius", "Areon", "Drakan", "Kaelen", "Jaxon", "Myron", "Torin", "Hadran", "Zephyrin", 
    "Belos", "Valian", "Oris", "Garran", "Tiber", "Kestus", "Marcus", "Falco", "Varek", 
    "Draxus", "Solon", "Kyrus", "Joran", "Kaelo", "Aris", "Kellen", "Varus", "Titus", 
    "Arturus", "Karsat", "Bjorn", "Zahariel", "Skold", "Ravi", "Tiberius", "Ogedei", "Haldor", 
    "Vaman", "Batu", "Sigurd", "Arjun", "Gaius", "Subotai", "Leif", "Indra", "Kublai", "Gunnar", 
    "Surya", "Mongke", "Erik", "Chandra", "Tolui", "Olaf", "Agni", "Hulagu", "Torsten", 
    "Ishwar", "Septimus", "Jochi", "Sven", "Rishi", "Julius", "Berke", "Hakon", "Flavius", 
    "Arghun", "Ivar", "Yama", "Claudius", "Gaykhatu", "Rollo", "Krishna", "Nero", "Baidu", 
    "Vitellius", "Abaqa", "Canute", "Domitian", "Tekuder", "Harald", "Hadrian", "Toghon", 
    "Egil", "Antoninus", "Buyantu", "Haakon", "Pertinax", "Gudrod", "Didius", "Shidebala", 
    "Sigtrygg", "Pescennius", "Clodius", "Tugh", "Caracalla", "Irinjibal", "Geta", "Sverre", 
    "Arjuna", "Macrinus", "Biligtu", "Inge", "Diadumenianus", "Uskhal", "Govinda", "Jorightu", 
    "Alexander", "Engke", "Eric", "Maximinus", "Elbeg", "Gordian", "Gun", "Pupienus", 
    "Balbinus", "Delbeg", "Philip", "Adai", "Decius", "Tayisung", "Trebonianus", "Esen", 
    "Eystein", "Aemilianus", "Markorgis", "Valerian", "Molon", "Gallienus", "Manduul", "Dayan", 
    "Aurelian", "Bars", "Tacitus", "Bodi", "Christian", "Probus", "Daraisung", "Frederick", 
    "Carus", "Tumen", "Carinus", "Buyan", "Gustav", "Numerian", "Ligdan", "Charles", "Ejei", 
    "Oscar", "Maximian", "Batmunkh", "Constantius", "Manduulai", "Galerius", "Agubar", 
    "Gideon", "Kenjiro", "Takeshi", "Hiroshi", "Jiro", "Saburo", "Shiro", "Goro", "Ichiro", 
    "Masaru", "Kaito", "Renzo", "Raiden", "Osamu", "Kenzo", "Katsuo", "Akio", "Hideo", 
    "Toshio", "Yori", "Kazuo", "Satoru", "Mitsuru", "Yoshiro", "Noboru", "Shinji", "Tetsuo", 
    "Ryuu", "Isamu", "Makoto", "Daiki", "Akihiko", "Hiroki", "Yoshio", "Kenichi", "Koji", 
    "Shoji", "Mamoru", "Eiji", "Keisuke", "Yusuke", "Malik", "Tariq", "Omar", "Hassan", 
    "Idris", "Nasir", "Khalid", "Zaid", "Hamza", "Bashir", "Yusuf", "Ibrahim", "Mustafa", 
    "Ahmad", "Salim", "Kareem", "Rafiq", "Mansour", "Hakim", "Saeed", "Jabir", "Qasim", 
    "Walid", "Habib", "Faris", "Amin", "Latif", "Nizar", "Adil", "Farid", "Kwame", "Kofi", 
    "Jengo", "Zuberi", "Obi", "Amadi", "Zola", "Kunto", "Baka", "Sekani", "Azizi", "Jabari", 
    "Thabo", "Neo", "Tau", "Simba", "Duma", "Enzi", "Faraji", "Jelani", "Madu", "Okoro", 
    "Sefu", "Tendai", "Xolani", "Zende", "Bamidele", "Chidi", "Daren", "Ebele", "Femi", 
    "Gada", "Ike", "Juma", "Kayode", "Leke", "Mosi", "Nnamdi", "Olufemi", "Paki", "Razak", 
    "Shola", "Taiwo", "Uche", "Uzoma", "Wekesa", "Yao", "Chen", "Li", "Wang", "Zhang", 
    "Liu", "Zhao", "Wu", "Zhou", "Xu", "Sun", "Ma", "Zhu", "Hu", "Guo", "Lin", "He", 
    "Gao", "Liang", "Luo", "Song", "Zheng", "Xie", "Han", "Tang", "Feng", "Yu", "Dong", 
    "Ye", "Pan", "Du", "Yuan", "Jiang", "Cai", "Wei", "Jin", "Fan", "Tian", "Cheng", 
    "Ding", "Tan", "Shao", "Huang", "Mo", "Kong", "Bai", "Wen", "Long", "Wan", "Duan", 
    "Lei", "Shi", "Mao", "Qiu", "Zou", "Xiong", "Meng", "Qin", "Gu", "Hou", "Xing", "Che", 
    "Fu", "Yan", "Dai", "Xia", "Zhong", "Fang", "Ren", "Ge", "Severus", "Constantin", 
    "Erasmus", "Soren", "Malakai", "Malchor", "Voros", "Xander", "Mordred", "Balthazar", 
    "Corvinus", "Alastor", "Porthos", "Zuriel", "Nathaniel", "Uriah", "Solomon", "Gabriel", 
    "Antonas", "Balan", "Castor", "Dracos", "Elian", "Icarus", "Jorius", "Kelman", "Octavius", 
    "Paulus", "Rufus", "Sergius", "Xerxes", "Yorin", "Zosimus", "Bran", "Dagur", "Gorm", 
    "Hrolf", "Jarl", "Knut", "Mimir", "Narvi", "Vidar", "Wulfgar", "Draven", "Garret", 
    "Ismael", "Orpheus", "Phocas", "Raziel", "Urbanus", "Wyrm", "Xathos", "Astoran", 
    "Cassian", "Doran", "Elam", "Joram", "Kaleb", "Lazarus", "Nathanael", "Obadiah", 
    "Phinehas", "Quintas", "Raphael", "Samson", "Thaddeus", "Uriel", "Zadkiel", "Albus", 
    "Arrian", "Barachiel", "Caeden", "Elos", "Faustus", "Gallus", "Helion", "Idmon", 
    "Juston", "Kyros", "Leonas", "Nestor", "Orentius", "Pollux", "Quinten", "Rhodus", 
    "Tiberon", "Ulphas", "Valen", "Xantus", "Yulian", "Zale", "Arvid", "Corin", "Eirik", 
    "Finn", "Geir", "Halvar", "Kjell", "Mord", "Njal", "Orin", "Siggeir", "Ulfric", 
    "Wulfric", "Yngvar", "Zephyr", "Cyprian", "Falen", "Hesiod", "Isidor", "Korbinian", 
    "Lucent", "Malphas", "Nox", "Oberon", "Phlegyas", "Quillon", "Rafe"
]
LAST_NAMES = [
    "Vane", "Vorne", "Marek", "Draken", "Thorne", "Tigris", "Stross", "Nyx", "Sevatar", 
    "Darko", "Max", "Kahl", "Cass", "Loken", "Torgaddon", "Qruze", "Tarvitz", "Voron", 
    "Hel", "Polux", "Rann", "Sanguis", "Flesh", "Night", "Haul", "Skraivok", "Sage", 
    "Valcoran", "Flay", "Bleak", "Sahaal", "Acerbus", "Angel", "Death", "Iron", "Omegon", 
    "Drake", "Lion", "Sigillite", "Constantin", "Endymion", "Coros", "Dominion", "Arkhan", 
    "Sulymanya", "Euphrati", "Kyril", "Mersadie", "Maggard", "Ullis", "Lufgt", "Asterion", 
    "Aikos", "Carab", "Porthos", "Adept", "T'kar", "Maat", "Pyrae", "Bale", "Amon", "Ahzek", 
    "Swords", "Master", "Kalliston", "Revuel", "Abaddon", "Kibre", "Relly", "Ekaddon", 
    "Sedirae", "Korda", "Targost", "Tybalt", "Danath", "Warsmith", "Breaker", "Falk", 
    "Vull", "Eras", "Dreygur", "Sharrowkyn", "Wayland", "Shadrak", "Thamatica", "Felix", 
    "Ptol", "Vitrian", "Talos", "Severus", "Cato", "Uriel", "Lysane", "Torias", "Antaro", 
    "Ortanius", "Varro", "Darnath", "Pedro", "Blackmane", "Slayer", "Storm", "Rock", 
    "Trickster", "Wolf", "Luis", "Donatos", "Guardian", "Redeemer", "Erasmus", "Gabriel", 
    "Merek", "High", "Mankind", "Hero", "Perpetual", "Persson", "Sureka", "Prytanis", 
    "Diviner", "Nemesor", "Vargard", "Illuminor", "Traveler", "Banner", "Ug", "Kaptain", 
    "Boss", "Ulthran", "Emissary", "Blade", "Zar", "Cry", "Shadow", "Burning", "Ra", 
    "Asdrubael", "Hesperax", "Decapitator", "Malys", "Vile", "Baron", "Duke", "Prince", 
    "Weaver", "Exile", "Kestrel", "Vos", "Helos", "Varl", "Moray", "Voss", "Wolfen", 
    "Krell", "Thrax", "Gaunt", "Sol", "Kaul", "Krane", "Valen", "Void", "Gallow", "Drax", 
    "Jago", "Sorn", "Bane", "Rhad", "Vex", "Nox", "Grey", "Krall", "Thrac", "Vorn", 
    "Mordant", "Karsos", "Varr", "Solari", "Mortis", "Grendel", "Khul", "Krios", "Malix", 
    "Valos", "Castor", "Skane", "Grix", "Krov", "Murne", "Klyne", "Dask", "Jast", "Zhor", 
    "Drask", "Hallow", "Kyre", "Malis", "Xylas", "Rone", "Vash", "Daxon", "Krost", "Hax", 
    "Valon", "Grend", "Skall", "Vexilla", "Han", "Iron-Eye", "Elurian", "Khanov", "Half-Hand", 
    "Shankaros", "Valerion", "Boru", "Twin-Fang", "Praetor", "Storm-Born", "Vahan", "Dax", 
    "Sky-Reaper", "Varuna", "Maximus", "Morn", "Red-Axe", "Kiran", "Cassian", "Blood-Mar", 
    "Gupta", "Herculios", "Stern", "Jala", "Ulpius", "Gnasher", "Deva", "Ghor", "Iron-Side", 
    "Muni", "Agrippa", "Batur", "Sunder", "Stilicho", "Temur", "Boneless", "Dharma", "Noyan", 
    "Sea-King", "Murari", "Drusus", "Orda", "Bare-Foot", "Prabu", "Galba", "Great", "Vidya", 
    "Vespasian", "Sultan", "Hardrada", "Sahasra", "Optimus", "Fork-Beard", "Aksha", "Aelius", 
    "Bukha", "Skalla", "Sena", "Pius", "Vel", "Helvius", "Hunter", "Julianus", "Gegeen", 
    "Silk-Beard", "Bajrang", "Niger", "Khor", "Tryggvason", "Albinus", "Erlingsson", "Sahadeva", 
    "Bassianus", "Broad-Shoulder", "Septimius", "Sigurdsson", "Partha", "Opellius", 
    "Hunchback", "Rao", "Antoninus", "Law-Mender", "Hari", "Varius", "Old", "Dana", 
    "Priest-Hater", "Good", "Ananta", "Antonius", "Quiet", "Madhav", "Gille", "Caelius", 
    "Crusader", "Sarva", "Arab", "Para", "Messius", "Haraldsson", "Hrid", "Gallus", "Taishi", 
    "Magnusson", "Pandu", "Aemilius", "Mouth", "Publius", "Licinius", "Sigurd", "Dhar", 
    "Gothicus", "Magnus", "Haakon", "Acharya", "Lucius", "Bolud", "Ish", "Oldenburg", 
    "Uttam", "Holstein", "Bhara", "Jasagtu", "Vasa", "Sechen", "Loka", "Palatinate", 
    "Rupa", "Valerius", "Bernadotte", "Natha", "Herculius", "Glumm", "Chlorus", "Bluetooth", 
    "Nandan", "Estridsson", "Rhayne", "Sakai", "Al-Fayed", "Ziad", "Wei", "Volos", "Drusk", 
    "Iron-Soul", "Prax", "Tylo", "Blood-Eye", "Swift-Strike", "Shadow-Walker", "Iron-Bound", 
    "Frost-Giant", "Storm-Herald", "Void-Stalker", "Flame-Bearer", "Stone-Crusher", 
    "Sky-Rage", "Shield-Breaker", "Doom-Bringer", "Star-Strider", "Ghost-Reaper", "Fang-Lord", 
    "Bolt-Slinger", "Light-Warder", "Grim-Vein", "Talon-King", "Steel-Shaper", "Wyrm-Slayer", 
    "Moon-Disciple", "Sun-Priest", "Oath-Keeper", "War-Born", "Rune-Caster", "Deep-Delver", 
    "Ash-Walker", "Ember-Fist", "Gold-Clad", "Silver-Tongue", "Copper-Skin", "Lead-Foot", 
    "Tin-Man", "Zinc-Eye", "Nickel-Heart", "Cobalt-Soul", "Chrome-Fist", "Titan-Skull", 
    "Adamant-Spine", "Quartz-Mind", "Flint-Shard", "Granite-Core", "Basalt-Base", "Obsidian-Edge", 
    "Marble-Brow", "Shale-Skin", "Slate-Eye", "Pumice-Bone", "Magma-Vein", "Plasma-Breath", 
    "Laser-Sight", "Sonic-Cry", "Kinetic-Force", "Thermal-Grip", "Gravity-Well", "Fusion-Core", 
    "Fission-Blade", "Proton-Pulse", "Neutron-Star", "Electron-Cloud", "Quark-Striker", 
    "Lepton-Leaper", "Muon-Master", "Gluon-Grip", "Boson-Blast", "Photon-Flash", "Graviton-Pull", 
    "Higgs-Hold", "Meson-Might", "Baryon-Bash", "Hadron-Hit", "Fermion-Field", "Scalar-Scale", 
    "Vector-Vane", "Tensor-Touch", "Matrix-Mind", "Lattice-Lord", "Crystal-King", "Polymer-Prince", 
    "Monomer-Man", "Isomer-Ion", "Isotope-Iron", "Allotrope-Ace", "Catalyst-Commander", 
    "Enzyme-Edge", "Substrate-Soul", "Reagent-Rage", "Product-Point", "Reactant-Ray", 
    "Solvent-Strike", "Solute-Slash", "Colloid-Cloud", "Aerosol-Aim", "Emulsion-End", 
    "Suspension-Sword", "Mixture-Mace", "Compound-Crush", "Element-Elder", "Atom-Axe", 
    "Molecule-Maul", "Particle-Pike", "Wave-Warp", "Frequency-Fail", "Amplitude-Arm", 
    "Period-Point", "Cycle-Cutter", "Hertz-Hammer", "Watt-Warrior", "Joule-Jolt", 
    "Volt", "Vanguard", "Ampere-Archer", "Ohm-Oracle", "Farad-Fighter", "Henry-Hero", 
    "Tesla-Titan", "Weber-Wolf", "Lumen-Knight", "Candela-Captain", "Mol-Master", 
    "Kelvin-King", "Pascal-Priest", "Newton-Noble", "Gray-Guard", "Sievert-Squire", 
    "Becquerel-Baron", "Curie-Count", "Roentgen-Ruler", "Fermi-Friend", "Bohr-Brother", 
    "Dirac-Duke", "Pauli-Prince", "Schrodinger-Saint", "Heisenberg-Head", "Einstein-Earl", 
    "Newton-Nomad", "Galileo-Ghost", "Kepler-Kid", "Copernicus-Commander", "Ptolemy-Patrol", 
    "Aristotle-Aide", "Plato-Pilot", "Socrates-Scout", "Homer-Hunter", "Virgil-Vigil", 
    "Dante-Devout", "Milton-Master", "Shakespeare-Shield", "Goethe-Guard", "Schiller-Striker", 
    "Byron-Blade", "Keats-King", "Shelley-Shadow", "Wordsworth-Warden", "Coleridge-Caller", 
    "Tennyson-Tall", "Browning-Bold", "Yeats-Young", "Eliot-Elder", "Pound-Pierce", "Auden-Ace", 
    "Frost-Free", "Stevens-Stern", "Williams-Wild", "Moore-Main", "Bishop-Bright", "Lowell-Long", 
    "Plath-Pale", "Hughes-Hard", "Heaney-High", "Walcott-Wide", "Neruda-Near", "Borges-Bound", 
    "Paz-Pure", "Lorca-Light", "Machado-Mark", "Jimenez-Just", "Darío-Deep", "Martí-Main", 
    "Mistral-Mild", "Vallejo-Vast", "Guillén-Great", "Cardenal-Clear", "Dalton-Dark", 
    "Roque-Red", "Benedetti-Blue", "Galeano-Green", "Cortázar-Cold", "Fuentes-Fast", 
    "Rulfo-Rough", "Paz-Point", "Vargas-Vane", "Marías-Moon", "Bolaño-Bold", "Wolf-Eye", 
    "Rime", "Gloom", "Ash", "Flint", "Quartz", "Shale", "Slate", "Pyre", "Cinder", "Embers", 
    "Frost", "Glaze", "Hail", "Sleat", "Drift", "Ridge", "Peak", "Crag", "Tor", "Cliff", 
    "Bluff", "Gorge", "Chasm", "Rift", "Trench", "Abyss", "Null", "Zero", "Naught", "Blank", 
    "Hollow", "Cave", "Grot", "Mine", "Shaft", "Pit", "Well", "Sink", "Drain", "Leak", 
    "Flow", "Surge", "Tide", "Wave", "Rip", "Swell", "Foam", "Spray", "Mist", "Fog", 
    "Haze", "Cloud", "Bolt", "Flash", "Spark", "Flare", "Beam", "Ray", "Glow", "Dim", 
    "Dark", "Murk", "Dusk", "Dawn", "Noon", "Day", "Night", "Eve", "Morn", "Spring", 
    "Fall", "Winter", "Summer", "Season", "Year", "Month", "Week", "Hour", "Minute", 
    "Second", "Instant", "Epoch", "Age", "Era", "Time", "Space", "Realm", "Zone", "Area", 
    "Spot", "Place", "Site", "Point", "Mark", "Sign", "Trace", "Hint", "Breath", "Pulse", 
    "Beat", "Thump", "Drum", "Chant", "Song", "Verse", "Rhyme", "Word", "Text", "Page", 
    "Book", "Tome", "Scroll", "Script", "Note", "File", "Data", "Bit", "Byte", "Code", 
    "Key", "Lock", "Bar", "Gate", "Wall", "Fence", "Post", "Pillar", "Arch", 
    "Dome", "Roof", "Floor", "Step", "Path", "Road", "Way", "Street", "Lane", "Track", 
    "Trail", "Route", "Map", "Chart", "Compass", "Star", "Sun", "Moon", "Orb", "Sphere", 
    "Cube", "Block", "Slab", "Tile", "Brick", "Stone", "Rock", "Pebble", "Sand", "Dust", 
    "Ash", "Smoke", "Steam", "Vapor", "Rain", "Snow", "Ice", "Fire", "Heat", "Cold", "Warm", 
    "Cool", "Dry", "Wet", "Damp", "Soft", "Hard", "Loud", "Quiet", "Fast", "Slow", "High", 
    "Low", "Near", "Far", "Big", "Small", "Wide", "Thin", "Thick", "Round", "Flat", 
    "Sharp", "Blunt", "Rough", "Smooth", "Grave-Walker", "Zenith", "Vexor", "Quake", 
    "Red-Hand", "Storm-Caller", "Cipher", "Entropy", "Firmware", "Circuit", "Sensor", 
    "Relay", "Switch", "Router", "Bridge", "Hub", "Cable", "Fiber", "Bandwidth", 
    "Protocol", "Schema", "Query", "Index", "Cache", "Storage", "Memory", "Sector", 
    "Cylinder", "Header", "Footer", "Payload", "Metadata", "Tag", "Label", "Macro", 
    "Micro", "Nano", "Giga", "Tera", "Peta", "Exa", "Zetta", "Yotta", "Nibble", "Long", 
    "Short", "Shift", "Rotate", "Push", "Pop", "Peek", "Poke", "Load", "Store", "Jump", 
    "Solder", "Flux", "Resin", "Alloy", "Silicon", "Wafer", "Die", "Fab", "Core", "Cycle", 
    "Clock", "Hertz", "Volt", "Watt", "Amp", "Ohm", "Farad", "Henry", "Tesla", "Weber", 
    "Lumen", "Lux", "Decibel", "Kelvin", "Pascal", "Joule", "Newton", "Mole", "Candela", 
    "Radian", "Steradian", "Degree", "Decade", "Century", "Millennium", "Phase", "Series", 
    "Parallel", "Mar", "Vahl", "Crow", "Bane", "Gloom", "Shadow-Step", "Bold", "Vulkan", 
    "Grime", "Burne", "Pious", "Kroll", "Truth-Bearer", "Rex", "Graves", "Halk", "Raine", 
    "Iron-Bound", "Wyrm-Slayer", "Blood-Eye", "Storm-Born", "Sky-Reaver", "Fell-Blade", 
    "Ghost-Walker", "Red-Beard", "Stone-Fist", "Ash-Walker", "Ghast", "Cain", "Shade", 
    "Night-Stalker", "Mord", "Dawn", "Hope", "Blight", "Vor", "Castor", "Valer", "Quintus", 
    "Grix", "Dax", "Castus", "Hel", "Red-Axe", "Iron-Will", "Storm-Eye", "Blood", "Fell-Hand", 
    "Frost-Vein", "Bone-Breaker", "Sky-Strider", "Earth-Render", "Iron-Hide", "Ghost", 
    "Ash-Soul", "Stone-Heart", "Fell", "Void-Walker", "Shield-Bane", "Wyrm-Bane", "Black", 
    "Vahn", "Dark", "Grave", "Crow-Eye"
]

PSY_PROFILES = [
    "Fatalistic (Industrial)", "Stoic (The Anchor)", "Dissociated (Hollow Risk)", "Aggressive (Furnace)", 
    "Methodical (Cogitator)", "Cold (Void-Hardened)", "Zealous (Chain-Bound)", "Pragmatic (Survivalist)"
]

# Ranks & Tiers
TIERS = {
    "Neophyte": 0,
    "Battle Brother": 1,
    "Battle Brother (Runt)": 1,
    "Artificer Brother": 2,
    "Iron Calculus": 3,
    "Bond-Keeper": 2,
    "Veteran Battle Brother": 3,
    "Sergeant": 3,
    "Sergeant (Runt)": 3,
    "Apothecary": 3,
    "Null-Warden": 3,
    "Veteran Sergeant": 4,
    "Lieutenant": 4,
    "Chaplain": 4,
    "Techmarine": 4,
    "Standard Bearer": 4,
    "Dreadnought": 5, 
    "Warden-General": 5,
    "Captain": 5,
    "Chapter Master": 6
}

# Specialist Career Paths (Strict)
SPECIALIST_PATHS = {
    "Chapter Master": ["Captain"],
    "Captain": ["Lieutenant"],
    "Lieutenant": ["Veteran Sergeant", "Veteran Battle Brother"],
    "Chaplain": ["Battle Brother", "Sergeant", "Veteran Battle Brother"],
    "Techmarine": ["Artificer Brother"],
    "Standard Bearer": ["Veteran Battle Brother", "Veteran Sergeant"],
    "Dreadnought": ["Veteran Battle Brother", "Veteran Sergeant"],
    "Veteran Sergeant": ["Sergeant"],
    "Sergeant": ["Battle Brother"],
    "Sergeant (Runt)": ["Battle Brother (Runt)"],
    "Apothecary": ["Battle Brother"],
    "Null-Warden": ["Battle Brother"],
    "Artificer Brother": ["Battle Brother"],
    "Bond-Keeper": ["Battle Brother"],
    "Veteran Battle Brother": ["Battle Brother"],
    "Battle Brother": ["Neophyte"],
    "Battle Brother (Runt)": ["Battle Brother"]
}

# Dreadnought Priority Assignment (Grid Coordinates: Company, Squad Index)
# Note: Standard Companies: Squad 2 = 1st Squad, Squad 4 = 3rd Squad.
# Note: 1st Company: Squad 7 = 1st Squad, Squad 9 = 3rd Squad.
DREADNOUGHT_PRIORITY = [
    (5, 3), (5, 4), (5, 5), (5, 6), # 5th Chapter: Old Squads 4-7 -> New Squads 3-6
    (1, 1), (2, 3), (3, 3),         # 1st (Sq 1), 2nd & 3rd (Old Sq 4 -> New Sq 3)
    (6, 1), (7, 1), (8, 1),         # 6th, 7th, 8th: Old Sq 2 -> New Sq 1
    (9, 3), (9, 4)                  # 9th Chapter: Old Sq 4-5 -> New Sq 3-4
]

DREADNOUGHT_NAMES = [
    "Haldor Iron-Casket",
    "Krell Pillar-Stay",
    "Vorn Static-Weight",
    "Moriar Deep-Anchor",
    "Thrax Vault-Warden",
    "Gorr Rust-Casing",
    "Draven Sump-Bedded",
    "Kaltos Core-Housed",
    "Brakos Silent-Gait",
    "Xeron Iron-Vessel",
    "Valerius Plinth-Walker"
]

# RELIC CONFIGURATION
# Format: {"id": "Rxxxx", "name": "Name", "type": "Type", "desc": "Description", "date": Year}
FOUND_RELICS = [

    {"id": "R0001", "name": "Sunder’s Whisper", "type": "Power Sword", "desc": "A heavy-bladed master-work gifted by the Storm Giants; its edge is tempered in geothermal vents.", "date": 650},
    {"id": "R0002", "name": "The Verdigris Aegis", "type": "Storm Shield", "desc": "Crafted from a hull-plate of the 'Gilded Lash'; it bears a permanent teal chemical patina.", "date": 725},
    {"id": "R0003", "name": "Iron-Sire's Breath", "type": "Heavy Flamer", "desc": "Recovered from the 'Shield of Terra' crash site; utilizes high-pressure mining fuel.", "date": 810},
    {"id": "R0004", "name": "The Lamented Link", "type": "Iron Halo", "desc": "A soot-stained generator gifted by the Lamenters; its field hums with a mournful frequency.", "date": 905},
    {"id": "R0005", "name": "Phoros’s Debt", "type": "Bolt Pistol", "desc": "Issued by Malakim Phoros; unpainted steel that never rusts despite Noxian humidity.", "date": 655},
    {"id": "R0006", "name": "The Scouring Drill", "type": "Chainfist", "desc": "Industrial boarding tool; teeth forged from recycled mining-rig grinders.", "date": 700},
    {"id": "R0007", "name": "Anchor-Bolt", "type": "Siege Mantlet", "desc": "Repurposed from an 'Anchor-Pillbox' hatch; establishes a mobile Ring of Steel.", "date": 820},
    {"id": "R0008", "name": "Vrox’s Patience", "type": "Stalker Bolter", "desc": "Precision rifle calibrated to pierce the thickest smog of the Verdigris Deep.", "date": 950},
    {"id": "R0009", "name": "The Thresher’s Coil", "type": "Power Maul", "desc": "Gifted by the Executioners; the head is a repurposed industrial crushing gear.", "date": 920},
    {"id": "R0010", "name": "Cinder-Plate Segment", "type": "Relic Pauldron", "desc": "A piece of High Paladin Garrick's original armor; a physical tether to the Chapter's birth.", "date": 970},
    {"id": "R0011", "name": "Slag-Stalker", "type": "Combat Knife", "desc": "Forged from the first batch of steel smelted in the Iron Forest capital.", "date": 640},
    {"id": "R0012", "name": "The Sovereign Link", "type": "Chainsword", "desc": "Features oversized obsidian teeth; gifted by the Doom Eagles survivors during the founding.", "date": 638},
    {"id": "R0013", "name": "Noxian Hearth-Fire", "type": "Plasma Pistol", "desc": "Its containment coil glows with the same teal hue as the Noxian auroras.", "date": 780},
    {"id": "R0014", "name": "The Pillar of Iron", "type": "Thunder Hammer", "desc": "The head is a solid block of high-density ore from the Nox-Hemisphere mines.", "date": 845},
    {"id": "R0015", "name": "Soot-Walker’s Plate", "type": "Artificer Armor", "desc": "Reinforced with slag-glass; provides superior protection against caustic environments.", "date": 712},
    {"id": "R0016", "name": "The Unbroken Cog", "type": "Refractor Field", "desc": "A gift from the Tech-Magi of Nox for protecting the Foundry Cities.", "date": 888},
    {"id": "R0017", "name": "Garrick’s Resolve", "type": "Storm Bolter", "desc": "Heavy-duty variant with a reinforced carry-handle for one-handed suppression.", "date": 755},
    {"id": "R0018", "name": "The Deep-Vigil", "type": "Auspex", "desc": "Modified to detect bio-signs through kilometers of industrial sludge.", "date": 690},
    {"id": "R0019", "name": "Mantle-Breaker", "type": "Meltagun", "desc": "Originally a thermal mining drill; sanctified for the destruction of traitor armor.", "date": 805},
    {"id": "R0020", "name": "The Bonded Blade", "type": "Power Sword", "desc": "Its hilt is wrapped in the flight suit of a fallen Noxian PDF pilot.", "date": 912},
    {"id": "R0021", "name": "Titan’s Tooth", "type": "Chainfist", "desc": "Recovered from a downed Warhound Titan; repurposed for Astartes-scale boarding.", "date": 730},
    {"id": "R0022", "name": "The Iron Rain Seal", "type": "Crux Terminatus", "desc": "Contains a shard of the first drop-pod to strike Terminus Nox.", "date": 639},
    {"id": "R0023", "name": "Noxian Storm-Caller", "type": "Boltgun", "desc": "Features a customized muzzle brake that mimics the roar of Terminator Line gales.", "date": 860},
    {"id": "R0024", "name": "The Tectonic Plate", "type": "Storm Shield", "desc": "Engraved with the map of the Ring of Steel; weighted for high-gravity combat.", "date": 895},
    {"id": "R0025", "name": "Ash-Eater", "type": "Heavy Bolter", "desc": "Equipped with specialized filters to prevent jamming in volcanic fallout zones.", "date": 740},
    {"id": "R0026", "name": "The Silent Foundry", "type": "Power Axe", "desc": "Forged in total silence during the Siege of the Magma-Gates.", "date": 815},
    {"id": "R0027", "name": "Link-Breaker’s End", "type": "Combat Knife", "desc": "Taken from a defeated Chaos Lord; purified and reforged into a tool of justice.", "date": 930},
    {"id": "R0028", "name": "The Sentinel’s Eye", "type": "Targeting Array", "desc": "Salvaged from an ancient Watch-Keep; grants superior low-light accuracy.", "date": 775},
    {"id": "R0029", "name": "The Heavy Toll", "type": "Power Maul", "desc": "When struck, it emits a low-frequency chime that steadies nearby allies.", "date": 850},
    {"id": "R0030", "name": "Rust-Bane", "type": "Bolter", "desc": "Coated in a rare frictionless polymer from the Lux-Hemisphere laboratories.", "date": 685},
    {"id": "R0031", "name": "The Vault-Key", "type": "Power Sword", "desc": "A thin, needle-like blade used for precision strikes in cramped hive-corridors.", "date": 760},
    {"id": "R0032", "name": "Atmospheric Anchor", "type": "Jump Pack", "desc": "Overpowered thrusters designed to function in Nox's 1.24 bar pressure.", "date": 940},
    {"id": "R0033", "name": "The Forgemaster’s Gift", "type": "Plasma Gun", "desc": "Features an external cooling rig designed by Forge-Master Xavor.", "date": 705},
    {"id": "R0034", "name": "Sump-Stalker's Hide", "type": "Camo-Cloak", "desc": "Treated with chemical-resistant resins from the Verdigris Deep.", "date": 825},
    {"id": "R0035", "name": "The Gilded Claw", "type": "Lightning Claw", "desc": "Salvaged from the 'Gilded Lash'; its blades are gold-etched steel.", "date": 767},
    {"id": "R0036", "name": "Void-Steel Buckler", "type": "Combat Shield", "desc": "Forged from the airlock door of the 'Iron Curtain' escort vessel.", "date": 835},
    {"id": "R0037", "name": "The Terminator Line", "type": "Chainsword", "desc": "The blade teeth rotate in alternating directions to maximize shredding.", "date": 960},
    {"id": "R0038", "name": "Smog-Piercer", "type": "Flamer", "desc": "Uses a concentrated oxygen-mix to burn even in oxygen-depleted sumps.", "date": 670},
    {"id": "R0039", "name": "The Iron Pulse", "type": "Grav-Pistol", "desc": "Utilizes the enhanced magnetic field of Nox to amplify its crushing force.", "date": 980},
    {"id": "R0040", "name": "Hearth-Guardian", "type": "Bolter", "desc": "Given to a brother who successfully defended a village for forty nights.", "date": 875},
    {"id": "R0041", "name": "The Piston-Blade", "type": "Combat Knife", "desc": "Features a spring-loaded hilt for increased armor-piercing thrusts.", "date": 720},
    {"id": "R0042", "name": "Cobalt-Shunt", "type": "Refractor Field", "desc": "Salvaged from the 'Cobalt Shield'; glows with a faint blue light.", "date": 840},
    {"id": "R0043", "name": "The Grinding Wheel", "type": "Power Axe", "desc": "Its circular blade spins at high RPM, doubling as a breach tool.", "date": 790},
    {"id": "R0044", "name": "Laden-Hand Token", "type": "Relic Pendant", "desc": "A piece of the Flagship's first anchor chain; brings stability to the soul.", "date": 661},
    {"id": "R0045", "name": "The Steel-Rain Spike", "type": "Lightning Claw", "desc": "A single, oversized claw meant for piercing heavy hull-plating.", "date": 645},
    {"id": "R0046", "name": "Noxian Night-Eye", "type": "Helmet Sensor", "desc": "Calibrated for the absolute darkness of the Nox-Hemisphere.", "date": 915},
    {"id": "R0047", "name": "The Chain-Link Bolt", "type": "Crossbow-Bolter", "desc": "A specialized silent weapon for covert operations in the Iron Forest.", "date": 735},
    {"id": "R0048", "name": "Mortal-Bond Plate", "type": "Chestpiece", "desc": "Includes a small compartment for a scroll containing the names of fallen Serfs.", "date": 890},
    {"id": "R0049", "name": "The Forge-Hammer", "type": "Thunder Hammer", "desc": "A functional tool turned weapon; used in the construction of the Ring of Steel.", "date": 800},
    {"id": "R0050", "name": "The Final Anchor", "type": "Storm Shield", "desc": "An impossibly heavy shield that requires a secondary power-assist to lift.", "date": 999},
    {"id": "R9001", "name": "Crust-Piercer", "type": "Relic Champion's Blade", "desc": "The ancestral blade of the Lost Trinity, claimed by Garrick from the cooling hands of the final Chapter Master at The Death of The Cinder-Commander; it is the master-key of the Chain Breakers' authority.", "date": 634},
    {"id": "R9002", "name": "Tempest Teeth", "type": "Master-Crafted Storm Bolter", "desc": "Salvaged from the 'Tempest Anvil' hull; the barrel rifling has been aggressively re-cut using diamond-tipped mining drills, causing the weapon to fire with a jagged, grinding roar that mimics the sound of a collapsing tunnel.", "date": 772},
    {"id": "R9003", "name": "The Bubble", "type": "Power Armor", "desc": "A master-crafted suit of Mark VIII 'Errant' plate, the pinnacle of 576.M41 protection; heavily modified with reinforced seals and high-density stabilizers to endure the crushing gravity of Nox.", "date": 775}
] 
# Format: {"id": "Rxxxx", "name": "Name", "type": "Type", "desc": "Description"} (Date assigned dynamically)
DEATHWATCH_RELICS = [

    {"id": "R1001", "name": "The Static Blade", "type": "Power Sword", "desc": "Inlaid with Noctilith; disrupts xenos psychic shielding upon contact."},
    {"id": "R1002", "name": "Blackstone Shard", "type": "Combat Knife", "desc": "Carved from deep-core Blackstone; its cold logic grounds the wielder's mind."},
    {"id": "R1003", "name": "The Slaugth-Bane", "type": "Combi-Melta", "desc": "Features thermal baffles designed to incinerate regenerative xenos tissue."},
    {"id": "R1004", "name": "Xenos-Hewer", "type": "Heavy Chainsword", "desc": "A twin-motored blade designed to shear through Tyranid carapace."},
    {"id": "R1005", "name": "The Void-Scanner", "type": "Auspex", "desc": "Equipped with compliance-shunts to safely track Necron dimensional shifts."},
    {"id": "R1006", "name": "The Magnetic Hook", "type": "Grappling Launcher", "desc": "Salvaged from a Halo Margin hulk; used for high-gravity boarding actions."},
    {"id": "R1007", "name": "Watch-Commander’s Gaze", "type": "Boltgun", "desc": "Equipped with a multi-spectral xenos-tracking scope."},
    {"id": "R1008", "name": "The Piston-Fist", "type": "Power Fist", "desc": "Hydraulic-boosted gauntlet recovered from a Dead World; mimic's Noxian tectonic force."},
    {"id": "R1009", "name": "Noctis-Shroud", "type": "Camo-Cloak", "desc": "Teal-dyed fibers woven with xenos light-bending technology."},
    {"id": "R1010", "name": "The Unbroken Shell", "type": "Artificer Plate", "desc": "Mark XIV plate reinforced with Deathwatch-grade Ceramite for extreme density."},
    {"id": "R1011", "name": "Bio-Eater", "type": "Heavy Flamer", "desc": "Modified to fire a specialized neuro-toxic promethium blend for Orks."},
    {"id": "R1012", "name": "The Ghost-Anchor", "type": "Storm Shield", "desc": "Flickers in and out of the material plane to deflect incoming fire."},
    {"id": "R1013", "name": "Aeldari-Hunter", "type": "Stalker Bolter", "desc": "Uses sound-dampened rounds to eliminate high-priority targets silently."},
    {"id": "R1014", "name": "The Hive-Piercer", "type": "Meltagun", "desc": "A short-barreled variant optimized for clearing cramped Tyranid tunnels."},
    {"id": "R1015", "name": "Ossified Blade", "type": "Chainsword", "desc": "Teeth made from hardened xenos bone; specifically effective against unarmored targets."},
    {"id": "R1016", "name": "The Ordo Shield", "type": "Combat Shield", "desc": "Bearing the Inquisition's I; its field is tuned to repel warp-lightning."},
    {"id": "R1017", "name": "Phase-Breaker", "type": "Power Maul", "desc": "Designed to strike enemies even if they are partially out of phase."},
    {"id": "R1018", "name": "The Long Vigil Bolt", "type": "Bolt Pistol", "desc": "Fires specialized 'Kraken' penetrator rounds as its standard loadout."},
    {"id": "R1019", "name": "Xenos-Hide Cloak", "type": "Relic Cape", "desc": "Treated skin of a massive beast; provides protection against acidic spit."},
    {"id": "R1020", "name": "The Gravity-Well", "type": "Grav-Gun", "desc": "Modified to pin down fast-moving Aeldari raiders for the final blow."},
    {"id": "R1021", "name": "The Talon of Talasa", "type": "Lightning Claw", "desc": "A gift from the Deathwatch Training Grounds at Talasa Prime."},
    {"id": "R1022", "name": "Void-Stalker Helm", "type": "Helmet", "desc": "Equipped with a 360-degree sensory suite for zero-G combat."},
    {"id": "R1023", "name": "The Corrosive Edge", "type": "Combat Knife", "desc": "The blade constantly weeps a mild acid that dissolves xenos armor plates."},
    {"id": "R1024", "name": "Anchor-Keep Protocol", "type": "Signum", "desc": "Coordinates orbital strikes from Deathwatch vessels with extreme precision."},
    {"id": "R1025", "name": "The Eternal Link", "type": "Iron Halo", "desc": "The central icon is replaced with a silver-etched chain link, symbolizing the vigil."}

]

# STORY CHARACTERS
# Define specific characters you want to exist at the end of the simulation.
# The script will find a marine matching the Rank/Company/Squad and rename them.
# Note: Officers (Captains, Chaplains, etc.) are typically in Squad 0 (Command Squad).
STORY_CHARACTERS = [
    {
        "Name": "Korris Asher", 
        "Cognomen": "Doctore", 
        "Rank": "Chaplain", 
        "Company": 10, 
        "Squad": 1  
    }
    ,{
        "Name": "Oenomaus Batiatus", 
        "Cognomen": "Venato", 
        "Rank": "Chaplain", 
        "Company": 10, 
        "Squad": 2  
    }
    ,{
        "Name": "Aris Thorne", 
        "Cognomen": "", 
        "Rank": "Bond-Keeper", 
        "Company": 6, 
        "Squad": 2 
    }
]

# HUMAN NOXIAN PDF OFFICERS CONFIGURATION
HUMAN_OFFICES = {
    "High Marshal of Nox (Human Commander)": {"Rank": "General", "MinAge": 65, "MaxAge": 110, "StartYear": 638},
    "Master of the Fleet (Lord Admiral)": {"Rank": "Admiral", "MinAge": 70, "MaxAge": 120, "Linked": "Shipmaster: The Arrow of Terminus", "StartYear": 638},
    "Shipmaster: The Laden Hand (Flagship)": {"Rank": "High-Commodore", "MinAge": 55, "MaxAge": 80, "StartYear": 758},
    "Shipmaster: The Mortal Link": {"Rank": "Commodore", "MinAge": 50, "MaxAge": 75, "StartYear": 728},
    "Shipmaster: The Unbroken Link": {"Rank": "Ship-Master", "MinAge": 35, "MaxAge": 55, "StartYear": 744},
    "Shipmaster: The Hammer of Emancipation": {"Rank": "Ship-Master", "MinAge": 35, "MaxAge": 55, "StartYear": 733},
    "Shipmaster: The Lantern of Nox": {"Rank": "Ship-Master", "MinAge": 35, "MaxAge": 55, "StartYear": 758},
    "Shipmaster: The Furnace of Youth": {"Rank": "Ship-Master", "MinAge": 45, "MaxAge": 65, "StartYear": 650},
    "Shipmaster: The Arrow of Terminus": {"Rank": "Admiral", "MinAge": 70, "MaxAge": 120, "IsLinked": True, "StartYear": 661},
    "Shipmaster: The Iron Curtain": {"Rank": "Ship-Master", "MinAge": 30, "MaxAge": 45, "StartYear": 661},
    "Shipmaster: The Soot Carrier": {"Rank": "Ship-Master", "MinAge": 30, "MaxAge": 45, "StartYear": 661},
    "Shipmaster: The Screaming Piston": {"Rank": "Ship-Master", "MinAge": 30, "MaxAge": 45, "StartYear": 661},
}