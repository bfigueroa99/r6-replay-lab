"""Constantes del formato Dissect (.rec) de Rainbow Six Siege.

IDs portados desde el trabajo de reverse engineering de r6-dissect (redraskal, MIT).
Los lados (ataque/defensa) de operadores nuevos se infieren en runtime si faltan aqui.
"""

from __future__ import annotations

# --- versiones de codigo del juego -------------------------------------------------
CODE_VERSIONS = {
    "Y7S1": 6884476,
    "Y7S2": 7040830,
    "Y7S4": 7338571,
    "Y8S1": 7408213,
    "Y8S2": 7601998,
    "Y8S3": 7762708,
    "Y8S4": 7921866,
    "Y9S1": 8111697,
    "Y9S1Update3": 8211379,
    "Y9S2": 8303162,
    "Y9S3": 8506016,
    "Y9S4": 8673114,
    "Y10S1": 8825661,
    "Y10S1_1": 8863180,
    "Y10S1_2": 8882422,
    "Y10S1_3": 8908078,
    "Y10S2_1": 9034019,
    "Y10S2_1_1": 9058361,
    "Y10S2_2": 9077538,
    "Y10S2_3": 9098584,
    "Y10S2_4": 9124272,
    "Y10S2_5": 9158643,
    "Y10S3": 9199003,
    "Y10S3_1": 9211553,
}

Y7S1 = 6884476
Y7S2 = 7040830
Y7S4 = 7338571
Y8S1 = 7408213
Y8S2 = 7601998
Y8S3 = 7762708
Y8S4 = 7921866
Y9S1 = 8111697
Y9S1_UPDATE3 = 8211379
Y9S2 = 8303162
Y9S3 = 8506016
Y9S4 = 8673114
Y10S1 = 8825661

# --- match types ------------------------------------------------------------------
MATCH_TYPES = {
    1: "QuickMatch",
    2: "Ranked",
    3: "CustomGameLocal",
    4: "CustomGameOnline",
    8: "Standard",
    9: "Unranked",
}

# --- game modes -------------------------------------------------------------------
GAME_MODES = {
    327933806: "Bomb",
    1983085217: "SecureArea",
    2838806006: "Hostage",
    400168582901: "QuickMatchBomb",
}
BOMB = 327933806

# --- mapas ------------------------------------------------------------------------
# id -> (identificador interno, nombre legible)
MAPS = {
    837214085: ("ClubHouse", "Club House"),
    1378191338: ("KafeDostoyevsky", "Kafe Dostoyevsky"),
    1460220617: ("Kanal", "Kanal"),
    1767965020: ("Yacht", "Yacht"),
    2609218856: ("PresidentialPlane", "Presidential Plane"),
    2609221242: ("ConsulateY7", "Consulate"),
    2697268122: ("BartlettU", "Bartlett U."),
    42090092951: ("Coastline", "Coastline"),
    53627213396: ("Tower", "Tower"),
    88107330328: ("Villa", "Villa"),
    126196841359: ("Fortress", "Fortress"),
    127951053400: ("HerefordBase", "Hereford Base"),
    199824623654: ("ThemePark", "Theme Park"),
    231702797556: ("Oregon", "Oregon"),
    237873412352: ("House", "House"),
    259816839773: ("Chalet", "Chalet"),
    276279025182: ("Skyscraper", "Skyscraper"),
    305979357167: ("Border", "Border"),
    329867321446: ("Favela", "Favela"),
    355496559878: ("Bank", "Bank"),
    362605108559: ("Outback", "Outback"),
    365284490964: ("EmeraldPlains", "Emerald Plains"),
    270063334510: ("StadiumBravo", "Stadium (Bravo)"),
    378595635123: ("NighthavenLabs", "Nighthaven Labs"),
    379218689149: ("Consulate", "Consulate"),
    388073319671: ("Lair", "Lair"),
    405306299908: ("Stadium2020", "Stadium 2020"),
    413779563590: ("BankY10", "Bank"),
    407987100456: ("BorderY10", "Border"),
    407558616688: ("ChaletY10", "Chalet"),
    407193663917: ("ClubHouseY10", "Club House"),
    413845419788: ("KafeDostoyevskyY10", "Kafe Dostoyevsky"),
    417890697769: ("LairY10", "Lair"),
    418119057546: ("NighthavenLabsY10", "Nighthaven Labs"),
    418126004176: ("ConsulateY10", "Consulate"),
}

# IDs observados en replays mas nuevos que la tabla de arriba. Se identifican
# por los nombres de los sitios de bomba que trae el propio replay.
MAPS_EXTRA = {
    436375283234: ("CoastlineY11", "Coastline"),
}
MAPS.update(MAPS_EXTRA)


