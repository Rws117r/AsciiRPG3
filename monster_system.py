# monster_system.py - Monster loading and management system
import json
import random
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

def get_stat_modifier(stat_value: int) -> int:
    """Calculate ability modifier from stat value"""
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

@dataclass
class MonsterAttack:
    name: str
    details: str  # e.g., "+2 (1d4 piercing)"
    count: int = 1
    
    def get_attack_bonus(self) -> int:
        """Extract attack bonus from details string"""
        try:
            if '+' in self.details:
                bonus_str = self.details.split('(')[0].strip()
                return int(bonus_str.replace('+', ''))
            return 0
        except:
            return 0
    
    def get_damage_dice(self) -> str:
        """Extract damage dice from details string"""
        try:
            if '(' in self.details and ')' in self.details:
                damage_part = self.details.split('(')[1].split(')')[0]
                # Extract just the dice part (e.g., "1d4" from "1d4 piercing")
                damage_dice = damage_part.split()[0]
                return damage_dice
            return "1d4"
        except:
            return "1d4"

@dataclass
class MonsterSpecialAbility:
    name: str
    description: str

@dataclass
class MonsterTemplate:
    name: str
    description: str
    ascii_char: str
    ac: int
    ac_details: str
    hp: int
    attacks: List[MonsterAttack]
    movement: str
    stats: Dict[str, int]
    alignment: str
    level: int
    special_abilities: List[MonsterSpecialAbility] = field(default_factory=list)
    dark_adapted: bool = False
    
    def get_stat_modifier(self, stat_name: str) -> int:
        """Get the modifier for a given stat"""
        stat_value = self.stats.get(stat_name.lower(), 10)
        return get_stat_modifier(stat_value)
    
    def get_primary_attack(self) -> Optional[MonsterAttack]:
        """Get the first/primary attack"""
        return self.attacks[0] if self.attacks else None
    
    def roll_hp(self) -> int:
        """Roll HP based on level and constitution (basic formula)"""
        con_mod = self.get_stat_modifier('constitution')
        # Simple formula: base HP + (level * constitution modifier)
        rolled_hp = max(1, self.hp + (self.level * con_mod))
        return rolled_hp

class MonsterDatabase:
    def __init__(self, monsters_directory: str = "monsters"):
        self.monsters_directory = monsters_directory
        self.monster_templates: Dict[str, MonsterTemplate] = {}
        self.load_all_monsters()
    
    def load_all_monsters(self):
        """Load all monster JSON files from the monsters directory"""
        if not os.path.exists(self.monsters_directory):
            print(f"Warning: Monsters directory '{self.monsters_directory}' not found. Creating with example monster.")
            self._create_example_monsters()
            return
        
        json_files = [f for f in os.listdir(self.monsters_directory) if f.endswith('.json')]
        
        for filename in json_files:
            filepath = os.path.join(self.monsters_directory, filename)
            try:
                with open(filepath, 'r') as f:
                    monster_data = json.load(f)
                    monster = self._parse_monster_json(monster_data)
                    self.monster_templates[monster.name] = monster
                    print(f"Loaded monster: {monster.name}")
            except Exception as e:
                print(f"Error loading monster file {filename}: {e}")
        
        if not self.monster_templates:
            print("No monsters loaded, creating example monsters.")
            self._create_example_monsters()
    
    def _parse_monster_json(self, data: Dict[str, Any]) -> MonsterTemplate:
        """Parse a monster JSON into a MonsterTemplate"""
        # Parse attacks
        attacks = []
        for attack_data in data.get('attacks', []):
            attack = MonsterAttack(
                name=attack_data['name'],
                details=attack_data['details'],
                count=attack_data.get('count', 1)
            )
            attacks.append(attack)
        
        # Parse special abilities
        special_abilities = []
        for ability_data in data.get('special_abilities', []):
            ability = MonsterSpecialAbility(
                name=ability_data['name'],
                description=ability_data['description']
            )
            special_abilities.append(ability)
        
        return MonsterTemplate(
            name=data['name'],
            description=data['description'],
            ascii_char=data.get('ascii_char', 'M'),
            ac=data['ac'],
            ac_details=data.get('ac_details', ''),
            hp=data['hp'],
            attacks=attacks,
            movement=data.get('movement', 'near'),
            stats=data['stats'],
            alignment=data['alignment'],
            level=data['level'],
            special_abilities=special_abilities,
            dark_adapted=data.get('dark_adapted', False)
        )
    
    def _create_example_monsters(self):
        """Create example monsters and save them to JSON files"""
        os.makedirs(self.monsters_directory, exist_ok=True)
        
        # Example monsters based on your Taskmaster Imp
        example_monsters = [
            {
                "name": "Taskmaster Imp",
                "description": "A diminutive, fussy fiend that delights in creating convoluted plans and tracking progress with infernal charts.",
                "ascii_char": "I",
                "ac": 12,
                "ac_details": "natural armor",
                "hp": 5,
                "attacks": [
                    {
                        "name": "Pointy Prod",
                        "details": "+2 (1d4 piercing)",
                        "count": 1
                    }
                ],
                "movement": "near (fly)",
                "stats": {
                    "strength": 8,
                    "dexterity": 12,
                    "constitution": 10,
                    "intelligence": 13,
                    "wisdom": 10,
                    "charisma": 14
                },
                "alignment": "L",
                "level": 1,
                "special_abilities": [
                    {
                        "name": "Scope Creep",
                        "description": "As a bonus action, the imp can assign a trivial task to one creature it can see. The target must make a DC 12 Wisdom saving throw or have disadvantage on its next attack roll, distracted by the pointless objective."
                    }
                ],
                "dark_adapted": True
            },
            {
                "name": "Giant Ant",
                "description": "A large, aggressive insect that swarms in groups and defends its colony fiercely.",
                "ascii_char": "a",
                "ac": 11,
                "ac_details": "natural armor",
                "hp": 8,
                "attacks": [
                    {
                        "name": "Bite",
                        "details": "+3 (1d6+1 piercing)",
                        "count": 1
                    }
                ],
                "movement": "near",
                "stats": {
                    "strength": 14,
                    "dexterity": 12,
                    "constitution": 13,
                    "intelligence": 2,
                    "wisdom": 11,
                    "charisma": 4
                },
                "alignment": "N",
                "level": 1,
                "special_abilities": [
                    {
                        "name": "Keen Smell",
                        "description": "The ant has advantage on Wisdom (Perception) checks that rely on smell."
                    }
                ],
                "dark_adapted": False
            },
            {
                "name": "Kobold Scout",
                "description": "A small, cunning reptilian humanoid that uses traps and ambush tactics.",
                "ascii_char": "k",
                "ac": 13,
                "ac_details": "leather armor",
                "hp": 7,
                "attacks": [
                    {
                        "name": "Spear",
                        "details": "+3 (1d6+1 piercing)",
                        "count": 1
                    },
                    {
                        "name": "Sling",
                        "details": "+4 (1d4+2 bludgeoning)",
                        "count": 1
                    }
                ],
                "movement": "near",
                "stats": {
                    "strength": 7,
                    "dexterity": 15,
                    "constitution": 9,
                    "intelligence": 8,
                    "wisdom": 7,
                    "charisma": 8
                },
                "alignment": "C",
                "level": 1,
                "special_abilities": [
                    {
                        "name": "Pack Tactics",
                        "description": "The kobold has advantage on attack rolls against a creature if at least one ally is within 5 feet of the creature and the ally isn't incapacitated."
                    }
                ],
                "dark_adapted": True
            }
        ]
        
        for monster_data in example_monsters:
            filename = f"{monster_data['name'].lower().replace(' ', '_')}.json"
            filepath = os.path.join(self.monsters_directory, filename)
            
            with open(filepath, 'w') as f:
                json.dump(monster_data, f, indent=2)
            
            # Also load into memory
            monster = self._parse_monster_json(monster_data)
            self.monster_templates[monster.name] = monster
            print(f"Created example monster: {monster.name}")
    
    def get_monster(self, name: str) -> Optional[MonsterTemplate]:
        """Get a monster template by name"""
        return self.monster_templates.get(name)
    
    def get_random_monster(self, level_range: Tuple[int, int] = (1, 3)) -> Optional[MonsterTemplate]:
        """Get a random monster within the given level range"""
        suitable_monsters = [
            monster for monster in self.monster_templates.values() 
            if level_range[0] <= monster.level <= level_range[1]
        ]
        
        if suitable_monsters:
            return random.choice(suitable_monsters)
        
        # Fallback to any monster if none in range
        if self.monster_templates:
            return random.choice(list(self.monster_templates.values()))
        
        return None
    
    def list_monsters(self) -> List[str]:
        """Get a list of all available monster names"""
        return list(self.monster_templates.keys())

