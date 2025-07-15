# ecs_components.py - Component definitions for the ECS system

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum, auto
from ecs_core import Component

# =============================================================================
# CORE COMPONENTS - Basic functionality every entity might need
# =============================================================================

@dataclass
class PositionComponent(Component):
    """Gives an entity a position in 2D space"""
    x: int
    y: int
    room_id: int = -1
    
    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    def distance_to(self, other: 'PositionComponent') -> int:
        """Calculate Chebyshev distance (max of dx, dy) - good for grid-based games"""
        return max(abs(self.x - other.x), abs(self.y - other.y))
    
    def manhattan_distance_to(self, other: 'PositionComponent') -> int:
        """Calculate Manhattan distance (dx + dy)"""
        return abs(self.x - other.x) + abs(self.y - other.y)

@dataclass 
class RenderableComponent(Component):
    """Makes an entity visible on screen"""
    ascii_char: str
    color: Tuple[int, int, int]
    render_layer: int = 0  # Higher numbers render on top
    visible: bool = True
    
    def __post_init__(self):
        # Ensure color is a valid RGB tuple
        if len(self.color) != 3:
            self.color = (255, 255, 255)  # Default to white

@dataclass
class NameComponent(Component):
    """Gives an entity a name and optional title"""
    name: str
    title: str = ""
    description: str = ""
    
    def full_name(self) -> str:
        """Get the full name with title if available"""
        if self.title:
            return f"{self.title} {self.name}"
        return self.name

@dataclass
class HealthComponent(Component):
    """Gives an entity hit points"""
    current_hp: int
    max_hp: int
    
    def __post_init__(self):
        # Ensure HP values are valid
        self.max_hp = max(1, self.max_hp)
        self.current_hp = max(0, min(self.current_hp, self.max_hp))
    
    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    @property
    def health_ratio(self) -> float:
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0
    
    @property
    def is_wounded(self) -> bool:
        return self.current_hp < self.max_hp
    
    @property
    def is_critical(self) -> bool:
        return self.health_ratio <= 0.25
    
    def heal(self, amount: int) -> int:
        """Heal the entity and return actual amount healed"""
        old_hp = self.current_hp
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        return self.current_hp - old_hp
    
    def damage(self, amount: int) -> int:
        """Damage the entity and return actual damage taken"""
        old_hp = self.current_hp
        self.current_hp = max(0, self.current_hp - amount)
        return old_hp - self.current_hp

@dataclass
class StatsComponent(Component):
    """Character statistics - the classic six D&D stats"""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    def get_modifier(self, stat_name: str) -> int:
        """Get the D&D-style modifier for a stat"""
        stat_value = getattr(self, stat_name.lower(), 10)
        if stat_value <= 3: return -4
        elif stat_value <= 5: return -3
        elif stat_value <= 7: return -2
        elif stat_value <= 9: return -1
        elif stat_value <= 11: return 0
        elif stat_value <= 13: return +1
        elif stat_value <= 15: return +2
        elif stat_value <= 17: return +3
        else: return +4
    
    def get_stat(self, stat_name: str) -> int:
        """Get a stat value by name"""
        return getattr(self, stat_name.lower(), 10)
    
    def set_stat(self, stat_name: str, value: int):
        """Set a stat value by name"""
        if hasattr(self, stat_name.lower()):
            setattr(self, stat_name.lower(), max(1, value))

# =============================================================================
# IDENTITY COMPONENTS - What type of entity is this?
# =============================================================================

@dataclass
class PlayerControlledComponent(Component):
    """Marks an entity as player-controlled"""
    player_id: int = 0  # For multiplayer support later

@dataclass  
class MonsterComponent(Component):
    """Marks an entity as a monster"""
    monster_type: str = "generic"
    challenge_rating: int = 1

@dataclass
class ItemComponent(Component):
    """Marks an entity as an item that can be picked up"""
    weight: float = 1.0
    value_cp: int = 0  # Value in copper pieces
    stackable: bool = False
    max_stack: int = 1
    gear_slots: int = 1  # How many inventory slots this takes

@dataclass
class EnvironmentComponent(Component):
    """Marks an entity as part of the environment (doors, furniture, etc.)"""
    environment_type: str = "generic"  # door, chest, altar, etc.
    destructible: bool = False

# =============================================================================
# MOVEMENT AND PHYSICS COMPONENTS
# =============================================================================

@dataclass
class MovementComponent(Component):
    """Allows an entity to move"""
    speed: int = 1  # Tiles per turn
    can_move_diagonally: bool = True
    
@dataclass
class BlocksMovementComponent(Component):
    """Prevents other entities from moving through this tile"""
    blocks_player: bool = True
    blocks_monsters: bool = True
    blocks_items: bool = False

@dataclass
class BlocksLightComponent(Component):
    """Blocks line of sight and light"""
    opacity: float = 1.0  # 0.0 = transparent, 1.0 = opaque

@dataclass
class MovableComponent(Component):
    """Can be pushed or pulled by other entities"""
    push_difficulty: int = 10  # Strength check needed to push
    can_be_pulled: bool = False
    weight: float = 100.0

