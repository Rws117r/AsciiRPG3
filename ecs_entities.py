# ecs_entities.py - Entity builders and templates for creating common game entities (Phase 3 Fixed)

from typing import Dict, List, Optional, Tuple
import random

from ecs_core import World, EntityID
from ecs_components import *

class EntityBuilder:
    """Factory class for creating common game entities"""
    
    @staticmethod
    def create_player_from_character_data(world: World, character_data: dict) -> EntityID:
        """Create a complete player entity from character creation data"""
        player = world.create_entity()
        
        # Extract data from character_data dict
        name = character_data.get('name', 'Hero')
        x = character_data.get('x', 0)
        y = character_data.get('y', 0)
        character_class = character_data.get('character_class', 'Fighter')
        race = character_data.get('race', 'Human')
        alignment = character_data.get('alignment', 'Neutral')
        level = character_data.get('level', 1)
        
        # Stats
        stats = {
            'strength': character_data.get('strength', 10),
            'dexterity': character_data.get('dexterity', 10),
            'constitution': character_data.get('constitution', 10),
            'intelligence': character_data.get('intelligence', 10),
            'wisdom': character_data.get('wisdom', 10),
            'charisma': character_data.get('charisma', 10)
        }
        
        # Core components
        world.add_component(player, PositionComponent(x, y))
        world.add_component(player, RenderableComponent('@', (255, 64, 64), 10))
        world.add_component(player, NameComponent(name, character_data.get('title', 'Adventurer')))
        
        # Health (based on class and constitution)
        base_hp = character_data.get('hp', 10)
        max_hp = character_data.get('max_hp', base_hp)
        world.add_component(player, HealthComponent(base_hp, max_hp))
        
        # Stats
        world.add_component(player, StatsComponent(**stats))
        
        # Player-specific
        world.add_component(player, PlayerControlledComponent())
        world.add_component(player, ClassComponent(character_class, race, alignment))
        world.add_component(player, ExperienceComponent(
            character_data.get('xp', 0), 
            level
        ))
        
        # Movement and interaction
        world.add_component(player, MovementComponent(speed=1))
        world.add_component(player, TurnOrderComponent())
        
        # Inventory and equipment
        max_slots = character_data.get('max_gear_slots', 10)
        gold = character_data.get('gold', 0.0)
        world.add_component(player, InventoryComponent([], max_slots, gold))
        world.add_component(player, EquipmentSlotsComponent())
        
        # Vision and interaction
        world.add_component(player, VisionComponent(vision_range=20))
        
        # Combat stats
        ac = character_data.get('ac', 10)
        world.add_component(player, CombatStatsComponent(armor_class=ac))
        
        # Spellcasting (if applicable)
        if character_class in ['Priest', 'Wizard']:
            starting_spells = character_data.get('starting_spells', [])
            world.add_component(player, SpellcastingComponent(known_spells=starting_spells))
        
        # Examination
        world.add_component(player, ExaminableComponent(
            f"This is {name}, a brave adventurer.",
            f"{name} looks determined and ready for adventure."
        ))
        
        return player

    @staticmethod
    def convert_legacy_player_to_ecs(world: World, legacy_player, x: int, y: int) -> EntityID:
        """Convert old Player object to ECS entity"""
        character_data = {
            'name': legacy_player.name,
            'title': legacy_player.title,
            'x': x,
            'y': y,
            'character_class': legacy_player.character_class,
            'race': legacy_player.race,
            'alignment': legacy_player.alignment,
            'level': legacy_player.level,
            'hp': legacy_player.hp,
            'max_hp': legacy_player.max_hp,
            'ac': legacy_player.ac,
            'xp': legacy_player.xp,
            'strength': legacy_player.strength,
            'dexterity': legacy_player.dexterity,
            'constitution': legacy_player.constitution,
            'intelligence': legacy_player.intelligence,
            'wisdom': legacy_player.wisdom,
            'charisma': legacy_player.charisma,
            'gold': legacy_player.gold,
            'max_gear_slots': legacy_player.max_gear_slots,
            'starting_spells': getattr(legacy_player, 'starting_spells', [])
        }
        
        return EntityBuilder.create_player_from_character_data(world, character_data)
    
    @staticmethod
    def create_goblin(world: World, x: int, y: int, room_id: int = -1) -> EntityID:
        """Create a goblin monster"""
        goblin = world.create_entity()
        
        # Core components
        world.add_component(goblin, PositionComponent(x, y, room_id))
        world.add_component(goblin, RenderableComponent('g', (0, 150, 50), 5))
        world.add_component(goblin, NameComponent("Goblin"))
        world.add_component(goblin, HealthComponent(7, 7))
        world.add_component(goblin, StatsComponent(8, 14, 10, 10, 8, 8))
        
        # Monster components
        world.add_component(goblin, MonsterComponent("goblin", 1))
        world.add_component(goblin, MovementComponent(speed=1))
        world.add_component(goblin, AIComponent("hostile", aggro_range=6))
        world.add_component(goblin, TurnOrderComponent())
        
        # Combat
        world.add_component(goblin, CombatStatsComponent(armor_class=12, attack_bonus=2))
        
        # Create a crude weapon for the goblin
        goblin_weapon = EntityBuilder.create_crude_weapon(world, "Rusty Dagger")
        world.add_component(goblin, EquipmentSlotsComponent())
        equipment = world.get_component(goblin, EquipmentSlotsComponent)
        equipment.equip_item('weapon', goblin_weapon)
        
        # Examination
        world.add_component(goblin, ExaminableComponent(
            "A small, green humanoid with sharp teeth and beady eyes.",
            "This goblin looks mean and hungry. Its beady eyes dart around nervously, and it clutches a crude weapon. Scars and dirt cover its green skin, and it moves with the quick, nervous energy of a creature used to fighting for survival."
        ))
        
        return goblin
    
    @staticmethod
    def create_door(world: World, x: int, y: int, door_type: int = 1, 
                   is_horizontal: bool = True) -> EntityID:
        """Create a door entity"""
        door = world.create_entity()
        
        # Core components
        world.add_component(door, PositionComponent(x, y))
        char = '-' if is_horizontal else '|'
        world.add_component(door, RenderableComponent(char, (139, 69, 19), 3))
        world.add_component(door, NameComponent("Door"))
        
        # Door functionality
        world.add_component(door, DoorComponent(is_open=False, locked=(door_type == 5), door_type=door_type))
        world.add_component(door, InteractableComponent("door", requires_adjacent=True))
        world.add_component(door, BlocksMovementComponent(blocks_player=True, blocks_monsters=True))
        world.add_component(door, BlocksLightComponent(opacity=1.0))
        
        # Environment
        world.add_component(door, EnvironmentComponent("door", destructible=False))
        
        # Examination
        door_state = "closed" if not world.get_component(door, DoorComponent).is_open else "open"
        lock_state = "locked" if world.get_component(door, DoorComponent).locked else "unlocked"
        
        world.add_component(door, ExaminableComponent(
            f"A {door_state} wooden door.",
            f"This sturdy wooden door is currently {door_state} and appears to be {lock_state}. The wood is weathered but solid, with iron hinges and a simple latch mechanism."
        ))
        
        return door
    
    @staticmethod
    def create_chest(world: World, x: int, y: int, locked: bool = False) -> EntityID:
        """Create a treasure chest"""
        chest = world.create_entity()
        
        # Core components
        world.add_component(chest, PositionComponent(x, y))
        world.add_component(chest, RenderableComponent('⊠', (160, 82, 45), 2))
        world.add_component(chest, NameComponent("Treasure Chest"))
        
        # Container functionality
        world.add_component(chest, ContainerComponent([], 10, False, locked))
        world.add_component(chest, InteractableComponent("container", requires_adjacent=True))
        world.add_component(chest, BlocksMovementComponent(blocks_player=False, blocks_monsters=True, blocks_items=True))
        
        # Environment
        world.add_component(chest, EnvironmentComponent("chest", destructible=True))
        
        # Add some random treasure
        EntityBuilder._populate_chest(world, chest)
        
        # Examination
        lock_desc = "It appears to be locked." if locked else "The lock is open."
        world.add_component(chest, ExaminableComponent(
            "An ornate wooden chest bound with iron.",
            f"This chest is crafted from dark hardwood and reinforced with iron bands. The lock mechanism looks intricate but functional. {lock_desc} You notice scratch marks around the lock - others have tried to open it before."
        ))
        
        return chest
    
    @staticmethod
    def create_torch(world: World, x: int, y: int, lit: bool = True) -> EntityID:
        """Create a torch light source"""
        torch = world.create_entity()
        
        # Core components
        world.add_component(torch, PositionComponent(x, y))
        color = (255, 165, 0) if lit else (100, 100, 100)
        world.add_component(torch, RenderableComponent('!', color, 1))
        world.add_component(torch, NameComponent("Torch"))
        
        # Light source
        world.add_component(torch, LightSourceComponent(
            brightness=6, 
            fuel_remaining=3600.0,  # 1 hour
            lit=lit,
            light_color=(255, 200, 100)
        ))
        
        # Interaction
        world.add_component(torch, InteractableComponent("light_source", requires_adjacent=True))
        
        # Fire properties
        world.add_component(torch, FlammableComponent(ignition_chance=1.0, burn_damage=2))
        if lit:
            world.add_component(torch, OnFireComponent(duration_remaining=-1, fire_damage=0))  # Controlled fire
        
        # Environment
        world.add_component(torch, EnvironmentComponent("light_source", destructible=True))
        
        # Examination
        state_desc = "burning steadily" if lit else "extinguished"
        world.add_component(torch, ExaminableComponent(
            f"A torch that is {state_desc}.",
            f"This wooden torch is wrapped with oil-soaked cloth at one end. The torch is currently {state_desc}. " +
            ("The flame flickers but seems stable, casting dancing shadows on nearby walls." if lit else 
             "The blackened cloth shows it was recently lit, and it could probably be relit with a flame source.")
        ))
        
        return torch
    
    @staticmethod
    def create_boulder(world: World, x: int, y: int) -> EntityID:
        """Create a pushable boulder"""
        boulder = world.create_entity()
        
        # Core components
        world.add_component(boulder, PositionComponent(x, y))
        world.add_component(boulder, RenderableComponent('■', (139, 69, 19), 3))
        world.add_component(boulder, NameComponent("Boulder"))
        
        # Movement blocking and pushability
        world.add_component(boulder, BlocksMovementComponent())
        world.add_component(boulder, BlocksLightComponent(opacity=1.0))
        world.add_component(boulder, MovableComponent(push_difficulty=15, can_be_pulled=False, weight=500.0))
        
        # Environment
        world.add_component(boulder, EnvironmentComponent("boulder", destructible=False))
        
        # Puzzle element (if part of a puzzle)
        world.add_component(boulder, PuzzleElementComponent("boulder_puzzle", "boulder", False))
        
        # Examination
        world.add_component(boulder, ExaminableComponent(
            "A large stone boulder blocking the way.",
            "This massive boulder is roughly carved from dark granite. Deep scratches and wear marks on its surface suggest it has been moved before, though it would take considerable strength to budge it. The stone feels cold and solid to the touch."
        ))
        
        return boulder
    
    @staticmethod
    def create_pressure_plate(world: World, x: int, y: int, puzzle_id: str = "boulder_puzzle") -> EntityID:
        """Create a pressure plate puzzle element"""
        plate = world.create_entity()
        
        # Core components
        world.add_component(plate, PositionComponent(x, y))
        world.add_component(plate, RenderableComponent('◉', (100, 100, 150), 1))
        world.add_component(plate, NameComponent("Pressure Plate"))
        
        # Pressure plate functionality
        world.add_component(plate, PressurePlateComponent(required_weight=1))
        world.add_component(plate, PuzzleElementComponent(puzzle_id, "pressure_plate", False))
        
        # Environment
        world.add_component(plate, EnvironmentComponent("pressure_plate", destructible=False))
        
        # Examination
        world.add_component(plate, ExaminableComponent(
            "A circular stone plate set into the floor.",
            "This pressure-sensitive plate is carefully fitted into the floor stones. Ancient mechanisms are visible around its edges, and you can see worn grooves where the plate can depress. It appears designed to trigger when sufficient weight is placed upon it."
        ))
        
        return plate
    
    @staticmethod
    def create_altar(world: World, x: int, y: int) -> EntityID:
        """Create a stone altar"""
        altar = world.create_entity()
        
        # Core components
        world.add_component(altar, PositionComponent(x, y))
        world.add_component(altar, RenderableComponent('Π', (255, 255, 255), 2))
        world.add_component(altar, NameComponent("Stone Altar"))
        
        # Interaction
        world.add_component(altar, InteractableComponent("altar", requires_adjacent=True))
        world.add_component(altar, BlocksMovementComponent(blocks_player=False, blocks_monsters=True))
        
        # Magic properties
        world.add_component(altar, MagicalComponent("holy", 2, enchanted=True))
        
        # Light source (holy light)
        world.add_component(altar, LightSourceComponent(
            brightness=4,
            fuel_remaining=-1,  # Infinite
            lit=True,
            light_color=(255, 255, 200)
        ))
        
        # Environment
        world.add_component(altar, EnvironmentComponent("altar", destructible=False))
        
        # Examination
        world.add_component(altar, ExaminableComponent(
            "An ancient stone altar carved with mystical runes.",
            "The altar is made of weathered granite, its surface worn smooth by countless rituals. Intricate runes spiral around its base, glowing faintly with residual magic. A sense of peace and sanctity emanates from the stone, and you feel it could be used for prayers or magical rituals."
        ))
        
        return altar
    
    @staticmethod
    def create_simple_item(world: World, name: str, description: str, 
                          ascii_char: str = 'o', color: Tuple[int, int, int] = (200, 200, 200),
                          weight: float = 1.0, value: int = 1) -> EntityID:
        """Create a basic item entity"""
        item = world.create_entity()
        
        # Core components
        world.add_component(item, NameComponent(name, description=description))
        world.add_component(item, RenderableComponent(ascii_char, color, 1))
        world.add_component(item, ItemComponent(weight, value, stackable=True, max_stack=10))
        
        # Examination
        world.add_component(item, ExaminableComponent(
            description,
            f"A {name.lower()}. {description}"
        ))
        
        return item
    
    @staticmethod
    def create_crude_weapon(world: World, name: str) -> EntityID:
        """Create a basic weapon for monsters"""
        weapon = world.create_entity()
        
        # Core components  
        world.add_component(weapon, NameComponent(name))
        world.add_component(weapon, RenderableComponent('/', (150, 150, 150), 1))
        world.add_component(weapon, ItemComponent(weight=2.0, value_cp=10))
        
        # Weapon properties
        world.add_component(weapon, WeaponComponent(
            damage_dice="1d4",
            attack_bonus=0,
            damage_bonus=0,
            weapon_type="melee",
            properties=["crude"]
        ))
        
        # Examination
        world.add_component(weapon, ExaminableComponent(
            f"A crude {name.lower()}.",
            f"This {name.lower()} is roughly made and shows signs of poor craftsmanship. Despite its crude appearance, it could still be dangerous in combat."
        ))
        
        return weapon
    
    @staticmethod
    def create_stairs(world: World, x: int, y: int, direction: str = "down") -> EntityID:
        """Create stairs (up or down)"""
        stairs = world.create_entity()
        
        # Core components
        world.add_component(stairs, PositionComponent(x, y))
        char = '∇' if direction == "down" else '△'
        world.add_component(stairs, RenderableComponent(char, (100, 100, 255), 1))
        world.add_component(stairs, NameComponent(f"Stairs {direction.title()}"))
        
        # Interaction
        world.add_component(stairs, InteractableComponent("stairs", requires_adjacent=True))
        
        # Environment
        world.add_component(stairs, EnvironmentComponent("stairs", destructible=False))
        
        # Examination
        world.add_component(stairs, ExaminableComponent(
            f"Stone steps leading {direction}ward.",
            f"These worn stone steps lead {direction}ward into the {'depths below' if direction == 'down' else 'upper levels'}. " +
            f"Cool air {'rises from' if direction == 'down' else 'drifts down from'} the darkness, carrying strange scents and the faint echo of distant sounds. " +
            "The steps are worn smooth by countless feet over the ages."
        ))
        
        return stairs
    
    @staticmethod
    def _get_class_stats(character_class: str) -> Dict[str, int]:
        """Get starting stats for a character class"""
        class_stats = {
            "Fighter": {"strength": 15, "dexterity": 13, "constitution": 14, "intelligence": 10, "wisdom": 12, "charisma": 8},
            "Priest": {"strength": 12, "dexterity": 10, "constitution": 13, "intelligence": 13, "wisdom": 15, "charisma": 14},
            "Thief": {"strength": 11, "dexterity": 16, "constitution": 12, "intelligence": 14, "wisdom": 13, "charisma": 10},
            "Wizard": {"strength": 8, "dexterity": 14, "constitution": 11, "intelligence": 16, "wisdom": 15, "charisma": 12}
        }
        return class_stats.get(character_class, class_stats["Fighter"])
    
    @staticmethod
    def _populate_chest(world: World, chest_entity: EntityID):
        """Add random treasure to a chest"""
        container = world.get_component(chest_entity, ContainerComponent)
        if not container:
            return
        
        # Add some random items
        treasure_count = random.randint(1, 3)
        
        for _ in range(treasure_count):
            if random.random() < 0.4:  # 40% chance for gold
                # Add gold (we'll handle this through the container's inventory system later)
                pass
            elif random.random() < 0.3:  # 30% chance for potion
                potion = EntityBuilder.create_simple_item(
                    world, "Health Potion", "A red potion that restores health",
                    '!', (255, 0, 0), 0.5, 50
                )
                container.contents.append(potion)
            elif random.random() < 0.2:  # 20% chance for torch
                torch = EntityBuilder.create_torch(world, 0, 0, True)  # Position doesn't matter for inventory items
                container.contents.append(torch)
            else:  # 10% chance for misc item
                misc_item = EntityBuilder.create_simple_item(
                    world, "Ancient Coin", "An old coin from a forgotten realm",
                    'o', (255, 215, 0), 0.1, 10
                )
                container.contents.append(misc_item)

