# game_constants.py - Enhanced with examination system and action framework
from enum import Enum
from typing import Dict, List

# --- Configuration ---
JSON_FILE = 'dungeon.json'
FONT_FILE = 'JetBrainsMonoNL-Regular.ttf'
BASE_FONT_SIZE = 16
BASE_CELL_SIZE = 24
INITIAL_VIEWPORT_WIDTH = 12
INITIAL_VIEWPORT_HEIGHT = 9
DEFAULT_ZOOM = 3.3
MIN_ZOOM = 0.5
MAX_ZOOM = 4.0
ZOOM_STEP = 0.1
HUD_HEIGHT = 120

# --- Colors ---
COLOR_BG = (183, 172, 160)
COLOR_VOID = (183, 172, 160)
COLOR_FLOOR = (240, 236, 224)
COLOR_FLOOR_GRID = (162, 160, 154)
COLOR_WALL = (0, 0, 0)
COLOR_WALL_SHADOW = (140, 134, 125)
COLOR_DOOR = (197, 185, 172)
COLOR_NOTE = (255, 255, 0)
COLOR_PLAYER = (255, 64, 64)
COLOR_MONSTER = (0, 150, 50)
COLOR_COLUMN = (100, 100, 100)
COLOR_WATER = (100, 150, 200)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_HP_BAR = (220, 20, 60)
COLOR_XP_BAR = (135, 206, 250)
COLOR_BAR_BG = (50, 50, 50)
COLOR_TORCH_ICON = (255, 165, 0)
COLOR_SPELL_CURSOR = (255, 0, 255)
COLOR_SPELL_MENU_BG = (10, 10, 40, 220)
COLOR_INPUT_BOX_ACTIVE = (200, 200, 255)
COLOR_INVENTORY_BG = (20, 20, 20)
COLOR_SELECTED_ITEM = (100, 150, 100)
COLOR_EQUIPPED_ITEM = (150, 100, 50)
COLOR_GREEN = (100, 255, 100)
COLOR_RED = (255, 100, 100)

# Puzzle-specific colors
COLOR_ALTAR = (255, 255, 255)
COLOR_HOLY_LIGHT = (255, 255, 100)
COLOR_BOULDER = (139, 69, 19)
COLOR_PRESSURE_PLATE = (100, 100, 150)
COLOR_PRESSURE_PLATE_ACTIVE = (150, 150, 255)
COLOR_GLYPH = (100, 255, 100)
COLOR_GLYPH_ACTIVE = (0, 255, 0)
COLOR_BARRIER = (255, 0, 0)
COLOR_CHEST = (160, 82, 45)
COLOR_TRAP_INDICATOR = (255, 165, 0)

# Examination system colors
COLOR_EXAMINE_CURSOR = (255, 255, 0)
COLOR_EXAMINE_HIGHLIGHT = (255, 255, 0, 100)
COLOR_EXAMINE_TEXTBOX_BG = (0, 0, 0, 200)
COLOR_ACTION_MENU_BG = (0, 0, 0, 240)
COLOR_INTERACTION_FEEDBACK = (100, 255, 100)
COLOR_WARNING_TEXT = (255, 100, 100)
COLOR_INFO_TEXT = (200, 200, 255)

# Action result colors
COLOR_SUCCESS = (100, 255, 100)
COLOR_FAILURE = (255, 100, 100)
COLOR_NEUTRAL = (200, 200, 200)

# --- UI Icons ---
UI_ICONS = {
    "DAGGER": "\U0001F5E1",
    "SHIELD": "\U0001F6E1",
    "MONSTER": "\U0001F47D",
    "SPELL_CURSOR": "☄",
    "HEART": "♥",
    "SUN": "☼",
    "GOLD": "¤",
    # Puzzle elements
    "ALTAR": "Π",
    "HOLY_LIGHT": "⊕",
    "BOULDER": "■",
    "PRESSURE_PLATE": "◉",
    "GLYPH": "∴",
    "BARRIER": "≡",
    "STAIRS_DOWN": "∇",
    "CHEST": "⊠",
    # Examination system icons
    "EXAMINE_CURSOR": "✚",
    "LOOK_ICON": "👁",
    "ACTION_ICON": "⚡",
    "INTERACTION_ICON": "🤝",
    "MOVEMENT_ICON": "→",
    "SPELL_ICON": "✨",
    "ITEM_ICON": "🎒",
    "COMBAT_ICON": "⚔",
    "SUCCESS_ICON": "✓",
    "FAILURE_ICON": "✗",
    "WARNING_ICON": "⚠",
    "INFO_ICON": "ℹ"
}

