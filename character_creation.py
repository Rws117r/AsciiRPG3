import pygame
import random
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

# Import character data from main game
RACES = ["Dwarf", "Elf", "Goblin", "Halfling", "Half-Orc", "Human"]
CLASSES = ["Fighter", "Priest", "Thief", "Wizard"]
ALIGNMENTS = ["Lawful", "Chaotic", "Neutral"]

# Stat names and their descriptions
STATS = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]

STAT_DESCRIPTIONS = {
    "Strength": "Fight with a sword, bash open doors, swim. Important for fighters.",
    "Dexterity": "Shoot a bow, balance on a ledge, sneak silently, hide. Important for thieves.",
    "Constitution": "Hold your breath, resist poison, endure injury.",
    "Intelligence": "Cast wizard spells, decipher runes, learn new skills. Important for wizards.",
    "Wisdom": "Cast priest spells, detect the hidden, recognize omens. Important for priests.",
    "Charisma": "Convince creatures to be friendly, resist mental control."
}

# Spell data
PRIEST_SPELLS_TIER_1 = {
    "Cure Wounds": {
        "tier": 1,
        "duration": "Instant",
        "range": "Close",
        "description": "Your touch restores ebbing life. Roll a number of d6s equal to 1 + half your level (rounded down). One target you touch regains that many hit points."
    },
    "Holy Weapon": {
        "tier": 1,
        "duration": "5 rounds",
        "range": "Close",
        "description": "One weapon you touch is imbued with a sacred blessing. The weapon becomes magical and has +1 to attack and damage rolls for the duration."
    },
    "Light": {
        "tier": 1,
        "duration": "1 hour real time",
        "range": "Close",
        "description": "One object you touch glows with bright, heatless light, illuminating out to a near distance for 1 hour of real time."
    },
    "Protection From Evil": {
        "tier": 1,
        "duration": "Focus",
        "range": "Close",
        "description": "For the spell's duration, chaotic beings have disadvantage on attack rolls and hostile spellcasting checks against the target. These beings also can't possess, compel, or beguile it."
    },
    "Shield of Faith": {
        "tier": 1,
        "duration": "5 rounds",
        "range": "Self",
        "description": "A protective force wrought of your holy conviction surrounds you. You gain a +2 bonus to your armor class for the duration."
    },
    "Turn Undead": {
        "tier": 1,
        "duration": "Instant",
        "range": "Near",
        "description": "You rebuke undead creatures, forcing them to flee. You must present a holy symbol to cast this spell. Undead creatures within near of you must make a CHA check vs. your spellcasting check."
    }
}

WIZARD_SPELLS_TIER_1 = {
    "Alarm": {
        "tier": 1,
        "duration": "1 day",
        "range": "Close",
        "description": "You touch one object, such as a door threshold, setting a magical alarm on it. If any creature you do not designate while casting the spell touches or crosses past the object, a magical bell sounds in your head."
    },
    "Burning Hands": {
        "tier": 1,
        "duration": "Instant",
        "range": "Close",
        "description": "You spread your fingers with thumbs touching, unleashing a circle of flame that fills a close area around where you stand. Creatures within the area of effect take 1d6 damage."
    },
    "Charm Person": {
        "tier": 1,
        "duration": "1d8 days",
        "range": "Near",
        "description": "You magically beguile one humanoid of level 2 or less within near range, who regards you as a friend for the duration. The spell ends if you or your allies do anything to hurt it."
    },
    "Detect Magic": {
        "tier": 1,
        "duration": "Focus",
        "range": "Near",
        "description": "You can sense the presence of magic within near range for the spell's duration. If you focus for two rounds, you discern its general properties. Full barriers block this spell."
    },
    "Feather Fall": {
        "tier": 1,
        "duration": "Instant",
        "range": "Self",
        "description": "You may make an attempt to cast this spell when you fall. Your rate of descent slows so that you land safely on your feet."
    },
    "Floating Disk": {
        "tier": 1,
        "duration": "10 rounds",
        "range": "Near",
        "description": "You create a floating, circular disk of force with a concave center. It can carry up to 20 gear slots. It hovers at waist level and automatically stays within near of you."
    },
    "Hold Portal": {
        "tier": 1,
        "duration": "10 rounds",
        "range": "Near",
        "description": "You magically hold a portal closed for the duration. A creature must make a successful STR check vs. your spellcasting check to open the portal."
    },
    "Light": {
        "tier": 1,
        "duration": "1 hour real time",
        "range": "Close",
        "description": "One object you touch glows with bright, heatless light, illuminating out to a near distance for 1 hour of real time."
    },
    "Mage Armor": {
        "tier": 1,
        "duration": "10 rounds",
        "range": "Self",
        "description": "An invisible layer of magical force protects your vitals. Your armor class becomes 14 (18 on a critical spellcasting check) for the spell's duration."
    },
    "Magic Missile": {
        "tier": 1,
        "duration": "Instant",
        "range": "Far",
        "description": "You have advantage on your check to cast this spell. A glowing bolt of force streaks from your open hand, dealing 1d4 damage to one target."
    },
    "Protection From Evil": {
        "tier": 1,
        "duration": "Focus",
        "range": "Close",
        "description": "For the spell's duration, chaotic beings have disadvantage on attack rolls and hostile spellcasting checks against the target. These beings also can't possess, compel, or beguile it."
    },
    "Sleep": {
        "tier": 1,
        "duration": "Instant",
        "range": "Near",
        "description": "You weave a lulling spell that fills a near-sized cube extending from you. Living creatures in the area of effect fall into a deep sleep if they are LV 2 or less."
    }
}