class MonsterTemplates:
    """Templates for creating different types of monsters"""
    
    @staticmethod
    def create_rat(world: World, x: int, y: int, room_id: int = -1) -> EntityID:
        """Create a giant rat"""
        rat = world.create_entity()
        
        world.add_component(rat, PositionComponent(x, y, room_id))
        world.add_component(rat, RenderableComponent('r', (139, 69, 19), 5))
        world.add_component(rat, NameComponent("Giant Rat"))
        world.add_component(rat, HealthComponent(4, 4))
        world.add_component(rat, StatsComponent(7, 15, 11, 2, 10, 4))
        world.add_component(rat, MonsterComponent("rat", 0))
        world.add_component(rat, MovementComponent(speed=1))
        world.add_component(rat, AIComponent("hostile", aggro_range=4))
        world.add_component(rat, CombatStatsComponent(armor_class=11, attack_bonus=2))
        
        world.add_component(rat, ExaminableComponent(
            "A large, aggressive rodent with yellowed teeth.",
            "This rat is much larger than normal, nearly the size of a small dog. Its matted fur is crawling with fleas, and its red eyes gleam with a feral intelligence. Sharp teeth and claws make it a surprisingly dangerous opponent."
        ))
        
        return rat
    
    @staticmethod
    def create_skeleton(world: World, x: int, y: int, room_id: int = -1) -> EntityID:
        """Create an animated skeleton"""
        skeleton = world.create_entity()
        
        world.add_component(skeleton, PositionComponent(x, y, room_id))
        world.add_component(skeleton, RenderableComponent('s', (240, 240, 240), 5))
        world.add_component(skeleton, NameComponent("Skeleton"))
        world.add_component(skeleton, HealthComponent(8, 8))
        world.add_component(skeleton, StatsComponent(10, 14, 15, 6, 8, 5))
        world.add_component(skeleton, MonsterComponent("undead", 1))
        world.add_component(skeleton, MovementComponent(speed=1))
        world.add_component(skeleton, AIComponent("hostile", aggro_range=8))
        world.add_component(skeleton, CombatStatsComponent(armor_class=13, attack_bonus=3))
        
        # Skeletons are immune to poison and don't need to breathe
        world.add_component(skeleton, MagicalComponent("undead", 1))
        
        # Create bone weapon
        bone_weapon = EntityBuilder.create_crude_weapon(world, "Bone Sword")
        world.add_component(skeleton, EquipmentSlotsComponent())
        equipment = world.get_component(skeleton, EquipmentSlotsComponent)
        equipment.equip_item('weapon', bone_weapon)
        
        world.add_component(skeleton, ExaminableComponent(
            "An animated skeleton warrior.",
            "This skeleton moves with unnatural purpose, its bones held together by dark magic. Empty eye sockets burn with an unholy light, and it clutches ancient weapons with bony fingers. The sound of clicking bones follows its every movement."
        ))
        
        return skeleton