# --- Game States ---
class GameState(Enum):
    MAIN_MENU = 0
    CHAR_CREATION = 1
    PLAYING = 10
    SPELL_MENU = 11
    SPELL_TARGETING = 12
    INVENTORY = 13
    EQUIPMENT = 14
    CONTAINER_VIEW = 15
    ITEM_ACTION = 16
    COMBAT = 17
    EXAMINING = 18
    EXAMINING_ACTION_MENU = 19  # Sub-state for action selection during examination

# --- Tile Types ---
class TileType(Enum):
    VOID = 0
    FLOOR = 1
    DOOR_HORIZONTAL = 2
    DOOR_VERTICAL = 3
    DOOR_OPEN = 4
    NOTE = 5
    STAIRS_HORIZONTAL = 6
    STAIRS_VERTICAL = 7
    # Puzzle elements
    ALTAR = 10
    HOLY_LIGHT = 11
    BOULDER = 12
    PRESSURE_PLATE = 13
    PRESSURE_PLATE_ACTIVE = 14
    GLYPH = 15
    GLYPH_ACTIVE = 16
    BARRIER = 17
    STAIRS_DOWN = 18
    CHEST = 19

# --- Puzzle Types ---
class PuzzleType(Enum):
    BOULDER_PRESSURE_PLATE = 1
    RUNE_SEQUENCE = 2
    SWITCH_COMBINATION = 3
    RIDDLE_DOOR = 4

# --- Puzzle States ---
class PuzzleState(Enum):
    INACTIVE = 0
    ACTIVE = 1
    SOLVING = 2
    SOLVED = 3
    FAILED = 4

# --- Examination System Types ---
class ExamineMode(Enum):
    INACTIVE = 0
    LOOKING = 1
    ACTION_MENU = 2

class ActionCategory(Enum):
    MOVEMENT = "movement"
    SPELL = "spell" 
    ITEM = "item"
    INTERACTION = "interaction"
    COMBAT = "combat"

class ActionResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    INVALID = "invalid"

# --- Input Keys for Examination ---
EXAMINATION_KEYS = {
    'ACTIVATE': 'l',  # L key to enter examination mode
    'MOVE_UP': ['up', 'w'],
    'MOVE_DOWN': ['down', 's'],
    'MOVE_LEFT': ['left', 'a'],
    'MOVE_RIGHT': ['right', 'd'],
    'SELECT': 'return',
    'CANCEL': 'escape',
    'CYCLE_ACTIONS': 'tab'
}

# --- Examination System Constants ---
EXAMINATION_CONFIG = {
    'MAX_EXAMINE_DISTANCE': 20,  # Maximum distance for examination
    'ACTION_MENU_MAX_ITEMS': 8,  # Maximum actions to show in menu
    'TEXT_WRAP_WIDTH': 350,      # Width for text wrapping in examination boxes
    'CURSOR_BLINK_RATE': 500,    # Milliseconds for cursor blinking
    'FEEDBACK_DURATION': 2000,   # How long to show action feedback (ms)
    'AUTO_CLOSE_DELAY': 5000     # Auto-close examination after inactivity (ms)
}

# --- Action System Constants ---
ACTION_REQUIREMENTS = {
    'TOUCH': {'distance': 1, 'requires_los': True},
    'PUSH': {'distance': 1, 'requires_los': True, 'requires_strength': True},
    'CAST_SPELL': {'distance': None, 'requires_los': True, 'requires_mana': True},  # Distance varies by spell
    'USE_ITEM': {'distance': None, 'requires_los': False},  # Distance varies by item
    'ATTACK': {'distance': 1, 'requires_los': True, 'requires_weapon': False},
    'PRAY': {'distance': 1, 'requires_los': True},
    'OPEN': {'distance': 1, 'requires_los': True},
    'SEARCH': {'distance': 1, 'requires_los': True}
}

# --- Spell Range Types ---
class SpellRange(Enum):
    SELF = "self"
    TOUCH = "touch"
    CLOSE = "close"      # 5 feet / 1 cell
    NEAR = "near"        # 30 feet / 6 cells  
    FAR = "far"          # 150 feet / 30 cells
    SIGHT = "sight"      # Line of sight

# --- Item Range Types ---
class ItemRange(Enum):
    TOUCH = 1
    CLOSE = 1
    NEAR = 6
    FAR = 20
    THROWN = 10

