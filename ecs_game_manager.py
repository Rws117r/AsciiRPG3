# ecs_game_manager.py - Updated for Phase 5 (Dungeon and Environment)

import pygame
import json
from typing import Optional, Dict, Any, Set, Tuple

from ecs_core import World, EntityID
from ecs_components import *
from ecs_input_handler import *
from ecs_systems import *
from ecs_entities import EntityBuilder, create_test_world
from ecs_render_coordinator import ECSRenderCoordinator
from ecs_dungeon_loader import ECSDungeonLoader
from game_constants import GameState, TileType

class ECSGameManager:
    """ECS-based game manager - Phase 5 with Dungeon and Environment"""
    
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
        
        # Dungeon system (Phase 5)
        self.dungeon_loader = ECSDungeonLoader(self.world)
        self.dungeon_data: Optional[Dict] = None
        self.dungeon_entities: Dict[str, Any] = {}
        self.walkable_positions: Set[Tuple[int, int]] = set()
        
        # Initialize core systems
        self._setup_core_systems()
        
        print("🔧 ECS Game Manager initialized - Phase 5")
        print(f"   World created with {len(self.world.systems)} systems")
        print(f"   Dungeon loader ready")

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

    def load_dungeon_data(self, filename: str = "dungeon.json"):
        """Load dungeon data from file"""
        try:
            with open(filename, 'r') as f:
                self.dungeon_data = json.load(f)
            print(f"   ✓ Dungeon data loaded from {filename}")
        except FileNotFoundError:
            print(f"   ⚠ Warning: {filename} not found, will create test world")
            self.dungeon_data = None

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
    
    def start_new_game(self):
        """Start a new game"""
        print("🎮 Starting new game with ECS Phase 5...")
        
        # Setup player systems first
        self._setup_player_systems()
        
        # Create player
        self._create_player_from_character_creation()
        
        # Load dungeon world
        if self.dungeon_data:
            self._load_dungeon_world()
        else:
            self._create_test_game_world()
        
        # Change to playing state
        self.game_state = GameState.PLAYING
        
        total_entities = self.world.get_entity_count()
        print(f"   ✓ Game world created with {total_entities} entities")
        print(f"   ✓ {len(self.walkable_positions)} walkable positions")
        print(f"   ✓ Game state: {self.game_state.name}")
    
    def _load_dungeon_world(self):
        """Load the real dungeon world from JSON data"""
        print("🏰 Loading dungeon world...")
        
        # Create player first
        if not self.player_entity:
            self._create_player_from_character_creation()
        
        # Load dungeon into ECS
        self.dungeon_entities = self.dungeon_loader.load_dungeon_data(self.dungeon_data)
        self.walkable_positions = self.dungeon_entities.get('walkable_positions', set())
        
        # Position player at starting position
        starting_pos = self.dungeon_entities.get('starting_position', (0, 0))
        player_pos = self.world.get_component(self.player_entity, PositionComponent)
        if player_pos:
            player_pos.x = starting_pos[0]
            player_pos.y = starting_pos[1]
        
        # Add some monsters (Phase 6 will handle this better)
        self._add_test_monsters()
        
        # Set camera to follow player
        self.render_coordinator.center_camera_on_entity(self.world, self.player_entity)
        
        print(f"   ✓ Dungeon loaded with {len(self.dungeon_entities.get('doors', []))} doors")
        print(f"   ✓ {len(self.dungeon_entities.get('environmental', []))} environmental objects")
        print(f"   ✓ {len(self.dungeon_entities.get('items', []))} items scattered")
    
    def _add_test_monsters(self):
        """Add some test monsters for Phase 5 (Phase 6 will improve this)"""
        from ecs_entities import MonsterTemplates
        
        # Add a few monsters in different rooms
        monster_positions = [(5, 5), (-8, 3), (12, -8), (-15, 15)]
        
        for i, (x, y) in enumerate(monster_positions):
            if (x, y) in self.walkable_positions:
                if i % 3 == 0:
                    monster = EntityBuilder.create_goblin(self.world, x, y, room_id=i)
                elif i % 3 == 1:
                    monster = MonsterTemplates.create_rat(self.world, x, y, room_id=i)
                else:
                    monster = MonsterTemplates.create_skeleton(self.world, x, y, room_id=i)
                
                print(f"   ✓ Added monster at ({x}, {y})")
    
    def _create_player_from_character_creation(self):
        """Create player from character creation"""
        # For Phase 5, create a test player with better stats
        self.player_entity = EntityBuilder.create_player_from_character_data(
            self.world, {
                'name': 'ECS Explorer',
                'title': 'Dungeon Mapper',
                'character_class': 'Fighter',
                'race': 'Human',
                'alignment': 'Neutral',
                'x': 0,
                'y': 0,
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
    
    def _create_test_game_world(self):
        """Create a test game world for Phase 5 if no dungeon data available"""
        print("🧪 Creating test game world...")
        
        # Create player first
        if not self.player_entity:
            self._create_player_from_character_creation()
        
        # Create a simple test dungeon layout
        test_dungeon_data = {
            'rects': [
                {'x': -3, 'y': -3, 'w': 6, 'h': 6},  # Starting room
                {'x': 5, 'y': -3, 'w': 4, 'h': 6},   # East room
                {'x': -3, 'y': 5, 'w': 6, 'h': 4},   # South room
                {'x': 5, 'y': 5, 'w': 4, 'h': 4, 'ending': True}  # End room
            ],
            'doors': [
                {'x': 3, 'y': 0, 'type': 1, 'dir': {'x': 1, 'y': 0}},  # East door
                {'x': 0, 'y': 3, 'type': 1, 'dir': {'x': 0, 'y': 1}},  # South door
                {'x': 7, 'y': 3, 'type': 1, 'dir': {'x': 0, 'y': 1}},  # End room door
                {'x': 7, 'y': 7, 'type': 7, 'dir': {'x': 0, 'y': 1}}   # Exit stairs
            ],
            'notes': [
                {'pos': {'x': 1, 'y': 1}, 'text': 'Welcome to the ECS test dungeon!'},
                {'pos': {'x': 6, 'y': 6}, 'text': 'You found the treasure room!'}
            ],
            'columns': [
                {'x': -1, 'y': -1},
                {'x': 6, 'y': 0}
            ],
            'water': []
        }
        
        # Load test dungeon
        self.dungeon_entities = self.dungeon_loader.load_dungeon_from_json(test_dungeon_data)
        self.walkable_positions = self.dungeon_entities.get('walkable_positions', set())
        
        # Add some test monsters
        self._add_test_monsters()
        
        # Set camera to follow player
        self.render_coordinator.center_camera_on_entity(self.world, self.player_entity)
        
        print(f"   ✓ Test world created with {self.world.get_entity_count()} entities")
    
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
            
            # Update walkable positions if needed
            self._update_walkable_positions()
            
            # Track rendering performance
            self.render_coordinator.frame_count += 1
    
    def _update_walkable_positions(self):
        """Update walkable positions based on current game state"""
        # This could be optimized to only update when needed
        # For now, we'll recalculate periodically
        
        # Get all walkable positions from revealed rooms
        new_walkable = set()
        
        # Add revealed room floor positions
        for room_id in self.dungeon_loader.revealed_rooms:
            if room_id in self.dungeon_loader.rooms:
                room = self.dungeon_loader.rooms[room_id]
                for x in range(room['x'], room['x'] + room['width']):
                    for y in range(room['y'], room['y'] + room['height']):
                        new_walkable.add((x, y))
        
        # Add positions of walkable entities (items, open doors, etc.)
        walkable_entities = self.world.get_entities_with_components(PositionComponent)
        for entity in walkable_entities:
            pos_comp = self.world.get_component(entity, PositionComponent)
            
            # Check if this entity blocks movement
            blocks_comp = self.world.get_component(entity, BlocksMovementComponent)
            if not blocks_comp or not blocks_comp.blocks_player:
                # Check if it's in a revealed area
                if pos_comp and self.dungeon_loader.is_position_revealed(pos_comp.x, pos_comp.y):
                    new_walkable.add((pos_comp.x, pos_comp.y))
        
        self.walkable_positions = new_walkable
    
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
            'walkable_positions': len(self.walkable_positions),
            'revealed_rooms': len(self.dungeon_loader.revealed_rooms),
            'dungeon_entities': {k: len(v) if isinstance(v, list) else 1 for k, v in self.dungeon_entities.items()},
            'renderable_entities': len(self.render_coordinator.renderable_entities)
        }
        
        if self.player_entity:
            player_pos = self.world.get_component(self.player_entity, PositionComponent)
            if player_pos:
                debug_info['player_position'] = (player_pos.x, player_pos.y)
                debug_info['player_room'] = player_pos.room_id
        
        return debug_info
    
    def get_entities_at_position(self, x: int, y: int) -> List[EntityID]:
        """Get all entities at a specific position"""
        return self.dungeon_loader.get_entities_at_position(x, y)
    
    def is_position_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable"""
        return (x, y) in self.walkable_positions
    
    def is_position_revealed(self, x: int, y: int) -> bool:
        """Check if a position is revealed"""
        return self.dungeon_loader.is_position_revealed(x, y)
    
    def reveal_room_at_position(self, x: int, y: int):
        """Reveal the room containing the given position"""
        for room_id, room in self.dungeon_loader.rooms.items():
            if (room['x'] <= x < room['x'] + room['width'] and 
                room['y'] <= y < room['y'] + room['height']):
                self.dungeon_loader.reveal_room(room_id)
                break
    
    def interact_with_entity(self, entity: EntityID) -> bool:
        """Interact with an entity"""
        # Check if entity is interactable
        interactable = self.world.get_component(entity, InteractableComponent)
        if not interactable:
            return False
        
        # Create interaction event
        if self.player_entity:
            interaction_event = InteractionEvent(
                self.player_entity,
                entity,
                interactable.interaction_type
            )
            self.world.add_event(interaction_event)
            return True
        
        return False
    
    def pickup_item(self, item_entity: EntityID) -> bool:
        """Attempt to pick up an item"""
        # Check if it's actually an item
        item_comp = self.world.get_component(item_entity, ItemComponent)
        if not item_comp:
            return False
        
        # Check if player has inventory space
        if self.player_entity:
            inventory = self.world.get_component(self.player_entity, InventoryComponent)
            if inventory and inventory.can_fit(1):
                # Remove position component (item is now in inventory)
                self.world.remove_component(item_entity, PositionComponent)
                
                # Add to inventory
                inventory.items.append(item_entity)
                
                # Get item name for feedback
                name_comp = self.world.get_component(item_entity, NameComponent)
                item_name = name_comp.name if name_comp else "Item"
                
                print(f"Picked up {item_name}")
                return True
        
        return False
    
    def shutdown(self):
        """Clean shutdown of the game manager"""
        print("🔧 ECS Game Manager shutting down...")
        print(f"   Final entity count: {self.world.get_entity_count()}")
        print(f"   Revealed rooms: {len(self.dungeon_loader.revealed_rooms)}")
        print(f"   Total frames rendered: {self.render_coordinator.frame_count}")
        
        # Clean up any resources
        self.world.entities.clear()
        self.world.components.clear()
        self.world.systems.clear()
        
        print("   ✓ ECS cleanup complete")