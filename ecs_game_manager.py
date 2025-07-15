# ecs_game_manager.py - ECS-based game manager for Phase 2

import pygame
import json
from typing import Optional, Dict, Any

from ecs_core import World, EntityID
from ecs_components import *
from ecs_systems import *
from ecs_entities import EntityBuilder, create_test_world
from game_constants import GameState, TileType

class ECSGameManager:
    """ECS-based game manager that coordinates all game systems"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        
        # ECS World
        self.world = World()
        
        # Game state
        self.game_state = GameState.MAIN_MENU
        self.running = True
        
        # Player reference
        self.player_entity: Optional[EntityID] = None
        
        # Initialize core systems
        self._setup_core_systems()
        
        # Game world state (we'll integrate with dungeon later)
        self.dungeon_data: Optional[Dict] = None
        
        print("🔧 ECS Game Manager initialized")
        print(f"   World created with {len(self.world.systems)} systems")
    # Add these methods to ECSGameManager class

    def _setup_player_systems(self):
        """Setup player-specific systems"""
        self.input_system = PlayerInputSystem()
        self.experience_system = ExperienceSystem()
        
        self.world.add_system(self.input_system)
        self.world.add_system(self.experience_system)

    def _create_player_from_character_creation(self):
        """Create player from character creation"""
        # For now, create a test player
        # Later this will integrate with character creation
        self.player_entity = EntityBuilder.create_player_from_character_data(
            self.world, {
                'name': 'ECS Hero',
                'title': 'Test Adventurer',
                'character_class': 'Fighter',
                'race': 'Human',
                'alignment': 'Neutral',
                'x': 10,
                'y': 10,
                'hp': 12,
                'max_hp': 12,
                'ac': 11,
                'strength': 15,
                'dexterity': 13,
                'constitution': 14,
                'intelligence': 10,
                'wisdom': 12,
                'charisma': 8,
                'level': 1,
                'xp': 0,
                'gold': 50.0,
                'max_gear_slots': 15
            }
        )
        
        # Setup input handler
        self.input_handler = ECSInputHandler(self.world)
        self.input_handler.set_player_entity(self.player_entity)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events with ECS input system"""
        if event.type == pygame.QUIT:
            return False
        
        if self.game_state == GameState.MAIN_MENU:
            return self._handle_main_menu_event(event)
        elif self.game_state == GameState.PLAYING:
            if hasattr(self, 'input_handler'):
                return self.input_handler.handle_event(event)
        
        return True
    def _setup_core_systems(self):
        """Initialize core ECS systems"""
        # Create and add systems
        self.render_system = RenderSystem()
        self.movement_system = MovementSystem()
        self.health_system = HealthSystem()
        self.status_effect_system = StatusEffectSystem()
        self.interaction_system = InteractionSystem()
        
        # Add to world
        self.world.add_system(self.render_system)
        self.world.add_system(self.movement_system)
        self.world.add_system(self.health_system)
        self.world.add_system(self.status_effect_system)
        self.world.add_system(self.interaction_system)
        
        # Configure render system
        self.render_system.set_viewport_size(20, 15)  # Default viewport
        self.render_system.set_camera(0, 0)
        
        print(f"   ✓ {len(self.world.systems)} core systems initialized")
    
    def load_dungeon_data(self, filename: str = "dungeon.json"):
        """Load dungeon data (for now, just store it)"""
        try:
            with open(filename, 'r') as f:
                self.dungeon_data = json.load(f)
            print(f"   ✓ Dungeon data loaded from {filename}")
        except FileNotFoundError:
            print(f"   ⚠ Warning: {filename} not found, will create test world")
            self.dungeon_data = None
    
    def start_new_game(self):
        """Start a new game (for now, create test world)"""
        print("🎮 Starting new game with ECS...")
        
        # For Phase 2, we'll create a simple test world
        # In later phases, we'll integrate with character creation and dungeon loading
        self._create_test_game_world()
        
        # Change to playing state
        self.game_state = GameState.PLAYING
        
        print(f"   ✓ Game world created with {self.world.get_entity_count()} entities")
        print(f"   ✓ Game state: {self.game_state.name}")
    
    def _create_test_game_world(self):
        """Create a test game world for Phase 3"""
        # Setup player systems first
        self._setup_player_systems()
        
        # Create player
        self._create_player_from_character_creation()
        
        # Create some test entities around the player
        EntityBuilder.create_goblin(self.world, 12, 10, room_id=1)
        EntityBuilder.create_chest(self.world, 8, 8, locked=False)
        EntityBuilder.create_door(self.world, 15, 10, door_type=1, is_horizontal=False)
        EntityBuilder.create_torch(self.world, 10, 8, lit=True)
        EntityBuilder.create_boulder(self.world, 5, 10)
        
        # Set camera to follow player
        player_pos = self.world.get_component(self.player_entity, PositionComponent)
        if player_pos:
            self.render_system.set_camera(
                player_pos.x - 10,
                player_pos.y - 7
            )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events. Returns False if game should quit."""
        if event.type == pygame.QUIT:
            return False
        
        if self.game_state == GameState.MAIN_MENU:
            return self._handle_main_menu_event(event)
        elif self.game_state == GameState.PLAYING:
            return self._handle_playing_event(event)
        
        return True
    
    def _handle_main_menu_event(self, event: pygame.event.Event) -> bool:
        """Handle main menu events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self.start_new_game()
            elif event.key == pygame.K_ESCAPE:
                return False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Simple click-to-start for now
            self.start_new_game()
        
        return True
    
    def _handle_playing_event(self, event: pygame.event.Event) -> bool:
        """Handle gameplay events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_state = GameState.MAIN_MENU
                return True
            
            # Handle player movement
            if self.player_entity:
                player_pos = self.world.get_component(self.player_entity, PositionComponent)
                if player_pos:
                    new_pos = None
                    
                    if event.key in [pygame.K_w, pygame.K_UP]:
                        new_pos = (player_pos.x, player_pos.y - 1)
                    elif event.key in [pygame.K_s, pygame.K_DOWN]:
                        new_pos = (player_pos.x, player_pos.y + 1)
                    elif event.key in [pygame.K_a, pygame.K_LEFT]:
                        new_pos = (player_pos.x - 1, player_pos.y)
                    elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                        new_pos = (player_pos.x + 1, player_pos.y)
                    
                    if new_pos:
                        # Create movement event
                        move_event = MoveEvent(
                            self.player_entity, 
                            (player_pos.x, player_pos.y), 
                            new_pos
                        )
                        self.world.add_event(move_event)
                        
                        # Update camera to follow player
                        self.render_system.set_camera(
                            new_pos[0] - 10,
                            new_pos[1] - 7
                        )
        
        return True
    
    def update(self, dt_seconds: float):
        """Update all systems"""
        if self.game_state == GameState.PLAYING:
            # Update ECS world (this calls update on all systems)
            self.world.update(dt_seconds)
    
    def render(self):
        """Render the current game state"""
        if self.game_state == GameState.MAIN_MENU:
            self._render_main_menu()
        elif self.game_state == GameState.PLAYING:
            self._render_game()
    
    def _render_main_menu(self):
        """Render the main menu"""
        self.screen.fill((20, 20, 40))  # Dark blue background
        
        # Load font
        try:
            font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 36)
            small_font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 24)
        except:
            font = pygame.font.Font(None, 36)
            small_font = pygame.font.Font(None, 24)
        
        # Title
        title_text = font.render("ECS Dungeon Crawler", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, self.screen_height // 3))
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        instructions = [
            "Phase 2: ECS Game Manager",
            "",
            "SPACE or ENTER: Start Game",
            "ESC: Quit"
        ]
        
        y_offset = title_rect.bottom + 50
        for instruction in instructions:
            if instruction:  # Skip empty lines
                inst_text = small_font.render(instruction, True, (200, 200, 200))
                inst_rect = inst_text.get_rect(center=(self.screen_width // 2, y_offset))
                self.screen.blit(inst_text, inst_rect)
            y_offset += 30
    
    def _render_game(self):
        """Render the game world"""
        # Clear screen
        self.screen.fill((40, 40, 60))  # Dark background
        
        # Update render system
        self.render_system.update(self.world, 0.016)
        
        # Get entities to render
        entities_to_render = self.render_system.get_renderable_entities()
        
        # Load font for rendering
        try:
            font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 24)
        except:
            font = pygame.font.Font(None, 24)
        
        # Calculate cell size and viewport offset
        cell_size = 32
        viewport_start_x = 50
        viewport_start_y = 50
        
        # Render all entities
        for entity, pos_comp, render_comp in entities_to_render:
            if render_comp.visible:
                # Calculate screen position
                screen_x = viewport_start_x + (pos_comp.x - self.render_system.camera_x) * cell_size
                screen_y = viewport_start_y + (pos_comp.y - self.render_system.camera_y) * cell_size
                
                # Only render if on screen
                if (0 <= screen_x < self.screen_width and 
                    0 <= screen_y < self.screen_height):
                    
                    # Render entity
                    text_surface = font.render(render_comp.ascii_char, True, render_comp.color)
                    text_rect = text_surface.get_rect(center=(screen_x + cell_size // 2, screen_y + cell_size // 2))
                    self.screen.blit(text_surface, text_rect)
        
        # Render HUD
        self._render_hud()
    
    def _render_hud(self):
        """Render heads-up display"""
        if not self.player_entity:
            return
        
        try:
            font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 20)
        except:
            font = pygame.font.Font(None, 20)
        
        # Get player info
        name_comp = self.world.get_component(self.player_entity, NameComponent)
        health_comp = self.world.get_component(self.player_entity, HealthComponent)
        pos_comp = self.world.get_component(self.player_entity, PositionComponent)
        
        if name_comp and health_comp and pos_comp:
            # Player name and health
            info_lines = [
                f"Player: {name_comp.name}",
                f"HP: {health_comp.current_hp}/{health_comp.max_hp}",
                f"Position: ({pos_comp.x}, {pos_comp.y})",
                f"Entities: {self.world.get_entity_count()}",
                "",
                "WASD/Arrows: Move",
                "ESC: Main Menu"
            ]
            
            y_offset = 10
            for line in info_lines:
                if line:  # Skip empty lines
                    text_surface = font.render(line, True, (255, 255, 255))
                    self.screen.blit(text_surface, (10, y_offset))
                y_offset += 25
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the ECS state"""
        debug_info = {
            'game_state': self.game_state.name,
            'world_info': self.world.debug_info(),
            'player_entity': str(self.player_entity) if self.player_entity else "None",
            'screen_size': (self.screen_width, self.screen_height)
        }
        
        if self.player_entity:
            player_pos = self.world.get_component(self.player_entity, PositionComponent)
            if player_pos:
                debug_info['player_position'] = (player_pos.x, player_pos.y)
        
        return debug_info
    
    def shutdown(self):
        """Clean shutdown of the game manager"""
        print("🔧 ECS Game Manager shutting down...")
        print(f"   Final entity count: {self.world.get_entity_count()}")
        
        # Clear the world
        self.world = None
        self.player_entity = None