# Gods and their descriptions
GODS = {
    "Saint Terragnis": {
        "alignment": "Lawful",
        "title": "SAINT TERRAGNIS (LAWFUL)",
        "description": "A legendary knight who is the patron of most lawful humans. She ascended to godhood long ago and is the embodiment of righteousness and justice."
    },
    "Gede": {
        "alignment": "Neutral",
        "title": "GEDE (NEUTRAL)",
        "description": "The god of feasts, mirth, and the wilds. Gede is usually peaceful, but primal storms rage when her anger rises. Many elves and halflings worship her."
    },
    "Madeera the Covenant": {
        "alignment": "Lawful",
        "title": "MADEERA THE COVENANT (LAWFUL)",
        "description": "Madeera was the first manifestation of Law. She carries every law of reality, a dictate called the Covenant, written on her skin in precise symbols."
    },
    "Ord": {
        "alignment": "Neutral",
        "title": "ORD (NEUTRAL)",
        "description": "Ord the Unbending, the Wise, the Secret-Keeper. He is the god of magic, knowledge, secrets, and equilibrium."
    },
    "Memnon": {
        "alignment": "Chaotic",
        "title": "MEMNON (CHAOTIC)",
        "description": "Memnon was the first manifestation of Chaos. He is Madeera's twin, a red-maned, leonine being whose ultimate ambition is to rend the cosmic laws of the Covenant from his sister's skin."
    },
    "Ramlaat": {
        "alignment": "Chaotic",
        "title": "RAMLAAT (CHAOTIC)",
        "description": "Ramlaat is the Pillager, the Barbaric, the Horde. Many orcs worship him and live by the Blood Rite, a prophecy that says only the strongest will survive a coming doom."
    },
    "Shune the Vile": {
        "alignment": "Chaotic",
        "title": "SHUNE THE VILE (CHAOTIC)",
        "description": "Shune whispers arcane secrets to sorcerers and witches who call to her in the dark hours. She schemes to displace Ord so she can control the vast flow of magic herself."
    }
}

NAMES = {
    "Dwarf": ["Hilde", "Torbin", "Marga", "Bruno", "Karina", "Naugrim", "Brenna", "Darvin", "Elga", "Alric", "Isolde", "Gendry", "Bruga", "Junnor", "Vidrid", "Torson", "Brielle", "Ulfgar", "Sarna", "Grimm"],
    "Elf": ["Eliara", "Ryarr", "Sariel", "Tirolas", "Galira", "Varos", "Daeniel", "Axidor", "Hiralia", "Cyrwin", "Lothiel", "Zaphiel", "Nayra", "Ithior", "Amriel", "Elyon", "Jirwyn", "Natinel", "Fiora", "Ruhiel"],
    "Goblin": ["Iggs", "Tark", "Nix", "Lenk", "Roke", "Fitz", "Tila", "Riggs", "Prim", "Zeb", "Finn", "Borg", "Yark", "Deeg", "Nibs", "Brak", "Fink", "Rizzo", "Squib", "Grix"],
    "Halfling": ["Willow", "Benny", "Annie", "Tucker", "Marie", "Hobb", "Cora", "Gordie", "Rose", "Ardo", "Alma", "Norbert", "Jennie", "Barvin", "Tilly", "Pike", "Lydia", "Marlow", "Astrid", "Jasper"],
    "Half-Orc": ["Vara", "Gralk", "Ranna", "Korv", "Zasha", "Hrogar", "Klara", "Tragan", "Brolga", "Drago", "Yelena", "Krull", "Ulara", "Tulk", "Shiraal", "Wulf", "Ivara", "Hirok", "Aja", "Zoraan"],
    "Human": ["Zali", "Bram", "Clara", "Nattias", "Rina", "Denton", "Mirena", "Aran", "Morgan", "Giralt", "Tamra", "Oscar", "Ishana", "Rogar", "Jasmin", "Tarin", "Yuri", "Malchor", "Lienna", "Godfrey"]
}

TITLES = {
    "Fighter": {
        "Lawful": { (1, 2): "Squire", (3, 4): "Cavalier", (5, 6): "Knight", (7, 8): "Thane", (9, 10): "Lord/Lady" },
        "Chaotic": { (1, 2): "Knave", (3, 4): "Bandit", (5, 6): "Slayer", (7, 8): "Reaver", (9, 10): "Warlord" },
        "Neutral": { (1, 2): "Warrior", (3, 4): "Barbarian", (5, 6): "Battlerager", (7, 8): "Warchief", (9, 10): "Chieftain" }
    },
    "Priest": {
        "Lawful": { (1, 2): "Acolyte", (3, 4): "Crusader", (5, 6): "Templar", (7, 8): "Champion", (9, 10): "Paladin" },
        "Chaotic": { (1, 2): "Initiate", (3, 4): "Zealot", (5, 6): "Cultist", (7, 8): "Scourge", (9, 10): "Chaos Knight" },
        "Neutral": { (1, 2): "Seeker", (3, 4): "Invoker", (5, 6): "Haruspex", (7, 8): "Mystic", (9, 10): "Oracle" }
    },
    "Thief": {
        "Lawful": { (1, 2): "Footpad", (3, 4): "Burglar", (5, 6): "Rook", (7, 8): "Underboss", (9, 10): "Boss" },
        "Chaotic": { (1, 2): "Thug", (3, 4): "Cutthroat", (5, 6): "Shadow", (7, 8): "Assassin", (9, 10): "Wraith" },
        "Neutral": { (1, 2): "Robber", (3, 4): "Outlaw", (5, 6): "Rogue", (7, 8): "Renegade", (9, 10): "Bandit King/Queen" }
    },
    "Wizard": {
        "Lawful": { (1, 2): "Apprentice", (3, 4): "Conjurer", (5, 6): "Arcanist", (7, 8): "Mage", (9, 10): "Archmage" },
        "Chaotic": { (1, 2): "Adept", (3, 4): "Channeler", (5, 6): "Witch/Warlock", (7, 8): "Diabolist", (9, 10): "Sorcerer" },
        "Neutral": { (1, 2): "Shaman", (3, 4): "Seer", (5, 6): "Warden", (7, 8): "Sage", (9, 10): "Druid" }
    }
}