# --- Status Effect Types ---
class StatusEffect(Enum):
    ICE_ENCHANTED = "ice_enchanted"
    BURNING = "burning"
    ELECTRIFIED = "electrified"
    SHADOW_TAINTED = "shadow_tainted"
    PURIFIED = "purified"
    BLESSED = "blessed"
    CURSED = "cursed"
    POISONED = "poisoned"
    PARALYZED = "paralyzed"
    CONFUSED = "confused"

# --- Interaction Feedback Messages ---
INTERACTION_MESSAGES = {
    'SUCCESS': {
        'boulder_pushed': "You successfully push the boulder!",
        'door_opened': "The door swings open.",
        'chest_opened': "The chest creaks open, revealing its contents.",
        'altar_prayed': "Your prayer is heard, and you feel blessed.",
        'trap_disarmed': "You carefully disarm the trap mechanism.",
        'spell_cast': "The spell takes effect successfully.",
        'item_used': "You use the item effectively."
    },
    'FAILURE': {
        'boulder_blocked': "The boulder won't budge - something is blocking its path.",
        'door_locked': "The door is firmly locked.",
        'chest_trapped': "A trap triggers as you try to open the chest!",
        'spell_failed': "The spell fizzles out without effect.",
        'item_ineffective': "The item has no effect here.",
        'action_impossible': "You cannot perform that action here."
    },
    'BLOCKED': {
        'out_of_range': "You are too far away to do that.",
        'no_line_of_sight': "You cannot see your target clearly.",
        'insufficient_resources': "You lack the necessary resources.",
        'wrong_tool': "You need a different tool for that task."
    }
}

# --- Entity Categories for Examination ---
ENTITY_CATEGORIES = {
    'INTERACTIVE': ['altar', 'chest', 'door', 'lever', 'button'],
    'MOVEABLE': ['boulder', 'crate', 'barrel'],
    'READABLE': ['note', 'book', 'scroll', 'sign'],
    'MAGICAL': ['glyph', 'rune', 'barrier', 'portal'],
    'DECORATIVE': ['column', 'statue', 'painting', 'tapestry'],
    'ENVIRONMENTAL': ['water', 'fire', 'pit', 'wall'],
    'CREATURE': ['monster', 'npc', 'familiar', 'pet']
}

# --- Default Entity Descriptions ---
DEFAULT_DESCRIPTIONS = {
    'DISTANT': "You can see something there, but you're too far away to make out details.",
    'UNKNOWN': "You see something here, but you're not sure what it is.",
    'BLOCKED': "Your view is obstructed.",
    'DARK': "It's too dark to see clearly.",
    'EMPTY': "There's nothing special here.",
    'UNREACHABLE': "You cannot reach that location."
}

# --- Examination UI Layout ---
EXAMINATION_UI = {
    'TEXTBOX_MIN_WIDTH': 300,
    'TEXTBOX_MAX_WIDTH': 450,
    'TEXTBOX_MIN_HEIGHT': 100,
    'TEXTBOX_MAX_HEIGHT': 300,
    'ACTION_MENU_WIDTH': 280,
    'ACTION_MENU_MIN_HEIGHT': 120,
    'PADDING': 15,
    'BORDER_WIDTH': 2,
    'TEXT_LINE_HEIGHT': 22,
    'ACTION_ITEM_HEIGHT': 30
}

# --- Key Binding Categories ---
class KeyCategory(Enum):
    MOVEMENT = "movement"
    INTERACTION = "interaction"
    EXAMINATION = "examination"
    INVENTORY = "inventory"
    COMBAT = "combat"
    SYSTEM = "system"

# --- Default Key Bindings ---
DEFAULT_KEYBINDS = {
    KeyCategory.MOVEMENT: {
        'move_north': ['w', 'up'],
        'move_south': ['s', 'down'],
        'move_east': ['d', 'right'],
        'move_west': ['a', 'left'],
        'wait': ['space', 'period']
    },
    KeyCategory.INTERACTION: {
        'use': ['space'],
        'get': ['g'],
        'drop': ['q'],
        'interact': ['enter']
    },
    KeyCategory.EXAMINATION: {
        'examine': ['l'],
        'look_around': ['shift+l'],
        'quick_examine': ['x']
    },
    KeyCategory.INVENTORY: {
        'inventory': ['i'],
        'equipment': ['e'],
        'quiver': ['q'],
        'spells': ['m']
    },
    KeyCategory.COMBAT: {
        'attack': ['return'],
        'defend': ['space'],
        'flee': ['shift+f']
    },
    KeyCategory.SYSTEM: {
        'fullscreen': ['f11'],
        'zoom_in': ['plus', 'equals'],
        'zoom_out': ['minus'],
        'escape': ['escape'],
        'help': ['f1', 'h']
    }
}

