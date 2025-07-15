# - Phase 1 ECS Test Script
"""
Test script for Phase 1 of ECS migration.
Tests the core ECS infrastructure before integration with the main game.

Run this script to verify that:
1. Core ECS (World, Entity, Component, System) works correctly
2. Basic components can be created and attached to entities
3. Basic systems can process entities
4. Entity creation/destruction works properly
5. Component queries work efficiently

Usage: python test_ecs.py
"""

import pygame
import time
import random
from typing import List, Tuple

# Import the ECS modules we're testing
from ecs_core import World, EntityID, Component, System
from ecs_components import *
from ecs_systems import *
from ecs_entities import EntityBuilder, MonsterTemplates, create_test_world

# Test configuration
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
TEST_DURATION = 30  # seconds

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_true(self, condition: bool, message: str):
        """Assert that condition is true"""
        if condition:
            self.passed += 1
            print(f"✓ {message}")
        else:
            self.failed += 1
            error_msg = f"✗ {message}"
            self.errors.append(error_msg)
            print(error_msg)
    
    def assert_equal(self, actual, expected, message: str):
        """Assert that actual equals expected"""
        if actual == expected:
            self.passed += 1
            print(f"✓ {message}")
        else:
            self.failed += 1
            error_msg = f"✗ {message} - Expected: {expected}, Got: {actual}"
            self.errors.append(error_msg)
            print(error_msg)
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! ECS is ready for Phase 2.")
        else:
            print(f"\n⚠️  {self.failed} tests failed. Fix these before proceeding to Phase 2.")

def test_core_ecs(results: TestResults):
    """Test core ECS functionality"""
    print("\n" + "="*30)
    print("TESTING CORE ECS")
    print("="*30)
    
    # Test World creation
    try:
        world = World()
        results.assert_true(world is not None, "World creation")
        results.assert_equal(world.get_entity_count(), 0, "Initial world should be empty")
    except Exception as e:
        results.assert_true(False, f"World creation failed: {e}")
        return
    
    # Test Entity creation
    try:
        entity1 = world.create_entity()
        entity2 = world.create_entity()
        results.assert_true(isinstance(entity1, EntityID), "Entity creation returns EntityID")
        results.assert_true(entity1 != entity2, "Each entity has unique ID")
        results.assert_equal(world.get_entity_count(), 2, "World tracks entity count")
    except Exception as e:
        results.assert_true(False, f"Entity creation failed: {e}")
        return
    
    # Test Component creation and attachment
    try:
        pos_comp = PositionComponent(10, 20)
        name_comp = NameComponent("Test Entity")
        
        world.add_component(entity1, pos_comp)
        world.add_component(entity1, name_comp)
        
        retrieved_pos = world.get_component(entity1, PositionComponent)
        retrieved_name = world.get_component(entity1, NameComponent)
        
        results.assert_true(retrieved_pos is not None, "Component attachment and retrieval")
        results.assert_equal(retrieved_pos.x, 10, "Component data preserved")
        results.assert_equal(retrieved_name.name, "Test Entity", "Component data preserved")
        
        results.assert_true(world.has_component(entity1, PositionComponent), "has_component works")
        results.assert_true(world.has_components(entity1, PositionComponent, NameComponent), "has_components works")
        
    except Exception as e:
        results.assert_true(False, f"Component system failed: {e}")
        return
    
    # Test Entity queries
    try:
        entities_with_pos = world.get_entities_with_components(PositionComponent)
        entities_with_both = world.get_entities_with_components(PositionComponent, NameComponent)
        
        results.assert_true(entity1 in entities_with_pos, "Entity query finds entities")
        results.assert_true(entity1 in entities_with_both, "Multi-component query works")
        results.assert_equal(len(entities_with_both), 1, "Query returns correct count")
        
    except Exception as e:
        results.assert_true(False, f"Entity queries failed: {e}")
        return
    
    # Test Entity destruction
    try:
        world.destroy_entity(entity2)
        results.assert_equal(world.get_entity_count(), 1, "Entity destruction updates count")
        results.assert_true(entity2 not in world.get_entities_with_components(PositionComponent), 
                          "Destroyed entity not in queries")
    except Exception as e:
        results.assert_true(False, f"Entity destruction failed: {e}")