# Race descriptions with full details
RACE_DETAILS = {
    "Dwarf": {
        "title": "DWARF",
        "description": "Brave, stalwart folk as sturdy as the stone kingdoms they carve inside mountains. You know the Common and Dwarvish languages.",
        "ability": "Stout. Start with +2 HP. Roll hit points per level with advantage."
    },
    "Elf": {
        "title": "ELF", 
        "description": "Ethereal, graceful people who revere knowledge and beauty. Elves see far and live long. You know the Common, Elvish, and Sylvan languages.",
        "ability": "Farsight. You get a +1 bonus to attack rolls with ranged weapons or a +1 bonus to spellcasting checks."
    },
    "Goblin": {
        "title": "GOBLIN",
        "description": "Green, clever beings who thrive in dark, cramped places. As fierce as they are tiny. You know the Common and Goblin languages.",
        "ability": "Keen Senses. You can't be surprised."
    },
    "Halfling": {
        "title": "HALFLING", 
        "description": "Small, cheerful country folk with mischievous streaks. They enjoy life's simple pleasures. You know the Common language.",
        "ability": "Stealthy. Once per day, you can become invisible for 3 rounds."
    },
    "Half-Orc": {
        "title": "HALF-ORC",
        "description": "Towering, tusked warriors who are as daring as humans and as relentless as orcs. You know the Common and Orcish languages.", 
        "ability": "Mighty. You have a +1 bonus to attack and damage rolls with melee weapons."
    },
    "Human": {
        "title": "HUMAN",
        "description": "Bold, adaptable, and diverse people who learn quickly and accomplish mighty deeds. You know the Common language and one additional common language.",
        "ability": "Ambitious. You gain one additional talent roll at 1st level."
    }
}

# Class descriptions with full details
CLASS_DETAILS = {
    "Fighter": {
        "title": "FIGHTER",
        "description": "Blood-soaked gladiators in dented armor, acrobatic duelists with darting swords, or far-eyed elven archers who carve their legends with steel and grit.",
        "stats": [
            "Weapons: All weapons",
            "Armor: All armor and shields", 
            "Hit Points: 1d8 per level"
        ],
        "abilities": [
            "Hauler. Add your Constitution modifier, if positive, to your gear slots.",
            "Weapon Mastery. Choose one type of weapon, such as longswords. You gain +1 to attack and damage with that weapon type. In addition, add half your level to these rolls (round down).",
            "Grit. Choose Strength or Dexterity. You have advantage on checks of that type to overcome an opposing force, such as kicking open a stuck door (Strength) or slipping free of rusty chains (Dexterity)."
        ]
    },
    "Priest": {
        "title": "PRIEST",
        "description": "Crusading templars, prophetic shamans, or mad-eyed zealots who wield the power of their gods to cleanse the unholy.",
        "stats": [
            "Weapons: Club, crossbow, dagger, mace, longsword, staff, warhammer",
            "Armor: All armor and shields",
            "Hit Points: 1d6 per level"
        ],
        "abilities": [
            "Languages. You know either Celestial, Diabolic, or Primordial.",
            "Turn Undead. You know the turn undead spell. It doesn't count toward your number of known spells.",
            "Deity. Choose a god to serve who matches your alignment. You have a holy symbol for your god (it takes up no gear slots).",
            "Spellcasting. You can cast priest spells you know. You know two tier 1 spells of your choice from the priest spell list."
        ]
    },
    "Thief": {
        "title": "THIEF",
        "description": "Rooftop assassins, grinning con artists, or cloaked cat burglars who can pluck a gem from the claws of a sleeping demon and sell it for twice its worth.",
        "stats": [
            "Weapons: Club, crossbow, dagger, shortbow, shortsword",
            "Armor: Leather armor, mithral chainmail",
            "Hit Points: 1d4 per level"
        ],
        "abilities": [
            "Backstab. If you hit a creature who is unaware of your attack, you deal an extra weapon die of damage. Add additional weapon dice of damage equal to half your level (round down).",
            "Thievery. You are adept at thieving skills and have the necessary tools of the trade secreted on your person. You are trained in climbing, sneaking and hiding, applying disguises, finding and disabling traps, and delicate tasks such as picking pockets and opening locks."
        ]
    },
    "Wizard": {
        "title": "WIZARD",
        "description": "Rune-tattooed adepts, bespectacled magi, and flame-conjuring witches who dare to manipulate the fell forces of magic.",
        "stats": [
            "Weapons: Dagger, staff",
            "Armor: None", 
            "Hit Points: 1d4 per level"
        ],
        "abilities": [
            "Languages. You know two additional common languages and two rare languages.",
            "Learning Spells. You can permanently learn a wizard spell from a spell scroll by studying it for a day and succeeding on a DC 15 Intelligence check.",
            "Spellcasting. You can cast wizard spells you know. You know three tier 1 spells of your choice from the wizard spell list."
        ]
    }
}

# Alignment descriptions
ALIGNMENT_DETAILS = {
    "Lawful": {
        "title": "LAWFUL",
        "description": "You believe in order, honor, and following established rules and traditions. You value justice, duty, and the greater good of society.",
        "traits": "Reliable, honorable, principled, sometimes inflexible"
    },
    "Chaotic": {
        "title": "CHAOTIC", 
        "description": "You value freedom above all else and oppose rigid authority. You follow your heart and conscience rather than rules imposed by others.",
        "traits": "Independent, unpredictable, free-spirited, sometimes reckless"
    },
    "Neutral": {
        "title": "NEUTRAL",
        "description": "You seek balance between order and chaos, neither fully embracing structure nor completely rejecting it. You judge each situation on its own merits.",
        "traits": "Balanced, pragmatic, adaptable, sometimes indecisive"
    }
}

# Colors - Updated to match game UI
COLOR_BG = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_CREAM = (240, 236, 224)
COLOR_BUTTON_NORMAL = (140, 134, 125)
COLOR_BUTTON_HOVER = (162, 160, 154)
COLOR_BUTTON_ACTIVE = (100, 100, 100)
COLOR_TEXT_INPUT = (255, 255, 255)
COLOR_TEXT_INPUT_BORDER = (100, 100, 100)

