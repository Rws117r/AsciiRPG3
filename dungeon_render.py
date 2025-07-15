import pygame
import json
import os

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50) # Darker gray for grid
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128) # Color for water
BROWN = (139, 69, 19)   # Color for columns

# Dungeon parameters
TILE_SIZE = 20

# Door Types
DOOR_COLORS = {
    1: YELLOW, # Standard Door
    2: WHITE,  # Open Door / Passage
    3: BLUE,   # Stairs (Up)
    5: RED,    # Locked Door
    6: GRAY,   # Secret Door
    7: BLUE,   # Stairs (Down)
    8: BLUE,   # Stairs (Lower Level)
}

def load_dungeon_data(filename="dungeon.json"):
    """Loads dungeon data from a JSON file."""
    if not os.path.exists(filename):
        print(f"Error: Dungeon file '{filename}' not found.")
        return None
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filename}'.")
        return None

def draw_grid(screen, camera_offset):
    """Draws the grid on the screen."""
    start_x = - (camera_offset[0] % TILE_SIZE)
    start_y = - (camera_offset[1] % TILE_SIZE)
    for x in range(start_x, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(start_y, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

def draw_dungeon(screen, dungeon_data, camera_offset):
    """Draws all elements of the dungeon."""
    if not dungeon_data:
        return

    # Find all corridor tiles by taking the set of all door locations and subtracting room tiles
    all_tiles = set()
    room_tiles = set()
    
    for rect in dungeon_data.get("rects", []):
        for x in range(rect['x'], rect['x'] + rect['w']):
            for y in range(rect['y'], rect['y'] + rect['h']):
                room_tiles.add((x, y))
                all_tiles.add((x,y))

    # A simple way to get corridor tiles is to assume any door not on a stair is connected to one
    corridor_tiles = set()
    for door in dungeon_data.get("doors", []):
        if door['type'] not in [3, 7, 8]: # Exclude stairs
             # The tile just outside the door is a corridor
             corridor_tiles.add((door['x'] + door['dir']['x'], door['y'] + door['dir']['y']))


    # Draw water
    for tile in dungeon_data.get("water", []):
        draw_x = tile['x'] * TILE_SIZE + camera_offset[0]
        draw_y = tile['y'] * TILE_SIZE + camera_offset[1]
        pygame.draw.rect(screen, BLUE, (draw_x, draw_y, TILE_SIZE, TILE_SIZE))

    # Draw rooms and corridors
    for x, y in all_tiles.union(corridor_tiles):
         draw_x = x * TILE_SIZE + camera_offset[0]
         draw_y = y * TILE_SIZE + camera_offset[1]
         pygame.draw.rect(screen, WHITE, (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
    
    # Draw room borders
    for rect in dungeon_data.get("rects", []):
        draw_x = rect['x'] * TILE_SIZE + camera_offset[0]
        draw_y = rect['y'] * TILE_SIZE + camera_offset[1]
        pygame.draw.rect(screen, GRAY, (draw_x, draw_y, rect['w'] * TILE_SIZE, rect['h'] * TILE_SIZE), 1)

    # Draw columns
    for tile in dungeon_data.get("columns", []):
        draw_x = tile['x'] * TILE_SIZE + camera_offset[0]
        draw_y = tile['y'] * TILE_SIZE + camera_offset[1]
        pygame.draw.rect(screen, BROWN, (draw_x, draw_y, TILE_SIZE, TILE_SIZE))


def draw_doors(screen, doors_data, camera_offset):
    """Draws doors and stairs on the map."""
    for door in doors_data:
        color = DOOR_COLORS.get(door['type'])
        if color:
            draw_x = door['x'] * TILE_SIZE + camera_offset[0]
            draw_y = door['y'] * TILE_SIZE + camera_offset[1]
            if door['type'] in [3, 7, 8]:
                 pygame.draw.rect(screen, color, (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
            else:
                pygame.draw.rect(screen, color, (draw_x + TILE_SIZE/4, draw_y + TILE_SIZE/4, TILE_SIZE/2, TILE_SIZE/2))

def draw_start_marker(screen, camera_offset):
    """Draws a marker at the (0,0) world coordinate."""
    marker_x = camera_offset[0]
    marker_y = camera_offset[1]
    pygame.draw.line(screen, GREEN, (marker_x, marker_y - 5), (marker_x, marker_y + 5), 2)
    pygame.draw.line(screen, GREEN, (marker_x - 5, marker_y), (marker_x + 5, marker_y), 2)

def main():
    """Main function to run the dungeon viewer."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Viewer (Looking for dungeon_active.json)")

    dungeon_data = load_dungeon_data()

    camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
    camera_speed = 10

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: # Press 'R' to reload the dungeon file
                    print("Reloading dungeon_active.json...")
                    dungeon_data = load_dungeon_data()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: camera_offset[0] += camera_speed
        if keys[pygame.K_RIGHT]: camera_offset[0] -= camera_speed
        if keys[pygame.K_UP]: camera_offset[1] += camera_speed
        if keys[pygame.K_DOWN]: camera_offset[1] -= camera_speed

        screen.fill(BLACK)
        draw_grid(screen, camera_offset)
        
        if dungeon_data:
            draw_dungeon(screen, dungeon_data, camera_offset)
            draw_doors(screen, dungeon_data.get("doors", []), camera_offset)
        
        draw_start_marker(screen, camera_offset)
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()