# --- Difficulty Settings ---
class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal" 
    HARD = "hard"
    NIGHTMARE = "nightmare"

DIFFICULTY_MODIFIERS = {
    Difficulty.EASY: {
        'monster_health': 0.75,
        'monster_damage': 0.75,
        'trap_damage': 0.5,
        'puzzle_hints': True,
        'examination_range': 1.5
    },
    Difficulty.NORMAL: {
        'monster_health': 1.0,
        'monster_damage': 1.0,
        'trap_damage': 1.0,
        'puzzle_hints': False,
        'examination_range': 1.0
    },
    Difficulty.HARD: {
        'monster_health': 1.25,
        'monster_damage': 1.25,
        'trap_damage': 1.5,
        'puzzle_hints': False,
        'examination_range': 0.75
    },
    Difficulty.NIGHTMARE: {
        'monster_health': 1.5,
        'monster_damage': 1.5,
        'trap_damage': 2.0,
        'puzzle_hints': False,
        'examination_range': 0.5
    }
}

# --- Audio Cues (for future sound system) ---
AUDIO_CUES = {
    'EXAMINATION': {
        'cursor_move': 'ui_cursor_move.wav',
        'item_select': 'ui_item_select.wav',
        'action_confirm': 'ui_action_confirm.wav',
        'action_cancel': 'ui_action_cancel.wav',
        'examine_start': 'ui_examine_start.wav',
        'examine_end': 'ui_examine_end.wav'
    },
    'INTERACTION': {
        'door_open': 'world_door_open.wav',
        'door_close': 'world_door_close.wav',
        'chest_open': 'world_chest_open.wav',
        'boulder_push': 'world_boulder_push.wav',
        'altar_pray': 'world_altar_pray.wav',
        'trap_trigger': 'world_trap_trigger.wav',
        'spell_cast': 'magic_spell_cast.wav',
        'item_use': 'inventory_item_use.wav',
        'success': 'ui_success.wav',
        'failure': 'ui_failure.wav'
    },
    'PUZZLE': {
        'pressure_plate_activate': 'puzzle_pressure_plate_on.wav',
        'pressure_plate_deactivate': 'puzzle_pressure_plate_off.wav',
        'glyph_activate': 'puzzle_glyph_glow.wav',
        'barrier_deactivate': 'puzzle_barrier_down.wav',
        'puzzle_solved': 'puzzle_complete.wav'
    }
}

# --- Accessibility Options ---
ACCESSIBILITY = {
    'HIGH_CONTRAST': False,
    'LARGE_TEXT': False,
    'COLORBLIND_FRIENDLY': False,
    'SCREEN_READER_SUPPORT': False,
    'REDUCED_MOTION': False,
    'AUDIO_CUES_ENABLED': True,
    'EXAMINATION_HINTS': True,
    'AUTO_PAUSE_ON_EXAMINE': True
}

# --- Debug Options ---
DEBUG_OPTIONS = {
    'SHOW_COORDINATES': False,
    'SHOW_ENTITY_IDS': False,
    'SHOW_ACTION_REQUIREMENTS': False,
    'LOG_INTERACTIONS': True,
    'HIGHLIGHT_WALKABLE': False,
    'SHOW_LINE_OF_SIGHT': False,
    'EXAMINATION_DEBUG': False
}

# --- Performance Settings ---
PERFORMANCE = {
    'MAX_VISIBLE_ENTITIES': 100,
    'EXAMINATION_UPDATE_RATE': 60,  # FPS for examination cursor updates
    'UI_ANIMATION_SPEED': 1.0,
    'PARTICLE_DENSITY': 1.0,
    'EFFECT_QUALITY': 'high'  # low, medium, high, ultra
}

# --- Localization Support ---
class Language(Enum):
    ENGLISH = "en"
    SPANISH = "es" 
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    JAPANESE = "ja"
    CHINESE = "zh"