# Configuration
TORCH_DURATION_SECONDS = 3600

class CharCreationState(Enum):
    NAME_INPUT = 0
    STAT_ROLLING = 1
    RACE_SELECTION = 2
    CLASS_SELECTION = 3
    ALIGNMENT_SELECTION = 4
    GOD_SELECTION = 5
    SPELL_SELECTION = 6
    GEAR_SELECTION = 7
    STATS_REVIEW = 8
    COMPLETE = 9

@dataclass
class Player:
    name: str
    title: str
    race: str
    alignment: str
    character_class: str
    level: int
    hp: int
    max_hp: int
    xp: int
    xp_to_next_level: int
    ac: int
    light_duration: float
    light_start_time: float
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    god: str = ""
    starting_spells: List[str] = field(default_factory=list)
    inventory: List = field(default_factory=list)
    equipment: dict = field(default_factory=dict)  # equipped items
    gold: float = 0.0
    gear_slots_used: int = 0
    max_gear_slots: int = 10

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
        self.clicked = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False
        return False
    
    def draw(self, surface: pygame.Surface):
        if self.clicked:
            color = COLOR_BUTTON_ACTIVE
        elif self.hovered:
            color = COLOR_BUTTON_HOVER
        else:
            color = COLOR_BUTTON_NORMAL
        
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, COLOR_BLACK, self.rect, 2)
        
        text_surf = self.font.render(self.text, True, COLOR_WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class TextInput:
    def __init__(self, x: int, y: int, width: int, height: int, font: pygame.font.Font, max_length: int = 20):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text = ""
        self.max_length = max_length
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True
            elif len(self.text) < self.max_length:
                char = event.unicode
                if char.isalpha() or char == " ":
                    self.text += char
        return False
    
    def update(self, dt: float):
        self.cursor_timer += dt
        if self.cursor_timer >= 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, COLOR_TEXT_INPUT, self.rect)
        pygame.draw.rect(surface, COLOR_TEXT_INPUT_BORDER, self.rect, 2)
        
        text_surf = self.font.render(self.text, True, COLOR_BLACK)
        text_rect = text_surf.get_rect(left=self.rect.left + 5, centery=self.rect.centery)
        surface.blit(text_surf, text_rect)
        
        if self.active and self.cursor_visible:
            cursor_x = text_rect.right + 2
            cursor_y = self.rect.centery
            pygame.draw.line(surface, COLOR_BLACK, 
                           (cursor_x, cursor_y - 10), (cursor_x, cursor_y + 10), 2)