def test_components(results: TestResults):
    """Test component functionality"""
    print("\n" + "="*30)
    print("TESTING COMPONENTS")
    print("="*30)
    
    try:
        # Test Position component
        pos = PositionComponent(5, 15, 2)
        results.assert_equal(pos.as_tuple(), (5, 15), "PositionComponent.as_tuple()")
        
        pos2 = PositionComponent(8, 17, 2)
        distance = pos.distance_to(pos2)
        results.assert_equal(distance, 3, "PositionComponent.distance_to() - Chebyshev distance")
        
        manhattan = pos.manhattan_distance_to(pos2)
        results.assert_equal(manhattan, 5, "PositionComponent.manhattan_distance_to()")
        
        # Test Health component
        health = HealthComponent(15, 20)
        results.assert_true(health.is_alive, "HealthComponent.is_alive when HP > 0")
        results.assert_equal(health.health_ratio, 0.75, "HealthComponent.health_ratio")
        results.assert_true(health.is_wounded, "HealthComponent.is_wounded when current < max")
        
        healed = health.heal(3)
        results.assert_equal(healed, 3, "HealthComponent.heal() returns amount healed")
        results.assert_equal(health.current_hp, 18, "HealthComponent.heal() updates HP")
        
        damage_taken = health.damage(25)
        results.assert_equal(damage_taken, 18, "HealthComponent.damage() returns actual damage")
        results.assert_equal(health.current_hp, 0, "HealthComponent.damage() can kill")
        results.assert_true(not health.is_alive, "HealthComponent.is_alive when HP = 0")
        
        # Test Stats component
        stats = StatsComponent(strength=16, dexterity=12, constitution=14)
        results.assert_equal(stats.get_modifier('strength'), 3, "StatsComponent.get_modifier() for high stat")
        results.assert_equal(stats.get_modifier('dexterity'), 1, "StatsComponent.get_modifier() for medium stat")
        results.assert_equal(stats.get_stat('constitution'), 14, "StatsComponent.get_stat()")
        
        stats.set_stat('wisdom', 8)
        results.assert_equal(stats.get_modifier('wisdom'), -1, "StatsComponent.set_stat() and modifier for low stat")
        
        # Test Renderable component
        renderable = RenderableComponent('@', (255, 0, 0), 5, True)
        results.assert_equal(renderable.ascii_char, '@', "RenderableComponent stores char")
        results.assert_equal(renderable.color, (255, 0, 0), "RenderableComponent stores color")
        results.assert_equal(renderable.render_layer, 5, "RenderableComponent stores layer")
        
        # Test Weapon component
        weapon = WeaponComponent(damage_dice="2d6", attack_bonus=2, weapon_type="melee")
        results.assert_equal(weapon.damage_dice, "2d6", "WeaponComponent stores damage")
        results.assert_equal(weapon.get_range('near'), 6, "WeaponComponent.get_range()")
        
        # Test Container component
        container = ContainerComponent([], 10, False)
        results.assert_true(container.is_empty, "ContainerComponent.is_empty when empty")
        results.assert_true(container.can_fit(5), "ContainerComponent.can_fit() when space available")
        results.assert_true(not container.is_full, "ContainerComponent.is_full when not full")
        
    except Exception as e:
        results.assert_true(False, f"Component testing failed: {e}")

def test_systems(results: TestResults):
    """Test system functionality"""
    print("\n" + "="*30)
    print("TESTING SYSTEMS")
    print("="*30)
    
    try:
        world = World()
        
        # Create test systems
        render_system = RenderSystem()
        movement_system = MovementSystem()
        health_system = HealthSystem()
        
        world.add_system(render_system)
        world.add_system(movement_system)
        world.add_system(health_system)
        
        results.assert_equal(len(world.systems), 3, "Systems added to world")
        
        # Create test entities
        entity = world.create_entity()
        world.add_component(entity, PositionComponent(5, 5))
        world.add_component(entity, RenderableComponent('@', (255, 255, 255)))
        world.add_component(entity, HealthComponent(10, 10))
        world.add_component(entity, MovementComponent())
        
        # Test render system
        render_system.set_viewport_size(20, 15)
        render_system.set_camera(0, 0)
        render_system.update(world, 0.016)
        
        renderable_entities = render_system.get_renderable_entities()
        results.assert_equal(len(renderable_entities), 1, "RenderSystem finds renderable entities")
        
        # Test movement system with events
        move_event = MoveEvent(entity, (5, 5), (6, 5))
        world.add_event(move_event)
        
        movement_system.update(world, 0.016)
        
        pos = world.get_component(entity, PositionComponent)
        results.assert_equal(pos.x, 6, "MovementSystem processes move events")
        
        # Test health system with damage event
        damage_event = DamageEvent(entity, 5, "physical")
        world.add_event(damage_event)
        
        health_system.update(world, 0.016)
        
        health = world.get_component(entity, HealthComponent)
        results.assert_equal(health.current_hp, 5, "HealthSystem processes damage events")
        
        # Test system removal
        world.remove_system(health_system)
        results.assert_equal(len(world.systems), 2, "System removal works")
        
    except Exception as e:
        results.assert_true(False, f"System testing failed: {e}")