# =============================================================================
# INTERACTION COMPONENTS
# =============================================================================

@dataclass
class ExaminableComponent(Component):
    """Can be examined by the player"""
    short_description: str
    detailed_description: str
    examination_range: int = 20  # Max distance for examination
    
    def get_description(self, distance: int) -> str:
        """Get appropriate description based on distance"""
        if distance <= 1:
            return self.detailed_description
        else:
            return self.short_description

@dataclass
class InteractableComponent(Component):
    """Can be interacted with by the player"""
    interaction_type: str  # "door", "chest", "button", "altar", etc.
    requires_adjacent: bool = True
    can_use_repeatedly: bool = True
    interaction_count: int = 0
    max_interactions: int = -1  # -1 = unlimited

@dataclass
class ContainerComponent(Component):
    """Can hold other entities (like a chest or backpack)"""
    contents: List['EntityID'] = field(default_factory=list)
    max_capacity: int = 10
    is_open: bool = False
    requires_key: bool = False
    key_item_name: str = ""
    
    @property
    def is_full(self) -> bool:
        return len(self.contents) >= self.max_capacity
    
    @property
    def is_empty(self) -> bool:
        return len(self.contents) == 0
    
    def can_fit(self, item_count: int = 1) -> bool:
        return len(self.contents) + item_count <= self.max_capacity

@dataclass
class DoorComponent(Component):
    """Represents a door that can be opened/closed"""
    is_open: bool = False
    locked: bool = False
    key_required: str = ""  # Name of key item needed
    door_type: int = 1  # From your original door types

# =============================================================================
# INVENTORY AND EQUIPMENT COMPONENTS  
# =============================================================================

@dataclass
class InventoryComponent(Component):
    """Entity can carry items"""
    items: List['EntityID'] = field(default_factory=list)
    max_slots: int = 10
    gold: float = 0.0
    
    @property
    def used_slots(self) -> int:
        return len(self.items)
    
    @property
    def free_slots(self) -> int:
        return self.max_slots - self.used_slots
    
    def can_fit(self, item_count: int = 1) -> bool:
        return self.used_slots + item_count <= self.max_slots

@dataclass
class EquippedComponent(Component):
    """Marks an item as equipped to a specific equipment slot"""
    slot: str  # "weapon", "armor", "shield", "light", etc.
    wearer: 'EntityID'
    equipped_at: float = 0.0  # Game time when equipped (for duration tracking)

@dataclass
class EquipmentSlotsComponent(Component):
    """Defines what equipment slots an entity has available"""
    slots: Dict[str, Optional['EntityID']] = field(default_factory=lambda: {
        'weapon': None,
        'armor': None, 
        'shield': None,
        'light': None
    })
    
    def get_equipped_item(self, slot: str) -> Optional['EntityID']:
        return self.slots.get(slot)
    
    def equip_item(self, slot: str, item: 'EntityID'):
        if slot in self.slots:
            self.slots[slot] = item
    
    def unequip_item(self, slot: str) -> Optional['EntityID']:
        if slot in self.slots:
            old_item = self.slots[slot]
            self.slots[slot] = None
            return old_item
        return None

# =============================================================================
# COMBAT COMPONENTS
# =============================================================================

@dataclass
class WeaponComponent(Component):
    """Makes an item usable as a weapon"""
    damage_dice: str = "1d4"
    attack_bonus: int = 0
    damage_bonus: int = 0
    weapon_type: str = "melee"  # melee, ranged, thrown
    range_close: int = 1
    range_near: int = 6
    range_far: int = 20
    properties: List[str] = field(default_factory=list)  # finesse, two-handed, etc.
    
    def get_range(self, range_type: str) -> int:
        """Get weapon range by type"""
        ranges = {
            'close': self.range_close,
            'near': self.range_near, 
            'far': self.range_far
        }
        return ranges.get(range_type.lower(), self.range_close)

@dataclass
class ArmorComponent(Component):
    """Provides armor class bonus"""
    ac_bonus: int = 0
    max_dex_bonus: Optional[int] = None  # None = no limit
    armor_type: str = "light"  # light, medium, heavy
    stealth_disadvantage: bool = False
    strength_requirement: int = 0

@dataclass
class CombatStatsComponent(Component):
    """Combat-specific statistics"""
    armor_class: int = 10
    initiative_bonus: int = 0
    attack_bonus: int = 0
    damage_bonus: int = 0
    
    def calculate_ac(self, dex_mod: int, armor_ac: int = 0, shield_ac: int = 0, max_dex: Optional[int] = None) -> int:
        """Calculate total armor class"""
        effective_dex = dex_mod if max_dex is None else min(dex_mod, max_dex)
        return 10 + effective_dex + armor_ac + shield_ac

# =============================================================================
# AI AND BEHAVIOR COMPONENTS
# =============================================================================