# --- operadores -------------------------------------------------------------------
OPERATORS = {
    359656345734: "Recruit",
    92270642682: "Castle",
    104189664704: "Aruni",
    161289666230: "Kaid",
    174977508820: "Mozzie",
    92270642708: "Pulse",
    104189664390: "Ace",
    92270642214: "Echo",
    378305069945: "Azami",
    391752120891: "Solis",
    92270644215: "Capitao",
    92270644189: "Zofia",
    92270644267: "Dokkaebi",
    104189662920: "Warden",
    92270644319: "Mira",
    92270642344: "Sledge",
    104189664273: "Melusi",
    92270642526: "Bandit",
    92270642188: "Valkyrie",
    92270644059: "Rook",
    92270641980: "Kapkan",
    291191151607: "Zero",
    104189664038: "Iana",
    92270642656: "Ash",
    92270642136: "Blackbeard",
    288200867444: "Osa",
    373711624351: "Thorn",
    92270642604: "Jager",
    104189663920: "Kali",
    92270642760: "Thermite",
    288200866821: "Brava",
    104189663607: "Amaru",
    92270642292: "Ying",
    92270642266: "Lesion",
    92270644007: "Doc",
    104189661861: "Lion",
    92270642032: "Fuze",
    92270642396: "Smoke",
    92270644293: "Vigil",
    92270642318: "Mute",
    104189663698: "Goyo",
    104189663803: "Wamai",
    92270644163: "Ela",
    92270644033: "Montagne",
    104189663024: "Nokk",
    104189662071: "Alibi",
    104189661965: "Finka",
    92270644241: "Caveira",
    161289666248: "Nomad",
    288200867351: "Thunderbird",
    384797789346: "Sens",
    92270642578: "IQ",
    92270642539: "Blitz",
    92270642240: "Hibana",
    104189662384: "Maverick",
    328397386974: "Flores",
    92270642474: "Buck",
    92270644111: "Twitch",
    174977508808: "Gridlock",
    92270642422: "Thatcher",
    92270642084: "Glaz",
    92270644345: "Jackal",
    374667788042: "Grim",
    291437347686: "Tachanka",
    104189664155: "Oryx",
    92270642500: "Frost",
    104189662175: "Maestro",
    104189662280: "Clash",
    288200867339: "Fenrir",
    395943091136: "Ram",
    288200867549: "Tubarao",
    374667787816: "Deimos",
    409899350463: "Striker",
    409899350403: "Sentry",
    386098331713: "Skopos",
    386098331923: "Rauora",
    374667787937: "Denari",
}
RECRUIT = 359656345734

ATTACK = "Attack"
DEFENSE = "Defense"

# Lado conocido por nombre de operador. Los que no esten aqui (operadores nuevos)
# se resuelven por mayoria dentro del equipo al parsear la ronda.
OPERATOR_SIDES = {
    "Castle": DEFENSE,
    "Aruni": DEFENSE,
    "Kaid": DEFENSE,
    "Mozzie": DEFENSE,
    "Pulse": DEFENSE,
    "Ace": ATTACK,
    "Echo": DEFENSE,
    "Azami": DEFENSE,
    "Solis": DEFENSE,
    "Capitao": ATTACK,
    "Zofia": ATTACK,
    "Dokkaebi": ATTACK,
    "Warden": DEFENSE,
    "Mira": DEFENSE,
    "Sledge": ATTACK,
    "Melusi": DEFENSE,
    "Bandit": DEFENSE,
    "Valkyrie": DEFENSE,
    "Rook": DEFENSE,
    "Kapkan": DEFENSE,
    "Zero": ATTACK,
    "Iana": ATTACK,
    "Ash": ATTACK,
    "Blackbeard": ATTACK,
    "Osa": ATTACK,
    "Thorn": DEFENSE,
    "Jager": DEFENSE,
    "Kali": ATTACK,
    "Thermite": ATTACK,
    "Brava": ATTACK,
    "Amaru": ATTACK,
    "Ying": ATTACK,
    "Lesion": DEFENSE,
    "Doc": DEFENSE,
    "Lion": ATTACK,
    "Fuze": ATTACK,
    "Smoke": DEFENSE,
    "Vigil": DEFENSE,
    "Mute": DEFENSE,
    "Goyo": DEFENSE,
    "Wamai": DEFENSE,
    "Ela": DEFENSE,
    "Montagne": ATTACK,
    "Nokk": ATTACK,
    "Alibi": DEFENSE,
    "Finka": ATTACK,
    "Caveira": DEFENSE,
    "Nomad": ATTACK,
    "Thunderbird": DEFENSE,
    "Sens": ATTACK,
    "IQ": ATTACK,
    "Blitz": ATTACK,
    "Hibana": ATTACK,
    "Maverick": ATTACK,
    "Flores": ATTACK,
    "Buck": ATTACK,
    "Twitch": ATTACK,
    "Gridlock": ATTACK,
    "Thatcher": ATTACK,
    "Glaz": ATTACK,
    "Jackal": ATTACK,
    "Grim": ATTACK,
    "Tachanka": DEFENSE,
    "Oryx": DEFENSE,
    "Frost": DEFENSE,
    "Maestro": DEFENSE,
    "Clash": DEFENSE,
    "Fenrir": DEFENSE,
    "Ram": ATTACK,
    "Tubarao": DEFENSE,
    "Deimos": ATTACK,
    "Striker": ATTACK,
    "Sentry": DEFENSE,
    "Skopos": DEFENSE,
    "Rauora": DEFENSE,
    "Denari": ATTACK,
}

# --- tipos de evento del match feedback -------------------------------------------
KILL = 0
DEATH = 1
DEFUSER_PLANT_START = 2
DEFUSER_PLANT_COMPLETE = 3
DEFUSER_DISABLE_START = 4
DEFUSER_DISABLE_COMPLETE = 5
LOCATE_OBJECTIVE = 6
OPERATOR_SWAP = 7
BATTLEYE = 8
PLAYER_LEAVE = 9
OTHER = 10

EVENT_NAMES = {
    0: "Kill",
    1: "Death",
    2: "DefuserPlantStart",
    3: "DefuserPlantComplete",
    4: "DefuserDisableStart",
    5: "DefuserDisableComplete",
    6: "LocateObjective",
    7: "OperatorSwap",
    8: "Battleye",
    9: "PlayerLeave",
    10: "Other",
}

# --- condiciones de victoria ------------------------------------------------------
KILLED_OPPONENTS = "KilledOpponents"
DISABLED_DEFUSER = "DisabledDefuser"
DEFUSED_BOMB = "DefusedBomb"
TIME = "Time"