# Text keys for localization
TEXT_KEYS = {
    'EXAMINATION': {
        'MODE_ACTIVATED': 'examination.mode_activated',
        'MODE_DEACTIVATED': 'examination.mode_deactivated',
        'NO_TARGET': 'examination.no_target',
        'OUT_OF_RANGE': 'examination.out_of_range',
        'SELECT_ACTION': 'examination.select_action',
        'DISTANCE_INDICATOR': 'examination.distance_indicator'
    },
    'ACTIONS': {
        'TOUCH': 'action.touch',
        'PUSH': 'action.push',
        'PRAY': 'action.pray',
        'OPEN': 'action.open',
        'SEARCH': 'action.search',
        'CAST_SPELL': 'action.cast_spell',
        'USE_ITEM': 'action.use_item',
        'ATTACK': 'action.attack'
    },
    'FEEDBACK': {
        'SUCCESS': 'feedback.success',
        'FAILURE': 'feedback.failure',
        'BLOCKED': 'feedback.blocked',
        'INVALID': 'feedback.invalid'
    },
    'UI': {
        'AVAILABLE_ACTIONS': 'ui.available_actions',
        'DISTANCE': 'ui.distance',
        'REQUIREMENTS': 'ui.requirements',
        'EFFECTS': 'ui.effects'
    }
}

# --- Version Information ---
GAME_VERSION = {
    'MAJOR': 1,
    'MINOR': 0,
    'PATCH': 0,
    'BUILD': 'alpha',
    'EXAMINATION_SYSTEM_VERSION': '1.0.0'
}

# --- Feature Flags ---
FEATURE_FLAGS = {
    'EXAMINATION_SYSTEM': True,
    'ADVANCED_INTERACTIONS': True,
    'CONTEXTUAL_ACTIONS': True,
    'DYNAMIC_DESCRIPTIONS': True,
    'ACTION_HISTORY': True,
    'SMART_TARGETING': True,
    'GESTURE_COMMANDS': False,  # Future feature
    'VOICE_COMMANDS': False,    # Future feature
    'VR_SUPPORT': False         # Future feature
}
# Add these constants to your existing game_constants.py file

# =============================================================================
# ECS SYSTEM CONSTANTS - Phase 2
# =============================================================================

# ECS Update frequencies (in Hz)
ECS_UPDATE_FREQUENCY = 60
ECS_PHYSICS_FREQUENCY = 60
ECS_AI_FREQUENCY = 30  # AI systems can run slower

# ECS Component limits
MAX_ENTITIES_PER_WORLD = 10000
MAX_COMPONENTS_PER_ENTITY = 32
ECS_CACHE_SIZE = 256

# ECS System priorities (lower numbers = higher priority)
SYSTEM_PRIORITY = {
    'InputSystem': 10,
    'MovementSystem': 20,
    'PhysicsSystem': 30,
    'AISystem': 40,
    'CombatSystem': 50,
    'StatusEffectSystem': 60,
    'InteractionSystem': 70,
    'RenderSystem': 80,
    'UISystem': 90,
    'AudioSystem': 100
}

# ECS Event types
class ECSEventType(Enum):
    # Core events
    ENTITY_CREATED = "entity_created"
    ENTITY_DESTROYED = "entity_destroyed"
    COMPONENT_ADDED = "component_added"
    COMPONENT_REMOVED = "component_removed"
    
    # Game events
    PLAYER_MOVED = "player_moved"
    ENTITY_DAMAGED = "entity_damaged"
    ENTITY_HEALED = "entity_healed"
    ENTITY_DIED = "entity_died"
    
    # Interaction events
    ITEM_PICKED_UP = "item_picked_up"
    ITEM_DROPPED = "item_dropped"
    DOOR_OPENED = "door_opened"
    DOOR_CLOSED = "door_closed"
    
    # Combat events
    ATTACK_INITIATED = "attack_initiated"
    ATTACK_HIT = "attack_hit"
    ATTACK_MISSED = "attack_missed"
    SPELL_CAST = "spell_cast"

# ECS Performance settings
ECS_PERFORMANCE = {
    'MAX_EVENTS_PER_FRAME': 100,
    'MAX_QUERIES_PER_FRAME': 1000,
    'ENABLE_PROFILING': False,
    'LOG_SLOW_SYSTEMS': True,
    'SLOW_SYSTEM_THRESHOLD_MS': 16.0  # Systems taking longer than 16ms
}

# ECS Debug settings
ECS_DEBUG = {
    'SHOW_ENTITY_IDS': False,
    'SHOW_COMPONENT_COUNTS': False,
    'SHOW_SYSTEM_PERFORMANCE': False,
    'LOG_EVENTS': False,
    'HIGHLIGHT_ACTIVE_ENTITIES': False
}

# ECS Rendering constants
ECS_RENDER = {
    'DEFAULT_LAYER': 0,
    'FLOOR_LAYER': 0,
    'ITEM_LAYER': 1,
    'CREATURE_LAYER': 5,
    'EFFECT_LAYER': 8,
    'UI_LAYER': 10,
    'DEBUG_LAYER': 15
}

print("✅ ECS constants loaded for Phase 2")