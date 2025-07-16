# ecs_dungeon_loader.py - Convert dungeon data to ECS entities (Phase 5)

import json
from typing import Dict, List, Tuple, Set, Optional
from ecs_core import World, EntityID
from ecs_components import *
from ecs_entities import EntityBuilder
from game_constants import TileType

class ECSDungeonLoader:
    """Loads dungeon data and converts it to ECS entities"""
    
    def __init__(self, world: World):
        self.world = world
        self.rooms: Dict[int, Dict] = {}
        self.walkable_entities: Set[EntityID] = set()
        self.revealed_rooms: Set[int] = set()
        
    def load_dungeon_from_json(self, dungeon_data: Dict) -> Dict[str, any]:
        """Load dungeon from JSON data and create ECS entities"""
        print("🏰 Loading dungeon into ECS world...")
        
        # Parse rooms first
        self._parse_rooms(dungeon_data.get('rects', []))
        
        # Create door entities
        door_entities = self._create_door_entities(dungeon_data.get('doors', []))
        
        # Create note entities
        note_entities = self._create_note_entities(dungeon_data.get('notes', []))
        
        # Create column entities
        column_entities = self._create_column_entities(dungeon_data.get('columns', []))
        
        # Create water entities
        water_entities = self._create_water_entities(dungeon_data.get('water', []))
        
        # Create floor tiles as entities (for areas that need special properties)
        floor_entities = self._create_floor_entities()
        
        # Create some environmental objects
        environmental_entities = self._create_environmental_objects()
        
        # Generate items and treasures
        item_entities = self._generate_items()
        
        # Set starting room as revealed
        starting_room = self._find_starting_room()
        if starting_room is not None:
            self.reveal_room(starting_room)
        
        total_entities = (len(door_entities) + len(note_entities) + len(column_entities) + 
                         len(water_entities) + len(floor_entities) + len(environmental_entities) +
                         len(item_entities))
        
        print(f"   ✓ Created {total_entities} dungeon entities")
        print(f"   ✓ {len(self.rooms)} rooms loaded")
        print(f"   ✓ Starting room: {starting_room}")
        
        return {
            'rooms': self.rooms,
            'doors': door_entities,
            'notes': note_entities,
            'columns': column_entities,
            'water': water_entities,
            'floors': floor_entities,
            'environmental': environmental_entities,
            'items': item_entities,
            'walkable_positions': self._calculate_walkable_positions(),
            'starting_position': (0, 0)  # Default starting position
        }
    
    def _parse_rooms(self, rects_data: List[Dict]):
        """Parse room data from JSON"""
        for i, rect in enumerate(rects_data):
            self.rooms[i] = {
                'id': i,
                'x': rect['x'],
                'y': rect['y'], 
                'width': rect['w'],
                'height': rect['h'],
                'is_ending': rect.get('ending', False)
            }
    
    def _create_door_entities(self, doors_data: List[Dict]) -> List[EntityID]:
        """Create door entities from JSON data"""
        door_entities = []
        
        for door_data in doors_data:
            x, y = door_data['x'], door_data['y']
            door_type = door_data.get('type', 1)
            
            # Determine door orientation
            dir_x = door_data.get('dir', {}).get('x', 0)
            dir_y = door_data.get('dir', {}).get('y', 0)
            is_horizontal = abs(dir_y) > abs(dir_x)
            
            # Determine initial state based on type
            is_open = door_type in [0, 2]  # Passages and open doors
            is_locked = door_type == 5
            is_secret = door_type == 6
            
            # Create door entity
            door = EntityBuilder.create_door(self.world, x, y, door_type, is_horizontal)
            
            # Get door component and set properties
            door_comp = self.world.get_component(door, DoorComponent)
            if door_comp:
                door_comp.is_open = is_open
                door_comp.locked = is_locked
            
            # Special handling for stairs
            if door_type in [3, 7, 9]:
                stairs = EntityBuilder.create_stairs(self.world, x, y, "down" if door_type == 7 else "up")
                door_entities.append(stairs)
            else:
                door_entities.append(door)
                
                # Update walkable positions
                if is_open:
                    self.walkable_entities.add(door)
        
        return door_entities
    
    def _create_note_entities(self, notes_data: List[Dict]) -> List[EntityID]:
        """Create note entities"""
        note_entities = []
        
        for note_data in notes_data:
            pos = note_data.get('pos', {})
            x, y = pos.get('x', 0), pos.get('y', 0)
            text = note_data.get('text', 'A mysterious note')
            
            # Create note entity
            note = self.world.create_entity()
            
            # Add components
            self.world.add_component(note, PositionComponent(x, y))
            self.world.add_component(note, RenderableComponent('?', (255, 255, 0), 2))
            self.world.add_component(note, NameComponent("Note", description=text))
            
            # Make it interactable
            self.world.add_component(note, InteractableComponent("note", requires_adjacent=True))
            self.world.add_component(note, ExaminableComponent(
                "A piece of parchment with writing",
                text
            ))
            
            # Environment
            self.world.add_component(note, EnvironmentComponent("note", destructible=True))
            
            note_entities.append(note)
            self.walkable_entities.add(note)  # Can walk on notes
        
        return note_entities
    
    def _create_column_entities(self, columns_data: List[Dict]) -> List[EntityID]:
        """Create column entities"""
        column_entities = []
        
        for column_data in columns_data:
            x, y = column_data['x'], column_data['y']
            
            # Create column entity
            column = self.world.create_entity()
            
            # Add components
            self.world.add_component(column, PositionComponent(x, y))
            self.world.add_component(column, RenderableComponent('♦', (100, 100, 100), 3))
            self.world.add_component(column, NameComponent("Stone Column"))
            
            # Blocks movement and light
            self.world.add_component(column, BlocksMovementComponent())
            self.world.add_component(column, BlocksLightComponent(opacity=1.0))
            
            # Environment
            self.world.add_component(column, EnvironmentComponent("column", destructible=False))
            
            # Examination
            self.world.add_component(column, ExaminableComponent(
                "A sturdy stone column",
                "This ancient column is carved from solid stone, supporting the ceiling above. Intricate patterns are etched into its surface, worn smooth by age."
            ))
            
            column_entities.append(column)
        
        return column_entities
    
    def _create_water_entities(self, water_data: List[Dict]) -> List[EntityID]:
        """Create water tile entities"""
        water_entities = []
        
        for water_tile in water_data:
            x, y = water_tile['x'], water_tile['y']
            
            # Create water entity
            water = self.world.create_entity()
            
            # Add components
            self.world.add_component(water, PositionComponent(x, y))
            self.world.add_component(water, RenderableComponent('~', (100, 150, 200), 1))
            self.world.add_component(water, NameComponent("Water"))
            
            # Blocks normal movement but not all entities
            self.world.add_component(water, BlocksMovementComponent(blocks_player=True, blocks_monsters=True, blocks_items=False))
            
            # Environment
            self.world.add_component(water, EnvironmentComponent("water", destructible=False))
            
            # Can extinguish fire
            self.world.add_component(water, WetComponent(duration_remaining=-1))
            
            # Examination
            self.world.add_component(water, ExaminableComponent(
                "Clear, still water",
                "The water is surprisingly clear and still. You can see the bottom, which appears to be made of smooth stone. The water is cool to the touch."
            ))
            
            water_entities.append(water)
        
        return water_entities
    
    def _create_floor_entities(self) -> List[EntityID]:
        """Create special floor entities (most floors don't need entities)"""
        floor_entities = []
        
        # Only create floor entities for special cases where we need component data
        # Most floors will be handled by the rendering system without entities
        
        # For now, we'll create entities for room centers (could be used for room effects)
        for room_id, room in self.rooms.items():
            center_x = room['x'] + room['width'] // 2
            center_y = room['y'] + room['height'] // 2
            
            # Create a "room essence" entity (invisible but detectable)
            room_essence = self.world.create_entity()
            
            self.world.add_component(room_essence, PositionComponent(center_x, center_y, room_id))
            self.world.add_component(room_essence, NameComponent(f"Room {room_id}", description=f"The heart of room {room_id}"))
            
            # Not renderable - this is just for game logic
            self.world.add_component(room_essence, EnvironmentComponent("room_essence", destructible=False))
            
            # Special properties for ending rooms
            if room.get('is_ending', False):
                self.world.add_component(room_essence, MagicalComponent("victory", 1, enchanted=True))
                self.world.add_component(room_essence, ExaminableComponent(
                    "You sense something special about this place",
                    "This room thrums with ancient magic. You feel you are close to completing your quest."
                ))
            
            floor_entities.append(room_essence)
        
        return floor_entities
    
    def _create_environmental_objects(self) -> List[EntityID]:
        """Create additional environmental objects for atmosphere"""
        environmental_entities = []
        
        # Add some atmosphere to rooms
        for room_id, room in self.rooms.items():
            room_x, room_y = room['x'], room['y']
            room_w, room_h = room['width'], room['height']
            
            # Skip very small rooms
            if room_w < 3 or room_h < 3:
                continue
            
            # 30% chance to add some environmental objects
            import random
            if random.random() < 0.3:
                # Pick a random position in the room (not on edges)
                obj_x = random.randint(room_x + 1, room_x + room_w - 2)
                obj_y = random.randint(room_y + 1, room_y + room_h - 2)
                
                # Choose object type
                obj_type = random.choice(['torch', 'chest', 'altar'])
                
                if obj_type == 'torch':
                    torch = EntityBuilder.create_torch(self.world, obj_x, obj_y, lit=True)
                    environmental_entities.append(torch)
                elif obj_type == 'chest':
                    chest = EntityBuilder.create_chest(self.world, obj_x, obj_y, locked=random.choice([True, False]))
                    environmental_entities.append(chest)
                elif obj_type == 'altar':
                    altar = EntityBuilder.create_altar(self.world, obj_x, obj_y)
                    environmental_entities.append(altar)
        
        return environmental_entities
    
    def _generate_items(self) -> List[EntityID]:
        """Generate random items throughout the dungeon"""
        item_entities = []
        
        # Add some random items to rooms
        for room_id, room in self.rooms.items():
            room_x, room_y = room['x'], room['y']
            room_w, room_h = room['width'], room['height']
            
            # Skip very small rooms and starting room
            if room_w < 4 or room_h < 4 or room_id == 0:
                continue
            
            # 20% chance to add an item
            import random
            if random.random() < 0.2:
                # Pick a random position in the room
                item_x = random.randint(room_x + 1, room_x + room_w - 2)
                item_y = random.randint(room_y + 1, room_y + room_h - 2)
                
                # Choose item type
                item_type = random.choice(['health_potion', 'coin', 'torch', 'dagger'])
                
                if item_type == 'health_potion':
                    potion = EntityBuilder.create_simple_item(
                        self.world, "Health Potion", "Restores health when used",
                        '!', (255, 0, 0), 0.5, 50
                    )
                    # Add position
                    self.world.add_component(potion, PositionComponent(item_x, item_y, room_id))
                    item_entities.append(potion)
                    self.walkable_entities.add(potion)
                
                elif item_type == 'coin':
                    coins = EntityBuilder.create_simple_item(
                        self.world, "Gold Coins", "Valuable currency",
                        '$', (255, 215, 0), 0.1, 10
                    )
                    # Add position
                    self.world.add_component(coins, PositionComponent(item_x, item_y, room_id))
                    item_entities.append(coins)
                    self.walkable_entities.add(coins)
                
                elif item_type == 'torch':
                    # Create an unlit torch item (different from environment torch)
                    torch_item = EntityBuilder.create_simple_item(
                        self.world, "Torch", "Provides light when lit",
                        '/', (139, 69, 19), 1.0, 5
                    )
                    # Add position
                    self.world.add_component(torch_item, PositionComponent(item_x, item_y, room_id))
                    item_entities.append(torch_item)
                    self.walkable_entities.add(torch_item)
                
                elif item_type == 'dagger':
                    dagger = self.world.create_entity()
                    
                    # Components
                    self.world.add_component(dagger, PositionComponent(item_x, item_y, room_id))
                    self.world.add_component(dagger, RenderableComponent('/', (200, 200, 200), 2))
                    self.world.add_component(dagger, NameComponent("Iron Dagger"))
                    self.world.add_component(dagger, ItemComponent(weight=1.0, value_cp=200))
                    
                    # Weapon properties
                    self.world.add_component(dagger, WeaponComponent(
                        damage_dice="1d4",
                        weapon_type="melee",
                        properties=["finesse", "thrown"]
                    ))
                    
                    # Examination
                    self.world.add_component(dagger, ExaminableComponent(
                        "A sharp iron dagger",
                        "This well-crafted dagger has a keen edge and comfortable grip. It would serve well in combat or utility tasks."
                    ))
                    
                    item_entities.append(dagger)
                    self.walkable_entities.add(dagger)
        
        return item_entities
    
    def _calculate_walkable_positions(self) -> Set[Tuple[int, int]]:
        """Calculate all walkable positions in the dungeon"""
        walkable_positions = set()
        
        # Add all floor positions in revealed rooms
        for room_id in self.revealed_rooms:
            if room_id in self.rooms:
                room = self.rooms[room_id]
                for x in range(room['x'], room['x'] + room['width']):
                    for y in range(room['y'], room['y'] + room['height']):
                        walkable_positions.add((x, y))
        
        # Add positions of walkable entities
        for entity in self.walkable_entities:
            pos_comp = self.world.get_component(entity, PositionComponent)
            if pos_comp:
                walkable_positions.add((pos_comp.x, pos_comp.y))
        
        return walkable_positions
    
    def _find_starting_room(self) -> Optional[int]:
        """Find the room containing position (0, 0) or return first room"""
        for room_id, room in self.rooms.items():
            if (room['x'] <= 0 < room['x'] + room['width'] and 
                room['y'] <= 0 < room['y'] + room['height']):
                return room_id
        
        # Fallback to first room
        return list(self.rooms.keys())[0] if self.rooms else None
    
    def reveal_room(self, room_id: int):
        """Reveal a room and update walkable positions"""
        if room_id not in self.revealed_rooms:
            self.revealed_rooms.add(room_id)
            print(f"   ✓ Revealed room {room_id}")
            
            # Update walkable positions
            # This would be called during gameplay when rooms are revealed
    
    def is_position_revealed(self, x: int, y: int) -> bool:
        """Check if a position is in a revealed room"""
        for room_id in self.revealed_rooms:
            if room_id in self.rooms:
                room = self.rooms[room_id]
                if (room['x'] <= x < room['x'] + room['width'] and 
                    room['y'] <= y < room['y'] + room['height']):
                    return True
        
        # Also check for revealed doors/entities
        entities_at_pos = self.world.get_entities_with_components(PositionComponent)
        for entity in entities_at_pos:
            pos_comp = self.world.get_component(entity, PositionComponent)
            if pos_comp and pos_comp.x == x and pos_comp.y == y:
                # Check if this is a door connecting to revealed rooms
                door_comp = self.world.get_component(entity, DoorComponent)
                if door_comp:
                    # For now, assume doors are revealed if any connected room is revealed
                    # This is a simplification - in full implementation you'd track door-room connections
                    return True
        
        return False
    
    def get_entities_at_position(self, x: int, y: int) -> List[EntityID]:
        """Get all entities at a specific position"""
        entities_at_pos = []
        
        entities = self.world.get_entities_with_components(PositionComponent)
        for entity in entities:
            pos_comp = self.world.get_component(entity, PositionComponent)
            if pos_comp and pos_comp.x == x and pos_comp.y == y:
                entities_at_pos.append(entity)
        
        return entities_at_pos
    
    def get_renderable_entities_in_view(self, viewport_x: int, viewport_y: int, 
                                       viewport_width: int, viewport_height: int) -> List[EntityID]:
        """Get all renderable entities within the viewport that are in revealed areas"""
        visible_entities = []
        
        entities = self.world.get_entities_with_components(PositionComponent, RenderableComponent)
        for entity in entities:
            pos_comp = self.world.get_component(entity, PositionComponent)
            render_comp = self.world.get_component(entity, RenderableComponent)
            
            if (pos_comp and render_comp and render_comp.visible and
                viewport_x <= pos_comp.x < viewport_x + viewport_width and
                viewport_y <= pos_comp.y < viewport_y + viewport_height and
                self.is_position_revealed(pos_comp.x, pos_comp.y)):
                visible_entities.append(entity)
        
        # Sort by render layer
        visible_entities.sort(key=lambda e: self.world.get_component(e, RenderableComponent).render_layer)
        
        return visible_entities