class CharacterCreator:
    def __init__(self, screen_width: int, screen_height: int, font_file: str):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.title_font = pygame.font.Font(font_file, 36)
        self.large_font = pygame.font.Font(font_file, 24)
        self.medium_font = pygame.font.Font(font_file, 20)
        self.small_font = pygame.font.Font(font_file, 16)
        self.tiny_font = pygame.font.Font(font_file, 14)
        
        self.state = CharCreationState.NAME_INPUT
        self.selected_index = 0
        
        self.name = ""
        self.race = ""
        self.character_class = ""
        self.alignment = ""
        self.god = ""
        self.selected_spells = []
        self.spells_to_select = 0
        
        self.stats = [10, 10, 10, 10, 10, 10]
        self.stat_rolls_history = []
        self.current_roll_set = 0
        
        self.text_input = None
        self.random_button = None
        self.roll_button = None
        self.accept_button = None
        self.reroll_button = None
        
        self.list_width = screen_width // 3
        self.detail_width = (screen_width * 2) // 3
        self.list_x = 20
        self.detail_x = self.list_width + 40
        
        self.fullscreen = False
        
        self._setup_ui()
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self.list_width = self.screen_width // 3
            self.detail_width = (self.screen_width * 2) // 3
            self.detail_x = self.list_width + 40
        else:
            pygame.display.set_mode((800, 600))
            self.screen_width = 800
            self.screen_height = 600
            self.list_width = self.screen_width // 3
            self.detail_width = (self.screen_width * 2) // 3
            self.detail_x = self.list_width + 40
    
    def get_stat_modifier(self, stat_value: int) -> int:
        if stat_value <= 3:
            return -4
        elif stat_value <= 5:
            return -3
        elif stat_value <= 7:
            return -2
        elif stat_value <= 9:
            return -1
        elif stat_value <= 11:
            return 0
        elif stat_value <= 13:
            return +1
        elif stat_value <= 15:
            return +2
        elif stat_value <= 17:
            return +3
        else:
            return +4
    
    def roll_stats(self) -> List[int]:
        return [sum(random.randint(1, 6) for _ in range(3)) for _ in range(6)]
    
    def has_high_stat(self, stats: List[int]) -> bool:
        return any(stat >= 14 for stat in stats)
    
    def _setup_ui(self):
        self.selected_index = 0
        
        self.text_input = None
        self.random_button = None
        self.roll_button = None
        self.accept_button = None
        self.reroll_button = None
        
        if self.state == CharCreationState.NAME_INPUT:
            input_width = 300
            input_height = 40
            input_x = (self.screen_width - input_width) // 2
            input_y = self.screen_height // 2 - 20
            self.text_input = TextInput(input_x, input_y, input_width, input_height, self.large_font)
            
            self.random_button = Button(input_x + input_width + 20, input_y, 100, input_height, "Random", self.medium_font)
        
        elif self.state == CharCreationState.STAT_ROLLING:
            button_y = self.screen_height // 2 + 100
            self.roll_button = Button(self.screen_width // 2 - 150, button_y, 100, 40, "Roll Stats", self.medium_font)
            self.accept_button = Button(self.screen_width // 2 - 40, button_y, 80, 40, "Accept", self.medium_font)
            self.reroll_button = Button(self.screen_width // 2 + 50, button_y, 100, 40, "Reroll", self.medium_font)
            
            if not self.stat_rolls_history:
                initial_stats = self.roll_stats()
                self.stat_rolls_history.append(initial_stats)
                self.stats = initial_stats[:]
    
    def _get_current_options(self):
        if self.state == CharCreationState.RACE_SELECTION:
            return RACES
        elif self.state == CharCreationState.CLASS_SELECTION:
            return CLASSES
        elif self.state == CharCreationState.ALIGNMENT_SELECTION:
            return ALIGNMENTS
        elif self.state == CharCreationState.GOD_SELECTION:
            if self.alignment:
                return [name for name, god in GODS.items() if god["alignment"] == self.alignment]
            return list(GODS.keys())
        elif self.state == CharCreationState.SPELL_SELECTION:
            if self.character_class == "Priest":
                return list(PRIEST_SPELLS_TIER_1.keys())
            elif self.character_class == "Wizard":
                return list(WIZARD_SPELLS_TIER_1.keys())
        return []
    
    def _get_current_details(self):
        options = self._get_current_options()
        if not options or self.selected_index >= len(options):
            return None
            
        selected_option = options[self.selected_index]
        
        if self.state == CharCreationState.RACE_SELECTION:
            return RACE_DETAILS.get(selected_option)
        elif self.state == CharCreationState.CLASS_SELECTION:
            return CLASS_DETAILS.get(selected_option)
        elif self.state == CharCreationState.ALIGNMENT_SELECTION:
            return ALIGNMENT_DETAILS.get(selected_option)
        elif self.state == CharCreationState.GOD_SELECTION:
            return GODS.get(selected_option)
        elif self.state == CharCreationState.SPELL_SELECTION:
            if self.character_class == "Priest":
                return PRIEST_SPELLS_TIER_1.get(selected_option)
            elif self.character_class == "Wizard":
                return WIZARD_SPELLS_TIER_1.get(selected_option)
        return None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return False
        
        if self.text_input and self.state == CharCreationState.NAME_INPUT:
            if self.text_input.handle_event(event):
                if self.text_input.text.strip():
                    self._next_state()
                    return False
        
        if self.random_button and self.random_button.handle_event(event):
            self._randomize_current_selection()
        
        if self.roll_button and self.roll_button.handle_event(event):
            new_stats = self.roll_stats()
            self.stat_rolls_history.append(new_stats)
            self.current_roll_set = len(self.stat_rolls_history) - 1
            self.stats = new_stats[:]
        
        if self.accept_button and self.accept_button.handle_event(event):
            if self.state == CharCreationState.STAT_ROLLING:
                self._next_state()
        
        if self.reroll_button and self.reroll_button.handle_event(event):
            if not self.has_high_stat(self.stats):
                new_stats = self.roll_stats()
                self.stat_rolls_history.append(new_stats)
                self.current_roll_set = len(self.stat_rolls_history) - 1
                self.stats = new_stats[:]
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state != CharCreationState.NAME_INPUT:
                    self._previous_state()
                    return False
                else:
                    return None
            
            elif event.key == pygame.K_RETURN:
                if self.state == CharCreationState.NAME_INPUT:
                    if self.text_input and self.text_input.text.strip():
                        self._next_state()
                elif self.state == CharCreationState.STAT_ROLLING:
                    self._next_state()
                elif self.state in [CharCreationState.RACE_SELECTION, CharCreationState.CLASS_SELECTION, 
                                   CharCreationState.ALIGNMENT_SELECTION, CharCreationState.GOD_SELECTION,
                                   CharCreationState.SPELL_SELECTION]:
                    if self._make_selection(self.selected_index):
                        self._next_state()
                    elif self.state != CharCreationState.SPELL_SELECTION:
                        self._next_state()
                elif self.state == CharCreationState.GEAR_SELECTION:
                    # This will be handled by returning the player object
                    return False
                elif self.state == CharCreationState.STATS_REVIEW:
                    return True
            
            elif event.key == pygame.K_UP:
                if self.state in [CharCreationState.RACE_SELECTION, CharCreationState.CLASS_SELECTION, 
                                 CharCreationState.ALIGNMENT_SELECTION, CharCreationState.GOD_SELECTION,
                                 CharCreationState.SPELL_SELECTION]:
                    options = self._get_current_options()
                    if options:
                        self.selected_index = (self.selected_index - 1) % len(options)
            
            elif event.key == pygame.K_DOWN:
                if self.state in [CharCreationState.RACE_SELECTION, CharCreationState.CLASS_SELECTION, 
                                 CharCreationState.ALIGNMENT_SELECTION, CharCreationState.GOD_SELECTION,
                                 CharCreationState.SPELL_SELECTION]:
                    options = self._get_current_options()
                    if options:
                        self.selected_index = (self.selected_index + 1) % len(options)
            
            elif event.key == pygame.K_SPACE:
                if self.state == CharCreationState.STAT_ROLLING:
                    new_stats = self.roll_stats()
                    self.stat_rolls_history.append(new_stats)
                    self.current_roll_set = len(self.stat_rolls_history) - 1
                    self.stats = new_stats[:]
        
        return False
    
    def _make_selection(self, index: int):
        options = self._get_current_options()
        if index < len(options):
            if self.state == CharCreationState.RACE_SELECTION:
                self.race = options[index]
            elif self.state == CharCreationState.CLASS_SELECTION:
                self.character_class = options[index]
            elif self.state == CharCreationState.ALIGNMENT_SELECTION:
                self.alignment = options[index]
            elif self.state == CharCreationState.GOD_SELECTION:
                self.god = options[index]
            elif self.state == CharCreationState.SPELL_SELECTION:
                spell = options[index]
                if spell not in self.selected_spells:
                    self.selected_spells.append(spell)
                    if len(self.selected_spells) >= self.spells_to_select:
                        return True
        return False
    
    def _randomize_current_selection(self):
        if self.state == CharCreationState.NAME_INPUT:
            temp_race = random.choice(RACES)
            random_name = random.choice(NAMES[temp_race])
            self.text_input.text = random_name
    
    def _next_state(self):
        if self.state == CharCreationState.NAME_INPUT:
            self.name = self.text_input.text.strip()
            self.state = CharCreationState.STAT_ROLLING
        elif self.state == CharCreationState.STAT_ROLLING:
            self.state = CharCreationState.RACE_SELECTION
        elif self.state == CharCreationState.RACE_SELECTION:
            self.state = CharCreationState.CLASS_SELECTION
        elif self.state == CharCreationState.CLASS_SELECTION:
            self.state = CharCreationState.ALIGNMENT_SELECTION
        elif self.state == CharCreationState.ALIGNMENT_SELECTION:
            if self.character_class == "Priest":
                self.state = CharCreationState.GOD_SELECTION
            elif self.character_class in ["Priest", "Wizard"]:
                self._setup_spell_selection()
                self.state = CharCreationState.SPELL_SELECTION
            else:
                self.state = CharCreationState.GEAR_SELECTION
        elif self.state == CharCreationState.GOD_SELECTION:
            if self.character_class in ["Priest", "Wizard"]:
                self._setup_spell_selection()
                self.state = CharCreationState.SPELL_SELECTION
            else:
                self.state = CharCreationState.GEAR_SELECTION
        elif self.state == CharCreationState.SPELL_SELECTION:
            self.state = CharCreationState.GEAR_SELECTION
        elif self.state == CharCreationState.GEAR_SELECTION:
            self.state = CharCreationState.STATS_REVIEW
        elif self.state == CharCreationState.STATS_REVIEW:
            self.state = CharCreationState.COMPLETE
        
        self._setup_ui()
    
    def _setup_spell_selection(self):
        self.selected_spells = []
        if self.character_class == "Priest":
            self.spells_to_select = 2
        elif self.character_class == "Wizard":
            self.spells_to_select = 3
    
    def _previous_state(self):
        if self.state == CharCreationState.STAT_ROLLING:
            self.state = CharCreationState.NAME_INPUT
        elif self.state == CharCreationState.RACE_SELECTION:
            self.state = CharCreationState.STAT_ROLLING
        elif self.state == CharCreationState.CLASS_SELECTION:
            self.state = CharCreationState.RACE_SELECTION
        elif self.state == CharCreationState.ALIGNMENT_SELECTION:
            self.state = CharCreationState.CLASS_SELECTION
        elif self.state == CharCreationState.GOD_SELECTION:
            self.state = CharCreationState.ALIGNMENT_SELECTION
        elif self.state == CharCreationState.SPELL_SELECTION:
            if self.character_class == "Priest":
                self.state = CharCreationState.GOD_SELECTION
            else:
                self.state = CharCreationState.ALIGNMENT_SELECTION
        elif self.state == CharCreationState.GEAR_SELECTION:
            if self.character_class in ["Priest", "Wizard"]:
                self.state = CharCreationState.SPELL_SELECTION
            elif self.character_class == "Priest":
                self.state = CharCreationState.GOD_SELECTION
            else:
                self.state = CharCreationState.ALIGNMENT_SELECTION
        elif self.state == CharCreationState.STATS_REVIEW:
            self.state = CharCreationState.GEAR_SELECTION
        
        self._setup_ui()
    
    def update(self, dt: float):
        if self.text_input:
            self.text_input.update(dt)
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        
        title = self._get_title()
        title_surf = self.title_font.render(title, True, COLOR_WHITE)
        title_rect = title_surf.get_rect(centerx=self.screen_width // 2, top=30)
        surface.blit(title_surf, title_rect)
        
        if self.state == CharCreationState.NAME_INPUT:
            self._draw_name_input(surface)
        elif self.state == CharCreationState.STAT_ROLLING:
            self._draw_stat_rolling(surface)
        elif self.state in [CharCreationState.RACE_SELECTION, CharCreationState.CLASS_SELECTION, 
                           CharCreationState.ALIGNMENT_SELECTION, CharCreationState.GOD_SELECTION,
                           CharCreationState.SPELL_SELECTION]:
            self._draw_selection_screen(surface)
        elif self.state == CharCreationState.GEAR_SELECTION:
            self._draw_gear_selection_placeholder(surface)
        elif self.state == CharCreationState.STATS_REVIEW:
            self._draw_stats_review(surface)
        
        if self.text_input:
            self.text_input.draw(surface)
        
        if self.random_button:
            self.random_button.draw(surface)
        
        if self.roll_button:
            self.roll_button.draw(surface)
        
        if self.accept_button:
            self.accept_button.draw(surface)
        
        if self.reroll_button:
            self.reroll_button.draw(surface)
        
        self._draw_instructions(surface)
    
    def _draw_gear_selection_placeholder(self, surface: pygame.Surface):
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        placeholder_text = "Loading Gear Selection..."
        placeholder_surf = self.large_font.render(placeholder_text, True, COLOR_WHITE)
        placeholder_rect = placeholder_surf.get_rect(centerx=center_x, centery=center_y)
        surface.blit(placeholder_surf, placeholder_rect)
    
    def _draw_stat_rolling(self, surface: pygame.Surface):
        separator_x = self.list_width + 30
        pygame.draw.line(surface, COLOR_WHITE, (separator_x, 100), (separator_x, self.screen_height - 100), 2)
        
        left_start_y = 150
        for i, (stat_name, stat_value) in enumerate(zip(STATS, self.stats)):
            y = left_start_y + i * 60
            modifier = self.get_stat_modifier(stat_value)
            modifier_str = f"+{modifier}" if modifier >= 0 else str(modifier)
            
            name_surf = self.large_font.render(f"{stat_name}:", True, COLOR_WHITE)
            surface.blit(name_surf, (self.list_x, y))
            
            value_text = f"{stat_value} ({modifier_str})"
            value_surf = self.large_font.render(value_text, True, COLOR_WHITE)
            surface.blit(value_surf, (self.list_x, y + 25))
        
        right_start_y = 150
        for i, stat_name in enumerate(STATS):
            y = right_start_y + i * 60
            desc = STAT_DESCRIPTIONS.get(stat_name, "")
            wrapped_lines = self._wrap_text(desc, self.detail_width - 40, self.small_font)
            for j, line in enumerate(wrapped_lines):
                line_surf = self.small_font.render(line, True, COLOR_WHITE)
                surface.blit(line_surf, (self.detail_x, y + j * 18))
        
        if not self.has_high_stat(self.stats):
            reroll_text = "No stat is 14+ - Reroll available"
            reroll_surf = self.medium_font.render(reroll_text, True, (255, 255, 0))
            reroll_rect = reroll_surf.get_rect(centerx=self.screen_width // 2, y=self.screen_height - 200)
            surface.blit(reroll_surf, reroll_rect)
    
    def _draw_selection_screen(self, surface: pygame.Surface):
        options = self._get_current_options()
        if not options:
            return
        
        separator_x = self.list_width + 30
        pygame.draw.line(surface, COLOR_WHITE, (separator_x, 100), (separator_x, self.screen_height - 100), 2)
        
        list_start_y = 120
        for i, option in enumerate(options):
            y = list_start_y + i * 50
            
            if i == self.selected_index:
                highlight_rect = pygame.Rect(self.list_x - 5, y - 5, self.list_width - 30, 40)
                pygame.draw.rect(surface, COLOR_BUTTON_HOVER, highlight_rect)
                pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
            
            color = COLOR_BLACK if i == self.selected_index else COLOR_WHITE
            option_surf = self.large_font.render(option, True, color)
            surface.blit(option_surf, (self.list_x, y))
            
            if self.state == CharCreationState.SPELL_SELECTION and option in self.selected_spells:
                selected_surf = self.small_font.render("✓ SELECTED", True, (0, 255, 0))
                surface.blit(selected_surf, (self.list_x, y + 25))
        
        if self.state == CharCreationState.SPELL_SELECTION:
            progress_text = f"Selected {len(self.selected_spells)}/{self.spells_to_select} spells"
            progress_surf = self.medium_font.render(progress_text, True, COLOR_WHITE)
            progress_rect = progress_surf.get_rect(centerx=self.list_width // 2, y=list_start_y + len(options) * 50 + 20)
            surface.blit(progress_surf, progress_rect)
        
        details = self._get_current_details()
        if details:
            self._draw_option_details(surface, details)
    
    def _draw_option_details(self, surface: pygame.Surface, details: dict):
        detail_y = 120
        line_height = 25
        
        title_surf = self.large_font.render(details.get("title", ""), True, COLOR_WHITE)
        surface.blit(title_surf, (self.detail_x, detail_y))
        detail_y += 40
        
        if "tier" in details:
            spell_info = f"Tier {details['tier']} | Duration: {details['duration']} | Range: {details['range']}"
            info_surf = self.small_font.render(spell_info, True, (200, 200, 200))
            surface.blit(info_surf, (self.detail_x, detail_y))
            detail_y += 30
        
        description = details.get("description", "")
        wrapped_lines = self._wrap_text(description, self.detail_width - 40, self.medium_font)
        for line in wrapped_lines:
            line_surf = self.medium_font.render(line, True, COLOR_WHITE)
            surface.blit(line_surf, (self.detail_x, detail_y))
            detail_y += line_height
        
        detail_y += 20
        
        if "ability" in details:
            wrapped_ability = self._wrap_text(details["ability"], self.detail_width - 40, self.medium_font)
            for line in wrapped_ability:
                line_surf = self.medium_font.render(line, True, COLOR_WHITE)
                surface.blit(line_surf, (self.detail_x, detail_y))
                detail_y += line_height
        
        elif "traits" in details:
            wrapped_traits = self._wrap_text(f"Traits: {details['traits']}", self.detail_width - 40, self.small_font)
            for line in wrapped_traits:
                line_surf = self.small_font.render(line, True, COLOR_WHITE)
                surface.blit(line_surf, (self.detail_x, detail_y))
                detail_y += line_height - 5
        
        elif "stats" in details:
            detail_y += 10
            for stat in details["stats"]:
                stat_surf = self.small_font.render(stat, True, COLOR_WHITE)
                surface.blit(stat_surf, (self.detail_x, detail_y))
                detail_y += line_height - 5
            
            detail_y += 15
            
            for ability in details["abilities"]:
                wrapped_ability = self._wrap_text(ability, self.detail_width - 40, self.small_font)
                for line in wrapped_ability:
                    line_surf = self.small_font.render(line, True, COLOR_WHITE)
                    surface.blit(line_surf, (self.detail_x, detail_y))
                    detail_y += line_height - 5
                detail_y += 10
    
    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> List[str]:
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _draw_instructions(self, surface: pygame.Surface):
        instructions = []
        
        if self.state == CharCreationState.NAME_INPUT:
            instructions = ["Enter your name and press ENTER", "Click Random for a random name", "F11 for fullscreen"]
        elif self.state == CharCreationState.STAT_ROLLING:
            instructions = ["SPACE or Roll Stats button to roll", "Press ENTER or Accept to continue", "Reroll if no stat is 14+"]
        elif self.state in [CharCreationState.RACE_SELECTION, CharCreationState.CLASS_SELECTION, 
                           CharCreationState.ALIGNMENT_SELECTION, CharCreationState.GOD_SELECTION]:
            instructions = ["Use UP/DOWN arrows to navigate", "Press ENTER to select", "Press ESC to go back"]
        elif self.state == CharCreationState.SPELL_SELECTION:
            if len(self.selected_spells) < self.spells_to_select:
                instructions = ["Use UP/DOWN arrows to navigate", "Press ENTER to select spell", f"Select {self.spells_to_select - len(self.selected_spells)} more spells"]
            else:
                instructions = ["Press ENTER to continue", "Press ESC to go back"]
        elif self.state == CharCreationState.GEAR_SELECTION:
            instructions = ["Gear selection will open automatically"]
        elif self.state == CharCreationState.STATS_REVIEW:
            instructions = ["Press ENTER to finish character creation", "Press ESC to go back"]
        
        y = self.screen_height - 80
        for instruction in instructions:
            inst_surf = self.small_font.render(instruction, True, COLOR_WHITE)
            inst_rect = inst_surf.get_rect(centerx=self.screen_width // 2, y=y)
            surface.blit(inst_surf, inst_rect)
            y += 20
    
    def _draw_name_input(self, surface: pygame.Surface):
        instruction = "Enter your character's name:"
        inst_surf = self.large_font.render(instruction, True, COLOR_WHITE)
        inst_rect = inst_surf.get_rect(centerx=self.screen_width // 2, y=self.screen_height // 2 - 80)
        surface.blit(inst_surf, inst_rect)
    
    def _draw_stats_review(self, surface: pygame.Surface):
        center_x = self.screen_width // 2
        start_y = 120
        line_height = 25
        
        title = self._get_character_title()
        
        char_info = [
            f"Name: {self.name}",
            f"Title: {title}",
            f"Race: {self.race}",
            f"Class: {self.character_class}",
            f"Alignment: {self.alignment}",
        ]
        
        if self.god:
            char_info.append(f"Deity: {self.god}")
        
        if self.selected_spells:
            char_info.append(f"Starting Spells: {', '.join(self.selected_spells)}")
        
        char_info.extend([
            "",
            "STATISTICS:",
        ])
        
        for i, (stat_name, stat_value) in enumerate(zip(STATS, self.stats)):
            modifier = self.get_stat_modifier(stat_value)
            modifier_str = f"+{modifier}" if modifier >= 0 else str(modifier)
            char_info.append(f"{stat_name}: {stat_value} ({modifier_str})")
        
        char_info.extend([
            "",
            "Level: 1",
            "Hit Points: 10/10",
            "Armor Class: 11",
            "Experience: 0/100"
        ])
        
        for i, info in enumerate(char_info):
            if info:
                font = self.large_font if info in ["STATISTICS:"] else self.medium_font
                color = COLOR_WHITE
                info_surf = font.render(info, True, color)
                info_rect = info_surf.get_rect(centerx=center_x, y=start_y + i * line_height)
                surface.blit(info_surf, info_rect)
    
    def _get_title(self) -> str:
        titles = {
            CharCreationState.NAME_INPUT: "Enter Your Name",
            CharCreationState.STAT_ROLLING: "Roll Your Statistics",
            CharCreationState.RACE_SELECTION: "Choose Your Ancestry", 
            CharCreationState.CLASS_SELECTION: "Choose Your Class",
            CharCreationState.ALIGNMENT_SELECTION: "Choose Your Alignment",
            CharCreationState.GOD_SELECTION: "Choose Your Deity",
            CharCreationState.SPELL_SELECTION: "Choose Your Starting Spells",
            CharCreationState.GEAR_SELECTION: "Select Your Gear",
            CharCreationState.STATS_REVIEW: "Character Summary"
        }
        return titles.get(self.state, "Character Creation")
    
    def _get_character_title(self) -> str:
        if not all([self.character_class, self.alignment]):
            return "Adventurer"
        
        try:
            for level_range, title in TITLES[self.character_class][self.alignment].items():
                if 1 >= level_range[0] and 1 <= level_range[1]:
                    return title
        except KeyError:
            pass
        
        return "Adventurer"
    
    def create_player(self) -> Player:
        title = self._get_character_title()
        
        return Player(
            name=self.name,
            title=title,
            race=self.race,
            alignment=self.alignment,
            character_class=self.character_class,
            level=1,
            hp=10,
            max_hp=10,
            xp=0,
            xp_to_next_level=100,
            ac=11,
            light_duration=TORCH_DURATION_SECONDS,
            light_start_time=time.time(),
            strength=self.stats[0],
            dexterity=self.stats[1],
            constitution=self.stats[2],
            intelligence=self.stats[3],
            wisdom=self.stats[4],
            charisma=self.stats[5],
            god=self.god,
            starting_spells=self.selected_spells[:],
            inventory=[],
            equipment={},
            gold=0.0,
            gear_slots_used=0,
            max_gear_slots=max(self.stats[0], 10)  # Strength or 10, whichever is higher
        )

def run_character_creation(screen_width: int, screen_height: int, font_file: str) -> Optional[Player]:
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Character Creation")
    clock = pygame.time.Clock()
    
    creator = CharacterCreator(screen_width, screen_height, font_file)
    
    running = True
    while running:
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and creator.state == CharCreationState.NAME_INPUT:
                    return None
            
            result = creator.handle_event(event)
            if result is True:
                # Check if we have a completed player from gear selection
                if hasattr(creator, 'completed_player'):
                    return creator.completed_player
                else:
                    return creator.create_player()
            elif result is None:
                return None
            
            # Handle gear selection transition
            if creator.state == CharCreationState.GEAR_SELECTION:
                # Import and run gear selection
                try:
                    from gear_selection import run_gear_selection
                    temp_player = creator.create_player()
                    gear_result = run_gear_selection(temp_player, screen_width, screen_height, font_file)
                    if gear_result:
                        # Gear selection completed successfully - store the result
                        creator.completed_player = gear_result
                        creator.state = CharCreationState.STATS_REVIEW
                        creator._setup_ui()
                    else:
                        # Gear selection was cancelled, go back
                        creator._previous_state()
                except ImportError:
                    print("Error: gear_selection.py not found. Skipping gear selection.")
                    creator.state = CharCreationState.STATS_REVIEW
                    creator._setup_ui()
        
        creator.update(dt)
        creator.draw(screen)
        pygame.display.flip()
    
    return None