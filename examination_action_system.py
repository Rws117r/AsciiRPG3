
# examination_action_system.py - Smart look/examine and contextual action system
import pygame
import math
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from game_constants import *

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

@dataclass
class ExaminableEntity:
    """Represents something that can be examined"""
    name: str
    description: str
    ascii_char: str
    detailed_description: str = ""
    entity_type: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def get_examination_text(self, distance: int, player=None) -> List[str]:
        """Get text to display when examining this entity"""
        lines = [f"**{self.name}**"]
        
        if distance <= 1:
            # Close examination - full details
            lines.append(self.detailed_description or self.description)
            if self.properties:
                for key, value in self.properties.items():
                    if key.startswith("visible_"):
                        display_key = key.replace("visible_", "").title()
                        lines.append(f"{display_key}: {value}")
        else:
            # Distant view - basic description
            lines.append(self.description)
        
        return lines

@dataclass 
class AvailableAction:
    """Represents an action the player can take"""
    name: str
    description: str
    category: ActionCategory
    range_required: int = 1
    requires_item: str = None
    requires_spell: str = None
    mana_cost: int = 0
    action_data: Dict[str, Any] = field(default_factory=dict)
    
    def can_perform(self, player, distance: int, target_entity: ExaminableEntity = None) -> Tuple[bool, str]:
        """Check if player can perform this action"""
        # Distance check
        if distance > self.range_required:
            return False, f"Too far away (need to be within {self.range_required} cells)"
        
        # Item requirement
        if self.requires_item:
            has_item = False
            for inv_item in player.inventory:
                if self.requires_item.lower() in inv_item.item.name.lower():
                    has_item = True
                    break
            if not has_item:
                return False, f"Requires {self.requires_item}"
        
        # Spell requirement  
        if self.requires_spell:
            if self.requires_spell not in player.starting_spells:
                return False, f"Don't know {self.requires_spell} spell"
            # TODO: Check mana when mana system exists
        
        # Special conditions based on action type
        if self.category == ActionCategory.MOVEMENT:
            # Check if movement is possible
            pass
        elif self.category == ActionCategory.INTERACTION:
            # Check if interaction is possible with this entity
            pass
        
        return True, ""

