# main.py - Updated for ECS Phase 2

import pygame
import sys
from ecs_game_manager import ECSGameManager

def main():
    """Main entry point for the ECS dungeon crawler game."""
    print("🚀 Starting ECS Dungeon Crawler - Phase 2")
    print("=" * 50)
    
    # Initialize Pygame
    pygame.init()
    
    # Initialize display
    screen_width = 1024
    screen_height = 768
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("ECS Dungeon Crawler - Phase 2")
    
    # Initialize ECS game manager
    game_manager = ECSGameManager(screen)
    game_manager.load_dungeon_data()  # Will warn if dungeon.json not found
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    print("🎮 Entering main game loop...")
    print("   Controls: SPACE/ENTER to start, WASD to move, ESC to quit/menu")
    
    try:
        while running:
            dt = clock.tick(60)
            dt_seconds = dt / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    # Let ECS game manager handle events
                    if not game_manager.handle_event(event):
                        running = False
            
            # Update game state
            game_manager.update(dt_seconds)
            
            # Render
            game_manager.render()
            pygame.display.flip()
            
            # Print debug info occasionally (every 5 seconds)
            if pygame.time.get_ticks() % 5000 < 16:  # Roughly every 5 seconds
                debug_info = game_manager.get_debug_info()
                if debug_info['game_state'] == 'PLAYING':
                    print(f"   🔧 Debug: {debug_info['world_info']['entity_count']} entities, "
                          f"Player at {debug_info.get('player_position', 'unknown')}")
    
    except KeyboardInterrupt:
        print("\n⚠️  Game interrupted by user")
    except Exception as e:
        print(f"\n❌ Game error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean shutdown
        print("\n🔧 Shutting down...")
        game_manager.shutdown()
        pygame.quit()
        print("✅ Game shutdown complete")
        sys.exit()

if __name__ == '__main__':
    main()