class RoomTemplates:
    """Templates for creating entire rooms with furniture and monsters"""
    
    @staticmethod
    def create_treasure_room(world: World, center_x: int, center_y: int, width: int, height: int) -> List[EntityID]:
        """Create a treasure room with chests and guards"""
        entities = []
        
        # Place treasure chests
        chest1 = EntityBuilder.create_chest(world, center_x - 1, center_y, locked=True)
        chest2 = EntityBuilder.create_chest(world, center_x + 1, center_y, locked=False)
        entities.extend([chest1, chest2])
        
        # Add some light
        torch1 = EntityBuilder.create_torch(world, center_x - width//2 + 1, center_y - height//2 + 1)
        torch2 = EntityBuilder.create_torch(world, center_x + width//2 - 1, center_y + height//2 - 1)
        entities.extend([torch1, torch2])
        
        # Add skeleton guards
        guard1 = MonsterTemplates.create_skeleton(world, center_x - 2, center_y - 1)
        guard2 = MonsterTemplates.create_skeleton(world, center_x + 2, center_y + 1)
        entities.extend([guard1, guard2])
        
        return entities
    
    @staticmethod
    def create_puzzle_room(world: World, center_x: int, center_y: int) -> List[EntityID]:
        """Create a boulder puzzle room"""
        entities = []
        
        # Central altar
        altar = EntityBuilder.create_altar(world, center_x, center_y)
        entities.append(altar)
        
        # Pressure plates
        plate_positions = [(center_x - 2, center_y - 1), (center_x + 2, center_y - 1), (center_x, center_y + 2)]
        for x, y in plate_positions:
            plate = EntityBuilder.create_pressure_plate(world, x, y, "main_puzzle")
            entities.append(plate)
        
        # Boulders (not on the plates initially)
        boulder_positions = [(center_x - 3, center_y), (center_x + 3, center_y), (center_x, center_y - 3)]
        for x, y in boulder_positions:
            boulder = EntityBuilder.create_boulder(world, x, y)
            entities.append(boulder)
        
        # Reward chest (opens when puzzle is solved)
        reward_chest = EntityBuilder.create_chest(world, center_x, center_y + 3, locked=True)
        entities.append(reward_chest)
        
        return entities

def create_test_world() -> World:
    """Create a simple test world for debugging"""
    world = World()
    
    # Create a player
    player = EntityBuilder.create_player_from_character_data(world, {
        'name': 'Test Hero',
        'x': 5,
        'y': 5,
        'character_class': 'Fighter',
        'race': 'Human'
    })
    
    # Create some monsters (2 total)
    goblin = EntityBuilder.create_goblin(world, 7, 5)
    rat = MonsterTemplates.create_rat(world, 3, 5)
    
    # Create some environment (2 total)
    chest = EntityBuilder.create_chest(world, 5, 3, locked=False)
    door = EntityBuilder.create_door(world, 8, 5, door_type=1, is_horizontal=False)
    
    # That's exactly 5 entities: player + goblin + rat + chest + door
    return world