class ExaminationSystem:
    """Manages the examination and action selection interface"""
    
    def __init__(self, screen_width: int, screen_height: int, font_file: str):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fonts
        try:
            self.title_font = pygame.font.Font(font_file, 24)
            self.text_font = pygame.font.Font(font_file, 18)
            self.small_font = pygame.font.Font(font_file, 14)
            self.action_font = pygame.font.Font(font_file, 16)
        except:
            self.title_font = pygame.font.Font(None, 24)
            self.text_font = pygame.font.Font(None, 18)
            self.small_font = pygame.font.Font(None, 14)
            self.action_font = pygame.font.Font(None, 16)
        
        # State
        self.mode = ExamineMode.INACTIVE
        self.cursor_x = 0
        self.cursor_y = 0
        self.selected_entity: Optional[ExaminableEntity] = None
        self.available_actions: List[AvailableAction] = []
        self.selected_action_index = 0
        
        # UI positioning
        self.textbox_width = 400
        self.textbox_height = 300
        self.action_menu_width = 350
        self.action_menu_height = 250
        
        # Entity database
        self.entity_database: Dict[Tuple[int, int], ExaminableEntity] = {}
        self._setup_base_entities()
    
    def _setup_base_entities(self):
        """Setup base entity descriptions"""
        self.base_entity_types = {
            TileType.ALTAR: ExaminableEntity(
                "Stone Altar",
                "An ancient stone altar carved with mystical runes.",
                UI_ICONS["ALTAR"],
                "The altar is made of weathered granite, its surface worn smooth by countless rituals. Intricate runes spiral around its base, glowing faintly with residual magic. You sense it could be used for prayers or magical rituals.",
                "altar",
                {"visible_material": "granite", "visible_condition": "ancient"}
            ),
            
            TileType.BOULDER: ExaminableEntity(
                "Large Boulder", 
                "A heavy stone boulder blocking the way.",
                UI_ICONS["BOULDER"],
                "This massive boulder is roughly carved from dark stone. It looks heavy but might be moveable with enough force. The surface shows scratches and wear marks, suggesting it has been moved before.",
                "boulder",
                {"visible_weight": "very heavy", "visible_material": "dark stone"}
            ),
            
            TileType.PRESSURE_PLATE: ExaminableEntity(
                "Pressure Plate",
                "A circular stone plate set into the floor.",
                UI_ICONS["PRESSURE_PLATE"], 
                "This pressure-sensitive plate is carefully fitted into the floor. Ancient mechanisms are visible around its edges. It appears designed to trigger when sufficient weight is placed upon it.",
                "pressure_plate",
                {"visible_mechanism": "pressure-sensitive", "visible_state": "inactive"}
            ),
            
            TileType.PRESSURE_PLATE_ACTIVE: ExaminableEntity(
                "Active Pressure Plate",
                "A glowing pressure plate with something heavy on it.",
                UI_ICONS["PRESSURE_PLATE"],
                "The pressure plate glows with magical energy, activated by the weight upon it. You can see magical circuits flowing beneath its surface, connecting to something elsewhere in the room.",
                "pressure_plate", 
                {"visible_mechanism": "pressure-sensitive", "visible_state": "activated"}
            ),
            
            TileType.GLYPH: ExaminableEntity(
                "Mystical Glyph",
                "Arcane symbols carved into the floor.",
                UI_ICONS["GLYPH"],
                "These mystical symbols are etched deep into the stone floor, filled with traces of silver and other precious metals. The glyph pulses faintly with dormant magical energy, waiting for the right conditions to activate.",
                "glyph",
                {"visible_material": "silver inlay", "visible_state": "dormant"}
            ),
            
            TileType.GLYPH_ACTIVE: ExaminableEntity(
                "Glowing Glyph", 
                "Brightly glowing arcane symbols.",
                UI_ICONS["GLYPH"],
                "The glyph blazes with magical light, its silver inlays now molten-bright with power. Waves of magical energy pulse outward from its center, and you can feel the air itself humming with arcane force.",
                "glyph",
                {"visible_material": "molten silver", "visible_state": "fully active"}
            ),
            
            TileType.BARRIER: ExaminableEntity(
                "Magical Barrier",
                "Shimmering red energy bars block passage.",
                UI_ICONS["BARRIER"],
                "Vertical bars of crackling red energy stretch from floor to ceiling, completely blocking passage. The magical barrier hums with contained power and feels dangerous to approach. It appears to be sustained by some external source.",
                "barrier",
                {"visible_energy": "red crackling", "visible_state": "active"}
            ),
            
            TileType.CHEST: ExaminableEntity(
                "Treasure Chest",
                "An ornate wooden chest bound with metal.",
                UI_ICONS["CHEST"],
                "This chest is crafted from dark hardwood and reinforced with iron bands. The lock mechanism looks intricate but functional. You notice scratch marks around the lock - others have tried to open it before.",
                "chest",
                {"visible_material": "dark wood & iron", "visible_lock": "complex mechanism"}
            ),
            
            TileType.STAIRS_DOWN: ExaminableEntity(
                "Descending Stairs",
                "Stone steps leading downward into darkness.",
                UI_ICONS["STAIRS_DOWN"],
                "These worn stone steps descend into the depths below. Cool air rises from the darkness, carrying strange scents and the faint echo of distant sounds. The steps are worn smooth by countless feet over the ages.",
                "stairs",
                {"visible_direction": "downward", "visible_condition": "worn smooth"}
            )
        }
    
    def activate_examine_mode(self, player_x: int, player_y: int):
        """Activate examination mode starting at player position"""
        self.mode = ExamineMode.LOOKING
        self.cursor_x = player_x
        self.cursor_y = player_y
        self.selected_entity = None
        self.available_actions = []
    
    def deactivate_examine_mode(self):
        """Exit examination mode"""
        self.mode = ExamineMode.INACTIVE
        self.selected_entity = None
        self.available_actions = []
    
    def move_cursor(self, dx: int, dy: int):
        """Move examination cursor"""
        if self.mode == ExamineMode.LOOKING:
            self.cursor_x += dx
            self.cursor_y += dy
    
    def examine_current_position(self, dungeon, player) -> bool:
        """Examine whatever is at the cursor position"""
        if self.mode != ExamineMode.LOOKING:
            return False
        
        # Get entity at cursor position
        entity = self._get_entity_at_position(self.cursor_x, self.cursor_y, dungeon)
        if not entity:
            return False
        
        self.selected_entity = entity
        
        # Calculate available actions
        distance = self._calculate_distance(player.x, player.y, self.cursor_x, self.cursor_y)
        self.available_actions = self._get_available_actions(entity, player, distance, self.cursor_x, self.cursor_y)
        
        if self.available_actions:
            self.mode = ExamineMode.ACTION_MENU
            self.selected_action_index = 0
            return True
        
        return False
    
    def navigate_action_menu(self, direction: int):
        """Navigate up/down in action menu"""
        if self.mode == ExamineMode.ACTION_MENU and self.available_actions:
            self.selected_action_index = (self.selected_action_index + direction) % len(self.available_actions)
    
    def select_action(self) -> Optional[AvailableAction]:
        """Select the currently highlighted action"""
        if (self.mode == ExamineMode.ACTION_MENU and 
            self.available_actions and 
            0 <= self.selected_action_index < len(self.available_actions)):
            return self.available_actions[self.selected_action_index]
        return None
    
    def _get_entity_at_position(self, x: int, y: int, dungeon) -> Optional[ExaminableEntity]:
        """Get the examinable entity at the given position"""
        # Check if position is revealed
        if not dungeon.is_revealed(x, y):
            return None
        
        # Check for monsters first (they're most interesting)
        for monster in dungeon.monsters:
            if monster.x == x and monster.y == y:
                return ExaminableEntity(
                    monster.name,
                    f"A {monster.name.lower()} lurks here.",
                    getattr(monster.template, 'ascii_char', 'M'),
                    self._get_monster_description(monster),
                    "monster",
                    {"visible_health": f"{monster.current_hp}/{monster.max_hp}"}
                )
        
        # Check dungeon tiles
        tile_type = dungeon.tiles.get((x, y), TileType.VOID)
        if tile_type in self.base_entity_types:
            entity = self.base_entity_types[tile_type]
            # Create a copy with position-specific modifications
            modified_entity = ExaminableEntity(
                entity.name, entity.description, entity.ascii_char,
                entity.detailed_description, entity.entity_type,
                entity.properties.copy()
            )
            
            # Add position-specific information
            self._enhance_entity_description(modified_entity, x, y, dungeon)
            return modified_entity
        
        # Default for floor/unknown
        if tile_type == TileType.FLOOR:
            return ExaminableEntity(
                "Stone Floor",
                "Worn stone flooring.",
                ".",
                "The floor is made of fitted stone blocks, worn smooth by age and foot traffic. Small cracks between the stones collect dust and debris.",
                "floor"
            )
        
        return None
    
    def _get_monster_description(self, monster) -> str:
        """Generate detailed monster description"""
        desc = f"This {monster.name.lower()} "
        
        health_ratio = monster.current_hp / monster.max_hp
        if health_ratio > 0.8:
            desc += "appears to be in excellent health, "
        elif health_ratio > 0.5:
            desc += "shows some signs of wear, "
        elif health_ratio > 0.2:
            desc += "is visibly wounded, "
        else:
            desc += "is badly injured and desperate, "
        
        # Add behavior description
        if hasattr(monster, 'fled') and monster.fled:
            desc += "and seems ready to flee at any moment."
        else:
            desc += "and looks ready for combat."
        
        return desc
    
    def _enhance_entity_description(self, entity: ExaminableEntity, x: int, y: int, dungeon):
        """Add context-specific details to entity descriptions"""
        # Check for puzzle state
        puzzle_element = dungeon.puzzle_manager.get_element_at_position(x, y)
        if puzzle_element:
            if entity.entity_type == "pressure_plate":
                if puzzle_element.active:
                    entity.properties["visible_state"] = "activated and glowing"
                else:
                    entity.properties["visible_state"] = "inactive"
            elif entity.entity_type == "glyph":
                if puzzle_element.active:
                    entity.properties["visible_state"] = "blazing with power"
                else:
                    entity.properties["visible_state"] = "dormant"
        
        # Check for special effects from entity interaction system
        if hasattr(dungeon, 'entity_manager'):
            interactive_entity = dungeon.entity_manager.interaction_system.get_entity(x, y)
            if interactive_entity:
                if interactive_entity.has_effect('ice_enchanted'):
                    entity.properties["visible_effect"] = "covered in frost"
                elif interactive_entity.has_effect('burning'):
                    entity.properties["visible_effect"] = "wreathed in flames"
                elif interactive_entity.has_effect('electrified'):
                    entity.properties["visible_effect"] = "crackling with electricity"
                elif interactive_entity.has_effect('shadow_tainted'):
                    entity.properties["visible_effect"] = "shrouded in dark energy"
                elif interactive_entity.has_effect('purified'):
                    entity.properties["visible_effect"] = "glowing with holy light"
    
    def _get_available_actions(self, entity: ExaminableEntity, player, distance: int, target_x: int, target_y: int) -> List[AvailableAction]:
        """Get all available actions for the given entity and player state"""
        actions = []
        
        # Movement actions
        if distance == 1 and entity.entity_type == "boulder":
            # Calculate push direction
            dx = target_x - player.x
            dy = target_y - player.y
            direction_name = self._get_direction_name(dx, dy)
            actions.append(AvailableAction(
                f"Push {direction_name}",
                f"Push the boulder {direction_name.lower()}",
                ActionCategory.MOVEMENT,
                range_required=1,
                action_data={"action": "push", "direction": (dx, dy)}
            ))
        
        # Basic interactions
        if distance <= 1:
            if entity.entity_type in ["altar", "chest", "pressure_plate"]:
                actions.append(AvailableAction(
                    "Touch",
                    f"Touch the {entity.name.lower()}",
                    ActionCategory.INTERACTION,
                    range_required=1,
                    action_data={"action": "touch"}
                ))
            
            if entity.entity_type == "altar":
                actions.append(AvailableAction(
                    "Pray",
                    "Offer a prayer at the altar",
                    ActionCategory.INTERACTION,
                    range_required=1,
                    action_data={"action": "pray"}
                ))
            
            if entity.entity_type == "chest":
                actions.append(AvailableAction(
                    "Open",
                    "Attempt to open the chest",
                    ActionCategory.INTERACTION,
                    range_required=1,
                    action_data={"action": "open"}
                ))
        
        # Combat actions
        if entity.entity_type == "monster" and distance <= 1:
            actions.append(AvailableAction(
                "Attack",
                f"Attack the {entity.name.lower()} with your weapon",
                ActionCategory.COMBAT,
                range_required=1,
                action_data={"action": "attack"}
            ))
        
        # Spell actions
        spell_actions = self._get_spell_actions(entity, player, distance, target_x, target_y)
        actions.extend(spell_actions)
        
        # Item actions  
        item_actions = self._get_item_actions(entity, player, distance, target_x, target_y)
        actions.extend(item_actions)
        
        # Filter out actions the player can't perform
        available_actions = []
        for action in actions:
            can_perform, reason = action.can_perform(player, distance, entity)
            if can_perform:
                available_actions.append(action)
            # Could add unavailable actions with reasons to show why they can't be used
        
        return available_actions
    
    def _get_spell_actions(self, entity: ExaminableEntity, player, distance: int, target_x: int, target_y: int) -> List[AvailableAction]:
        """Get available spell actions"""
        actions = []
        
        for spell_name in player.starting_spells:
            spell_range = self._get_spell_range(spell_name)
            if distance <= spell_range:
                # Determine if spell makes sense for this target
                spell_element = self._get_spell_element(spell_name)
                if self._spell_target_makes_sense(spell_name, spell_element, entity):
                    actions.append(AvailableAction(
                        f"Cast {spell_name}",
                        f"Cast {spell_name} on the {entity.name.lower()}",
                        ActionCategory.SPELL,
                        range_required=spell_range,
                        requires_spell=spell_name,
                        action_data={"action": "cast_spell", "spell": spell_name, "element": spell_element}
                    ))
        
        return actions
    
    def _get_item_actions(self, entity: ExaminableEntity, player, distance: int, target_x: int, target_y: int) -> List[AvailableAction]:
        """Get available item actions"""
        actions = []
        
        # Check inventory for usable items
        for inv_item in player.inventory:
            item_name = inv_item.item.name
            item_range = self._get_item_range(item_name)
            
            if distance <= item_range:
                if "Wand" in item_name:
                    element = self._get_item_element(item_name)
                    actions.append(AvailableAction(
                        f"Use {item_name}",
                        f"Use {item_name} on the {entity.name.lower()}",
                        ActionCategory.ITEM,
                        range_required=item_range,
                        requires_item=item_name,
                        action_data={"action": "use_item", "item": item_name, "element": element}
                    ))
                elif "Potion" in item_name and distance <= 1:
                    actions.append(AvailableAction(
                        f"Apply {item_name}",
                        f"Apply {item_name} to the {entity.name.lower()}",
                        ActionCategory.ITEM,
                        range_required=1,
                        requires_item=item_name,
                        action_data={"action": "use_item", "item": item_name}
                    ))
        
        return actions
    
    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        """Calculate Chebyshev distance (max of dx, dy)"""
        return max(abs(x2 - x1), abs(y2 - y1))
    
    def _get_direction_name(self, dx: int, dy: int) -> str:
        """Convert direction vector to name"""
        if dx == 0 and dy == -1: return "North"
        elif dx == 0 and dy == 1: return "South"
        elif dx == -1 and dy == 0: return "West"
        elif dx == 1 and dy == 0: return "East"
        elif dx == -1 and dy == -1: return "Northwest"
        elif dx == 1 and dy == -1: return "Northeast"
        elif dx == -1 and dy == 1: return "Southwest"
        elif dx == 1 and dy == 1: return "Southeast"
        else: return "Forward"
    
    def _get_spell_range(self, spell_name: str) -> int:
        """Get the range of a spell in cells"""
        # Import the spell range function
        try:
            from rendering_engine import get_spell_range_in_cells
            return get_spell_range_in_cells(spell_name)
        except ImportError:
            # Fallback ranges
            if spell_name in ["Cure Wounds", "Holy Weapon", "Light", "Burning Hands"]:
                return 1  # Close range
            elif spell_name in ["Turn Undead", "Charm Person", "Sleep"]:
                return 6  # Near range  
            elif spell_name in ["Magic Missile"]:
                return 20  # Far range
            else:
                return 1
    
    def _get_spell_element(self, spell_name: str) -> str:
        """Get the elemental type of a spell"""
        spell_elements = {
            'Burning Hands': 'fire',
            'Turn Undead': 'holy',
            'Light': 'holy',
            'Holy Weapon': 'holy',
            'Protection From Evil': 'holy',
            'Cure Wounds': 'holy',
            'Magic Missile': 'arcane',
            'Charm Person': 'arcane',
            'Sleep': 'arcane',
            'Detect Magic': 'arcane'
        }
        return spell_elements.get(spell_name, 'arcane')
    
    def _get_item_range(self, item_name: str) -> int:
        """Get the range of an item"""
        if "Wand" in item_name:
            return 6  # Most wands have moderate range
        elif "Potion" in item_name:
            return 1  # Must be adjacent to apply
        elif "Scroll" in item_name:
            return 3  # Reading distance
        else:
            return 1
    
    def _get_item_element(self, item_name: str) -> str:
        """Get the elemental type of an item"""
        if "Ice" in item_name: return "ice"
        elif "Fire" in item_name: return "fire"
        elif "Lightning" in item_name: return "lightning"
        elif "Holy" in item_name: return "holy"
        elif "Shadow" in item_name: return "shadow"
        else: return "physical"
    
    def _spell_target_makes_sense(self, spell_name: str, element: str, entity: ExaminableEntity) -> bool:
        """Check if it makes sense to cast this spell on this entity"""
        # Healing spells don't work on inanimate objects
        if spell_name in ["Cure Wounds"] and entity.entity_type != "monster":
            return False
        
        # Turn Undead only affects undead
        if spell_name == "Turn Undead" and entity.entity_type != "monster":
            return False
        
        # Most damage spells can target anything
        if spell_name in ["Burning Hands", "Magic Missile"]:
            return True
        
        # Utility spells work on most things
        if spell_name in ["Light", "Detect Magic"]:
            return True
        
        return True
    
    def draw(self, surface: pygame.Surface, player, dungeon, viewport_x: int, viewport_y: int, cell_size: int):
        """Draw the examination interface"""
        if self.mode == ExamineMode.INACTIVE:
            return
        
        # Draw cursor
        if self.mode == ExamineMode.LOOKING:
            self._draw_examination_cursor(surface, viewport_x, viewport_y, cell_size)
        
        # Draw information textbox
        if self.selected_entity:
            self._draw_entity_info(surface, player)
        
        # Draw action menu
        if self.mode == ExamineMode.ACTION_MENU:
            self._draw_action_menu(surface)
        
        # Draw instructions
        self._draw_instructions(surface)
    
    def _draw_examination_cursor(self, surface: pygame.Surface, viewport_x: int, viewport_y: int, cell_size: int):
        """Draw the examination cursor"""
        cursor_screen_x = (self.cursor_x - viewport_x) * cell_size
        cursor_screen_y = (self.cursor_y - viewport_y) * cell_size
        
        # Draw highlight rectangle
        highlight_rect = pygame.Rect(cursor_screen_x, cursor_screen_y, cell_size, cell_size)
        pygame.draw.rect(surface, (255, 255, 0, 100), highlight_rect)
        pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
        
        # Draw crosshair
        center_x = cursor_screen_x + cell_size // 2
        center_y = cursor_screen_y + cell_size // 2
        pygame.draw.line(surface, COLOR_WHITE, (center_x - 5, center_y), (center_x + 5, center_y), 2)
        pygame.draw.line(surface, COLOR_WHITE, (center_x, center_y - 5), (center_x, center_y + 5), 2)
    
    def _draw_entity_info(self, surface: pygame.Surface, player):
        """Draw the entity information textbox"""
        # Position textbox on the right side
        textbox_x = self.screen_width - self.textbox_width - 20
        textbox_y = 50
        
        textbox_rect = pygame.Rect(textbox_x, textbox_y, self.textbox_width, self.textbox_height)
        
        # Draw background
        pygame.draw.rect(surface, (0, 0, 0, 200), textbox_rect)
        pygame.draw.rect(surface, COLOR_WHITE, textbox_rect, 2)
        
        # Get examination text
        distance = self._calculate_distance(player.x, player.y, self.cursor_x, self.cursor_y)
        examination_lines = self.selected_entity.get_examination_text(distance, player)
        
        # Draw text
        y_offset = textbox_y + 15
        for line in examination_lines:
            if line.startswith("**") and line.endswith("**"):
                # Title line
                title_text = line[2:-2]
                text_surf = self.title_font.render(title_text, True, COLOR_WHITE)
            else:
                # Regular text - wrap if needed
                wrapped_lines = self._wrap_text(line, self.textbox_width - 30, self.text_font)
                for wrapped_line in wrapped_lines:
                    text_surf = self.text_font.render(wrapped_line, True, COLOR_WHITE)
                    surface.blit(text_surf, (textbox_x + 15, y_offset))
                    y_offset += 22
                continue
            
            surface.blit(text_surf, (textbox_x + 15, y_offset))
            y_offset += 30
        
        # Draw distance info
        distance_text = f"Distance: {distance} cell{'s' if distance != 1 else ''}"
        distance_surf = self.small_font.render(distance_text, True, (200, 200, 200))
        surface.blit(distance_surf, (textbox_x + 15, textbox_y + self.textbox_height - 25))
    
    def _draw_action_menu(self, surface: pygame.Surface):
        """Draw the action selection menu"""
        menu_x = (self.screen_width - self.action_menu_width) // 2
        menu_y = (self.screen_height - self.action_menu_height) // 2
        
        menu_rect = pygame.Rect(menu_x, menu_y, self.action_menu_width, self.action_menu_height)
        
        # Draw background
        pygame.draw.rect(surface, (0, 0, 0, 240), menu_rect)
        pygame.draw.rect(surface, COLOR_WHITE, menu_rect, 2)
        
        # Draw title
        title_text = "Available Actions"
        title_surf = self.title_font.render(title_text, True, COLOR_WHITE)
        title_rect = title_surf.get_rect(centerx=menu_rect.centerx, top=menu_y + 15)
        surface.blit(title_surf, title_rect)
        
        # Draw actions
        action_y = title_rect.bottom + 20
        for i, action in enumerate(self.available_actions):
            # Highlight selected action
            if i == self.selected_action_index:
                highlight_rect = pygame.Rect(menu_x + 10, action_y - 5, self.action_menu_width - 20, 25)
                pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
                pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 1)
            
            # Draw action name
            color = COLOR_BLACK if i == self.selected_action_index else COLOR_WHITE
            action_surf = self.action_font.render(action.name, True, color)
            surface.blit(action_surf, (menu_x + 20, action_y))
            
            # Draw action description (smaller text)
            desc_surf = self.small_font.render(action.description, True, 
                                             (50, 50, 50) if i == self.selected_action_index else (180, 180, 180))
            surface.blit(desc_surf, (menu_x + 20, action_y + 20))
            
            action_y += 45
    
    def _draw_instructions(self, surface: pygame.Surface):
        """Draw control instructions"""
        instructions = []
        
        if self.mode == ExamineMode.LOOKING:
            instructions = [
                "EXAMINE MODE",
                "Arrow Keys: Move cursor",
                "ENTER: Examine/Select",
                "ESC: Exit examine mode"
            ]
        elif self.mode == ExamineMode.ACTION_MENU:
            instructions = [
                "ACTION MENU", 
                "UP/DOWN: Select action",
                "ENTER: Perform action",
                "ESC: Back to examining"
            ]
        
        # Draw on bottom left
        inst_x = 20
        inst_y = self.screen_height - (len(instructions) * 18) - 20
        
        for instruction in instructions:
            if instruction == instructions[0]:  # Title
                inst_surf = self.action_font.render(instruction, True, COLOR_WHITE)
            else:
                inst_surf = self.small_font.render(instruction, True, (200, 200, 200))
            
            surface.blit(inst_surf, (inst_x, inst_y))
            inst_y += 18
    
    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> List[str]:
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