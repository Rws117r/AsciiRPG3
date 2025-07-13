# main.py - Main entry point and game loop
import pygame
import sys
from game_manager import GameManager
from game_constants import *

def main():
    """Main entry point for the dungeon crawler game."""
    pygame.init()
    
    # Initialize display
    initial_width = INITIAL_VIEWPORT_WIDTH * int(BASE_CELL_SIZE * DEFAULT_ZOOM)
    initial_height = INITIAL_VIEWPORT_HEIGHT * int(BASE_CELL_SIZE * DEFAULT_ZOOM)
    screen = pygame.display.set_mode((initial_width, initial_height + HUD_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Dungeon Explorer")
    
    # Initialize game manager
    game_manager = GameManager(screen)
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    try:
        while running:
            dt = clock.tick(60)
            dt_seconds = dt / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    # Let game manager handle all other events
                    result = game_manager.handle_event(event)
                    if result == "quit":
                        running = False
            
            # Update game state
            game_manager.update(dt_seconds)
            
            # Render
            game_manager.render()
            
            pygame.display.flip()
    
    except KeyboardInterrupt:
        print("Game interrupted by user")
    except Exception as e:
        print(f"Game error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()