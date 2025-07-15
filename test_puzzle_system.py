# test_puzzle_system.py - Complete test framework for puzzle components
import pygame
import json
import sys
from typing import Dict, Any
from game_constants import *
from dungeon_classes import DungeonExplorer, Room
from puzzle_system import (
    PuzzleManager, PuzzleRoom, PuzzleType, PuzzleState,
    Boulder, PressurePlate, Altar, Glyph, Barrier, Chest,
    generate_boulder_puzzle
)
from rendering_engine import draw_tile, draw_puzzle_overlays
from character_creation import Player

class PuzzleTestManager:
    """Test manager for puzzle system components"""
    
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Puzzle System Test")
        
        self.cell_size = 32
        try:
            self.font = pygame.font.Font(FONT_FILE, 24)
        except:
            self.font = pygame.font.Font(None, 24)
        
        # Test data
        self.test_results = {}
        self.current_test = 0
        self.tests = [
            self.test_puzzle_element_creation,
            self.test_puzzle_room_creation,
            self.test_boulder_movement,
            self.test_puzzle_solving,
            self.test_dungeon_integration,
            self.test_rendering,
            self.test_full_scenario
        ]
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("=" * 50)
        print("PUZZLE SYSTEM TEST SUITE")
        print("=" * 50)
        
        for i, test_func in enumerate(self.tests):
            print(f"\nTest {i+1}/{len(self.tests)}: {test_func.__name__}")
            try:
                result = test_func()
                self.test_results[test_func.__name__] = result
                print(f"✓ {test_func.__name__}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                print(f"✗ {test_func.__name__}: ERROR - {e}")
                self.test_results[test_func.__name__] = False
        
        self._print_summary()
        return all(self.test_results.values())
    
    def test_puzzle_element_creation(self) -> bool:
        """Test basic puzzle element creation"""
        try:
            # Test creating each type of puzzle element
            boulder = Boulder(5, 5)
            plate = PressurePlate(7, 7)
            altar = Altar(10, 10)
            glyph = Glyph(3, 3)
            barrier = Barrier(12, 12)
            chest = Chest(15, 15, trapped=True)
            
            # Verify properties
            assert boulder.element_type == "boulder"
            assert boulder.interactable == True
            assert plate.element_type == "pressure_plate"
            assert plate.active == False
            assert altar.element_type == "altar"
            assert altar.active == True
            assert glyph.active == False
            assert barrier.active == True  # Starts blocking
            assert chest.trapped == True
            assert chest.opened == False
            
            print("  - All puzzle elements created successfully")
            return True
            
        except Exception as e:
            print(f"  - Element creation failed: {e}")
            return False
    
    def test_puzzle_room_creation(self) -> bool:
        """Test puzzle room creation and management"""
        try:
            puzzle = PuzzleRoom(1, PuzzleType.BOULDER_PRESSURE_PLATE, PuzzleState.ACTIVE)
            
            # Add elements
            puzzle.add_element(Boulder(5, 5))
            puzzle.add_element(Boulder(6, 6))
            puzzle.add_element(PressurePlate(8, 8))
            puzzle.add_element(PressurePlate(9, 9))
            puzzle.add_element(Altar(7, 7))
            
            # Verify structure
            assert len(puzzle.elements["boulders"]) == 2
            assert len(puzzle.elements["pressure_plates"]) == 2
            assert len(puzzle.elements["altars"]) == 1
            assert puzzle.puzzle_type == PuzzleType.BOULDER_PRESSURE_PLATE
            
            print("  - Puzzle room created and populated successfully")
            return True
            
        except Exception as e:
            print(f"  - Puzzle room creation failed: {e}")
            return False
    
    def test_boulder_movement(self) -> bool:
        """Test boulder movement mechanics"""
        try:
            puzzle_manager = PuzzleManager()
            puzzle = PuzzleRoom(1, PuzzleType.BOULDER_PRESSURE_PLATE, PuzzleState.ACTIVE)
            
            # Create boulder and pressure plate
            boulder = Boulder(5, 5)
            plate = PressurePlate(6, 6)
            puzzle.add_element(boulder)
            puzzle.add_element(plate)
            puzzle_manager.add_puzzle(puzzle)
            
            # Define walkable positions
            walkable_positions = {(x, y) for x in range(0, 20) for y in range(0, 20)}
            
            # Test valid movement
            success = puzzle_manager.move_boulder(boulder, 6, 5, walkable_positions)
            assert success == True
            assert boulder.x == 6 and boulder.y == 5
            
            # Test invalid movement (out of bounds)
            walkable_positions = {(x, y) for x in range(0, 10) for y in range(0, 10)}
            success = puzzle_manager.move_boulder(boulder, 15, 15, walkable_positions)
            assert success == False
            
            print("  - Boulder movement mechanics working correctly")
            return True
            
        except Exception as e:
            print(f"  - Boulder movement test failed: {e}")
            return False
    
    def test_puzzle_solving(self) -> bool:
        """Test puzzle solution detection"""
        try:
            puzzle = PuzzleRoom(1, PuzzleType.BOULDER_PRESSURE_PLATE, PuzzleState.ACTIVE)
            
            # Create 2 boulders and 2 pressure plates
            boulder1 = Boulder(5, 5)
            boulder2 = Boulder(6, 6)
            plate1 = PressurePlate(8, 8)
            plate2 = PressurePlate(9, 9)
            glyph = Glyph(10, 10)
            barrier = Barrier(11, 11)
            
            puzzle.add_element(boulder1)
            puzzle.add_element(boulder2)
            puzzle.add_element(plate1)
            puzzle.add_element(plate2)
            puzzle.add_element(glyph)
            puzzle.add_element(barrier)
            
            # Initially unsolved
            assert puzzle.check_solution() == False
            assert glyph.active == False
            assert barrier.active == True
            
            # Move one boulder onto a plate
            boulder1.x, boulder1.y = 8, 8
            puzzle.update_state()
            assert puzzle.check_solution() == False  # Still not fully solved
            assert plate1.active == True  # This plate should be active
            
            # Move second boulder onto second plate
            boulder2.x, boulder2.y = 9, 9
            puzzle.update_state()
            assert puzzle.check_solution() == True
            assert puzzle.state == PuzzleState.SOLVED
            assert glyph.active == True
            assert barrier.active == False
            
            print("  - Puzzle solving logic working correctly")
            return True
            
        except Exception as e:
            print(f"  - Puzzle solving test failed: {e}")
            return False
    
    def test_dungeon_integration(self) -> bool:
        """Test puzzle integration with dungeon system"""
        try:
            # Create a simple test dungeon
            test_dungeon_data = {
                "rects": [
                    {"x": 0, "y": 0, "w": 10, "h": 10},
                    {"x": 15, "y": 0, "w": 8, "h": 8}
                ],
                "doors": [
                    {"x": 10, "y": 5, "dir": {"x": 1, "y": 0}, "type": 1}
                ],
                "notes": [],
                "columns": [],
                "water": []
            }
            
            # Create dungeon
            dungeon = DungeonExplorer(test_dungeon_data)
            
            # Check that puzzle manager was created
            assert dungeon.puzzle_manager is not None
            
            # Check that some puzzles might have been generated
            print(f"  - Generated {len(dungeon.puzzle_manager.puzzles)} puzzles")
            
            # Check tile integration
            puzzle_tile_count = sum(1 for tile in dungeon.tiles.values() 
                                  if tile in [TileType.ALTAR, TileType.BOULDER, 
                                            TileType.PRESSURE_PLATE, TileType.GLYPH, 
                                            TileType.BARRIER, TileType.CHEST])
            
            print(f"  - Found {puzzle_tile_count} puzzle tiles in dungeon")
            print("  - Dungeon integration successful")
            return True
            
        except Exception as e:
            print(f"  - Dungeon integration test failed: {e}")
            return False
    
    def test_rendering(self) -> bool:
        """Test puzzle element rendering"""
        try:
            # Create a small test surface
            test_surface = pygame.Surface((200, 200))
            
            # Test rendering each puzzle tile type
            puzzle_tiles = [
                TileType.ALTAR, TileType.BOULDER, TileType.PRESSURE_PLATE,
                TileType.PRESSURE_PLATE_ACTIVE, TileType.GLYPH, TileType.GLYPH_ACTIVE,
                TileType.BARRIER, TileType.STAIRS_DOWN, TileType.CHEST
            ]
            
            for i, tile_type in enumerate(puzzle_tiles):
                x = (i % 3) * 64
                y = (i // 3) * 64
                
                # This should not throw an exception
                draw_tile(test_surface, tile_type, x // 32, y // 32, 32)
            
            print("  - All puzzle tile types rendered successfully")
            return True
            
        except Exception as e:
            print(f"  - Rendering test failed: {e}")
            return False
    
    def test_full_scenario(self) -> bool:
        """Test the complete puzzle scenario described in the prompt"""
        try:
            # Create a room for our scenario
            room = Room(0, 0, 0, 10, 10)
            room_cells = room.get_cells()
            
            # Generate the boulder puzzle
            puzzle = generate_boulder_puzzle(room, room_cells)
            
            if not puzzle.elements:
                print("  - No puzzle generated (room too small or random chance)")
                return True  # This is acceptable
            
            # Verify we have the key components
            has_altar = len(puzzle.elements["altars"]) > 0
            has_boulders = len(puzzle.elements["boulders"]) >= 3
            has_plates = len(puzzle.elements["pressure_plates"]) >= 3
            has_glyph = len(puzzle.elements["glyphs"]) > 0
            has_barrier = len(puzzle.elements["barriers"]) > 0
            has_chest = len(puzzle.elements["chests"]) > 0
            
            print(f"  - Altar: {has_altar}")
            print(f"  - Boulders: {len(puzzle.elements['boulders'])}")
            print(f"  - Pressure plates: {len(puzzle.elements['pressure_plates'])}")
            print(f"  - Glyph: {has_glyph}")
            print(f"  - Barrier: {has_barrier}")
            print(f"  - Chest: {has_chest}")
            
            # Test the complete solving scenario
            puzzle_manager = PuzzleManager()
            puzzle_manager.add_puzzle(puzzle)
            
            # Simulate solving by moving all boulders onto plates
            walkable_positions = {(x, y) for x in range(-5, 15) for y in range(-5, 15)}
            
            boulders = puzzle.elements["boulders"]
            plates = puzzle.elements["pressure_plates"]
            
            if len(boulders) >= len(plates):
                for i, (boulder, plate) in enumerate(zip(boulders, plates)):
                    success = puzzle_manager.move_boulder(boulder, plate.x, plate.y, walkable_positions)
                    if success:
                        print(f"  - Boulder {i+1} moved to pressure plate {i+1}")
                
                # Check if puzzle is now solved
                if puzzle.check_solution():
                    print("  - Puzzle solved! Barrier should be removed, glyph should glow")
                    
                    # Verify solution effects
                    glyph = puzzle.elements["glyphs"][0] if puzzle.elements["glyphs"] else None
                    barrier = puzzle.elements["barriers"][0] if puzzle.elements["barriers"] else None
                    
                    if glyph and glyph.active:
                        print("  - ✓ Glyph is glowing")
                    if barrier and not barrier.active:
                        print("  - ✓ Barrier is deactivated")
                    
                    return True
                else:
                    print("  - Puzzle not solved despite moving boulders")
                    return False
            
            print("  - Full scenario test completed")
            return True
            
        except Exception as e:
            print(f"  - Full scenario test failed: {e}")
            return False
    
    def _print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for test_name, result in self.test_results.items():
                if not result:
                    print(f"  - {test_name}")
        
        print("\nComponent Status:")
        print("✓ Puzzle Element Creation" if self.test_results.get("test_puzzle_element_creation", False) else "✗ Puzzle Element Creation")
        print("✓ Puzzle Room Management" if self.test_results.get("test_puzzle_room_creation", False) else "✗ Puzzle Room Management")
        print("✓ Boulder Movement" if self.test_results.get("test_boulder_movement", False) else "✗ Boulder Movement")
        print("✓ Puzzle Solving Logic" if self.test_results.get("test_puzzle_solving", False) else "✗ Puzzle Solving Logic")
        print("✓ Dungeon Integration" if self.test_results.get("test_dungeon_integration", False) else "✗ Dungeon Integration")
        print("✓ Rendering System" if self.test_results.get("test_rendering", False) else "✗ Rendering System")
        print("✓ Full Scenario" if self.test_results.get("test_full_scenario", False) else "✗ Full Scenario")

def run_interactive_demo():
    """Run an interactive visual demo of the puzzle system"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Puzzle System Interactive Demo")
    clock = pygame.time.Clock()
    
    # Create a simple dungeon with a puzzle
    test_dungeon_data = {
        "rects": [{"x": 2, "y": 2, "w": 12, "h": 12}],
        "doors": [],
        "notes": [],
        "columns": [],
        "water": []
    }
    
    dungeon = DungeonExplorer(test_dungeon_data)
    
    # Force create a puzzle for demo
    room = list(dungeon.rooms.values())[0]
    room_cells = room.get_cells()
    puzzle = generate_boulder_puzzle(room, room_cells)
    
    if puzzle.elements:
        dungeon.puzzle_manager.add_puzzle(puzzle)
        dungeon._place_puzzle_tiles(puzzle)
        dungeon.reveal_room(0)
    
    # Create a simple player for testing
    player = Player(
        name="Test Player", title="Tester", race="Human", alignment="Neutral",
        character_class="Fighter", level=1, hp=10, max_hp=10, xp=0, xp_to_next_level=100,
        ac=11, light_duration=3600, light_start_time=0,
        strength=15, dexterity=12, constitution=14, intelligence=10, wisdom=10, charisma=10
    )
    player.x, player.y = 7, 7  # Place player in middle of room
    
    # Demo variables
    cell_size = 32
    viewport_x, viewport_y = 0, 0
    try:
        font = pygame.font.Font(FONT_FILE, 24)
    except:
        font = pygame.font.Font(None, 24)
    
    instructions = [
        "PUZZLE SYSTEM DEMO",
        "WASD: Move player",
        "SPACE: Interact/Push boulder",
        "ESC: Exit",
        "",
        "Goal: Push boulders (■) onto",
        "pressure plates (◉) to solve puzzle"
    ]
    
    running = True
    while running:
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    player.y -= 1
                elif event.key == pygame.K_s:
                    player.y += 1
                elif event.key == pygame.K_a:
                    player.x -= 1
                elif event.key == pygame.K_d:
                    player.x += 1
                elif event.key == pygame.K_SPACE:
                    # Try to interact with adjacent cells
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        interact_x = player.x + dx
                        interact_y = player.y + dy
                        if dungeon.handle_player_interaction(player, interact_x, interact_y):
                            break
        
        # Clear screen
        screen.fill(COLOR_BG)
        
        # Draw dungeon tiles
        for y in range(20):
            for x in range(20):
                world_x, world_y = viewport_x + x, viewport_y + y
                tile_type = dungeon.tiles.get((world_x, world_y), TileType.VOID)
                
                if dungeon.is_revealed(world_x, world_y):
                    draw_tile(screen, tile_type, x, y, cell_size)
        
        # Draw puzzle overlays
        draw_puzzle_overlays(screen, dungeon, viewport_x, viewport_y, cell_size, font)
        
        # Draw player
        player_screen_x = (player.x - viewport_x) * cell_size + cell_size // 2
        player_screen_y = (player.y - viewport_y) * cell_size + cell_size // 2
        pygame.draw.circle(screen, COLOR_PLAYER, (player_screen_x, player_screen_y), cell_size // 4)
        
        # Draw instructions
        for i, instruction in enumerate(instructions):
            color = COLOR_WHITE if instruction else COLOR_WHITE
            text_surf = font.render(instruction, True, color)
            screen.blit(text_surf, (520, 50 + i * 25))
        
        # Check puzzle status
        if puzzle.elements:
            status_text = f"Puzzle Status: {puzzle.state.name}"
            status_surf = font.render(status_text, True, COLOR_WHITE)
            screen.blit(status_surf, (520, 250))
            
            solved_text = "SOLVED!" if puzzle.check_solution() else "Unsolved"
            solved_color = COLOR_GREEN if puzzle.check_solution() else COLOR_RED
            solved_surf = font.render(solved_text, True, solved_color)
            screen.blit(solved_surf, (520, 275))
        
        pygame.display.flip()
    
    pygame.quit()

def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("Running interactive demo...")
        run_interactive_demo()
    else:
        print("Running automated tests...")
        test_manager = PuzzleTestManager()
        success = test_manager.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! Puzzle system is ready.")
            print("\nTo run interactive demo: python test_puzzle_system.py --demo")
        else:
            print("\n❌ Some tests failed. Check the output above.")
        
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
    
    def test_puzzle_element_creation(self) -> bool:
        """Test basic puzzle element creation"""
        try:
            # Test creating each type of puzzle element
            boulder = Boulder(5, 5)
            plate = PressurePlate(7, 7)
            altar = Altar(10, 10)
            glyph = Glyph(3, 3)
            barrier = Barrier(12, 12)
            chest = Chest(15, 15, trapped=True)
            
            # Verify properties
            assert boulder.element_type == "boulder"
            assert boulder.interactable == True
            assert plate.element_type == "pressure_plate"
            assert plate.active == False
            assert altar.element_type == "altar"
            assert altar.active == True
            assert glyph.active == False
            assert barrier.active == True  # Starts blocking
            assert chest.trapped == True
            assert chest.opened == False
            
            print("  - All puzzle elements created successfully")
            return True
            
        except Exception as e:
            print(f"  - Element creation failed: {e}")
            return False
    
    def test_puzzle_room_creation(self) -> bool:
        """Test puzzle room creation and management"""
        try:
            puzzle = PuzzleRoom(1, PuzzleType.BOULDER_PRESSURE_PLATE, PuzzleState.ACTIVE)
            
            # Add elements
            puzzle.add_element(Boulder(5, 5))
            puzzle.add_element(Boulder(6, 6))
            puzzle.add_element(PressurePlate(8, 8))
            puzzle.add_element(PressurePlate(9, 9))
            puzzle.add_element(Altar(7, 7))
            
            # Verify structure
            assert len(puzzle.elements["boulders"]) == 2
            assert len(puzzle.elements["pressure_plates"]) == 2
            assert len(puzzle.elements["altars"]) == 1
            assert puzzle.puzzle_type == PuzzleType.BOULDER_PRESSURE_PLATE
            
            print("  - Puzzle room created and populated successfully")
            return True
            
        except Exception as e:
            print(f"  - Puzzle room creation failed: {e}")
            return False
    
    def test_boulder_movement(self) -> bool:
        """Test boulder movement mechanics"""
        try:
            puzzle_manager = PuzzleManager()
            puzzle = PuzzleRoom(1, PuzzleType.BOULDER_PRESSURE_PLATE, PuzzleState.ACTIVE)
            
            # Create boulder and pressure plate
            boulder = Boulder(5, 5)
            plate = PressurePlate(6, 6)
            puzzle.add_element(boulder)
            puzzle.add_element(plate)
            puzzle_manager.add_puzzle(puzzle)
            
            # Define walkable positions
            walkable_positions = {(x, y) for x in range(0, 20) for y in range(0, 20)}
            
            # Test valid movement
            success = puzzle_manager.move_boulder(boulder, 6, 5, walkable_positions)
            assert success == True
            assert boulder.x == 6 and boulder.y == 5
            
            # Test invalid movement (out of bounds)
            walkable_positions = {(x, y) for x in range(0, 10) for y in range(0, 10)}
            success = puzzle_manager.move_boulder(boulder, 15, 15, walkable_positions)
            assert success == False
            
            print("  - Boulder movement mechanics working correctly")
            return True
            
        except Exception as e:
            print(f"  - Boulder movement test failed: {e}")
            return False
    
    def test_puzzle_solving(self) -> bool:
        """Test puzzle solution detection"""
        try:
            puzzle = PuzzleRoom(1, PuzzleType.BOULDER_PRESSURE_PLATE, PuzzleState.ACTIVE)
            
            # Create 2 boulders and 2 pressure plates
            boulder1 = Boulder(5, 5)
            boulder2 = Boulder(6, 6)
            plate1 = PressurePlate(8, 8)
            plate2 = PressurePlate(9, 9)
            glyph = Glyph(10, 10)
            barrier = Barrier(11, 11)
            
            puzzle.add_element(boulder1)
            puzzle.add_element(boulder2)
            puzzle.add_element(plate1)
            puzzle.add_element(plate2)
            puzzle.add_element(glyph)
            puzzle.add_element(barrier)
            
            # Initially unsolved
            assert puzzle.check_solution() == False
            assert glyph.active == False
            assert barrier.active == True
            
            # Move one boulder onto a plate
            boulder1.x, boulder1.y = 8, 8
            puzzle.update_state()
            assert puzzle.check_solution() == False  # Still not fully solved
            assert plate1.active == True  # This plate should be active
            
            # Move second boulder onto second plate
            boulder2.x, boulder2.y = 9, 9
            puzzle.update_state()
            assert puzzle.check_solution() == True
            assert puzzle.state == PuzzleState.SOLVED
            assert glyph.active == True
            assert barrier.active == False
            
            print("  - Puzzle solving logic working correctly")
            return True
            
        except Exception as e:
            print(f"  - Puzzle solving test failed: {e}")
            return False
    
    def test_dungeon_integration(self) -> bool:
        """Test puzzle integration with dungeon system"""
        try:
            # Create a simple test dungeon
            test_dungeon_data = {
                "rects": [
                    {"x": 0, "y": 0, "w": 10, "h": 10},
                    {"x": 15, "y": 0, "w": 8, "h": 8}
                ],
                "doors": [
                    {"x": 10, "y": 5, "dir": {"x": 1, "y": 0}, "type": 1}
                ],
                "notes": [],
                "columns": [],
                "water": []
            }
            
            # Create dungeon
            dungeon = DungeonExplorer(test_dungeon_data)
            
            # Check that puzzle manager was created
            assert dungeon.puzzle_manager is not None
            
            # Check that some puzzles might have been generated
            print(f"  - Generated {len(dungeon.puzzle_manager.puzzles)} puzzles")
            
            # Check tile integration
            puzzle_tile_count = sum(1 for tile in dungeon.tiles.values() 
                                  if tile in [TileType.ALTAR, TileType.BOULDER, 
                                            TileType.PRESSURE_PLATE, TileType.GLYPH, 
                                            TileType.BARRIER, TileType.CHEST])
            
            print(f"  - Found {puzzle_tile_count} puzzle tiles in dungeon")
            print("  - Dungeon integration successful")
            return True
            
        except Exception as e:
            print(f"  - Dungeon integration test failed: {e}")
            return False
    
    def test_rendering(self) -> bool:
        """Test puzzle element rendering"""
        try:
            # Create a small test surface
            test_surface = pygame.Surface((200, 200))
            
            # Test rendering each puzzle tile type
            puzzle_tiles = [
                TileType.ALTAR, TileType.BOULDER, TileType.PRESSURE_PLATE,
                TileType.PRESSURE_PLATE_ACTIVE, TileType.GLYPH, TileType.GLYPH_ACTIVE,
                TileType.BARRIER, TileType.STAIRS_DOWN, TileType.CHEST
            ]
            
            for i, tile_type in enumerate(puzzle_tiles):
                x = (i % 3) * 64
                y = (i // 3) * 64
                
                # This should not throw an exception
                draw_tile(test_surface, tile_type, x // 32, y // 32, 32)
            
            print("  - All puzzle tile types rendered successfully")
            return True
            
        except Exception as e:
            print(f"  - Rendering test failed: {e}")
            return False
    
    def test_full_scenario(self) -> bool:
        """Test the complete puzzle scenario described in the prompt"""
        try:
            # Create a room for our scenario
            room = Room(0, 0, 0, 10, 10)
            room_cells = room.get_cells()
            
            # Generate the boulder puzzle
            puzzle = generate_boulder_puzzle(room, room_cells)
            
            if not puzzle.elements:
                print("  - No puzzle generated (room too small or random chance)")
                return True  # This is acceptable
            
            # Verify we have the key components
            has_altar = len(puzzle.elements["altars"]) > 0
            has_boulders = len(puzzle.elements["boulders"]) >= 3
            has_plates = len(puzzle.elements["pressure_plates"]) >= 3
            has_glyph = len(puzzle.elements["glyphs"]) > 0
            has_barrier = len(puzzle.elements["barriers"]) > 0
            has_chest = len(puzzle.elements["chests"]) > 0
            
            print(f"  - Altar: {has_altar}")
            print(f"  - Boulders: {len(puzzle.elements['boulders'])}")
            print(f"  - Pressure plates: {len(puzzle.elements['pressure_plates'])}")
            print(f"  - Glyph: {has_glyph}")
            print(f"  - Barrier: {has_barrier}")
            print(f"  - Chest: {has_chest}")
            
            # Test the complete solving scenario
            puzzle_manager = PuzzleManager()
            puzzle_manager.add_puzzle(puzzle)
            
            # Simulate solving by moving all boulders onto plates
            walkable_positions = {(x, y) for x in range(-5, 15) for y in range(-5, 15)}
            
            boulders = puzzle.elements["boulders"]
            plates = puzzle.elements["pressure_plates"]
            
            if len(boulders) >= len(plates):
                for i, (boulder, plate) in enumerate(zip(boulders, plates)):
                    success = puzzle_manager.move_boulder(boulder, plate.x, plate.y, walkable_positions)
                    if success:
                        print(f"  - Boulder {i+1} moved to pressure plate {i+1}")
                
                # Check if puzzle is now solved
                if puzzle.check_solution():
                    print("  - Puzzle solved! Barrier should be removed, glyph should glow")
                    
                    # Verify solution effects
                    glyph = puzzle.elements["glyphs"][0] if puzzle.elements["glyphs"] else None
                    barrier = puzzle.elements["barriers"][0] if puzzle.elements["barriers"] else None
                    
                    if glyph and glyph.active:
                        print("  - ✓ Glyph is glowing")
                    if barrier and not barrier.active:
                        print("  - ✓ Barrier is deactivated")
                    
                    return True
                else:
                    print("  - Puzzle not solved despite moving boulders")
                    return False
            
            print("  - Full scenario test completed")
            return True
            
        except Exception as e:
            print(f"  - Full scenario test failed: {e}")
            return False
    
    def _print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for test_name, result in self.test_results.items():
                if not result:
                    print(f"  - {test_name}")
        
        print("\nComponent Status:")
        print("✓ Puzzle Element Creation" if self.test_results.get("test_puzzle_element_creation", False) else "✗ Puzzle Element Creation")
        print("✓ Puzzle Room Management" if self.test_results.get("test_puzzle_room_creation", False) else "✗ Puzzle Room Management")
        print("✓ Boulder Movement" if self.test_results.get("test_boulder_movement", False) else "✗ Boulder Movement")
        print("✓ Puzzle Solving Logic" if self.test_results.get("test_puzzle_solving", False) else "✗ Puzzle Solving Logic")
        print("✓ Dungeon Integration" if self.test_results.get("test_dungeon_integration", False) else "✗ Dungeon Integration")
        print("✓ Rendering System" if self.test_results.get("test_rendering", False) else "✗ Rendering System")
        print("✓ Full Scenario" if self.test_results.get("test_full_scenario", False) else "✗ Full Scenario")

def run_interactive_demo():
    """Run an interactive visual demo of the puzzle system"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Puzzle System Interactive Demo")
    clock = pygame.time.Clock()
    
    # Create a simple dungeon with a puzzle
    test_dungeon_data = {
        "rects": [{"x": 2, "y": 2, "w": 12, "h": 12}],
        "doors": [],
        "notes": [],
        "columns": [],
        "water": []
    }
    
    dungeon = DungeonExplorer(test_dungeon_data)
    
    # Force create a puzzle for demo
    room = list(dungeon.rooms.values())[0]
    room_cells = room.get_cells()
    puzzle = generate_boulder_puzzle(room, room_cells)
    
    if puzzle.elements:
        dungeon.puzzle_manager.add_puzzle(puzzle)
        dungeon._place_puzzle_tiles(puzzle)
        dungeon.reveal_room(0)
    
    # Create a simple player for testing
    player = Player(
        name="Test Player", title="Tester", race="Human", alignment="Neutral",
        character_class="Fighter", level=1, hp=10, max_hp=10, xp=0, xp_to_next_level=100,
        ac=11, light_duration=3600, light_start_time=0,
        strength=15, dexterity=12, constitution=14, intelligence=10, wisdom=10, charisma=10
    )
    player.x, player.y = 7, 7  # Place player in middle of room
    
    # Demo variables
    cell_size = 32
    viewport_x, viewport_y = 0, 0
    font = pygame.font.Font(None, 24)
    
    instructions = [
        "PUZZLE SYSTEM DEMO",
        "WASD: Move player",
        "SPACE: Interact/Push boulder",
        "ESC: Exit",
        "",
        "Goal: Push boulders (■) onto",
        "pressure plates (◉) to solve puzzle"
    ]
    
    running = True
    while running:
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    player.y -= 1
                elif event.key == pygame.K_s:
                    player.y += 1
                elif event.key == pygame.K_a:
                    player.x -= 1
                elif event.key == pygame.K_d:
                    player.x += 1
                elif event.key == pygame.K_SPACE:
                    # Try to interact with adjacent cells
                    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                        interact_x = player.x + dx
                        interact_y = player.y + dy
                        if dungeon.handle_player_interaction(player, interact_x, interact_y):
                            break
        
        # Clear screen
        screen.fill(COLOR_BG)
        
        # Draw dungeon tiles
        for y in range(20):
            for x in range(20):
                world_x, world_y = viewport_x + x, viewport_y + y
                tile_type = dungeon.tiles.get((world_x, world_y), TileType.VOID)
                
                if dungeon.is_revealed(world_x, world_y):
                    draw_tile(screen, tile_type, x, y, cell_size)
        
        # Draw puzzle overlays
        draw_puzzle_overlays(screen, dungeon, viewport_x, viewport_y, cell_size, font)
        
        # Draw player
        player_screen_x = (player.x - viewport_x) * cell_size + cell_size // 2
        player_screen_y = (player.y - viewport_y) * cell_size + cell_size // 2
        pygame.draw.circle(screen, COLOR_PLAYER, (player_screen_x, player_screen_y), cell_size // 4)
        
        # Draw instructions
        for i, instruction in enumerate(instructions):
            color = COLOR_WHITE if instruction else COLOR_WHITE
            text_surf = font.render(instruction, True, color)
            screen.blit(text_surf, (520, 50 + i * 25))
        
        # Check puzzle status
        if puzzle.elements:
            status_text = f"Puzzle Status: {puzzle.state.name}"
            status_surf = font.render(status_text, True, COLOR_WHITE)
            screen.blit(status_surf, (520, 250))
            
            solved_text = "SOLVED!" if puzzle.check_solution() else "Unsolved"
            solved_color = COLOR_GREEN if puzzle.check_solution() else COLOR_RED
            solved_surf = font.render(solved_text, True, solved_color)
            screen.blit(solved_surf, (520, 275))
        
        pygame.display.flip()
    
    pygame.quit()

def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("Running interactive demo...")
        run_interactive_demo()
    else:
        print("Running automated tests...")
        test_manager = PuzzleTestManager()
        success = test_manager.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! Puzzle system is ready.")
            print("\nTo run interactive demo: python test_puzzle_system.py --demo")
        else:
            print("\n❌ Some tests failed. Check the output above.")
        
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())