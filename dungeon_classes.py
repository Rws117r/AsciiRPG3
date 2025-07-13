# dungeon_classes.py - Dungeon-related classes and logic
import random
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from game_constants import TileType

# Import the new monster system
from monster_system import MonsterInstance, spawn_random_monster, get_monster_database

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
        self.monsters: List[MonsterInstance] = []  # Changed to use MonsterInstance
        
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
        """Spawns monsters in rooms based on a random chance, using JSON monster data."""
        # Initialize the monster database
        monster_db = get_monster_database()
        print(f"Monster database loaded with {len(monster_db.list_monsters())} monster types:")
        for monster_name in monster_db.list_monsters():
            print(f"  - {monster_name}")
        
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

            # 50% chance to spawn a monster in each room
            if random.randint(1, 6) <= 3:
                # Spawn a monster in a random valid cell of the room
                valid_cells = [cell for cell in room.get_cells() if cell not in door_locations]
                if valid_cells:
                    x, y = random.choice(valid_cells)
                    
                    # Determine monster level based on distance from start (simple difficulty scaling)
                    distance_from_start = max(abs(x - start_pos[0]), abs(y - start_pos[1]))
                    if distance_from_start < 5:
                        level_range = (1, 1)  # Easy monsters near start
                    elif distance_from_start < 10:
                        level_range = (1, 2)  # Mixed difficulty
                    else:
                        level_range = (1, 3)  # Harder monsters farther away
                    
                    # Spawn a random monster
                    monster = spawn_random_monster(x, y, room_id, level_range)
                    if monster:
                        self.monsters.append(monster)
                        print(f"Spawned {monster.name} at ({x}, {y}) in room {room_id}")
                    else:
                        print(f"Failed to spawn monster at ({x}, {y})")
        
        print(f"Total monsters spawned: {len(self.monsters)}")

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