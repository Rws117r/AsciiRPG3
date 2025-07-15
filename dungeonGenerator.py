import pygame
import json
import random
import math

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# --- DEBUGGER FLAG ---
# Set to True to see detailed corridor generation output in the console
DEBUG_MODE = True

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50) # Darker gray for grid
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Dungeon parameters
NUM_ROOMS = 10
MIN_ROOM_SIZE = 5
MAX_ROOM_SIZE = 10
TILE_SIZE = 20
WORLD_WIDTH = 50
WORLD_HEIGHT = 50

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

class Room:
    """
    A class to represent a room or a corridor in the dungeon.
    """
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.w = w
        self.h = h
        self.connected_to = []
        self.ending = False

    def center(self):
        """
        Returns the center of the room.
        """
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersects(self, other):
        """
        Returns true if this room intersects with another room, with a buffer.
        """
        return (self.x1 <= other.x2 + 2 and self.x2 >= other.x1 - 2 and
                self.y1 <= other.y2 + 2 and self.y2 >= other.y1 - 2)

    def get_connection_points(self):
        """Returns a list of valid connection points on the room's perimeter, one tile OUTSIDE the room."""
        points = []
        # Top and bottom edges (excluding corners)
        for x in range(self.x1 + 1, self.x2 - 1):
            points.append(((x, self.y1 - 1), (0, -1))) # Point above top edge, dir is North
            points.append(((x, self.y2),     (0, 1)))  # Point below bottom edge, dir is South
        # Left and right edges (excluding corners)
        for y in range(self.y1 + 1, self.y2 - 1):
            points.append(((self.x1 - 1, y), (-1, 0))) # Point left of left edge, dir is West
            points.append(((self.x2, y),     (1, 0)))  # Point right of right edge, dir is East
        return points