@dataclass
class MonsterInstance:
    """An actual monster instance in the game"""
    template: MonsterTemplate
    x: int
    y: int
    room_id: int
    current_hp: int
    max_hp: int
    name: str = ""
    fled: bool = False
    
    def __post_init__(self):
        if not self.name:
            self.name = self.template.name
    
    @classmethod
    def from_template(cls, template: MonsterTemplate, x: int, y: int, room_id: int) -> 'MonsterInstance':
        """Create a monster instance from a template"""
        max_hp = template.roll_hp()
        return cls(
            template=template,
            x=x,
            y=y,
            room_id=room_id,
            current_hp=max_hp,
            max_hp=max_hp
        )
    
    def get_attack_bonus(self) -> int:
        """Get the attack bonus for this monster's primary attack"""
        primary_attack = self.template.get_primary_attack()
        if primary_attack:
            return primary_attack.get_attack_bonus()
        return 0
    
    def get_damage_dice(self) -> str:
        """Get the damage dice for this monster's primary attack"""
        primary_attack = self.template.get_primary_attack()
        if primary_attack:
            return primary_attack.get_damage_dice()
        return "1d4"
    
    def is_alive(self) -> bool:
        """Check if the monster is still alive"""
        return self.current_hp > 0
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to the monster. Returns True if monster dies."""
        self.current_hp -= damage
        return self.current_hp <= 0

# Global monster database instance
monster_db = None

def get_monster_database() -> MonsterDatabase:
    """Get the global monster database, creating it if necessary"""
    global monster_db
    if monster_db is None:
        monster_db = MonsterDatabase()
    return monster_db

def spawn_random_monster(x: int, y: int, room_id: int, level_range: Tuple[int, int] = (1, 3)) -> Optional[MonsterInstance]:
    """Spawn a random monster at the given location"""
    db = get_monster_database()
    template = db.get_random_monster(level_range)
    
    if template:
        return MonsterInstance.from_template(template, x, y, room_id)
    
    return None

def spawn_specific_monster(monster_name: str, x: int, y: int, room_id: int) -> Optional[MonsterInstance]:
    """Spawn a specific monster by name"""
    db = get_monster_database()
    template = db.get_monster(monster_name)
    
    if template:
        return MonsterInstance.from_template(template, x, y, room_id)
    
    return None