# ecs_game_manager.py - Fixed for Phase 4 Rendering

import pygame
import json
from typing import Optional, Dict, Any

from ecs_core import World, EntityID
from ecs_components import *
from ecs_input_handler import *
from ecs_systems import *
from ecs_entities import EntityBuilder, create_test_world
from ecs_render_coordinator import ECSRenderCoordinator
from game_constants import GameState, TileType
from ecs_entities import EntityBuilder, MonsterTemplates, create_test_world

class ECSGameManager:
    """ECS-based game manager that coordinates all game systems - Phase 4 Fixed"""
    
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
        
        # Rendering system (Phase 4)
        self.render_coordinator = ECSRenderCoordinator(screen)
        
        # Initialize core systems
        self._setup_core_systems()
        
        # Game world state (we'll integrate with dungeon later)
        self.dungeon_data: Optional[Dict] = None
        
        print("🔧 ECS Game Manager initialized - Phase 4")
        print(f"   World created with {len(self.world.systems)} systems")
        print(f"   Render coordinator ready")

    def _setup_core_systems(self):
        """Initialize core ECS systems"""
        # Create and add systems
        self.movement_system = MovementSystem()
        self.health_system = HealthSystem()
        self.status_effect_system = StatusEffectSystem()
        self.interaction_system = InteractionSystem()
        
        # Add to world
        self.world.add_system(self.movement_system)
        self.world.add_system(self.health_system)
        self.world.add_system(self.status_effect_system)
        self.world.add_system(self.interaction_system)
        
        print(f"   ✓ {len(self.world.systems)} core systems initialized")

    def _setup_player_systems(self):
        """Setup player-specific systems"""
        self.input_system = PlayerInputSystem()
        self.experience_system = ExperienceSystem()
        
        self.world.add_system(self.input_system)
        self.world.add_system(self.experience_system)

    def _create_player_from_character_creation(self):
        """Create player from character creation"""
        # For Phase 4, create a test player with better stats
        self.player_entity = EntityBuilder.create_player_from_character_data(
            self.world, {
                'name': 'ECS Hero',
                'title': 'Rendering Tester',
                'character_class': 'Fighter',
                'race': 'Human',
                'alignment': 'Neutral',
                'x': 10,
                'y': 10,
                'hp': 15,
                'max_hp': 15,
                'ac': 14,
                'strength': 16,
                'dexterity': 14,
                'constitution': 15,
                'intelligence': 12,
                'wisdom': 13,
                'charisma': 10,
                'level': 2,
                'xp': 50,
                'gold': 150.0,
                'max_gear_slots': 18
            }
        )
        
        # Setup input handler
        self.input_handler = ECSInputHandler(self.world)
        self.input_handler.set_player_entity(self.player_entity)
        
        # Center camera on player
        self.render_coordinator.center_camera_on_entity(self.world, self.player_entity)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle events with ECS input system"""
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            # Debug toggle
            if event.key == pygame.K_F1:
                self.render_coordinator.toggle_debug_info()
                return True
            
            # Main menu escape to quit
            if self.game_state == GameState.MAIN_MENU and event.key == pygame.K_ESCAPE:
                return False
        
        if self.game_state == GameState.MAIN_MENU:
            return self._handle_main_menu_event(event)
        elif self.game_state == GameState.PLAYING:
            if hasattr(self, 'input_handler'):
                # Let input handler process the event
                self.input_handler.handle_event(event)
                return True
        
        return True
    
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
        """Start a new game"""
        print("🎮 Starting new game with ECS Phase 4...")
        
        # Create test game world
        self._create_test_game_world()
        
        # Change to playing state
        self.game_state = GameState.PLAYING
        
        print(f"   ✓ Game world created with {self.world.get_entity_count()} entities")
        print(f"   ✓ Game state: {self.game_state.name}")
    
    def _create_test_game_world(self):
        """Create a test game world for Phase 4"""
        # Setup player systems first
        self._setup_player_systems()
        
        # Create player
        self._create_player_from_character_creation()
        
        # Create a variety of test entities to show off rendering
        
        # Create some monsters at different positions
        goblin1 = EntityBuilder.create_goblin(self.world, 12, 10, room_id=1)
        goblin2 = EntityBuilder.create_goblin(self.world, 8, 12, room_id=1)
        rat = MonsterTemplates.create_rat(self.world, 15, 8, room_id=1)
        skeleton = MonsterTemplates.create_skeleton(self.world, 6, 8, room_id=1)
        
        # Create interactive objects
        chest = EntityBuilder.create_chest(self.world, 8, 8, locked=False)
        door = EntityBuilder.create_door(self.world, 15, 10, door_type=1, is_horizontal=False)
        torch = EntityBuilder.create_torch(self.world, 10, 8, lit=True)
        altar = EntityBuilder.create_altar(self.world, 13, 13)
        
        # Create puzzle elements
        boulder = EntityBuilder.create_boulder(self.world, 5, 10)
        pressure_plate = EntityBuilder.create_pressure_plate(self.world, 7, 12, "test_puzzle")
        
        # Create stairs
        stairs_down = EntityBuilder.create_stairs(self.world, 18, 15, "down")
        stairs_up = EntityBuilder.create_stairs(self.world, 5, 5, "up")
        
        # Add some status effects for testing
        self.world.add_component(goblin1, OnFireComponent(duration_remaining=10, fire_damage=1))
        self.world.add_component(rat, PoisonedComponent("poisoned", duration_remaining=5, damage_per_turn=1))
        self.world.add_component(skeleton, BlessedComponent("blessed", duration_remaining=20, bonus_amount=2))
        
        # Damage one of the goblins to test health bars
        goblin1_health = self.world.get_component(goblin1, HealthComponent)
        if goblin1_health:
            goblin1_health.damage(3)
        
        # Set camera to follow player
        self.render_coordinator.center_camera_on_entity(self.world, self.player_entity)
    
    def _handle_main_menu_event(self, event: pygame.event.Event) -> bool:
        """Handle main menu events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self.start_new_game()
                return True
            elif event.key == pygame.K_ESCAPE:
                return False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Simple click-to-start for now
            self.start_new_game()
            return True
        
        return True
    
    def update(self, dt_seconds: float):
        """Update all systems"""
        if self.game_state == GameState.PLAYING:
            # Update ECS world (this calls update on all systems)
            self.world.update(dt_seconds)
            
            # Update camera to follow player
            if self.player_entity:
                self.render_coordinator.center_camera_on_entity(self.world, self.player_entity)
            
            # Track rendering performance
            self.render_coordinator.frame_count += 1
    
    def render(self):
        """Render the current game state"""
        if self.game_state == GameState.MAIN_MENU:
            self.render_coordinator.render_main_menu(self.world)
        elif self.game_state == GameState.PLAYING:
            self.render_coordinator.render_world(self.world)
    
    def handle_screen_resize(self, new_screen: pygame.Surface):
        """Handle screen resize events"""
        self.screen = new_screen
        self.screen_width, self.screen_height = new_screen.get_size()
        self.render_coordinator.update_screen(new_screen)
        print(f"   ✓ Screen resized to {self.screen_width}x{self.screen_height}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the ECS state"""
        debug_info = {
            'game_state': self.game_state.name,
            'world_info': self.world.debug_info(),
            'player_entity': str(self.player_entity) if self.player_entity else "None",
            'screen_size': (self.screen_width, self.screen_height),
            'camera_position': (self.render_coordinator.camera_x, self.render_coordinator.camera_y),
            'viewport_size': (self.render_coordinator.viewport_width_cells, self.render_coordinator.viewport_height_cells),
            'renderable_entities': len(self.render_coordinator.renderable_entities)
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
        print(f"   Total frames rendered: {self.render_coordinator.frame_count}")