# Inventory/Equipment state
import pygame
import json
import random
import time
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import character creation
from character_creation import run_character_creation, Player

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

# --- UI Icons ---
UI_ICONS = {
    "DAGGER": "\U0001F5E1",
    "SHIELD": "\U0001F6E1",
    "MONSTER": "\U0001F47D",
    "SPELL_CURSOR": "☄",
    "HEART": "♥",
    "SUN": "☼",
    "GOLD": "¤"
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

# --- Spell Range Implementation ---
def get_spell_range_in_cells(spell_name: str) -> int:
    """Convert spell ranges to grid cells (5 feet per cell)"""
    # Based on the gear document: close=5ft, near=30ft, far=sight
    if spell_name in ["Cure Wounds", "Holy Weapon", "Light", "Protection From Evil", 
                      "Burning Hands", "Detect Magic", "Hold Portal", "Mage Armor", "Alarm"]:
        return 1  # Close range (5 feet = 1 cell)
    elif spell_name in ["Turn Undead", "Charm Person", "Floating Disk", "Sleep"]:
        return 6  # Near range (30 feet = 6 cells)
    elif spell_name in ["Magic Missile"]:
        return 20  # Far range (within sight, limited for gameplay)
    else:
        return 1  # Default to close range

def is_valid_spell_target(player_pos: Tuple[int, int], target_pos: Tuple[int, int], 
                         spell_name: str) -> bool:
    """Check if spell target is within range"""
    max_range = get_spell_range_in_cells(spell_name)
    distance = max(abs(target_pos[0] - player_pos[0]), 
                   abs(target_pos[1] - player_pos[1]))
    return distance <= max_range

def draw_spell_range_indicator(surface: pygame.Surface, player_pos: Tuple[int, int], 
                              spell_name: str, viewport_x: int, viewport_y: int, 
                              cell_size: int, viewport_width_cells: int, viewport_height_cells: int):
    """Draw spell range indicator around player"""
    max_range = get_spell_range_in_cells(spell_name)
    player_screen_x = (viewport_width_cells // 2) * cell_size + (cell_size // 2)
    player_screen_y = (viewport_height_cells // 2) * cell_size + (cell_size // 2)
    
    # Create transparent surface for range indicator
    range_size = max_range * cell_size
    if range_size > 0:
        range_surface = pygame.Surface((range_size * 2, range_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(range_surface, (255, 255, 0, 50), 
                          (range_size, range_size), range_size)
        
        range_rect = (player_screen_x - range_size, player_screen_y - range_size)
        surface.blit(range_surface, range_rect)

# --- Container/Backpack System ---
@dataclass
class Container:
    """Represents a container that can hold items"""
    name: str
    capacity: int  # Max gear slots it can hold
    contents: List = field(default_factory=list)  # List of InventoryItems
    
    def get_used_capacity(self) -> int:
        """Calculate how many gear slots are used in this container"""
        total = 0
        for inv_item in self.contents:
            try:
                from gear_selection import GearItem
                if hasattr(inv_item.item, 'gear_slots'):
                    slots_per_item = inv_item.item.gear_slots
                    if hasattr(inv_item.item, 'quantity_per_slot') and inv_item.item.quantity_per_slot > 1:
                        # Items that can stack
                        slots_needed = (inv_item.quantity + inv_item.item.quantity_per_slot - 1) // inv_item.item.quantity_per_slot
                        total += slots_needed * slots_per_item
                    else:
                        total += slots_per_item * inv_item.quantity
                else:
                    total += inv_item.quantity
            except ImportError:
                total += inv_item.quantity
        return total
    
    def can_fit_item(self, item, quantity: int = 1) -> bool:
        """Check if item can fit in this container"""
        try:
            from gear_selection import GearItem
            if hasattr(item, 'gear_slots'):
                slots_needed = item.gear_slots * quantity
                if hasattr(item, 'quantity_per_slot') and item.quantity_per_slot > 1:
                    slots_needed = (quantity + item.quantity_per_slot - 1) // item.quantity_per_slot
                return self.get_used_capacity() + slots_needed <= self.capacity
            else:
                return self.get_used_capacity() + quantity <= self.capacity
        except ImportError:
            return self.get_used_capacity() + quantity <= self.capacity

def is_container(item) -> bool:
    """Check if an item is a container"""
    return hasattr(item, 'name') and 'Backpack' in item.name

def get_containers_from_inventory(player: Player) -> List[Container]:
    """Get all containers from player's inventory"""
    containers = []
    
    # Find backpacks and convert them to containers
    for inv_item in player.inventory:
        if is_container(inv_item.item):
            # Create container for each backpack
            for i in range(inv_item.quantity):
                container_name = f"{inv_item.item.name} {i+1}" if inv_item.quantity > 1 else inv_item.item.name
                # Standard backpack holds all items the character can carry
                capacity = player.max_gear_slots
                containers.append(Container(container_name, capacity))
    
    # If no backpacks, create a default "carried items" container
    if not containers:
        containers.append(Container("Carried Items", player.max_gear_slots))
    
    return containers

def organize_inventory_into_containers(player: Player) -> List[Container]:
    """Organize player's inventory into containers"""
    containers = get_containers_from_inventory(player)
    
    if not containers:
        return containers
    
    # For now, put all non-container items in the first container
    main_container = containers[0]
    
    for inv_item in player.inventory:
        if not is_container(inv_item.item):
            # Check if item can fit
            if main_container.can_fit_item(inv_item.item, inv_item.quantity):
                main_container.contents.append(inv_item)
            else:
                # Try other containers or create overflow
                placed = False
                for container in containers[1:]:
                    if container.can_fit_item(inv_item.item, inv_item.quantity):
                        container.contents.append(inv_item)
                        placed = True
                        break
                
                if not placed:
                    # Create overflow container
                    overflow = Container("Overflow (No Backpack)", player.max_gear_slots)
                    overflow.contents.append(inv_item)
                    containers.append(overflow)
    
    return containers
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

def calculate_armor_class(player: Player) -> int:
    """Calculate player's AC based on equipped armor"""
    base_ac = 10
    dex_modifier = get_stat_modifier(player.dexterity)
    
    # Check for equipped armor
    if 'armor' in player.equipment:
        armor_name = player.equipment['armor'].item.name
        if 'Leather' in armor_name:
            base_ac = 11 + dex_modifier
        elif 'Chainmail' in armor_name:
            base_ac = 13 + dex_modifier
        elif 'Plate' in armor_name:
            base_ac = 15
    else:
        # No armor, just dex bonus
        base_ac = 10 + dex_modifier
    
    # Add shield bonus
    if 'shield' in player.equipment:
        base_ac += 2
    
    return base_ac

def get_equipped_weapon_damage(player: Player) -> str:
    """Get damage of equipped weapon"""
    if 'weapon' in player.equipment:
        weapon = player.equipment['weapon'].item
        if hasattr(weapon, 'damage'):
            return weapon.damage
    return "1d4"  # Unarmed damage

def can_equip_item(player: Player, item) -> bool:
    """Check if player can equip an item based on class restrictions"""
    # Import here to avoid circular imports
    try:
        from gear_selection import CLASS_WEAPON_RESTRICTIONS, CLASS_ARMOR_RESTRICTIONS, Weapon, Armor
        
        if isinstance(item, Weapon):
            restrictions = CLASS_WEAPON_RESTRICTIONS.get(player.character_class, [])
            if restrictions and item.name not in restrictions:
                return False
        elif isinstance(item, Armor):
            restrictions = CLASS_ARMOR_RESTRICTIONS.get(player.character_class, [])
            if restrictions and item.name not in restrictions:
                return False
    except ImportError:
        pass  # If gear_selection not available, allow all equipment
    
    return True

def get_equipment_slot(item) -> str:
    """Determine which equipment slot an item goes in"""
    try:
        from gear_selection import Weapon, Armor
        
        if isinstance(item, Weapon):
            return 'weapon'
        elif isinstance(item, Armor):
            if 'Shield' in item.name:
                return 'shield'
            else:
                return 'armor'
        elif item.name == 'Torch':
            return 'light'
        elif item.name == 'Lantern':
            return 'light'
    except ImportError:
        pass
    
    return None

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

@dataclass
class Monster:
    x: int
    y: int
    room_id: int

@dataclass
class Room:
    id: int
    x: int
    y: int
    width: int
    height: int
    
    def contains_point(self, x: int, y: int) -> bool:
        return (self.x <= x < self.x + self.width and 
                self.y <= y < self.y + self.height)
    
    def get_cells(self) -> List[Tuple[int, int]]:
        cells = []
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                cells.append((x, y))
        return cells

@dataclass 
class Door:
    x: int
    y: int
    room1_id: int
    room2_id: int
    is_horizontal: bool
    type: int
    is_open: bool = False

@dataclass
class Note:
    x: int
    y: int
    content: str

@dataclass
class Column:
    x: int
    y: int

@dataclass
class WaterTile:
    x: int
    y: int

class DungeonExplorer:
    def __init__(self, dungeon_data: dict):
        self.rooms: Dict[int, Room] = {}
        self.doors: List[Door] = []
        self.notes: List[Note] = []
        self.columns: List[Column] = []
        self.water_tiles: List[WaterTile] = []
        self.tiles: Dict[Tuple[int, int], TileType] = {}
        self.revealed_rooms: Set[int] = set()
        self.monsters: List[Monster] = []
        
        self._parse_data(dungeon_data)
        self._generate_tiles()
        self._spawn_monsters()
        
        # Reveal the room at the starting position
        start_pos = self.get_starting_position()
        start_room_found = False
        for room_id, room in self.rooms.items():
            if room.contains_point(start_pos[0], start_pos[1]):
                self.reveal_room(room_id)
                start_room_found = True
                break
        
        # Fallback if starting position is not in any room
        if not start_room_found and self.rooms:
             first_room_id = list(self.rooms.keys())[0]
             self.reveal_room(first_room_id)
    
    def _parse_data(self, data: dict):
        # Parse rooms
        for i, rect in enumerate(data['rects']):
            self.rooms[i] = Room(i, rect['x'], rect['y'], rect['w'], rect['h'])
        
        # Parse doors
        for door_data in data['doors']:
            # Find which rooms this door connects
            connected_rooms = []
            for room_id, room in self.rooms.items():
                if room.contains_point(door_data['x'], door_data['y']):
                    connected_rooms.append(room_id)
                # Check if door is adjacent to room
                elif (abs(door_data['x'] - room.x) <= 1 and room.y <= door_data['y'] < room.y + room.height) or \
                     (abs(door_data['x'] - (room.x + room.width - 1)) <= 1 and room.y <= door_data['y'] < room.y + room.height) or \
                     (abs(door_data['y'] - room.y) <= 1 and room.x <= door_data['x'] < room.x + room.width) or \
                     (abs(door_data['y'] - (room.y + room.height - 1)) <= 1 and room.x <= door_data['x'] < room.x + room.width):
                    connected_rooms.append(room_id)
            
            # Determine orientation
            is_horizontal = True
            if len(connected_rooms) >= 2:
                room1 = self.rooms[connected_rooms[0]]
                room2 = self.rooms[connected_rooms[1]]
                # If rooms are vertically adjacent, door is horizontal
                if abs(room1.y - room2.y) > abs(room1.x - room2.x):
                    is_horizontal = True
                else:
                    is_horizontal = False
            
            door = Door(
                door_data['x'], door_data['y'],
                connected_rooms[0] if len(connected_rooms) > 0 else -1,
                connected_rooms[1] if len(connected_rooms) > 1 else -1,
                is_horizontal,
                door_data.get('type', 1)
            )
            self.doors.append(door)
        
        # Parse notes
        for note_data in data['notes']:
            self.notes.append(Note(
                int(note_data['pos']['x']),
                int(note_data['pos']['y']),
                note_data.get('text', 'Note')
            ))
        
        # Parse columns/pillars
        if 'columns' in data:
            for column_data in data['columns']:
                self.columns.append(Column(
                    column_data['x'],
                    column_data['y']
                ))
        
        # Parse water tiles
        if 'water' in data:
            for water_data in data['water']:
                self.water_tiles.append(WaterTile(
                    water_data['x'],
                    water_data['y']
                ))
    
    def _generate_tiles(self):
        # Calculate bounds
        min_x = min(room.x for room in self.rooms.values()) - 3
        max_x = max(room.x + room.width for room in self.rooms.values()) + 3
        min_y = min(room.y for room in self.rooms.values()) - 3
        max_y = max(room.y + room.height for room in self.rooms.values()) + 3
        
        self.bounds = (min_x, min_y, max_x - min_x, max_y - min_y)
        
        # Initialize as void
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                self.tiles[(x, y)] = TileType.VOID
        
        # Fill rooms with floors
        for room in self.rooms.values():
            for x, y in room.get_cells():
                self.tiles[(x, y)] = TileType.FLOOR
        
        # Place doors
        for door in self.doors:
            if door.is_open:
                self.tiles[(door.x, door.y)] = TileType.DOOR_OPEN
            # Types 0 (No Door) and 2 (Open Door) are just open passages
            elif door.type in [0, 2]:
                self.tiles[(door.x, door.y)] = TileType.DOOR_OPEN
            # Types 3, 7, and 9 are stairs
            elif door.type in [3, 7, 9]:
                self.tiles[(door.x, door.y)] = TileType.STAIRS_HORIZONTAL if door.is_horizontal else TileType.STAIRS_VERTICAL
            # Type 6 is a secret door, which initially appears as a wall.
            elif door.type == 6:
                # It's treated as a floor tile, but the wall drawing logic will draw a wall over it.
                continue
            # Types 1 (Door) and 5 (Locked Door) are standard doors
            elif door.type in [1, 5]:
                self.tiles[(door.x, door.y)] = TileType.DOOR_HORIZONTAL if door.is_horizontal else TileType.DOOR_VERTICAL
        
        # Place notes
        for note in self.notes:
            if (note.x, note.y) in self.tiles:
                self.tiles[(note.x, note.y)] = TileType.NOTE

    def _spawn_monsters(self):
        """Spawns monsters in rooms based on a random chance."""
        start_pos = self.get_starting_position()
        start_room_id = -1
        for room_id, room in self.rooms.items():
            if room.contains_point(start_pos[0], start_pos[1]):
                start_room_id = room_id
                break

        door_locations = {(d.x, d.y) for d in self.doors}

        for room_id, room in self.rooms.items():
            # Don't spawn monsters in the starting room
            if room_id == start_room_id:
                continue

            if random.randint(1, 6) <= 3:
                # Spawn a monster in a random valid cell of the room
                valid_cells = [cell for cell in room.get_cells() if cell not in door_locations]
                if valid_cells:
                    x, y = random.choice(valid_cells)
                    self.monsters.append(Monster(x=x, y=y, room_id=room_id))

    def reveal_room(self, room_id_to_reveal: int):
        """
        Reveals a given room and recursively reveals any adjacent rooms
        connected by open passages (passages, open doors, stairs).
        """
        if room_id_to_reveal < 0 or room_id_to_reveal in self.revealed_rooms:
            return

        # Use a queue for a breadth-first search of connected open rooms
        queue = [room_id_to_reveal]
        
        while queue:
            current_room_id = queue.pop(0)
            
            if current_room_id in self.revealed_rooms:
                continue
                
            self.revealed_rooms.add(current_room_id)
            
            # Find all doors connected to the newly revealed room
            for door in self.doors:
                neighbor_id = -1
                if door.room1_id == current_room_id:
                    neighbor_id = door.room2_id
                elif door.room2_id == current_room_id:
                    neighbor_id = door.room1_id
                
                # If it's a valid neighbor and the door is an open type, add to queue
                if neighbor_id >= 0 and door.type in [0, 2, 3, 7, 9]:
                    if neighbor_id not in self.revealed_rooms:
                        queue.append(neighbor_id)
    
    def get_walkable_positions(self, for_monster: bool = False) -> Set[Tuple[int, int]]:
        """Determines the set of tiles a character or monster can move to."""
        walkable = set()
        
        # Define which tiles are generally passable
        passable_tiles = {
            TileType.FLOOR, TileType.DOOR_OPEN, TileType.NOTE,
            TileType.STAIRS_HORIZONTAL, TileType.STAIRS_VERTICAL,
            TileType.DOOR_HORIZONTAL, TileType.DOOR_VERTICAL
        }
        
        for pos, tile_type in self.tiles.items():
            # A tile is walkable if its type is passable AND it's in a revealed area.
            if tile_type in passable_tiles and self.is_revealed(pos[0], pos[1]):
                 walkable.add(pos)
    
        return walkable
    
    def open_door_at_position(self, x: int, y: int) -> bool:
        for door in self.doors:
            if door.x == x and door.y == y and not door.is_open:
                # Regular (1), locked (5), and secret (6) doors can be "opened"
                if door.type in [1, 5, 6]:
                    door.is_open = True
                    self.tiles[(door.x, door.y)] = TileType.DOOR_OPEN
                    
                    # Reveal connected rooms, which will cascade if they lead to more open areas
                    if door.room1_id >= 0:
                        self.reveal_room(door.room1_id)
                    if door.room2_id >= 0:
                        self.reveal_room(door.room2_id)
                    
                    return True
        return False
    
    def get_starting_position(self) -> Tuple[int, int]:
        return (0, 0)
    
    def is_revealed(self, x: int, y: int) -> bool:
        """Check if a cell at given coordinates is revealed"""        
        # Check if in revealed room
        for room_id in self.revealed_rooms:
            room = self.rooms[room_id]
            if room.contains_point(x, y):
                return True
        
        # Check if it's a door that connects to at least one revealed room
        for door in self.doors:
            if door.x == x and door.y == y:
                # Secret doors are never revealed this way
                if door.type == 6 and not door.is_open:
                    return False
                # Door is visible if either connected room is revealed
                if (door.room1_id in self.revealed_rooms or 
                    door.room2_id in self.revealed_rooms):
                    return True
        
        return False

# --- Inventory & Equipment UI ---
def draw_inventory_screen(surface: pygame.Surface, player: Player, selected_index: int, 
                         font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw inventory management screen showing containers"""
    surface.fill(COLOR_BLACK)
    
    screen_width, screen_height = surface.get_size()
    
    # Title
    title_surf = font.render(f"{player.name}'s Inventory", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=screen_width//2, top=20)
    surface.blit(title_surf, title_rect)
    
    # Draw separator line
    separator_x = screen_width // 3 + 30
    pygame.draw.line(surface, COLOR_WHITE, (separator_x, 80), (separator_x, screen_height - 100), 2)
    
    # Get containers
    containers = organize_inventory_into_containers(player)
    
    # Left side - container list
    list_x = 20
    list_width = screen_width // 3
    y = 100
    
    if not containers:
        empty_surf = font.render("No containers found", True, COLOR_WHITE)
        surface.blit(empty_surf, (list_x, y))
    else:
        for i, container in enumerate(containers):
            # Highlight selected container
            if i == selected_index:
                highlight_rect = pygame.Rect(list_x - 5, y - 5, list_width - 30, 60)
                pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
                pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
            
            color = COLOR_BLACK if i == selected_index else COLOR_WHITE
            
            # Container name
            container_surf = font.render(container.name, True, color)
            surface.blit(container_surf, (list_x, y))
            
            # Container capacity info
            used_capacity = container.get_used_capacity()
            capacity_text = f"{used_capacity}/{container.capacity} slots"
            capacity_color = COLOR_RED if used_capacity > container.capacity else color
            capacity_surf = small_font.render(capacity_text, True, capacity_color)
            surface.blit(capacity_surf, (list_x, y + 25))
            
            # Item count
            item_count_text = f"{len(container.contents)} items"
            item_surf = small_font.render(item_count_text, True, color)
            surface.blit(item_surf, (list_x, y + 40))
            
            y += 70
    
    # Right side - container contents
    detail_x = separator_x + 20
    detail_width = screen_width - detail_x - 20
    
    if containers and 0 <= selected_index < len(containers):
        selected_container = containers[selected_index]
        draw_container_contents(surface, selected_container, detail_x, 100, detail_width, font, small_font)
    
    # Instructions
    instructions = ["UP/DOWN: Navigate containers", "ENTER: View container contents", "ESC: Back to game"]
    inst_y = screen_height - 60
    for instruction in instructions:
        inst_surf = small_font.render(instruction, True, COLOR_WHITE)
        inst_rect = inst_surf.get_rect(centerx=screen_width//2, y=inst_y)
        surface.blit(inst_surf, inst_rect)
        inst_y += 15

def draw_container_contents(surface: pygame.Surface, container: Container, x: int, y: int, width: int,
                           font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw the contents of a container"""
    current_y = y
    
    # Container header
    header_surf = font.render(f"Contents of {container.name}", True, COLOR_WHITE)
    surface.blit(header_surf, (x, current_y))
    current_y += 30
    
    # Capacity bar
    used_capacity = container.get_used_capacity()
    capacity_text = f"Capacity: {used_capacity}/{container.capacity}"
    capacity_surf = small_font.render(capacity_text, True, COLOR_WHITE)
    surface.blit(capacity_surf, (x, current_y))
    current_y += 20
    
    # Visual capacity bar
    bar_width = min(200, width - 20)
    bar_height = 8
    pygame.draw.rect(surface, (50, 50, 50), (x, current_y, bar_width, bar_height))
    
    if container.capacity > 0:
        fill_ratio = min(used_capacity / container.capacity, 1.0)
        fill_width = int(bar_width * fill_ratio)
        fill_color = COLOR_RED if used_capacity > container.capacity else COLOR_GREEN
        pygame.draw.rect(surface, fill_color, (x, current_y, fill_width, bar_height))
    
    current_y += 25
    
    # Contents list
    if not container.contents:
        empty_surf = small_font.render("(Empty)", True, (150, 150, 150))
        surface.blit(empty_surf, (x, current_y))
    else:
        for inv_item in container.contents:
            item_name = getattr(inv_item.item, 'name', 'Unknown Item')
            quantity = getattr(inv_item, 'quantity', 1)
            
            item_text = f"• {quantity}x {item_name}"
            item_surf = small_font.render(item_text, True, COLOR_WHITE)
            surface.blit(item_surf, (x, current_y))
            current_y += 18
            
            # Show item properties briefly
            if hasattr(inv_item.item, 'damage'):
                prop_text = f"    Damage: {inv_item.item.damage}"
                prop_surf = small_font.render(prop_text, True, (150, 150, 150))
                surface.blit(prop_surf, (x, current_y))
                current_y += 15
            elif hasattr(inv_item.item, 'ac_bonus'):
                prop_text = f"    AC: {inv_item.item.ac_bonus}"
                prop_surf = small_font.render(prop_text, True, (150, 150, 150))
                surface.blit(prop_surf, (x, current_y))
                current_y += 15
            
            current_y += 5

def draw_container_view_screen(surface: pygame.Surface, player: Player, container: Container, 
                              selected_index: int, font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw detailed container view for item management"""
    surface.fill(COLOR_BLACK)
    
    screen_width, screen_height = surface.get_size()
    
    # Title
    title_surf = font.render(f"Contents: {container.name}", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=screen_width//2, top=20)
    surface.blit(title_surf, title_rect)
    
    # Draw separator line
    separator_x = screen_width // 3 + 30
    pygame.draw.line(surface, COLOR_WHITE, (separator_x, 80), (separator_x, screen_height - 100), 2)
    
    # Left side - item list
    list_x = 20
    list_width = screen_width // 3
    y = 100
    
    if not container.contents:
        empty_surf = font.render("Container is empty", True, COLOR_WHITE)
        surface.blit(empty_surf, (list_x, y))
    else:
        for i, inv_item in enumerate(container.contents):
            # Highlight selected item
            if i == selected_index:
                highlight_rect = pygame.Rect(list_x - 5, y - 5, list_width - 30, 40)
                pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
                pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
            
            color = COLOR_BLACK if i == selected_index else COLOR_WHITE
            
            item_name = getattr(inv_item.item, 'name', 'Unknown Item')
            quantity = getattr(inv_item, 'quantity', 1)
            
            item_text = f"{quantity}x {item_name}"
            item_surf = font.render(item_text, True, color)
            surface.blit(item_surf, (list_x, y))
            y += 45
    
    # Right side - item details
    detail_x = separator_x + 20
    detail_width = screen_width - detail_x - 20
    
    if container.contents and 0 <= selected_index < len(container.contents):
        selected_item = container.contents[selected_index]
        draw_item_details(surface, selected_item.item, detail_x, 100, detail_width, font, small_font)
    
    # Container info at bottom of left side
    info_y = screen_height - 120
    used_capacity = container.get_used_capacity()
    capacity_text = f"Capacity: {used_capacity}/{container.capacity}"
    capacity_surf = small_font.render(capacity_text, True, COLOR_WHITE)
    surface.blit(capacity_surf, (list_x, info_y))
    
    # Instructions
    instructions = ["UP/DOWN: Navigate items", "ENTER: Item actions", "ESC: Back to containers"]
    inst_y = screen_height - 60
    for instruction in instructions:
        inst_surf = small_font.render(instruction, True, COLOR_WHITE)
        inst_rect = inst_surf.get_rect(centerx=screen_width//2, y=inst_y)
        surface.blit(inst_surf, inst_rect)
        inst_y += 15

def draw_item_action_screen(surface: pygame.Surface, item, selected_action: int,
                           font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw item action selection screen"""
    screen_width, screen_height = surface.get_size()
    
    # Semi-transparent overlay
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    # Action selection box
    box_width = 300
    box_height = 200
    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2
    
    # Background
    pygame.draw.rect(surface, COLOR_BLACK, (box_x, box_y, box_width, box_height))
    pygame.draw.rect(surface, COLOR_WHITE, (box_x, box_y, box_width, box_height), 2)
    
    # Title
    item_name = getattr(item, 'name', 'Unknown Item')
    title_surf = font.render(f"Actions: {item_name}", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=box_x + box_width//2, top=box_y + 10)
    surface.blit(title_surf, title_rect)
    
    # Action options
    actions = ["Use/Consume", "Equip", "Drop Here", "Throw", "Examine"]
    
    start_y = box_y + 50
    for i, action in enumerate(actions):
        action_y = start_y + i * 25
        
        if i == selected_action:
            highlight_rect = pygame.Rect(box_x + 10, action_y - 5, box_width - 20, 20)
            pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
        
        color = COLOR_BLACK if i == selected_action else COLOR_WHITE
        action_surf = small_font.render(action, True, color)
        surface.blit(action_surf, (box_x + 20, action_y))
    
    # Instructions
    inst_surf = small_font.render("UP/DOWN: Navigate  ENTER: Select  ESC: Cancel", True, COLOR_WHITE)
    inst_rect = inst_surf.get_rect(centerx=box_x + box_width//2, bottom=box_y + box_height - 10)
    surface.blit(inst_surf, inst_rect)

def draw_equipment_screen(surface: pygame.Surface, player: Player, selected_slot: str,
                         font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw equipment management screen"""
    surface.fill(COLOR_BLACK)  # Changed to black background
    
    screen_width, screen_height = surface.get_size()
    
    # Title
    title_surf = font.render(f"{player.name}'s Equipment", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=screen_width//2, top=20)
    surface.blit(title_surf, title_rect)
    
    # Draw separator line
    separator_x = screen_width // 3 + 30
    pygame.draw.line(surface, COLOR_WHITE, (separator_x, 80), (separator_x, screen_height - 100), 2)
    
    # Equipment slots
    equipment_slots = ['weapon', 'armor', 'shield', 'light']
    slot_names = {
        'weapon': 'Weapon',
        'armor': 'Armor', 
        'shield': 'Shield',
        'light': 'Light Source'
    }
    
    list_x = 20
    list_width = screen_width // 3
    y = 100
    
    for slot in equipment_slots:
        # Highlight selected slot
        if slot == selected_slot:
            highlight_rect = pygame.Rect(list_x - 5, y - 5, list_width - 30, 60)
            pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
            pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
        
        color = COLOR_BLACK if slot == selected_slot else COLOR_WHITE
        
        # Slot name
        slot_surf = font.render(slot_names[slot], True, color)
        surface.blit(slot_surf, (list_x, y))
        
        # Equipped item
        if slot in player.equipment:
            item_name = player.equipment[slot].item.name
            item_surf = small_font.render(f"  {item_name}", True, color)
            surface.blit(item_surf, (list_x, y + 25))
        else:
            empty_surf = small_font.render("  (Empty)", True, (150, 150, 150))
            surface.blit(empty_surf, (list_x, y + 25))
        
        y += 70
    
    # Right side - item details or available equipment
    detail_x = separator_x + 20
    detail_width = screen_width - detail_x - 20
    
    if selected_slot in player.equipment:
        # Show equipped item details
        equipped_item = player.equipment[selected_slot]
        draw_item_details(surface, equipped_item.item, detail_x, 100, detail_width, font, small_font)
    else:
        # Show available items for this slot
        available_items = get_available_items_for_slot(player, selected_slot)
        if available_items:
            avail_title = small_font.render("Available to equip:", True, COLOR_WHITE)
            surface.blit(avail_title, (detail_x, 100))
            
            item_y = 130
            for inv_item in available_items:
                item_surf = small_font.render(f"• {inv_item.item.name}", True, COLOR_WHITE)
                surface.blit(item_surf, (detail_x, item_y))
                item_y += 20
        else:
            no_items_surf = small_font.render("No items available for this slot", True, (150, 150, 150))
            surface.blit(no_items_surf, (detail_x, 100))
    
    # Instructions
    instructions = ["UP/DOWN: Navigate slots", "ENTER: Change equipment", "ESC: Back to game"]
    inst_y = screen_height - 60
    for instruction in instructions:
        inst_surf = small_font.render(instruction, True, COLOR_WHITE)
        inst_rect = inst_surf.get_rect(centerx=screen_width//2, y=inst_y)
        surface.blit(inst_surf, inst_rect)
        inst_y += 15

def draw_item_details(surface: pygame.Surface, item, x: int, y: int, width: int,
                     font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw detailed information about an item"""
    current_y = y
    
    # Item name
    item_name = getattr(item, 'name', 'Unknown Item')
    name_surf = font.render(item_name, True, COLOR_WHITE)
    surface.blit(name_surf, (x, current_y))
    current_y += 35
    
    # Item type/category
    category = getattr(item, 'category', 'General')
    category_surf = small_font.render(f"Category: {category}", True, (200, 200, 200))
    surface.blit(category_surf, (x, current_y))
    current_y += 25
    
    # Weapon-specific details
    if hasattr(item, 'damage'):
        damage_surf = small_font.render(f"Damage: {item.damage}", True, COLOR_WHITE)
        surface.blit(damage_surf, (x, current_y))
        current_y += 20
        
        if hasattr(item, 'weapon_properties') and item.weapon_properties:
            props_surf = small_font.render(f"Properties: {', '.join(item.weapon_properties)}", True, COLOR_WHITE)
            surface.blit(props_surf, (x, current_y))
            current_y += 20
    
    # Armor-specific details
    elif hasattr(item, 'ac_bonus'):
        ac_surf = small_font.render(f"Armor Class: {item.ac_bonus}", True, COLOR_WHITE)
        surface.blit(ac_surf, (x, current_y))
        current_y += 20
        
        if hasattr(item, 'armor_properties') and item.armor_properties:
            props_surf = small_font.render(f"Properties: {', '.join(item.armor_properties)}", True, COLOR_WHITE)
            surface.blit(props_surf, (x, current_y))
            current_y += 20
    
    # Gear slots
    gear_slots = getattr(item, 'gear_slots', 1)
    slots_surf = small_font.render(f"Gear Slots: {gear_slots}", True, COLOR_WHITE)
    surface.blit(slots_surf, (x, current_y))
    current_y += 20
    
    # Cost (if available)
    cost_text = format_item_cost(item)
    if cost_text != "Priceless":
        cost_surf = small_font.render(f"Value: {cost_text}", True, (255, 215, 0))
        surface.blit(cost_surf, (x, current_y))
        current_y += 25
    
    # Description
    description = getattr(item, 'description', '')
    if description:
        desc_lines = wrap_text(description, width - 20, small_font)
        for line in desc_lines:
            line_surf = small_font.render(line, True, COLOR_WHITE)
            surface.blit(line_surf, (x, current_y))
            current_y += 18

def format_item_cost(item) -> str:
    """Format item cost as a readable string"""
    if hasattr(item, 'cost_gp') and item.cost_gp > 0:
        return f"{item.cost_gp} gp"
    elif hasattr(item, 'cost_sp') and item.cost_sp > 0:
        return f"{item.cost_sp} sp"
    elif hasattr(item, 'cost_cp') and item.cost_cp > 0:
        return f"{item.cost_cp} cp"
    else:
        return "Priceless"

def wrap_text(text: str, max_width: int, font: pygame.font.Font) -> List[str]:
    """Wrap text to fit within max_width"""
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

def get_available_items_for_slot(player: Player, slot: str):
    """Get inventory items that can be equipped in the given slot"""
    available = []
    for inv_item in player.inventory:
        item_slot = get_equipment_slot(inv_item.item)
        if item_slot == slot and can_equip_item(player, inv_item.item):
            available.append(inv_item)
    return available

def equip_item(player: Player, inv_item, slot: str = None):
    """Equip an item to the appropriate slot"""
    if slot is None:
        slot = get_equipment_slot(inv_item.item)
    
    if slot and can_equip_item(player, inv_item.item):
        # Unequip current item in slot if any
        if slot in player.equipment:
            unequip_item(player, slot)
        
        # Equip new item
        player.equipment[slot] = inv_item
        
        # Update AC if armor/shield equipped
        if slot in ['armor', 'shield']:
            player.ac = calculate_armor_class(player)
        
        return True
    return False

def unequip_item(player: Player, slot: str):
    """Unequip an item from the given slot"""
    if slot in player.equipment:
        del player.equipment[slot]
        
        # Update AC if armor/shield unequipped
        if slot in ['armor', 'shield']:
            player.ac = calculate_armor_class(player)
        
        return True
    return False

def show_equipment_selection(surface: pygame.Surface, player: Player, slot: str, selected_index: int,
                           font: pygame.font.Font, small_font: pygame.font.Font):
    """Show selection screen for equipment slot"""
    screen_width, screen_height = surface.get_size()
    
    # Semi-transparent overlay
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    # Equipment selection box
    box_width = 400
    box_height = 300
    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2
    
    # Background
    pygame.draw.rect(surface, COLOR_INVENTORY_BG, (box_x, box_y, box_width, box_height))
    pygame.draw.rect(surface, COLOR_WHITE, (box_x, box_y, box_width, box_height), 2)
    
    # Title
    slot_names = {
        'weapon': 'Select Weapon',
        'armor': 'Select Armor', 
        'shield': 'Select Shield',
        'light': 'Select Light Source'
    }
    title_surf = font.render(slot_names.get(slot, f"Select {slot}"), True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=box_x + box_width//2, top=box_y + 10)
    surface.blit(title_surf, title_rect)
    
    # Available items
    available_items = get_available_items_for_slot(player, slot)
    available_items.insert(0, None)  # Add "Unequip" option
    
    start_y = box_y + 50
    for i, inv_item in enumerate(available_items):
        item_y = start_y + i * 30
        
        if i == selected_index:
            highlight_rect = pygame.Rect(box_x + 10, item_y - 5, box_width - 20, 25)
            pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
        
        color = COLOR_BLACK if i == selected_index else COLOR_WHITE
        
        if inv_item is None:
            item_text = "(Unequip)"
        else:
            item_text = inv_item.item.name
        
        item_surf = small_font.render(item_text, True, color)
        surface.blit(item_surf, (box_x + 20, item_y))
    
    # Instructions
    inst_surf = small_font.render("UP/DOWN: Navigate  ENTER: Select  ESC: Cancel", True, COLOR_WHITE)
    inst_rect = inst_surf.get_rect(centerx=box_x + box_width//2, bottom=box_y + box_height - 10)
    surface.blit(inst_surf, inst_rect)

# --- Original tile drawing functions (unchanged) ---
def draw_tile(surface: pygame.Surface, tile_type: TileType, x: int, y: int, cell_size: int):
    left = x * cell_size
    top = y * cell_size
    center_x = left + cell_size // 2
    center_y = top + cell_size // 2
    
    if tile_type == TileType.VOID:
        pygame.draw.rect(surface, COLOR_VOID, (left, top, cell_size, cell_size))
    
    elif tile_type == TileType.FLOOR or tile_type == TileType.DOOR_OPEN:
        # Draw cream floor for floor, open doors, and passages
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
    
    elif tile_type in [TileType.DOOR_HORIZONTAL, TileType.DOOR_VERTICAL]:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # The outline thickness is 1 to match the floor grid
        outline_thickness = 1
        
        if tile_type == TileType.DOOR_HORIZONTAL:
            door_width = int(cell_size * 0.8)
            door_height = int(cell_size * 0.3)
            door_rect = pygame.Rect(center_x - door_width // 2, center_y - door_height // 2, door_width, door_height)
        else: # DOOR_VERTICAL
            door_width = int(cell_size * 0.3)
            door_height = int(cell_size * 0.8)
            door_rect = pygame.Rect(center_x - door_width // 2, center_y - door_height // 2, door_width, door_height)

        # Draw the filled interior of the door
        pygame.draw.rect(surface, COLOR_DOOR, door_rect)
        # Draw the black outline
        pygame.draw.rect(surface, COLOR_WALL, door_rect, width=outline_thickness)

    elif tile_type in [TileType.STAIRS_HORIZONTAL, TileType.STAIRS_VERTICAL]:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)

        line_thickness = 1
        line_color = COLOR_FLOOR_GRID # Match grid color for subtle effect

        if tile_type == TileType.STAIRS_HORIZONTAL:
            # 3 horizontal lines for stairs in a vertical hallway
            spacing = cell_size // 4
            y1 = top + spacing
            y2 = top + 2 * spacing
            y3 = top + 3 * spacing
            pygame.draw.line(surface, line_color, (left, y1), (left + cell_size, y1), line_thickness)
            pygame.draw.line(surface, line_color, (left, y2), (left + cell_size, y2), line_thickness)
            pygame.draw.line(surface, line_color, (left, y3), (left + cell_size, y3), line_thickness)
        else: # STAIRS_VERTICAL
            # 3 vertical lines for stairs in a horizontal hallway
            spacing = cell_size // 4
            x1 = left + spacing
            x2 = left + 2 * spacing
            x3 = left + 3 * spacing
            pygame.draw.line(surface, line_color, (x1, top), (x1, top + cell_size), line_thickness)
            pygame.draw.line(surface, line_color, (x2, top), (x2, top + cell_size), line_thickness)
            pygame.draw.line(surface, line_color, (x3, top), (x3, top + cell_size), line_thickness)

    elif tile_type == TileType.NOTE:
        # Draw cream floor
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        # Draw grid on floor
        draw_floor_grid(surface, left, top, cell_size)
        # Note indicator (could be enhanced with better graphics)
        note_size = max(2, cell_size // 8)
        note_rect = pygame.Rect(center_x - note_size//2, center_y - note_size//2, note_size, note_size)
        pygame.draw.rect(surface, COLOR_NOTE, note_rect)

def draw_floor_grid(surface: pygame.Surface, left: int, top: int, cell_size: int):
    """Draw a grid pattern that aligns with character movement"""
    # Very thin lines for the grid
    line_thickness = 1
    
    # The grid should match the cell_size used for character movement
    # Each character movement cell should have its own grid square
    grid_spacing = cell_size  # One grid square = one movement cell
    
    # Draw vertical grid lines at cell boundaries
    # Start from the left edge and draw lines at cell_size intervals
    x = left
    while x <= left + cell_size:
        pygame.draw.line(surface, COLOR_FLOOR_GRID, 
                        (x, top), (x, top + cell_size), line_thickness)
        x += grid_spacing
    
    # Draw horizontal grid lines at cell boundaries
    y = top
    while y <= top + cell_size:
        pygame.draw.line(surface, COLOR_FLOOR_GRID,
                        (left, y), (left + cell_size, y), line_thickness)
        y += grid_spacing

def draw_boundary_walls(surface: pygame.Surface, dungeon: DungeonExplorer, 
                       viewport_x: int, viewport_y: int, cell_size: int,
                       viewport_width_cells: int, viewport_height_cells: int):
    """Draw walls around the perimeter of revealed areas with drop shadow effect"""
    # Make walls much thicker for the hand-drawn aesthetic
    line_thickness = max(4, cell_size // 4)  # Much thicker walls
    shadow_offset = max(2, cell_size // 12)  # Drop shadow offset
    
    # Get all revealed cells  
    revealed_cells = set()
    for room_id in dungeon.revealed_rooms:
        room = dungeon.rooms[room_id]
        for x, y in room.get_cells():
            revealed_cells.add((x, y))
    
    # Also add revealed doors (only if they connect to revealed rooms)
    for door in dungeon.doors:
        # Do not add secret doors to revealed cells for wall drawing purposes
        if door.type == 6 and not door.is_open:
            continue
        if (door.room1_id in dungeon.revealed_rooms or 
            door.room2_id in dungeon.revealed_rooms):
            revealed_cells.add((door.x, door.y))

    # Pre-calculate a set of secret door locations for faster lookup
    secret_horizontal_doors = {(d.x, d.y) for d in dungeon.doors if d.type == 6 and d.is_horizontal and not d.is_open}
    secret_vertical_doors = {(d.x, d.y) for d in dungeon.doors if d.type == 6 and not d.is_horizontal and not d.is_open}
    
    if not revealed_cells:
        return
    
    # Collect all wall segments for both shadow and main walls
    wall_segments = []
    
    # For each revealed cell, check if it's on the boundary and collect wall segments
    for cell_x, cell_y in revealed_cells:
        # Check if this cell is within viewport bounds (with some margin)
        if (cell_x < viewport_x - 1 or cell_x > viewport_x + viewport_width_cells + 1 or
            cell_y < viewport_y - 1 or cell_y > viewport_y + viewport_height_cells + 1):
            continue
        
        # Convert to screen coordinates
        screen_x = (cell_x - viewport_x) * cell_size
        screen_y = (cell_y - viewport_y) * cell_size
        
        # Check each direction for boundaries and collect wall segments
        # Bottom wall (of current cell)
        if (cell_x, cell_y + 1) not in revealed_cells or (cell_x, cell_y + 1) in secret_horizontal_doors:
            start_pos = (screen_x, screen_y + cell_size)
            end_pos = (screen_x + cell_size, screen_y + cell_size)
            wall_segments.append(('horizontal', start_pos, end_pos))
        
        # Top wall (of current cell)
        if (cell_x, cell_y - 1) not in revealed_cells or (cell_x, cell_y) in secret_horizontal_doors:
            start_pos = (screen_x, screen_y)
            end_pos = (screen_x + cell_size, screen_y)
            wall_segments.append(('horizontal', start_pos, end_pos))
        
        # Right wall (of current cell)
        if (cell_x + 1, cell_y) not in revealed_cells or (cell_x + 1, cell_y) in secret_vertical_doors:
            start_pos = (screen_x + cell_size, screen_y)
            end_pos = (screen_x + cell_size, screen_y + cell_size)
            wall_segments.append(('vertical', start_pos, end_pos))
        
        # Left wall (of current cell)
        if (cell_x - 1, cell_y) not in revealed_cells or (cell_x, cell_y) in secret_vertical_doors:
            start_pos = (screen_x, screen_y)
            end_pos = (screen_x, screen_y + cell_size)
            wall_segments.append(('vertical', start_pos, end_pos))
    
    # Extend line segments to fill corners properly
    extended_segments = []
    half_thickness = line_thickness // 2
    
    for orientation, start_pos, end_pos in wall_segments:
        if orientation == 'horizontal':
            # Extend horizontal lines left and right by half thickness
            extended_start = (start_pos[0] - half_thickness, start_pos[1])
            extended_end = (end_pos[0] + half_thickness, end_pos[1])
        else:  # vertical
            # Extend vertical lines up and down by half thickness
            extended_start = (start_pos[0], start_pos[1] - half_thickness)
            extended_end = (end_pos[0], end_pos[1] + half_thickness)
        
        extended_segments.append((extended_start, extended_end))
    
    # Draw drop shadows first (offset down and right)
    for start_pos, end_pos in extended_segments:
        shadow_start = (start_pos[0] + shadow_offset, start_pos[1] + shadow_offset)
        shadow_end = (end_pos[0] + shadow_offset, end_pos[1] + shadow_offset)
        pygame.draw.line(surface, COLOR_WALL_SHADOW, shadow_start, shadow_end, line_thickness)
    
    # Draw main black walls on top
    for start_pos, end_pos in extended_segments:
        pygame.draw.line(surface, COLOR_WALL, start_pos, end_pos, line_thickness)

def draw_terrain_features(surface: pygame.Surface, dungeon: DungeonExplorer,
                         viewport_x: int, viewport_y: int, cell_size: int):
    """Draw water and other terrain features with organic polygon shapes"""
    
    # Collect all visible water tiles
    visible_water = []
    for water in dungeon.water_tiles:
        if dungeon.is_revealed(water.x, water.y):
            screen_x = (water.x - viewport_x) * cell_size
            screen_y = (water.y - viewport_y) * cell_size
            
            # Only include if roughly in viewport (with margin for blob effects)
            if (screen_x > -cell_size * 2 and screen_x < surface.get_width() + cell_size * 2 and
                screen_y > -cell_size * 2 and screen_y < surface.get_height() + cell_size * 2):
                visible_water.append((screen_x + cell_size // 2, screen_y + cell_size // 2, water.x, water.y))
    
    if not visible_water:
        return
    
    # Group connected water tiles into clusters
    water_clusters = group_water_clusters(visible_water, cell_size)
    
    # Draw each cluster as an organic polygon
    for cluster in water_clusters:
        if len(cluster) >= 3:  # Need at least 3 points for a polygon
            draw_organic_water_polygon(surface, cluster, cell_size)
        elif len(cluster) == 2:  # Draw connecting blob for 2 points
            draw_water_connection(surface, cluster, cell_size)
        else:  # Single water tile
            draw_single_water_blob(surface, cluster[0], cell_size)

def group_water_clusters(water_positions: list, cell_size: int):
    """Group nearby water tiles into connected clusters"""
    clusters = []
    unprocessed = water_positions.copy()
    
    while unprocessed:
        # Start new cluster with first unprocessed point
        current_cluster = [unprocessed.pop(0)]
        cluster_changed = True
        
        # Keep adding connected points until no more can be added
        while cluster_changed:
            cluster_changed = False
            to_remove = []
            
            for i, point in enumerate(unprocessed):
                # Check if this point is adjacent to any point in current cluster
                for cluster_point in current_cluster:
                    world_dist = max(abs(point[2] - cluster_point[2]), abs(point[3] - cluster_point[3]))
                    if world_dist <= 1.5:  # Adjacent or diagonal (allowing some tolerance)
                        current_cluster.append(point)
                        to_remove.append(i)
                        cluster_changed = True
                        break
                if cluster_changed:
                    break
            
            # Remove processed points (in reverse order to maintain indices)
            for i in reversed(to_remove):
                unprocessed.pop(i)
        
        clusters.append(current_cluster)
    
    return clusters

def draw_organic_water_polygon(surface: pygame.Surface, cluster: list, cell_size: int):
    """Draw an organic polygon for a cluster of water tiles"""
    if len(cluster) < 3:
        return
    
    # Create organic boundary points around the cluster
    boundary_points = create_organic_boundary(cluster, cell_size)
    
    if len(boundary_points) >= 3:
        # Draw the main water polygon
        pygame.draw.polygon(surface, COLOR_WATER, boundary_points)
        
        # Draw border for depth effect
        border_points = create_organic_boundary(cluster, cell_size, border_offset=3)
        if len(border_points) >= 3:
            pygame.draw.polygon(surface, (80, 120, 160), border_points, 2)

def create_organic_boundary(cluster: list, cell_size: int, border_offset: int = 0):
    """Create organic boundary points around a water cluster using convex hull with organic modifications"""
    if len(cluster) < 3:
        return []
    
    # Extract screen coordinates
    points = [(point[0], point[1]) for point in cluster]
    
    # Calculate the center of the cluster
    center_x = sum(p[0] for p in points) / len(points)
    center_y = sum(p[1] for p in points) / len(points)
    
    # Sort points by angle from center to create a rough hull
    def angle_from_center(point):
        import math
        return math.atan2(point[1] - center_y, point[0] - center_x)
    
    sorted_points = sorted(points, key=angle_from_center)
    
    # Create organic boundary by expanding points outward and adding smoothing
    boundary_points = []
    expansion = cell_size * 0.4 + border_offset  # How much to expand outward
    
    for i, (x, y) in enumerate(sorted_points):
        # Calculate direction from center to this point
        dx = x - center_x
        dy = y - center_y
        dist = (dx * dx + dy * dy) ** 0.5
        
        if dist > 0:
            # Normalize and expand
            nx = dx / dist
            ny = dy / dist
            
            # Add organic variation
            variation = 0.3 + 0.2 * abs((i % 3) - 1)  # Varies between 0.1 and 0.5
            expand_dist = expansion * variation
            
            new_x = x + nx * expand_dist
            new_y = y + ny * expand_dist
            boundary_points.append((int(new_x), int(new_y)))
    
    # Add intermediate points for smoother curves
    smooth_boundary = []
    for i in range(len(boundary_points)):
        current = boundary_points[i]
        next_point = boundary_points[(i + 1) % len(boundary_points)]
        
        smooth_boundary.append(current)
        
        # Add intermediate point for smoother curves
        mid_x = (current[0] + next_point[0]) // 2
        mid_y = (current[1] + next_point[1]) // 2
        smooth_boundary.append((mid_x, mid_y))
    
    return smooth_boundary

def draw_water_connection(surface: pygame.Surface, cluster: list, cell_size: int):
    """Draw connection between two water tiles"""
    if len(cluster) != 2:
        return
    
    point1, point2 = cluster[0], cluster[1]
    
    # Calculate connection parameters
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    dist = (dx * dx + dy * dy) ** 0.5
    
    if dist > 0:
        # Create capsule-like shape
        radius = cell_size * 0.35
        
        # Draw circles at endpoints
        pygame.draw.circle(surface, COLOR_WATER, (point1[0], point1[1]), int(radius))
        pygame.draw.circle(surface, COLOR_WATER, (point2[0], point2[1]), int(radius))
        
        # Draw connecting rectangle
        if dist > radius:
            # Calculate perpendicular vector for rectangle width
            perp_x = -dy / dist * radius
            perp_y = dx / dist * radius
            
            rect_points = [
                (point1[0] + perp_x, point1[1] + perp_y),
                (point1[0] - perp_x, point1[1] - perp_y),
                (point2[0] - perp_x, point2[1] - perp_y),
                (point2[0] + perp_x, point2[1] + perp_y)
            ]
            pygame.draw.polygon(surface, COLOR_WATER, rect_points)

def draw_single_water_blob(surface: pygame.Surface, point, cell_size: int):
    """Draw a single organic water blob"""
    x, y = point[0], point[1]
    radius = int(cell_size * 0.4)
    
    # Draw main blob
    pygame.draw.circle(surface, COLOR_WATER, (x, y), radius)
    
    # Draw border
    pygame.draw.circle(surface, (80, 120, 160), (x, y), radius, 2)

def draw_main_menu(surface: pygame.Surface, large_font, medium_font):
    """Draws the main menu screen."""
    screen_width, screen_height = surface.get_size()
    
    # Background
    surface.fill(COLOR_BG)
    
    # Title
    title_surf = large_font.render("Dungeon Explorer", True, COLOR_BLACK)
    title_rect = title_surf.get_rect(centerx=screen_width/2, top=screen_height * 0.2)
    surface.blit(title_surf, title_rect)

    # Start button
    button_width = 300
    button_height = 60
    start_button_rect = pygame.Rect((screen_width - button_width)/2, screen_height * 0.5, button_width, button_height)
    
    pygame.draw.rect(surface, COLOR_WHITE, start_button_rect, 3)
    
    button_text_surf = medium_font.render("Create New Character", True, COLOR_BLACK)
    button_text_rect = button_text_surf.get_rect(center=start_button_rect.center)
    surface.blit(button_text_surf, button_text_rect)
    
    # Instructions
    inst_text = "Press ESC to quit"
    inst_surf = medium_font.render(inst_text, True, COLOR_BLACK)
    inst_rect = inst_surf.get_rect(centerx=screen_width/2, bottom=screen_height * 0.9)
    surface.blit(inst_surf, inst_rect)
    
    return start_button_rect

def draw_hud(surface: pygame.Surface, player: Player, large_font: pygame.font.Font, medium_font: pygame.font.Font, small_font: pygame.font.Font):
    """Draws the player information HUD at the bottom of the screen."""
    screen_width, screen_height = surface.get_size()
    hud_rect = pygame.Rect(0, screen_height - HUD_HEIGHT, screen_width, HUD_HEIGHT)
    
    # Draw outer black box
    pygame.draw.rect(surface, COLOR_BLACK, hud_rect)
    
    # Draw inner white box
    inner_margin = 4
    inner_rect = hud_rect.inflate(-inner_margin * 2, -inner_margin * 2)
    pygame.draw.rect(surface, COLOR_WHITE, inner_rect, width=1)
    
    # --- Left Section: Character Info ---
    left_padding = inner_rect.left + 20
    name_surf = large_font.render(player.name, True, COLOR_WHITE)
    name_rect = name_surf.get_rect(left=left_padding, top=inner_rect.top + 10)
    surface.blit(name_surf, name_rect)

    title_surf = medium_font.render(player.title, True, COLOR_WHITE)
    title_rect = title_surf.get_rect(left=left_padding, top=name_rect.bottom + 2)
    surface.blit(title_surf, title_rect)

    info_text = f"Lvl {player.level} {player.alignment} {player.race} {player.character_class}"
    info_surf = small_font.render(info_text, True, COLOR_WHITE)
    info_rect = info_surf.get_rect(left=left_padding, bottom=inner_rect.bottom - 10)
    surface.blit(info_surf, info_rect)

    # --- Right Section: Vitals & Resources ---
    right_padding = inner_rect.right - 20
    bar_width = 150 
    bar_height = 15
    
    # HP Bar
    hp_y = inner_rect.top + 15
    
    hp_value_surf = medium_font.render(f"{player.hp}/{player.max_hp}", True, COLOR_WHITE)
    hp_value_rect = hp_value_surf.get_rect(right=right_padding, centery=hp_y + bar_height/2)
    surface.blit(hp_value_surf, hp_value_rect)
    
    hp_bar_rect = pygame.Rect(hp_value_rect.left - bar_width - 10, hp_y, bar_width, bar_height)
    hp_ratio = player.hp / player.max_hp
    hp_bar_fill_width = int(bar_width * hp_ratio)
    pygame.draw.rect(surface, COLOR_BAR_BG, hp_bar_rect)
    pygame.draw.rect(surface, COLOR_HP_BAR, (hp_bar_rect.x, hp_bar_rect.y, hp_bar_fill_width, bar_height))

    hp_text_surf = medium_font.render(f'{UI_ICONS["HEART"]} HP', True, COLOR_HP_BAR)
    hp_text_rect = hp_text_surf.get_rect(right=hp_bar_rect.left - 10, centery=hp_bar_rect.centery)
    surface.blit(hp_text_surf, hp_text_rect)

    # XP Bar
    xp_y = hp_y + bar_height + 10
    
    xp_bar_rect = pygame.Rect(hp_bar_rect.x, xp_y, bar_width, bar_height)
    xp_ratio = player.xp / player.xp_to_next_level
    xp_bar_fill_width = int(bar_width * xp_ratio)
    pygame.draw.rect(surface, COLOR_BAR_BG, xp_bar_rect)
    pygame.draw.rect(surface, COLOR_XP_BAR, (xp_bar_rect.x, xp_bar_rect.y, xp_bar_fill_width, bar_height))

    xp_text_surf = medium_font.render("XP", True, COLOR_XP_BAR)
    xp_text_rect = xp_text_surf.get_rect(right=xp_bar_rect.left - 10, centery=xp_bar_rect.centery)
    surface.blit(xp_text_surf, xp_text_rect)

    # --- Bottom Right: Other Stats ---
    bottom_y = inner_rect.bottom - 10
    
    ac_icon_surf = large_font.render(UI_ICONS["SHIELD"], True, COLOR_WHITE)
    ac_text_surf = medium_font.render(f"{player.ac}", True, COLOR_WHITE)
    ac_text_rect = ac_text_surf.get_rect(right=right_padding, bottom=bottom_y)
    ac_icon_rect = ac_icon_surf.get_rect(right=ac_text_rect.left - 5, centery=ac_text_rect.centery)
    surface.blit(ac_icon_surf, ac_icon_rect)
    surface.blit(ac_text_surf, ac_text_rect)
    
    gold_icon_surf = large_font.render(UI_ICONS["GOLD"], True, (255, 215, 0))
    gold_text_surf = medium_font.render(f"{player.gold:.0f}", True, COLOR_WHITE)
    gold_text_rect = gold_text_surf.get_rect(right=ac_icon_rect.left - 20, bottom=bottom_y)
    gold_icon_rect = gold_icon_surf.get_rect(right=gold_text_rect.left - 5, centery=gold_text_rect.centery)
    surface.blit(gold_icon_surf, gold_icon_rect)
    surface.blit(gold_text_surf, gold_text_rect)

def draw_timer_box(surface: pygame.Surface, player: Player, font: pygame.font.Font):
    """Draws the torch timer in its own box in the top right corner."""
    margin = 10
    screen_width, _ = surface.get_size()
    
    time_left = max(0, player.light_duration - (time.time() - player.light_start_time))
    minutes, seconds = divmod(int(time_left), 60)
    light_text = f'{UI_ICONS["SUN"]} {minutes:02d}:{seconds:02d}'
    
    light_surf = font.render(light_text, True, COLOR_TORCH_ICON)
    
    box_width = light_surf.get_width() + 20
    box_height = light_surf.get_height() + 10
    
    box_rect = pygame.Rect(screen_width - box_width - margin, margin, box_width, box_height)
    pygame.draw.rect(surface, COLOR_BLACK, box_rect)
    
    inner_rect = box_rect.inflate(-4, -4)
    pygame.draw.rect(surface, COLOR_WHITE, inner_rect, 1)
    
    light_rect = light_surf.get_rect(center=box_rect.center)
    surface.blit(light_surf, light_rect)

def draw_spell_menu(surface: pygame.Surface, font: pygame.font.Font, spells: List[str]):
    """Draws the spell selection menu."""
    menu_width = 300
    menu_height = 200
    screen_width, screen_height = surface.get_size()
    
    menu_rect = pygame.Rect((screen_width - menu_width) / 2, (screen_height - HUD_HEIGHT - menu_height) / 2, menu_width, menu_height)
    
    # Draw a solid black background box
    pygame.draw.rect(surface, COLOR_BLACK, menu_rect)
    
    # Draw border
    pygame.draw.rect(surface, COLOR_WHITE, menu_rect, 1)
    
    # Draw title
    title_surf = font.render("Choose a Spell", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=menu_rect.centerx, top=menu_rect.top + 10)
    surface.blit(title_surf, title_rect)
    
    # Draw spell options
    for i, spell_name in enumerate(spells):
        text = f"{i+1}. {spell_name}"
        spell_surf = font.render(text, True, COLOR_WHITE)
        spell_rect = spell_surf.get_rect(left=menu_rect.left + 20, top=title_rect.bottom + 10 + (i * 30))
        surface.blit(spell_surf, spell_rect)

def main():
    pygame.init()
    
    # Load data
    try:
        with open(JSON_FILE, 'r') as f:
            dungeon_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{JSON_FILE}' not found.")
        pygame.quit()
        return
    
    # Initialize game variables
    player = None
    dungeon = None
    
    # Display setup
    zoom_level = DEFAULT_ZOOM
    cell_size = int(BASE_CELL_SIZE * zoom_level)
    
    initial_width = INITIAL_VIEWPORT_WIDTH * cell_size
    initial_height = INITIAL_VIEWPORT_HEIGHT * cell_size

    screen = pygame.display.set_mode((initial_width, initial_height + HUD_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption(f"{dungeon_data.get('title', 'Dungeon')}")
    
    # Create fonts for the UI
    hud_font_large = pygame.font.Font(FONT_FILE, 28)
    hud_font_medium = pygame.font.Font(FONT_FILE, 20)
    hud_font_small = pygame.font.Font(FONT_FILE, 14)
    coords_font = pygame.font.Font(FONT_FILE, 16)
    timer_font = pygame.font.Font(FONT_FILE, 22)
    spell_menu_font = pygame.font.Font(FONT_FILE, 20)

    # Game state
    game_state = GameState.MAIN_MENU
    spell_target_pos = (0, 0)
    player_pos = (0, 0)
    walkable_positions = set()
    fullscreen = False
    current_spell = ""
    
    # Inventory/Equipment state
    inventory_selected_index = 0
    equipment_selected_slot = 'weapon'
    equipment_selection_mode = False
    equipment_selection_index = 0
    container_selected_index = 0
    container_view_selected_index = 0
    item_action_selected_index = 0
    current_container = None
    current_containers = []
    
    # Initialize viewport variables
    viewport_width_cells = 0
    viewport_height_cells = 0
    viewport_x = 0
    viewport_y = 0
    player_font = None
    spell_cursor_font = None
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Get current screen dimensions
        screen_width, screen_height = screen.get_size()
        game_area_height = screen_height - HUD_HEIGHT
        
        # Update rendering values based on zoom (only when playing)
        if game_state == GameState.PLAYING and player is not None and dungeon is not None:
            cell_size = int(BASE_CELL_SIZE * zoom_level)
            player_font = pygame.font.Font(FONT_FILE, max(8, int(BASE_FONT_SIZE * zoom_level)))
            spell_cursor_font = pygame.font.Font(FONT_FILE, cell_size)
            
            # Calculate dynamic viewport dimensions in cells
            viewport_width_cells = screen_width // cell_size
            viewport_height_cells = game_area_height // cell_size

            # Calculate world coordinates of the top-left corner of the viewport
            viewport_x = player_pos[0] - viewport_width_cells // 2
            viewport_y = player_pos[1] - viewport_height_cells // 2
        
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == GameState.PLAYING and player is not None and dungeon is not None:
                        running = False
                    elif game_state in [GameState.SPELL_MENU, GameState.SPELL_TARGETING]:
                        game_state = GameState.PLAYING
                    elif game_state == GameState.INVENTORY:
                        game_state = GameState.PLAYING
                    elif game_state == GameState.CONTAINER_VIEW:
                        game_state = GameState.INVENTORY
                    elif game_state == GameState.ITEM_ACTION:
                        game_state = GameState.CONTAINER_VIEW
                    elif game_state == GameState.EQUIPMENT:
                        if equipment_selection_mode:
                            equipment_selection_mode = False
                        else:
                            game_state = GameState.PLAYING
                    else:
                        running = False

                # Game controls
                if game_state == GameState.PLAYING:
                    if event.key == pygame.K_F11:
                        fullscreen = not fullscreen
                        if fullscreen:
                            info = pygame.display.Info()
                            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((initial_width, initial_height + HUD_HEIGHT), pygame.RESIZABLE)
                        
                        # Update screen dimensions after fullscreen toggle
                        screen_width, screen_height = screen.get_size()
                    elif event.key in [pygame.K_PLUS, pygame.K_EQUALS]:
                        zoom_level = min(zoom_level + ZOOM_STEP, MAX_ZOOM)
                    elif event.key == pygame.K_MINUS:
                        zoom_level = max(zoom_level - ZOOM_STEP, MIN_ZOOM)
                    elif event.key == pygame.K_m:
                        game_state = GameState.SPELL_MENU
                        spell_target_pos = player_pos
                    elif event.key == pygame.K_i:
                        game_state = GameState.INVENTORY
                        inventory_selected_index = 0
                        current_containers = organize_inventory_into_containers(player)
                    elif event.key == pygame.K_e:
                        game_state = GameState.EQUIPMENT
                        equipment_selected_slot = 'weapon'
                        equipment_selection_mode = False
                    
                    # Movement
                    next_pos = player_pos
                    moved = False
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        next_pos = (player_pos[0], player_pos[1] - 1)
                        moved = True
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        next_pos = (player_pos[0], player_pos[1] + 1)
                        moved = True
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        next_pos = (player_pos[0] - 1, player_pos[1])
                        moved = True
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        next_pos = (player_pos[0] + 1, player_pos[1])
                        moved = True
                    elif event.key == pygame.K_SPACE:
                        # Open doors
                        for dx, dy in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
                            if dungeon.open_door_at_position(player_pos[0] + dx, player_pos[1] + dy):
                                walkable_positions = dungeon.get_walkable_positions(for_monster=False)
                                break
                    
                    if moved and next_pos in walkable_positions:
                        player_pos = next_pos
                        # Auto-open regular/locked doors on move
                        tile_at_pos = dungeon.tiles.get(player_pos)
                        if tile_at_pos in [TileType.DOOR_HORIZONTAL, TileType.DOOR_VERTICAL]:
                             if dungeon.open_door_at_position(player_pos[0], player_pos[1]):
                                walkable_positions = dungeon.get_walkable_positions(for_monster=False)
                        
                        # Monster Turn
                        occupied_tiles = {(m.x, m.y) for m in dungeon.monsters}
                        occupied_tiles.add(player_pos)
                        monster_walkable = dungeon.get_walkable_positions(for_monster=True)

                        for monster in dungeon.monsters:
                            if monster.room_id in dungeon.revealed_rooms:
                                dx = player_pos[0] - monster.x
                                dy = player_pos[1] - monster.y
                                
                                # Move monster one step closer to player
                                next_monster_pos = monster.x, monster.y
                                if abs(dx) > abs(dy):
                                    next_monster_pos = (monster.x + (1 if dx > 0 else -1), monster.y)
                                else:
                                    next_monster_pos = (monster.x, monster.y + (1 if dy > 0 else -1))
                                
                                if next_monster_pos in monster_walkable and next_monster_pos not in occupied_tiles:
                                    monster.x, monster.y = next_monster_pos

                # Spell menu controls
                elif game_state == GameState.SPELL_MENU:
                    if event.key == pygame.K_1:
                        print("Selected Fireball!")
                        current_spell = "Burning Hands"
                        game_state = GameState.SPELL_TARGETING
                    # Add more spell selections here...

                # Spell targeting controls
                elif game_state == GameState.SPELL_TARGETING:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        new_target = (spell_target_pos[0], spell_target_pos[1] - 1)
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        new_target = (spell_target_pos[0], spell_target_pos[1] + 1)
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        new_target = (spell_target_pos[0] - 1, spell_target_pos[1])
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        new_target = (spell_target_pos[0] + 1, spell_target_pos[1])
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key == pygame.K_RETURN:
                        print(f"Casting {current_spell} at {spell_target_pos}!")
                        game_state = GameState.PLAYING

                # Inventory controls (container selection)
                elif game_state == GameState.INVENTORY:
                    if event.key == pygame.K_UP:
                        if current_containers:
                            inventory_selected_index = (inventory_selected_index - 1) % len(current_containers)
                    elif event.key == pygame.K_DOWN:
                        if current_containers:
                            inventory_selected_index = (inventory_selected_index + 1) % len(current_containers)
                    elif event.key == pygame.K_RETURN:
                        if current_containers and 0 <= inventory_selected_index < len(current_containers):
                            current_container = current_containers[inventory_selected_index]
                            container_view_selected_index = 0
                            game_state = GameState.CONTAINER_VIEW

                # Container view controls (item selection within container)
                elif game_state == GameState.CONTAINER_VIEW:
                    if event.key == pygame.K_UP:
                        if current_container and current_container.contents:
                            container_view_selected_index = (container_view_selected_index - 1) % len(current_container.contents)
                    elif event.key == pygame.K_DOWN:
                        if current_container and current_container.contents:
                            container_view_selected_index = (container_view_selected_index + 1) % len(current_container.contents)
                    elif event.key == pygame.K_RETURN:
                        if (current_container and current_container.contents and 
                            0 <= container_view_selected_index < len(current_container.contents)):
                            item_action_selected_index = 0
                            game_state = GameState.ITEM_ACTION

                # Item action controls
                elif game_state == GameState.ITEM_ACTION:
                    actions = ["Use/Consume", "Equip", "Drop Here", "Throw", "Examine"]
                    if event.key == pygame.K_UP:
                        item_action_selected_index = (item_action_selected_index - 1) % len(actions)
                    elif event.key == pygame.K_DOWN:
                        item_action_selected_index = (item_action_selected_index + 1) % len(actions)
                    elif event.key == pygame.K_RETURN:
                        if (current_container and current_container.contents and 
                            0 <= container_view_selected_index < len(current_container.contents)):
                            selected_inv_item = current_container.contents[container_view_selected_index]
                            action = actions[item_action_selected_index]
                            
                            # Handle different actions
                            if action == "Equip":
                                slot = get_equipment_slot(selected_inv_item.item)
                                if slot:
                                    equip_item(player, selected_inv_item, slot)
                            elif action == "Use/Consume":
                                # TODO: Implement item usage
                                print(f"Used {selected_inv_item.item.name}")
                            elif action == "Drop Here":
                                # TODO: Implement item dropping
                                print(f"Dropped {selected_inv_item.item.name}")
                            elif action == "Throw":
                                # TODO: Implement item throwing
                                print(f"Threw {selected_inv_item.item.name}")
                            elif action == "Examine":
                                # TODO: Implement detailed examination
                                print(f"Examined {selected_inv_item.item.name}")
                            
                            game_state = GameState.CONTAINER_VIEW

                # Equipment controls  
                elif game_state == GameState.EQUIPMENT:
                    if not equipment_selection_mode:
                        # Navigate equipment slots
                        equipment_slots = ['weapon', 'armor', 'shield', 'light']
                        if event.key == pygame.K_UP:
                            current_index = equipment_slots.index(equipment_selected_slot)
                            equipment_selected_slot = equipment_slots[(current_index - 1) % len(equipment_slots)]
                        elif event.key == pygame.K_DOWN:
                            current_index = equipment_slots.index(equipment_selected_slot)
                            equipment_selected_slot = equipment_slots[(current_index + 1) % len(equipment_slots)]
                        elif event.key == pygame.K_RETURN:
                            # Enter equipment selection mode
                            equipment_selection_mode = True
                            equipment_selection_index = 0
                    else:
                        # Equipment selection mode
                        available_items = get_available_items_for_slot(player, equipment_selected_slot)
                        available_items.insert(0, None)  # Add unequip option
                        
                        if event.key == pygame.K_UP:
                            equipment_selection_index = (equipment_selection_index - 1) % len(available_items)
                        elif event.key == pygame.K_DOWN:
                            equipment_selection_index = (equipment_selection_index + 1) % len(available_items)
                        elif event.key == pygame.K_RETURN:
                            selected_item = available_items[equipment_selection_index]
                            
                            if selected_item is None:
                                # Unequip
                                unequip_item(player, equipment_selected_slot)
                            else:
                                # Equip
                                equip_item(player, selected_item, equipment_selected_slot)
                            
                            equipment_selection_mode = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == GameState.MAIN_MENU:
                    if 'start_button_rect' in locals() and start_button_rect.collidepoint(event.pos):
                        # Start character creation
                        pygame.display.quit()
                        created_player = run_character_creation(screen_width, screen_height, FONT_FILE)
                        
                        if created_player is None:
                            # Character creation was cancelled, exit game
                            running = False
                            break
                        
                        # Character creation successful, continue with game
                        if fullscreen:
                            info = pygame.display.Info()  
                            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                        pygame.display.set_caption(f"{dungeon_data.get('title', 'Dungeon')}")
                        
                        player = created_player
                        # Calculate initial AC and update gear slots
                        player.ac = calculate_armor_class(player)
                        
                        # Update gear slots if Fighter with Constitution bonus
                        if player.character_class == "Fighter":
                            constitution_bonus = get_stat_modifier(player.constitution)
                            if constitution_bonus > 0:
                                player.max_gear_slots += constitution_bonus
                        
                        # Calculate actual gear slots used from inventory
                        player.gear_slots_used = 0
                        for inv_item in player.inventory:
                            item_slots = getattr(inv_item.item, 'gear_slots', 1)
                            if hasattr(inv_item.item, 'quantity_per_slot') and inv_item.item.quantity_per_slot > 1:
                                # Items that can stack
                                slots_needed = (inv_item.quantity + inv_item.item.quantity_per_slot - 1) // inv_item.item.quantity_per_slot
                                player.gear_slots_used += slots_needed * item_slots
                            else:
                                player.gear_slots_used += item_slots * inv_item.quantity
                        
                        # Debug print to verify inventory
                        print(f"Player created with {len(player.inventory)} items")
                        if player.inventory:
                            for item in player.inventory:
                                print(f"  - {item.quantity}x {item.item.name}")
                        print(f"Player gold: {player.gold}")
                        print(f"Gear slots: {player.gear_slots_used}/{player.max_gear_slots}")
                        
                        dungeon = DungeonExplorer(dungeon_data)
                        player_pos = dungeon.get_starting_position()
                        walkable_positions = dungeon.get_walkable_positions(for_monster=False)
                        game_state = GameState.PLAYING

        # --- RENDER ---
        if game_state == GameState.MAIN_MENU:
            start_button_rect = draw_main_menu(screen, hud_font_large, hud_font_medium)
        
        elif game_state == GameState.INVENTORY:
            draw_inventory_screen(screen, player, inventory_selected_index, hud_font_medium, hud_font_small)
        
        elif game_state == GameState.CONTAINER_VIEW:
            if current_container:
                draw_container_view_screen(screen, player, current_container, container_view_selected_index, hud_font_medium, hud_font_small)
        
        elif game_state == GameState.ITEM_ACTION:
            if current_container and current_container.contents and 0 <= container_view_selected_index < len(current_container.contents):
                # Draw container view first
                draw_container_view_screen(screen, player, current_container, container_view_selected_index, hud_font_medium, hud_font_small)
                # Then draw action overlay
                selected_item = current_container.contents[container_view_selected_index]
                draw_item_action_screen(screen, selected_item.item, item_action_selected_index, hud_font_medium, hud_font_small)
        
        elif game_state == GameState.EQUIPMENT:
            if equipment_selection_mode:
                # Draw equipment screen first
                draw_equipment_screen(screen, player, equipment_selected_slot, hud_font_medium, hud_font_small)
                # Then draw selection overlay
                show_equipment_selection(screen, player, equipment_selected_slot, equipment_selection_index, hud_font_medium, hud_font_small)
            else:
                draw_equipment_screen(screen, player, equipment_selected_slot, hud_font_medium, hud_font_small)
        
        elif game_state == GameState.PLAYING and player is not None and dungeon is not None:
            # Ensure fonts are available for rendering
            if player_font is None:
                cell_size = int(BASE_CELL_SIZE * zoom_level)
                player_font = pygame.font.Font(FONT_FILE, max(8, int(BASE_FONT_SIZE * zoom_level)))
                spell_cursor_font = pygame.font.Font(FONT_FILE, cell_size)
                
                # Calculate dynamic viewport dimensions in cells
                viewport_width_cells = screen_width // cell_size
                viewport_height_cells = game_area_height // cell_size

                # Calculate world coordinates of the top-left corner of the viewport
                viewport_x = player_pos[0] - viewport_width_cells // 2
                viewport_y = player_pos[1] - viewport_height_cells // 2
            
            screen.fill(COLOR_BG)
            
            # Create viewport surface
            viewport_surface = pygame.Surface((screen_width, game_area_height))
            viewport_surface.fill(COLOR_BG)
            
            # Draw tiles
            for screen_cell_y in range(viewport_height_cells + 2):
                for screen_cell_x in range(viewport_width_cells + 2):
                    world_x = viewport_x + screen_cell_x
                    world_y = viewport_y + screen_cell_y
                    
                    tile_type = dungeon.tiles.get((world_x, world_y), TileType.VOID)
                    
                    # Check visibility - fog of war rules
                    if dungeon.is_revealed(world_x, world_y):
                        draw_tile(viewport_surface, tile_type, screen_cell_x, screen_cell_y, cell_size)
            
            # Draw terrain features (water) on top of tiles but under walls
            draw_terrain_features(viewport_surface, dungeon, viewport_x, viewport_y, cell_size)
            
            # Draw walls using proper marching squares
            draw_boundary_walls(viewport_surface, dungeon, viewport_x, viewport_y, cell_size, viewport_width_cells, viewport_height_cells)
            
            # Draw spell range indicator if targeting
            if game_state == GameState.SPELL_TARGETING:
                draw_spell_range_indicator(viewport_surface, player_pos, current_spell, viewport_x, viewport_y, cell_size, viewport_width_cells, viewport_height_cells)
            
            # Draw monsters
            for monster in dungeon.monsters:
                if dungeon.is_revealed(monster.x, monster.y):
                    monster_screen_x = (monster.x - viewport_x) * cell_size + (cell_size // 2)
                    monster_screen_y = (monster.y - viewport_y) * cell_size + (cell_size // 2)
                    monster_surf = player_font.render(UI_ICONS["MONSTER"], True, COLOR_MONSTER)
                    monster_rect = monster_surf.get_rect(center=(monster_screen_x, monster_screen_y))
                    viewport_surface.blit(monster_surf, monster_rect)

            # Draw player
            player_screen_x = (viewport_width_cells // 2) * cell_size + (cell_size // 2)
            player_screen_y = (viewport_height_cells // 2) * cell_size + (cell_size // 2)
            
            player_surf = player_font.render('@', True, COLOR_PLAYER)
            player_rect = player_surf.get_rect(center=(player_screen_x, player_screen_y))
            viewport_surface.blit(player_surf, player_rect)
            
            # Draw spell cursor if targeting
            if game_state == GameState.SPELL_TARGETING:
                cursor_screen_x = (spell_target_pos[0] - viewport_x) * cell_size + (cell_size // 2)
                cursor_screen_y = (spell_target_pos[1] - viewport_y) * cell_size + (cell_size // 2)
                cursor_surf = spell_cursor_font.render(UI_ICONS["SPELL_CURSOR"], True, COLOR_SPELL_CURSOR)
                cursor_rect = cursor_surf.get_rect(center=(cursor_screen_x, cursor_screen_y))
                viewport_surface.blit(cursor_surf, cursor_rect)

            # Blit viewport to screen
            screen.blit(viewport_surface, (0, 0))
            
            # Display coordinates and timer
            coord_text = f"({player_pos[0]}, {player_pos[1]})"
            coord_surf = coords_font.render(coord_text, True, COLOR_WALL)
            screen.blit(coord_surf, (10, 10))
            
            draw_timer_box(screen, player, timer_font)

            # Draw HUD
            draw_hud(screen, player, hud_font_large, hud_font_medium, hud_font_small)

            # Draw spell menu if active
            if game_state == GameState.SPELL_MENU:
                draw_spell_menu(screen, spell_menu_font, ["Fireball", "Magic Missile", "Invisibility"])
        else:
            # Fallback for any other state
            screen.fill(COLOR_BG)

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == '__main__':
    main()