@dataclass
class AIComponent(Component):
    """Controls AI behavior for monsters"""
    ai_type: str = "hostile"  # hostile, neutral, friendly, fleeing, wandering
    aggro_range: int = 6
    chase_range: int = 10  # How far to chase before giving up
    last_known_player_pos: Optional[Tuple[int, int]] = None
    turns_since_saw_player: int = 0
    home_position: Optional[Tuple[int, int]] = None  # Where to return when not chasing

@dataclass
class TurnOrderComponent(Component):
    """Tracks initiative and turn order in combat"""
    initiative: int = 0
    has_acted_this_round: bool = False
    
# =============================================================================
# LIGHT AND VISION COMPONENTS
# =============================================================================

@dataclass
class LightSourceComponent(Component):
    """Entity emits light"""
    brightness: int = 6  # Radius in tiles
    fuel_remaining: float = -1  # -1 = infinite, else seconds remaining
    lit: bool = True
    light_color: Tuple[int, int, int] = (255, 255, 200)  # Warm white default
    
    @property
    def is_lit(self) -> bool:
        return self.lit and (self.fuel_remaining != 0)

@dataclass
class VisionComponent(Component):
    """Entity can see things"""
    vision_range: int = 20
    can_see_in_dark: bool = False
    visible_positions: Set[Tuple[int, int]] = field(default_factory=set)
    
    def can_see_position(self, pos: Tuple[int, int]) -> bool:
        return pos in self.visible_positions

# =============================================================================
# STATUS EFFECT COMPONENTS
# =============================================================================

@dataclass
class StatusEffectComponent(Component):
    """Base for temporary effects"""
    effect_type: str
    duration_remaining: int = 5  # Turns remaining, -1 = permanent
    intensity: int = 1
    source: Optional['EntityID'] = None
    
    @property
    def is_permanent(self) -> bool:
        return self.duration_remaining == -1
    
    @property
    def is_expired(self) -> bool:
        return self.duration_remaining == 0

# Common status effects
@dataclass
class PoisonedComponent(StatusEffectComponent):
    """Entity is poisoned"""
    damage_per_turn: int = 1
    
    def __post_init__(self):
        self.effect_type = "poisoned"

@dataclass  
class BlessedComponent(StatusEffectComponent):
    """Entity has divine blessing"""
    bonus_amount: int = 1
    
    def __post_init__(self):
        self.effect_type = "blessed"

@dataclass
class CursedComponent(StatusEffectComponent):
    """Entity is cursed"""
    penalty_amount: int = 1
    
    def __post_init__(self):
        self.effect_type = "cursed"

@dataclass
class OnFireComponent(StatusEffectComponent):
    """Entity is burning"""
    fire_damage: int = 1
    spread_chance: float = 0.1
    
    def __post_init__(self):
        self.effect_type = "on_fire"

@dataclass
class WetComponent(StatusEffectComponent):
    """Entity is wet (affects fire and electricity)"""
    
    def __post_init__(self):
        self.effect_type = "wet"

# =============================================================================
# SPECIAL COMPONENTS
# =============================================================================

@dataclass
class FlammableComponent(Component):
    """Entity can catch fire"""
    ignition_chance: float = 0.1  # Chance to ignite when exposed to fire
    burn_damage: int = 1
    fire_resistance: int = 0  # Reduces fire damage

@dataclass
class MagicalComponent(Component):
    """Entity has magical properties"""
    magic_type: str = "generic"  # fire, ice, holy, shadow, etc.
    magic_intensity: int = 1
    enchanted: bool = False

@dataclass
class PuzzleElementComponent(Component):
    """Part of a puzzle mechanism"""
    puzzle_id: str
    element_type: str  # pressure_plate, glyph, altar, etc.
    active: bool = False
    required_for_solution: bool = True

@dataclass
class PressurePlateComponent(Component):
    """Activated by entities standing on it"""
    required_weight: int = 1  # Number of entities needed
    currently_pressed_by: Set['EntityID'] = field(default_factory=set)
    
    @property
    def is_pressed(self) -> bool:
        return len(self.currently_pressed_by) >= self.required_weight

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_component_dependencies() -> Dict[type, List[type]]:
    """Returns component dependencies - which components require others"""
    return {
        EquippedComponent: [ItemComponent],  # Only items can be equipped
        WeaponComponent: [ItemComponent],    # Only items can be weapons
        ArmorComponent: [ItemComponent],     # Only items can be armor
        CombatStatsComponent: [StatsComponent],  # Combat stats need base stats
        AIComponent: [PositionComponent],    # AI needs position to work
        VisionComponent: [PositionComponent], # Vision needs position
        LightSourceComponent: [PositionComponent], # Light sources need position
    }

def validate_entity_components(world, entity_id) -> List[str]:
    """Validate that an entity's components are consistent"""
    errors = []
    dependencies = get_component_dependencies()
    
    for comp_type, required_types in dependencies.items():
        if world.has_component(entity_id, comp_type):
            for required_type in required_types:
                if not world.has_component(entity_id, required_type):
                    errors.append(f"Entity has {comp_type.__name__} but missing required {required_type.__name__}")
    
    return errors