class Door:
    """A class to represent a door or stairwell."""
    def __init__(self, x, y, dx, dy, door_type):
        self.x = x
        self.y = y
        self.dir = {'x': dx, 'y': dy}
        self.type = door_type

    def to_dict(self):
        """Converts the door object to a dictionary for JSON serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "dir": self.dir,
            "type": self.type
        }

def create_rooms(rooms):
    """
    Creates a list of non-overlapping rooms, with the first room containing (0,0).
    """
    w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
    h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
    x = -random.randint(1, w - 2)
    y = -random.randint(1, h - 2)
    start_room = Room(x, y, w, h)
    rooms.append(start_room)

    for _ in range(NUM_ROOMS - 1):
        for i in range(100):
            w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            x = random.randint(-WORLD_WIDTH // 2, WORLD_WIDTH // 2 - w)
            y = random.randint(-WORLD_HEIGHT // 2, WORLD_HEIGHT // 2 - h)
            new_room = Room(x, y, w, h)
            if not any(new_room.intersects(other) for other in rooms):
                rooms.append(new_room)
                break

def create_dungeon_layout(main_rooms):
    """
    Creates corridors and doors to connect all rooms, and returns the final list of doors.
    This function modifies the main_rooms list by adding corridor rects.
    """
    if DEBUG_MODE: print("--- Starting Dungeon Layout Generation (Door-only Corridors) ---")
    
    doors = []
    all_large_rooms = main_rooms[:]
    
    # Create a list of all possible pairs of rooms
    room_pairs = []
    for i in range(len(all_large_rooms)):
        for j in range(i + 1, len(all_large_rooms)):
            room_pairs.append((all_large_rooms[i], all_large_rooms[j]))
            
    # Sort pairs by distance between their centers
    room_pairs.sort(key=lambda pair: math.hypot(pair[0].center()[0] - pair[1].center()[0], pair[0].center()[1] - pair[1].center()[1]))

    # Limit the maximum distance for connections to avoid overly long corridors
    MAX_CONNECTION_DISTANCE = 15

    for room1, room2 in room_pairs:
        # If both rooms are already connected, skip
        if room1 in room2.connected_to:
            continue

        # Check if rooms are too far apart
        center_distance = math.hypot(room1.center()[0] - room2.center()[0], room1.center()[1] - room2.center()[1])
        if center_distance > MAX_CONNECTION_DISTANCE:
            continue

        points1 = room1.get_connection_points()
        points2 = room2.get_connection_points()
        
        best_connection = None
        best_dist = float('inf')

        # Find the best connection (straight line or L-shaped)
        for p1_data in points1:
            for p2_data in points2:
                p1, p1_dir = p1_data
                p2, p2_dir = p2_data

                # Check for straight-line opposing doors (e.g., East facing West)
                if p1_dir[0] == -p2_dir[0] and p1_dir[1] == -p2_dir[1]:
                    # Check for horizontal or vertical alignment
                    if p1[1] == p2[1] or p1[0] == p2[0]:
                        dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                        if dist < best_dist and dist >= 2:  # Minimum distance to avoid adjacent rooms
                            best_dist = dist
                            best_connection = (p1_data, p2_data, 'straight')
                
                # Check for L-shaped corridors (perpendicular directions)
                elif (p1_dir[0] == 0 and p2_dir[1] == 0) or (p1_dir[1] == 0 and p2_dir[0] == 0):
                    # Calculate L-shaped distance
                    dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
                    if dist < best_dist and dist >= 3:  # Minimum distance for L-shape
                        best_dist = dist
                        best_connection = (p1_data, p2_data, 'L-shaped')
        
        if best_connection:
            p1_data, p2_data, corridor_type = best_connection
            p1, p1_dir = p1_data
            p2, p2_dir = p2_data

            if DEBUG_MODE:
                print(f"\nConnecting Room at {room1.center()} to Room at {room2.center()}")
                print(f"  -> {corridor_type} connection: {p1} to {p2} (distance: {best_dist})")

            # Create doors at the connection points
            doors.append(Door(p1[0], p1[1], -p1_dir[0], -p1_dir[1], 1))  # Standard door
            doors.append(Door(p2[0], p2[1], -p2_dir[0], -p2_dir[1], 1))  # Standard door

            if corridor_type == 'straight':
                # Create a single straight corridor rectangle that includes the door positions
                x1, y1 = p1
                x2, y2 = p2
                
                if x1 == x2:  # Vertical corridor
                    start_y = min(y1, y2)
                    end_y = max(y1, y2)
                    corridor_height = end_y - start_y + 1
                    main_rooms.append(Room(x1, start_y, 1, corridor_height))
                    if DEBUG_MODE:
                        print(f"    -> Added vertical corridor at ({x1}, {start_y}) size 1x{corridor_height}")
                
                elif y1 == y2:  # Horizontal corridor
                    start_x = min(x1, x2)
                    end_x = max(x1, x2)
                    corridor_width = end_x - start_x + 1
                    main_rooms.append(Room(start_x, y1, corridor_width, 1))
                    if DEBUG_MODE:
                        print(f"    -> Added horizontal corridor at ({start_x}, {y1}) size {corridor_width}x1")
            
            elif corridor_type == 'L-shaped':
                # Create L-shaped corridor with junction
                x1, y1 = p1
                x2, y2 = p2
                
                # Choose junction point (prefer simpler paths)
                junction_x = x2
                junction_y = y1
                
                if DEBUG_MODE:
                    print(f"    -> Creating L-corridor via junction ({junction_x}, {junction_y})")
                
                # Create horizontal segment from p1 to junction
                if x1 != junction_x:
                    start_x = min(x1, junction_x)
                    end_x = max(x1, junction_x)
                    h_corridor_width = end_x - start_x + 1
                    main_rooms.append(Room(start_x, y1, h_corridor_width, 1))
                    if DEBUG_MODE:
                        print(f"    -> Added horizontal segment at ({start_x}, {y1}) size {h_corridor_width}x1")
                
                # Create vertical segment from junction to p2
                if y1 != y2:
                    start_y = min(y1, y2)
                    end_y = max(y1, y2)
                    v_corridor_height = end_y - start_y + 1
                    main_rooms.append(Room(junction_x, start_y, 1, v_corridor_height))
                    if DEBUG_MODE:
                        print(f"    -> Added vertical segment at ({junction_x}, {start_y}) size 1x{v_corridor_height}")
                
                # Add open passage at junction if it's not already covered by the segments
                if x1 != junction_x and y1 != y2:
                    doors.append(Door(junction_x, junction_y, 0, 1, 2))  # Open passage at junction
                    if DEBUG_MODE:
                        print(f"    -> Added open passage at junction ({junction_x}, {junction_y})")

            room1.connected_to.append(room2)
            room2.connected_to.append(room1)

    # Ensure all rooms are connected using a minimum spanning tree approach
    connected_rooms = set([all_large_rooms[0]]) if all_large_rooms else set()
    unconnected_rooms = set(all_large_rooms[1:]) if len(all_large_rooms) > 1 else set()

    while unconnected_rooms:
        best_connection = None
        best_dist = float('inf')
        
        for connected_room in connected_rooms:
            for unconnected_room in unconnected_rooms:
                # Skip if already connected
                if connected_room in unconnected_room.connected_to:
                    continue
                    
                points1 = connected_room.get_connection_points()
                points2 = unconnected_room.get_connection_points()
                
                for p1_data in points1:
                    for p2_data in points2:
                        p1, p1_dir = p1_data
                        p2, p2_dir = p2_data

                        # Check for straight-line opposing doors and alignment
                        if (p1_dir[0] == -p2_dir[0] and p1_dir[1] == -p2_dir[1] and
                            (p1[1] == p2[1] or p1[0] == p2[0])):
                            dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                            if dist < best_dist and dist >= 2:
                                best_dist = dist
                                best_connection = (connected_room, unconnected_room, p1_data, p2_data, 'straight')
                        
                        # Check for L-shaped corridors
                        elif (p1_dir[0] == 0 and p2_dir[1] == 0) or (p1_dir[1] == 0 and p2_dir[0] == 0):
                            dist = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
                            if dist < best_dist and dist >= 3:
                                best_dist = dist
                                best_connection = (connected_room, unconnected_room, p1_data, p2_data, 'L-shaped')
        
        if best_connection:
            room1, room2, p1_data, p2_data, corridor_type = best_connection
            p1, p1_dir = p1_data
            p2, p2_dir = p2_data
            
            if DEBUG_MODE:
                print(f"\nForced connection for connectivity: {room1.center()} to {room2.center()}")
                print(f"  -> {corridor_type} connection: {p1} to {p2}")
            
            # Create doors
            doors.append(Door(p1[0], p1[1], -p1_dir[0], -p1_dir[1], 1))  # Standard door
            doors.append(Door(p2[0], p2[1], -p2_dir[0], -p2_dir[1], 1))  # Standard door
            
            if corridor_type == 'straight':
                # Create straight corridor rectangle that includes the door positions
                x1, y1 = p1
                x2, y2 = p2
                
                if x1 == x2:  # Vertical corridor
                    start_y = min(y1, y2)
                    end_y = max(y1, y2)
                    corridor_height = end_y - start_y + 1
                    main_rooms.append(Room(x1, start_y, 1, corridor_height))
                elif y1 == y2:  # Horizontal corridor
                    start_x = min(x1, x2)
                    end_x = max(x1, x2)
                    corridor_width = end_x - start_x + 1
                    main_rooms.append(Room(start_x, y1, corridor_width, 1))
            
            elif corridor_type == 'L-shaped':
                # Create L-shaped corridor with junction
                x1, y1 = p1
                x2, y2 = p2
                junction_x = x2
                junction_y = y1
                
                # Create horizontal segment from p1 to junction
                if x1 != junction_x:
                    start_x = min(x1, junction_x)
                    end_x = max(x1, junction_x)
                    h_corridor_width = end_x - start_x + 1
                    main_rooms.append(Room(start_x, y1, h_corridor_width, 1))
                
                # Create vertical segment from junction to p2
                if y1 != y2:
                    start_y = min(y1, y2)
                    end_y = max(y1, y2)
                    v_corridor_height = end_y - start_y + 1
                    main_rooms.append(Room(junction_x, start_y, 1, v_corridor_height))
                
                # Add open passage at junction
                if x1 != junction_x and y1 != y2:
                    doors.append(Door(junction_x, junction_y, 0, 1, 2))  # Open passage at junction
            
            # Update connection tracking
            room1.connected_to.append(room2)
            room2.connected_to.append(room1)
            connected_rooms.add(room2)
            unconnected_rooms.remove(room2)
        else:
            # If no valid connection found, connect to closest room regardless of alignment
            if DEBUG_MODE:
                print("No aligned connections found, breaking to avoid infinite loop")
            break

    # Add stairs and ending flag
    sorted_large_rooms = sorted([r for r in main_rooms if r.w >= MIN_ROOM_SIZE and r.h >= MIN_ROOM_SIZE], 
                               key=lambda r: math.hypot(r.center()[0], r.center()[1]))
    if sorted_large_rooms:
        start_room = sorted_large_rooms[0]
        sx, sy = start_room.center()
        doors.append(Door(sx, sy, 0, 1, 3))  # Stairs up

        end_room = sorted_large_rooms[-1]
        ex, ey = end_room.center()
        doors.append(Door(ex, ey, 0, 1, 7))  # Stairs down
        end_room.ending = True

    if DEBUG_MODE:
        print(f"\nGeneration complete:")
        print(f"  Total rooms (including corridors): {len(main_rooms)}")
        print(f"  Total doors: {len(doors)}")
        print(f"  Large rooms: {len([r for r in main_rooms if r.w >= MIN_ROOM_SIZE])}")
        print(f"  Corridor rectangles: {len([r for r in main_rooms if (r.w == 1 or r.h == 1) and not (r.w >= MIN_ROOM_SIZE and r.h >= MIN_ROOM_SIZE)])}")

    return doors

def draw_grid(screen, camera_offset):
    start_x = - (camera_offset[0] % TILE_SIZE)
    start_y = - (camera_offset[1] % TILE_SIZE)
    for x in range(start_x, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(start_y, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))

def draw_dungeon(screen, rooms, camera_offset):
    for room in rooms:
        draw_x = room.x1 * TILE_SIZE + camera_offset[0]
        draw_y = room.y1 * TILE_SIZE + camera_offset[1]
        
        # Use different colors for different room types
        if room.w == 1 or room.h == 1:
            color = (200, 200, 200)  # Light gray for corridor rectangles
        elif room.ending:
            color = (255, 200, 200)  # Light red for ending room
        else:
            color = WHITE  # White for regular rooms
            
        pygame.draw.rect(screen, color, (draw_x, draw_y, room.w * TILE_SIZE, room.h * TILE_SIZE))
        pygame.draw.rect(screen, GRAY, (draw_x, draw_y, room.w * TILE_SIZE, room.h * TILE_SIZE), 1)

def draw_doors(screen, doors, camera_offset):
    for door in doors:
        color = DOOR_COLORS.get(door.type, WHITE)
        draw_x = door.x * TILE_SIZE + camera_offset[0]
        draw_y = door.y * TILE_SIZE + camera_offset[1]
        if door.type in [3, 7, 8]:
             pygame.draw.rect(screen, color, (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
        else:
            pygame.draw.rect(screen, color, (draw_x + TILE_SIZE/4, draw_y + TILE_SIZE/4, TILE_SIZE/2, TILE_SIZE/2))

def draw_start_marker(screen, camera_offset):
    marker_x = camera_offset[0]
    marker_y = camera_offset[1]
    pygame.draw.line(screen, GREEN, (marker_x, marker_y - 5), (marker_x, marker_y + 5), 2)
    pygame.draw.line(screen, GREEN, (marker_x - 5, marker_y), (marker_x + 5, marker_y), 2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Generator (Use Arrow Keys to Pan)")

    rooms = []
    create_rooms(rooms)
    doors = create_dungeon_layout(rooms)

    camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
    camera_speed = 10

    # Prepare rects for JSON, adding the 'ending' flag where appropriate
    rects_data = []
    for r in rooms:
        rect_dict = {"x": r.x1, "y": r.y1, "w": r.w, "h": r.h}
        if r.ending:
            rect_dict["ending"] = True
        rects_data.append(rect_dict)

    dungeon_data = {
        "version": "12.0.0",
        "title": "Dungeon with Door-only Corridors",
        "story": "A dungeon where corridors only occupy door positions and connecting tiles.",
        "rects": rects_data,
        "doors": [d.to_dict() for d in doors],
        "notes": [],
        "columns": [],
        "water": []
    }

    with open("dungeon.json", "w") as outfile:
        json.dump(dungeon_data, outfile, indent=2)
        print("dungeon.json has been generated with the fixed corridor logic.")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: camera_offset[0] += camera_speed
        if keys[pygame.K_RIGHT]: camera_offset[0] -= camera_speed
        if keys[pygame.K_UP]: camera_offset[1] += camera_speed
        if keys[pygame.K_DOWN]: camera_offset[1] -= camera_speed

        screen.fill(BLACK)
        draw_grid(screen, camera_offset)
        draw_dungeon(screen, rooms, camera_offset)
        draw_doors(screen, doors, camera_offset)
        draw_start_marker(screen, camera_offset)
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()