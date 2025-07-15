# game_manager.py - Complete fixed version with examination system integration
import pygame
import json
from typing import Optional
from game_constants import *
from dungeon_classes import DungeonExplorer
from character_creation import run_character_creation, Player
from input_handler import InputHandler
from combat_coordinator import CombatCoordinator
from rendering_coordinator import RenderingCoordinator
from player_manager import PlayerManager
from ui_systems import organize_inventory_into_containers
from examination_action_system import ExaminationSystem, ExaminationInputHandler

class GameManager:
    """Manages overall game state and coordinates between systems."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.game_state = GameState.MAIN_MENU
        
        # Load dungeon data
        self.dungeon_data = self._load_dungeon_data()
        
        # Initialize subsystems
        self.input_handler = InputHandler()
        self.combat_coordinator = CombatCoordinator()
        self.rendering_coordinator = RenderingCoordinator(screen)
        self.player_manager = PlayerManager()
        
        # Initialize examination system
        screen_width, screen_height = screen.get_size()
        self.examination_system = ExaminationSystem(screen_width, screen_height, FONT_FILE)
        self.examination_input = ExaminationInputHandler(self.examination_system)
        
        # Game world state
        self.dungeon: Optional[DungeonExplorer] = None
        self.player: Optional[Player] = None
        self.player_pos = (0, 0)
        self.walkable_positions = set()
        
        # UI state
        self.fullscreen = False
        self.zoom_level = DEFAULT_ZOOM
        
        # Menu/UI state
        self.inventory_selected_index = 0
        self.equipment_selected_slot = 'weapon'
        self.equipment_selection_mode = False
        self.equipment_selection_index = 0
        self.current_containers = []
        
        # Spell system state
        self.spell_target_pos = (0, 0)
        self.current_spell = ""
        
        # Initialize input handler callbacks
        self._setup_input_callbacks()
    
    def _load_dungeon_data(self) -> dict:
        """Load dungeon data from JSON file."""
        try:
            with open(JSON_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: '{JSON_FILE}' not found.")
            raise
    
    def _setup_input_callbacks(self):
        """Setup callbacks for input handler."""
        # Movement callbacks
        self.input_handler.set_movement_callback(self._handle_movement)
        
        # Menu callbacks
        self.input_handler.set_menu_callback('inventory', self._open_inventory)
        self.input_handler.set_menu_callback('equipment', self._open_equipment)
        self.input_handler.set_menu_callback('spells', self._open_spell_menu)
        self.input_handler.set_menu_callback('examine', self._open_examine_mode)
        
        # Navigation callbacks for UI screens
        self.input_handler.set_navigation_callback(self._handle_navigation)
        self.input_handler.set_selection_callback(self._handle_selection)
        
        # Examination callback
        self.input_handler.set_examination_callback(self._handle_examination_input)
        
        # System callbacks
        self.input_handler.set_system_callback('fullscreen', self._toggle_fullscreen)
        self.input_handler.set_system_callback('zoom_in', self._zoom_in)
        self.input_handler.set_system_callback('zoom_out', self._zoom_out)
        self.input_handler.set_system_callback('escape', self._handle_escape)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle pygame events. Returns 'quit' if game should exit."""
        if self.game_state == GameState.MAIN_MENU:
            return self._handle_main_menu_event(event)
        else:
            return self.input_handler.handle_event(event, self.game_state, self.examination_system.mode)
    
    def _handle_main_menu_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle main menu events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Get start button rect from rendering coordinator
            start_button_rect = self.rendering_coordinator.get_main_menu_button_rect()
            if start_button_rect and start_button_rect.collidepoint(event.pos):
                result = self._start_character_creation()
                if result == "quit":
                    return "quit"
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "quit"
        return None
    
    def _start_character_creation(self):
        """Start character creation process."""
        # Store current screen dimensions before quitting display
        screen_width, screen_height = self.screen.get_size()
        
        # Quit the current display
        pygame.display.quit()
        
        # Run character creation (it will create its own display)
        created_player = run_character_creation(screen_width, screen_height, FONT_FILE)
        
        if created_player is None:
            # Character creation was cancelled, need to recreate display for main menu
            self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            pygame.display.set_caption("Dungeon Explorer")
            self.rendering_coordinator.update_screen(self.screen)
            return None  # Stay on main menu
        
        # Character creation successful, reinitialize display for game
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Dungeon Explorer")
        
        # Update rendering coordinator with new screen
        self.rendering_coordinator.update_screen(self.screen)
        
        # Update examination system screen size
        screen_width, screen_height = self.screen.get_size()
        self.examination_system.screen_width = screen_width
        self.examination_system.screen_height = screen_height
        
        # Setup player and world
        self.player = created_player
        self.player_manager.setup_player(self.player)
        
        # Initialize dungeon
        self.dungeon = DungeonExplorer(self.dungeon_data)
        self.player_pos = self.dungeon.get_starting_position()
        self.walkable_positions = self.dungeon.get_walkable_positions(for_monster=False)
        
        # Setup rendering coordinator with game world
        self.rendering_coordinator.setup_world(self.dungeon, self.player, self.player_pos)
        
        # Change to playing state
        self.game_state = GameState.PLAYING
    
    def update(self, dt_seconds: float):
        """Update game systems."""
        if self.game_state == GameState.PLAYING and self.player and self.dungeon:
            # Update combat
            self.combat_coordinator.update(dt_seconds)
            
            # Update rendering coordinator
            self.rendering_coordinator.update(dt_seconds, self.player_pos, self.zoom_level)
    
    def render(self):
        """Render current game state."""
        if self.game_state == GameState.MAIN_MENU:
            self.rendering_coordinator.render_main_menu()
        
        elif self.game_state == GameState.PLAYING:
            if self.player and self.dungeon:
                self.rendering_coordinator.render_game(
                    self.player, self.player_pos, self.dungeon, 
                    self.combat_coordinator, self.zoom_level
                )
                
                # Render examination interface if active
                if self.examination_system.mode != ExamineMode.INACTIVE:
                    viewport_x, viewport_y = self.rendering_coordinator.viewport_x, self.rendering_coordinator.viewport_y
                    cell_size = self.rendering_coordinator.cell_size
                    self.examination_system.draw(self.screen, self.player, self.dungeon, 
                                               viewport_x, viewport_y, cell_size)
        
        elif self.game_state == GameState.INVENTORY:
            self.rendering_coordinator.render_inventory(
                self.player, self.current_containers, self.inventory_selected_index
            )
        
        elif self.game_state == GameState.EQUIPMENT:
            self.rendering_coordinator.render_equipment(
                self.player, self.equipment_selected_slot, 
                self.equipment_selection_mode, self.equipment_selection_index
            )
        
        elif self.game_state == GameState.SPELL_MENU:
            self.rendering_coordinator.render_spell_menu(self.player)
        
        elif self.game_state == GameState.SPELL_TARGETING:
            self.rendering_coordinator.render_spell_targeting(
                self.player, self.player_pos, self.current_spell, self.spell_target_pos
            )
    
    def _handle_examination_input(self, event: pygame.event.Event, examine_mode: ExamineMode) -> Optional[str]:
        """Handle examination system input."""
        if not self.player or not self.dungeon:
            return None
        
        result = self.examination_input.handle_event(event, self.player, self.dungeon)
        
        # Process examination results
        if result and result.startswith("action_executed:"):
            action_type = result.split(":")[1]
            print(f"Action performed: {action_type.replace('_', ' ').title()}")
            
            # Update walkable positions after actions that might change the world
            if action_type in ["pushed_boulder", "prayed", "cast_spell", "used_item"]:
                self.walkable_positions = self.dungeon.get_walkable_positions(for_monster=False)
        
        return result
    
    def _open_examine_mode(self):
        """Open examination mode."""
        if self.combat_coordinator.is_in_combat():
            return
        if self.player:
            self.examination_system.activate_examine_mode(self.player.x, self.player.y)
            print("Examination mode activated. Use arrow keys to look around, ENTER to examine.")
    
    def _handle_navigation(self, screen_type: str, direction: str):
        """Handle navigation in UI screens."""
        if screen_type == 'inventory':
            if direction == 'up':
                if self.current_containers:
                    self.inventory_selected_index = (self.inventory_selected_index - 1) % len(self.current_containers)
            elif direction == 'down':
                if self.current_containers:
                    self.inventory_selected_index = (self.inventory_selected_index + 1) % len(self.current_containers)
        
        elif screen_type == 'equipment':
            equipment_slots = ['weapon', 'armor', 'shield', 'light']
            
            if not self.equipment_selection_mode:
                # Navigating equipment slots
                if direction == 'up':
                    current_index = equipment_slots.index(self.equipment_selected_slot)
                    self.equipment_selected_slot = equipment_slots[(current_index - 1) % len(equipment_slots)]
                elif direction == 'down':
                    current_index = equipment_slots.index(self.equipment_selected_slot)
                    self.equipment_selected_slot = equipment_slots[(current_index + 1) % len(equipment_slots)]
            else:
                # Navigating equipment selection
                from ui_systems import get_available_items_for_slot
                available_items = get_available_items_for_slot(self.player, self.equipment_selected_slot)
                available_items.insert(0, None)  # Add unequip option
                
                if direction == 'up':
                    self.equipment_selection_index = (self.equipment_selection_index - 1) % len(available_items)
                elif direction == 'down':
                    self.equipment_selection_index = (self.equipment_selection_index + 1) % len(available_items)
        
        elif screen_type == 'spell_target':
            # Handle spell targeting movement
            from rendering_engine import is_valid_spell_target
            dx, dy = {
                'up': (0, -1), 'down': (0, 1),
                'left': (-1, 0), 'right': (1, 0)
            }.get(direction, (0, 0))
            
            new_target = (self.spell_target_pos[0] + dx, self.spell_target_pos[1] + dy)
            if is_valid_spell_target(self.player_pos, new_target, self.current_spell):
                self.spell_target_pos = new_target

    def _handle_selection(self, screen_type: str, action):
        """Handle selection in UI screens."""
        if screen_type == 'inventory':
            if action == 'select':
                if self.current_containers and 0 <= self.inventory_selected_index < len(self.current_containers):
                    current_container = self.current_containers[self.inventory_selected_index]
                    # Could implement container viewing here
                    print(f"Selected container: {current_container.name}")
        
        elif screen_type == 'equipment':
            if action == 'select':
                if not self.equipment_selection_mode:
                    # Enter selection mode
                    self.equipment_selection_mode = True
                    self.equipment_selection_index = 0
                else:
                    # Make selection
                    from ui_systems import get_available_items_for_slot, equip_item, unequip_item
                    available_items = get_available_items_for_slot(self.player, self.equipment_selected_slot)
                    available_items.insert(0, None)  # Add unequip option
                    
                    if 0 <= self.equipment_selection_index < len(available_items):
                        selected_item = available_items[self.equipment_selection_index]
                        
                        if selected_item is None:
                            unequip_item(self.player, self.equipment_selected_slot)
                            print(f"Unequipped {self.equipment_selected_slot}")
                        else:
                            equip_item(self.player, selected_item, self.equipment_selected_slot)
                            print(f"Equipped {selected_item.item.name} to {self.equipment_selected_slot}")
                        
                        self.equipment_selection_mode = False
        
        elif screen_type == 'spell':
            if isinstance(action, int):
                # Spell selection
                self.current_spell = "Burning Hands"  # For now, just one spell
                self.game_state = GameState.SPELL_TARGETING
        
        elif screen_type == 'spell_target':
            if action == 'cast':
                print(f"Casting {self.current_spell} at {self.spell_target_pos}!")
                self.game_state = GameState.PLAYING
    
    # Movement handling
    def _handle_movement(self, direction: str) -> bool:
        """Handle player movement. Returns True if movement was processed."""
        if not self.player or not self.dungeon:
            return False
        
        # Calculate next position
        dx, dy = {
            'up': (0, -1), 'down': (0, 1),
            'left': (-1, 0), 'right': (1, 0),
            'defend': (0, 0)  # Space key for defend
        }.get(direction, (0, 0))
        
        # Handle defend action
        if direction == 'defend':
            if self.combat_coordinator.is_in_combat():
                combat_ended = self.combat_coordinator.handle_defend_action(
                    self.player, self.player_pos, self.walkable_positions
                )
                if combat_ended:
                    self._handle_combat_end()
                return True
            else:
                # Out of combat, space opens doors
                self._try_open_doors()
                return True
        
        next_pos = (self.player_pos[0] + dx, self.player_pos[1] + dy)
        
        if self.combat_coordinator.is_in_combat():
            return self._handle_combat_movement(next_pos)
        else:
            return self._handle_exploration_movement(next_pos)
    
    def _try_open_doors(self):
        """Try to open doors around the player."""
        from game_constants import TileType
        for dx, dy in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            if self.dungeon.open_door_at_position(self.player_pos[0] + dx, self.player_pos[1] + dy):
                self.walkable_positions = self.dungeon.get_walkable_positions(for_monster=False)
                break
    
    def _handle_exploration_movement(self, next_pos: tuple) -> bool:
        """Handle movement during exploration."""
        # Check for monster at target position
        monster_at_target = None
        for monster in self.dungeon.monsters:
            if (monster.x, monster.y) == next_pos and self.dungeon.is_revealed(monster.x, monster.y):
                monster_at_target = monster
                break
        
        if monster_at_target:
            # Initiate combat
            combat_ended = self.combat_coordinator.initiate_combat(
                self.player, self.player_pos, monster_at_target, 
                self.dungeon, self.walkable_positions
            )
            
            if combat_ended:
                self._handle_combat_end()
            
            return True
        
        elif next_pos in self.walkable_positions:
            # Safe movement
            self.player_pos = next_pos
            self._handle_safe_movement()
            return True
        
        return False
    
    def _handle_combat_movement(self, next_pos: tuple) -> bool:
        """Handle movement during combat."""
        combat_ended = self.combat_coordinator.handle_combat_movement(
            self.player, self.player_pos, next_pos, 
            self.dungeon, self.walkable_positions
        )
        
        if combat_ended:
            self._handle_combat_end()
        else:
            # Only update player position if they safely moved (not attacking)
            from combat_system import attempt_positional_attack
            can_attack, target_monster = attempt_positional_attack(
                self.player_pos, next_pos, 
                self.combat_coordinator.get_combat_manager(), 
                self.dungeon.monsters
            )
            
            # Only move if NOT attacking and position is walkable
            if not can_attack and next_pos in self.walkable_positions:
                self.player_pos = next_pos
        
        return True
    
    def _handle_safe_movement(self):
        """Handle effects of safe movement (doors, monster movement, etc.)."""
        from game_constants import TileType
        
        # Auto-open doors
        tile_at_pos = self.dungeon.tiles.get(self.player_pos)
        if tile_at_pos in [TileType.DOOR_HORIZONTAL, TileType.DOOR_VERTICAL]:
            if self.dungeon.open_door_at_position(self.player_pos[0], self.player_pos[1]):
                self.walkable_positions = self.dungeon.get_walkable_positions(for_monster=False)
        
        # Move monsters toward player
        self._update_monster_positions()
    
    def _update_monster_positions(self):
        """Update monster positions based on player movement."""
        occupied_tiles = {(m.x, m.y) for m in self.dungeon.monsters}
        occupied_tiles.add(self.player_pos)
        monster_walkable = self.dungeon.get_walkable_positions(for_monster=True)

        for monster in self.dungeon.monsters:
            if monster.room_id in self.dungeon.revealed_rooms:
                dx = self.player_pos[0] - monster.x
                dy = self.player_pos[1] - monster.y
                
                next_monster_pos = monster.x, monster.y
                if abs(dx) > abs(dy):
                    next_monster_pos = (monster.x + (1 if dx > 0 else -1), monster.y)
                else:
                    next_monster_pos = (monster.x, monster.y + (1 if dy > 0 else -1))
                
                if next_monster_pos in monster_walkable and next_monster_pos not in occupied_tiles:
                    monster.x, monster.y = next_monster_pos
    
    def _handle_combat_end(self):
        """Handle combat ending."""
        # Check if player died before cleanup
        player_participant = self.combat_coordinator.get_combat_manager().get_player_in_combat()
        player_died = False
        
        if player_participant and player_participant.hp <= 0:
            player_died = True
        
        # Do normal cleanup
        self.combat_coordinator.cleanup_combat(self.player, self.dungeon)
        
        # Handle respawn if player died
        if player_died:
            self._respawn_player()

    def _respawn_player(self):
        """Respawn the player at the starting position."""
        print(f"{self.player.name} respawns at the dungeon entrance...")
        
        # Reset player position to start
        self.player_pos = self.dungeon.get_starting_position()
        
        # Give player some HP back (not full heal, to maintain challenge)
        self.player.hp = max(1, self.player.max_hp // 2)  # Half health
        
        # Optional: Reset some monsters (make it less punishing)
        # You could respawn some monsters or leave them dead
        
        print(f"{self.player.name} has {self.player.hp}/{self.player.max_hp} HP")
    
    # Menu callbacks
    def _open_inventory(self):
        """Open inventory screen."""
        if self.combat_coordinator.is_in_combat():
            return
        self.game_state = GameState.INVENTORY
        self.inventory_selected_index = 0
        self.current_containers = organize_inventory_into_containers(self.player)
    
    def _open_equipment(self):
        """Open equipment screen."""
        if self.combat_coordinator.is_in_combat():
            return
        self.game_state = GameState.EQUIPMENT
        self.equipment_selected_slot = 'weapon'
        self.equipment_selection_mode = False
    
    def _open_spell_menu(self):
        """Open spell menu."""
        if self.combat_coordinator.is_in_combat():
            return
        self.game_state = GameState.SPELL_MENU
        self.spell_target_pos = self.player_pos
    
    # System callbacks
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            initial_width = INITIAL_VIEWPORT_WIDTH * int(BASE_CELL_SIZE * DEFAULT_ZOOM)
            initial_height = INITIAL_VIEWPORT_HEIGHT * int(BASE_CELL_SIZE * DEFAULT_ZOOM)
            self.screen = pygame.display.set_mode((initial_width, initial_height + HUD_HEIGHT), pygame.RESIZABLE)
        
        # Update rendering coordinator with new screen
        self.rendering_coordinator.update_screen(self.screen)
        
        # Update examination system screen size
        screen_width, screen_height = self.screen.get_size()
        self.examination_system.screen_width = screen_width
        self.examination_system.screen_height = screen_height
    
    def _zoom_in(self):
        """Zoom in."""
        self.zoom_level = min(self.zoom_level + ZOOM_STEP, MAX_ZOOM)
    
    def _zoom_out(self):
        """Zoom out."""
        self.zoom_level = max(self.zoom_level - ZOOM_STEP, MIN_ZOOM)
    
    def _handle_escape(self):
        """Handle escape key."""
        if self.examination_system.mode != ExamineMode.INACTIVE:
            if self.examination_system.mode == ExamineMode.ACTION_MENU:
                self.examination_system.mode = ExamineMode.LOOKING
            else:
                self.examination_system.deactivate_examine_mode()
            return None
        elif self.game_state == GameState.PLAYING:
            if self.combat_coordinator.is_in_combat():
                return  # Can't escape during combat
            return "quit"
        elif self.game_state in [GameState.SPELL_MENU, GameState.SPELL_TARGETING]:
            self.game_state = GameState.PLAYING
        elif self.game_state == GameState.INVENTORY:
            self.game_state = GameState.PLAYING
        elif self.game_state == GameState.EQUIPMENT:
            if self.equipment_selection_mode:
                self.equipment_selection_mode = False  # Exit selection mode
            else:
                self.game_state = GameState.PLAYING  # Exit equipment screen
        else:
            return "quit"