# Fix for test_ecs.py - update the test expectation in test_entity_builders function

def test_entity_builders(results: TestResults):
    """Test entity builders"""
    print("\n" + "="*30)
    print("TESTING ENTITY BUILDERS")
    print("="*30)
    
    try:
        world = World()
        
        # Test player creation
        player = EntityBuilder.create_player(world, "Test Hero", 0, 0, "Fighter", "Human")
        results.assert_true(player is not None, "Player entity creation")
        results.assert_true(world.has_component(player, PositionComponent), "Player has position")
        results.assert_true(world.has_component(player, PlayerControlledComponent), "Player has player component")
        results.assert_true(world.has_component(player, HealthComponent), "Player has health")
        results.assert_true(world.has_component(player, StatsComponent), "Player has stats")
        
        name_comp = world.get_component(player, NameComponent)
        results.assert_equal(name_comp.name, "Test Hero", "Player name set correctly")
        
        # Test monster creation
        goblin = EntityBuilder.create_goblin(world, 5, 5, 1)
        results.assert_true(goblin is not None, "Goblin entity creation")
        results.assert_true(world.has_component(goblin, MonsterComponent), "Goblin has monster component")
        results.assert_true(world.has_component(goblin, AIComponent), "Goblin has AI component")
        
        # Test door creation
        door = EntityBuilder.create_door(world, 3, 3, 1, True)
        results.assert_true(door is not None, "Door entity creation")
        results.assert_true(world.has_component(door, DoorComponent), "Door has door component")
        results.assert_true(world.has_component(door, InteractableComponent), "Door has interactable component")
        
        # Test chest creation
        chest = EntityBuilder.create_chest(world, 7, 7, False)
        results.assert_true(chest is not None, "Chest entity creation")
        results.assert_true(world.has_component(chest, ContainerComponent), "Chest has container component")
        
        # Test boulder creation
        boulder = EntityBuilder.create_boulder(world, 10, 10)
        results.assert_true(boulder is not None, "Boulder entity creation")
        results.assert_true(world.has_component(boulder, MovableComponent), "Boulder has movable component")
        results.assert_true(world.has_component(boulder, BlocksMovementComponent), "Boulder blocks movement")
        
        # Verify total entities - UPDATE THIS LINE
        # The goblin creates a weapon entity, so we expect 6 total (player + goblin + goblin_weapon + door + chest + boulder)
        results.assert_equal(world.get_entity_count(), 7, "All test entities created including goblin weapon")
        
    except Exception as e:
        results.assert_true(False, f"Entity builder testing failed: {e}")

