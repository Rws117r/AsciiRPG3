# puzzle_system.py - Interactive puzzle mechanics
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from game_constants import TileType, PuzzleType, PuzzleState

@dataclass
class PuzzleElement:
    """Base class for puzzle elements"""
    x: int
    y: int
    element_type: str
    active: bool = False
    interactable: bool = True

@dataclass
class Boulder(PuzzleElement):
    """Moveable boulder for pressure plate puzzles"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "boulder", False, True)

@dataclass
class PressurePlate(PuzzleElement):
    """Pressure plate that activates when boulder is placed on it"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "pressure_plate", False, False)

@dataclass
class Glyph(PuzzleElement):
    """Magical glyph that glows when puzzle conditions are met"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "glyph", False, False)

@dataclass
class Barrier(PuzzleElement):
    """Magical barrier that blocks passage until dissolved"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "barrier", True, False)  # Starts active (blocking)

@dataclass
class Altar(PuzzleElement):
    """Stone altar with holy light"""
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "altar", True, True)

@dataclass
class Chest(PuzzleElement):
    """Treasure chest, potentially trapped"""
    trapped: bool = False
    opened: bool = False
    
    def __init__(self, x: int, y: int, trapped: bool = False):
        super().__init__(x, y, "chest", False, True)
        self.trapped = trapped

@dataclass
class PuzzleRoom:
    """Represents a complete puzzle in a room"""
    room_id: int
    puzzle_type: PuzzleType
    state: PuzzleState
    elements: Dict[str, List[PuzzleElement]] = field(default_factory=dict)
    solution_positions: List[Tuple[int, int]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.elements:
            self.elements = {
                "boulders": [],
                "pressure_plates": [],
                "glyphs": [],
                "barriers": [],
                "altars": [],
                "chests": []
            }
    
    def add_element(self, element: PuzzleElement):
        """Add an element to the puzzle"""
        element_type = element.element_type
        if element_type == "boulder":
            self.elements["boulders"].append(element)
        elif element_type == "pressure_plate":
            self.elements["pressure_plates"].append(element)
        elif element_type == "glyph":
            self.elements["glyphs"].append(element)
        elif element_type == "barrier":
            self.elements["barriers"].append(element)
        elif element_type == "altar":
            self.elements["altars"].append(element)
        elif element_type == "chest":
            self.elements["chests"].append(element)
    
    def check_solution(self) -> bool:
        """Check if the puzzle is solved"""
        if self.puzzle_type == PuzzleType.BOULDER_PRESSURE_PLATE:
            return self._check_boulder_puzzle()
        return False
    
    def _check_boulder_puzzle(self) -> bool:
        """Check if all pressure plates have boulders on them"""
        boulder_positions = {(b.x, b.y) for b in self.elements["boulders"]}
        plate_positions = {(p.x, p.y) for p in self.elements["pressure_plates"]}
        
        # All pressure plates must have boulders on them
        return plate_positions.issubset(boulder_positions)
    
    def update_state(self):
        """Update puzzle state based on current conditions"""
        if self.state == PuzzleState.SOLVED:
            return  # Already solved
        
        if self.check_solution():
            self._solve_puzzle()
        else:
            self._update_partial_solution()
    
    def _solve_puzzle(self):
        """Execute puzzle solution effects"""
        print(f"Puzzle in room {self.room_id} solved!")
        self.state = PuzzleState.SOLVED
        
        # Activate glyphs
        for glyph in self.elements["glyphs"]:
            glyph.active = True
        
        # Deactivate barriers
        for barrier in self.elements["barriers"]:
            barrier.active = False
        
        # Activate pressure plates
        for plate in self.elements["pressure_plates"]:
            plate.active = True
    
    def _update_partial_solution(self):
        """Update elements for partial solutions"""
        # Update pressure plate states
        boulder_positions = {(b.x, b.y) for b in self.elements["boulders"]}
        
        for plate in self.elements["pressure_plates"]:
            plate.active = (plate.x, plate.y) in boulder_positions

class PuzzleManager:
    """Manages all puzzles in the dungeon"""
    
    def __init__(self):
        self.puzzles: Dict[int, PuzzleRoom] = {}  # room_id -> PuzzleRoom
        self.element_positions: Dict[Tuple[int, int], PuzzleElement] = {}
    
    def add_puzzle(self, puzzle: PuzzleRoom):
        """Add a puzzle to the manager"""
        self.puzzles[puzzle.room_id] = puzzle
        
        # Index all elements by position
        for element_list in puzzle.elements.values():
            for element in element_list:
                self.element_positions[(element.x, element.y)] = element
    
    def get_element_at_position(self, x: int, y: int) -> Optional[PuzzleElement]:
        """Get puzzle element at given position"""
        return self.element_positions.get((x, y))
    
    def move_boulder(self, boulder: Boulder, new_x: int, new_y: int, walkable_positions: Set[Tuple[int, int]]) -> bool:
        """Attempt to move a boulder to a new position"""
        old_pos = (boulder.x, boulder.y)
        new_pos = (new_x, new_y)
        
        # Check if new position is walkable and not occupied by another boulder
        if new_pos not in walkable_positions:
            return False
        
        # Check if there's already a boulder at the new position
        existing_element = self.get_element_at_position(new_x, new_y)
        if existing_element and existing_element.element_type == "boulder":
            return False
        
        # Move the boulder
        del self.element_positions[old_pos]
        boulder.x = new_x
        boulder.y = new_y
        self.element_positions[new_pos] = boulder
        
        # Update puzzle state
        for puzzle in self.puzzles.values():
            if boulder in puzzle.elements["boulders"]:
                puzzle.update_state()
                break
        
        return True
    
    def interact_with_element(self, player, x: int, y: int) -> bool:
        """Handle player interaction with puzzle element"""
        element = self.get_element_at_position(x, y)
        if not element or not element.interactable:
            return False
        
        if element.element_type == "altar":
            return self._interact_with_altar(element)
        elif element.element_type == "chest":
            return self._interact_with_chest(element, player)
        elif element.element_type == "boulder":
            # Boulder interaction is handled by movement system
            return False
        
        return False
    
    def _interact_with_altar(self, altar: Altar) -> bool:
        """Handle altar interaction"""
        print("You touch the stone altar. It radiates warmth and holy energy.")
        print("Ancient runes along its edge glow faintly, as if responding to your presence.")
        return True
    
    def _interact_with_chest(self, chest: Chest, player) -> bool:
        """Handle chest interaction"""
        if chest.opened:
            print("The chest is already empty.")
            return True
        
        if chest.trapped:
            # Simple trap check - could be expanded
            trap_difficulty = 12
            player_skill = 10 + random.randint(1, 20)  # Basic skill check
            
            if player_skill >= trap_difficulty:
                print("You carefully disarm the trap mechanism.")
            else:
                damage = random.randint(1, 4)
                player.hp -= damage
                print(f"The trap triggers! You take {damage} damage from poison needles.")
                if player.hp <= 0:
                    print("The trap proves deadly!")
                    return True
        
        # Open chest and give rewards
        chest.opened = True
        self._generate_chest_rewards(player)
        return True
    
    def _generate_chest_rewards(self, player):
        """Generate random rewards for opening a chest"""
        # Simple reward system
        gold_reward = random.randint(10, 50)
        player.gold += gold_reward
        print(f"You find {gold_reward} gold pieces in the chest!")
        
        # Small chance for magic item
        if random.randint(1, 100) <= 20:
            print("You also discover a glowing potion!")
            # Could add actual potion to inventory here

def generate_boulder_puzzle(room, room_cells: List[Tuple[int, int]]) -> PuzzleRoom:
    """Generate a boulder and pressure plate puzzle for a room"""
    puzzle = PuzzleRoom(room.id, PuzzleType.BOULDER_PRESSURE_PLATE, PuzzleState.ACTIVE)
    
    # Filter out cells near the edges for puzzle elements
    interior_cells = [
        (x, y) for x, y in room_cells 
        if (x > room.x + 1 and x < room.x + room.width - 2 and
            y > room.y + 1 and y < room.y + room.height - 2)
    ]
    
    if len(interior_cells) < 8:  # Need space for altar + 3 boulders + 3 plates + chest + barrier
        return puzzle
    
    # Place altar in center
    center_x = room.x + room.width // 2
    center_y = room.y + room.height // 2
    altar = Altar(center_x, center_y)
    puzzle.add_element(altar)
    
    # Remove center from available positions
    available_cells = [cell for cell in interior_cells if cell != (center_x, center_y)]
    
    if len(available_cells) < 7:
        return puzzle
    
    # Randomly place 3 pressure plates
    random.shuffle(available_cells)
    pressure_plate_positions = available_cells[:3]
    
    for x, y in pressure_plate_positions:
        plate = PressurePlate(x, y)
        puzzle.add_element(plate)
    
    # Place 3 boulders near pressure plates but not on them
    boulder_positions = available_cells[3:6]
    for x, y in boulder_positions:
        boulder = Boulder(x, y)
        puzzle.add_element(boulder)
    
    # Place glyph on a wall (approximate)
    glyph_pos = available_cells[6]
    glyph = Glyph(glyph_pos[0], glyph_pos[1])
    puzzle.add_element(glyph)
    
    # Place barrier near room exit
    if len(available_cells) > 7:
        barrier_pos = available_cells[7]
        barrier = Barrier(barrier_pos[0], barrier_pos[1])
        puzzle.add_element(barrier)
    
    # Place chest
    if len(available_cells) > 8:
        chest_pos = available_cells[8]
        # 30% chance for trapped chest
        is_trapped = random.randint(1, 100) <= 30
        chest = Chest(chest_pos[0], chest_pos[1], is_trapped)
        puzzle.add_element(chest)
    
    print(f"Generated boulder puzzle for room {room.id}")
    return puzzle

def should_generate_puzzle(room) -> bool:
    """Determine if a room should have a puzzle"""
    # Only generate puzzles in larger rooms
    room_area = room.width * room.height
    if room_area < 25:  # 5x5 minimum
        return False
    
    # 20% chance for eligible rooms
    return random.randint(1, 100) <= 20