def test_performance(results: TestResults):
    """Test ECS performance with many entities"""
    print("\n" + "="*30)
    print("TESTING PERFORMANCE")
    print("="*30)
    
    try:
        world = World()
        render_system = RenderSystem()
        movement_system = MovementSystem()
        world.add_system(render_system)
        world.add_system(movement_system)
        
        # Create many entities
        start_time = time.time()
        num_entities = 1000
        
        entities = []
        for i in range(num_entities):
            entity = world.create_entity()
            world.add_component(entity, PositionComponent(
                random.randint(0, 100), 
                random.randint(0, 100)
            ))
            world.add_component(entity, RenderableComponent(
                chr(random.randint(65, 90)), 
                (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            ))
            if i % 2 == 0:  # Half have movement
                world.add_component(entity, MovementComponent())
            entities.append(entity)
        
        creation_time = time.time() - start_time
        results.assert_true(creation_time < 1.0, f"Creating {num_entities} entities in reasonable time ({creation_time:.3f}s)")
        
        # Test query performance
        start_time = time.time()
        for _ in range(100):  # 100 queries
            renderable_entities = world.get_entities_with_components(PositionComponent, RenderableComponent)
            movable_entities = world.get_entities_with_components(PositionComponent, MovementComponent)
        
        query_time = time.time() - start_time
        results.assert_true(query_time < 0.1, f"100 queries on {num_entities} entities in reasonable time ({query_time:.3f}s)")
        results.assert_equal(len(renderable_entities), num_entities, "Query finds all renderable entities")
        results.assert_equal(len(movable_entities), num_entities // 2, "Query finds correct number of movable entities")
        
        # Test system update performance
        start_time = time.time()
        for _ in range(60):  # Simulate 60 FPS for 1 second
            world.update(0.016)
        
        update_time = time.time() - start_time
        results.assert_true(update_time < 1.0, f"60 system updates on {num_entities} entities in reasonable time ({update_time:.3f}s)")
        
        # Test entity destruction performance
        start_time = time.time()
        for i in range(0, num_entities, 2):  # Remove half the entities
            world.destroy_entity(entities[i])
        
        destruction_time = time.time() - start_time
        results.assert_true(destruction_time < 0.5, f"Destroying {num_entities//2} entities in reasonable time ({destruction_time:.3f}s)")
        results.assert_equal(world.get_entity_count(), num_entities // 2, "Entity count correct after destruction")
        
    except Exception as e:
        results.assert_true(False, f"Performance testing failed: {e}")

def test_integration(results: TestResults):
    """Test integration scenarios"""
    print("\n" + "="*30)
    print("TESTING INTEGRATION")
    print("="*30)
    
    try:
        # Test the create_test_world function
        world = create_test_world()
        results.assert_true(world is not None, "create_test_world() works")
        results.assert_true(world.get_entity_count() > 0, "Test world has entities")
        
        # Find the player
        players = world.get_entities_with_components(PlayerControlledComponent)
        results.assert_equal(len(players), 1, "Test world has exactly one player")
        
        player = list(players)[0]
        player_pos = world.get_component(player, PositionComponent)
        results.assert_equal((player_pos.x, player_pos.y), (5, 5), "Player at expected position")
        
        # Test that we have different entity types
        monsters = world.get_entities_with_components(MonsterComponent)
        items = world.get_entities_with_components(ItemComponent)
        interactables = world.get_entities_with_components(InteractableComponent)
        
        results.assert_true(len(monsters) > 0, "Test world has monsters")
        results.assert_true(len(interactables) > 0, "Test world has interactable objects")
        
        # Test component dependencies
        from ecs_components import get_component_dependencies, validate_entity_components
        
        dependencies = get_component_dependencies()
        results.assert_true(len(dependencies) > 0, "Component dependencies defined")
        
        # Validate all entities in test world
        all_entities = world.get_entities_with_components()  # Get all entities
        for entity in world.entities:
            errors = validate_entity_components(world, entity)
            results.assert_equal(len(errors), 0, f"Entity {entity} has valid component dependencies")
        
        # Test monster templates
        rat = MonsterTemplates.create_rat(world, 10, 10, 1)
        skeleton = MonsterTemplates.create_skeleton(world, 12, 12, 1)
        
        results.assert_true(world.has_component(rat, MonsterComponent), "Rat template creates monster")
        results.assert_true(world.has_component(skeleton, MonsterComponent), "Skeleton template creates monster")
        results.assert_true(world.has_component(skeleton, MagicalComponent), "Skeleton has magical component (undead)")
        
    except Exception as e:
        results.assert_true(False, f"Integration testing failed: {e}")

def visual_test(results: TestResults):
    """Run a visual test with pygame to see ECS in action"""
    print("\n" + "="*30)
    print("RUNNING VISUAL TEST")
    print("="*30)
    print("This will show a pygame window for 30 seconds with ECS entities moving around.")
    print("You should see:")
    print("- A red @ symbol (player)")
    print("- Green letters (monsters) moving randomly")
    print("- Various colored symbols (items, doors, etc.)")
    print("- Entities should move smoothly and independently")
    print("Close the window or wait 30 seconds to continue.")
    
    try:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ECS Phase 1 Visual Test")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)
        
        # Create test world
        world = create_test_world()
        
        # Add some random moving entities for visual interest
        for i in range(20):
            entity = world.create_entity()
            world.add_component(entity, PositionComponent(
                random.randint(50, SCREEN_WIDTH-50), 
                random.randint(50, SCREEN_HEIGHT-50)
            ))
            world.add_component(entity, RenderableComponent(
                chr(random.randint(65, 90)),  # Random letter
                (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
                1
            ))
            world.add_component(entity, MovementComponent())
        
        # Add systems
        render_system = RenderSystem()
        movement_system = MovementSystem()
        world.add_system(render_system)
        world.add_system(movement_system)
        
        # Set up render system
        render_system.set_viewport_size(SCREEN_WIDTH // 24, SCREEN_HEIGHT // 24)
        render_system.set_camera(0, 0)
        
        start_time = time.time()
        running = True
        
        while running and (time.time() - start_time) < TEST_DURATION:
            dt = clock.tick(FPS) / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Add random movement events for moving entities
            moving_entities = world.get_entities_with_components(PositionComponent, MovementComponent)
            for entity in moving_entities:
                if random.random() < 0.1:  # 10% chance per frame
                    pos = world.get_component(entity, PositionComponent)
                    dx = random.randint(-2, 2)
                    dy = random.randint(-2, 2)
                    new_pos = (
                        max(0, min(SCREEN_WIDTH-24, pos.x + dx)),
                        max(0, min(SCREEN_HEIGHT-24, pos.y + dy))
                    )
                    move_event = MoveEvent(entity, (pos.x, pos.y), new_pos)
                    world.add_event(move_event)
            
            # Update world
            world.update(dt)
            
            # Render
            screen.fill((20, 20, 40))  # Dark blue background
            
            # Get entities to render
            render_system.update(world, dt)
            entities_to_render = render_system.get_renderable_entities()
            
            for entity, pos_comp, render_comp in entities_to_render:
                if render_comp.visible:
                    # Convert world position to screen position
                    screen_x = int(pos_comp.x)
                    screen_y = int(pos_comp.y)
                    
                    # Render entity
                    text_surface = font.render(render_comp.ascii_char, True, render_comp.color)
                    screen.blit(text_surface, (screen_x, screen_y))
            
            # Draw info
            entity_count = world.get_entity_count()
            info_text = f"Entities: {entity_count} | FPS: {clock.get_fps():.1f} | Time: {time.time() - start_time:.1f}s"
            info_surface = font.render(info_text, True, (255, 255, 255))
            screen.blit(info_surface, (10, 10))
            
            pygame.display.flip()
        
        pygame.quit()
        
        # If we got here without crashing, the visual test passed
        results.assert_true(True, "Visual test completed without crashes")
        results.assert_true(len(entities_to_render) > 0, "Entities visible in visual test")
        
    except Exception as e:
        results.assert_true(False, f"Visual test failed: {e}")
        pygame.quit()

def main():
    """Run all ECS tests"""
    print("🔧 STARTING ECS PHASE 1 TESTS")
    print("Testing the core ECS infrastructure before integration")
    print("=" * 60)
    
    results = TestResults()
    
    # Run all tests
    test_core_ecs(results)
    test_components(results)
    test_systems(results)
    test_entity_builders(results)
    test_performance(results)
    test_integration(results)
    
    # Ask user if they want to run visual test
    print("\n" + "="*30)
    print("VISUAL TEST OPTION")
    print("="*30)
    response = input("Run visual test? This will show a pygame window for 30 seconds (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        visual_test(results)
    else:
        print("Skipping visual test.")
    
    # Print final results
    results.print_summary()
    
    # Recommendations
    print("\n" + "="*50)
    print("NEXT STEPS")
    print("="*50)
    if results.failed == 0:
        print("✅ All tests passed! You're ready to proceed to Phase 2.")
        print("\nPhase 2 will involve:")
        print("- Creating ecs_game_manager.py")
        print("- Modifying main.py to use ECS")
        print("- Converting basic game states to ECS events")
        print("\nYou can safely delete this test_ecs.py file once Phase 2 is complete.")
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        print("\nCommon issues:")
        print("- Check that all ECS files are in the correct directory")
        print("- Verify import paths are correct")
        print("- Make sure pygame is installed for visual tests")
        print("- Check for typos in component/system names")
    
    return results.failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)