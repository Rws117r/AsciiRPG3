# rendering_engine.py - Complete enhanced version with puzzle elements
import pygame
from typing import List, Tuple
from game_constants import *
from dungeon_classes import DungeonExplorer

# --- Spell Range Implementation ---
def get_spell_range_in_cells(spell_name: str) -> int:
    """Convert spell ranges to grid cells (5 feet per cell)"""
    if spell_name in ["Cure Wounds", "Holy Weapon", "Light", "Protection From Evil", 
                      "Burning Hands", "Detect Magic", "Hold Portal", "Mage Armor", "Alarm"]:
        return 1  # Close range (5 feet = 1 cell)
    elif spell_name in ["Turn Undead", "Charm Person", "Floating Disk", "Sleep"]:
        return 6  # Near range (30 feet = 6 cells)
    elif spell_name in ["Magic Missile"]:
        return 20  # Far range (within sight, limited for gameplay)
    else:
        return 1  # Default to close range

def is_valid_spell_target(player_pos: Tuple[int, int], target_pos: Tuple[int, int], 
                         spell_name: str) -> bool:
    """Check if spell target is within range"""
    max_range = get_spell_range_in_cells(spell_name)
    distance = max(abs(target_pos[0] - player_pos[0]), 
                   abs(target_pos[1] - player_pos[1]))
    return distance <= max_range

def draw_spell_range_indicator(surface: pygame.Surface, player_pos: Tuple[int, int], 
                              spell_name: str, viewport_x: int, viewport_y: int, 
                              cell_size: int, viewport_width_cells: int, viewport_height_cells: int):
    """Draw spell range indicator around player"""
    max_range = get_spell_range_in_cells(spell_name)
    player_screen_x = (viewport_width_cells // 2) * cell_size + (cell_size // 2)
    player_screen_y = (viewport_height_cells // 2) * cell_size + (cell_size // 2)
    
    # Create transparent surface for range indicator
    range_size = max_range * cell_size
    if range_size > 0:
        range_surface = pygame.Surface((range_size * 2, range_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(range_surface, (255, 255, 0, 50), 
                          (range_size, range_size), range_size)
        
        range_rect = (player_screen_x - range_size, player_screen_y - range_size)
        surface.blit(range_surface, range_rect)

# --- Enhanced Tile Drawing Functions ---
def draw_tile(surface: pygame.Surface, tile_type: TileType, x: int, y: int, cell_size: int):
    left = x * cell_size
    top = y * cell_size
    center_x = left + cell_size // 2
    center_y = top + cell_size // 2
    
    if tile_type == TileType.VOID:
        pygame.draw.rect(surface, COLOR_VOID, (left, top, cell_size, cell_size))
    
    elif tile_type == TileType.FLOOR or tile_type == TileType.DOOR_OPEN:
        # Draw cream floor for floor, open doors, and passages
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
    
    elif tile_type in [TileType.DOOR_HORIZONTAL, TileType.DOOR_VERTICAL]:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # The outline thickness is 1 to match the floor grid
        outline_thickness = 1
        
        if tile_type == TileType.DOOR_HORIZONTAL:
            door_width = int(cell_size * 0.8)
            door_height = int(cell_size * 0.3)
            door_rect = pygame.Rect(center_x - door_width // 2, center_y - door_height // 2, door_width, door_height)
        else: # DOOR_VERTICAL
            door_width = int(cell_size * 0.3)
            door_height = int(cell_size * 0.8)
            door_rect = pygame.Rect(center_x - door_width // 2, center_y - door_height // 2, door_width, door_height)

        # Draw the filled interior of the door
        pygame.draw.rect(surface, COLOR_DOOR, door_rect)
        # Draw the black outline
        pygame.draw.rect(surface, COLOR_WALL, door_rect, width=outline_thickness)

    elif tile_type in [TileType.STAIRS_HORIZONTAL, TileType.STAIRS_VERTICAL]:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)

        line_thickness = 1
        line_color = COLOR_FLOOR_GRID # Match grid color for subtle effect

        if tile_type == TileType.STAIRS_HORIZONTAL:
            # 3 horizontal lines for stairs in a vertical hallway
            spacing = cell_size // 4
            y1 = top + spacing
            y2 = top + 2 * spacing
            y3 = top + 3 * spacing
            pygame.draw.line(surface, line_color, (left, y1), (left + cell_size, y1), line_thickness)
            pygame.draw.line(surface, line_color, (left, y2), (left + cell_size, y2), line_thickness)
            pygame.draw.line(surface, line_color, (left, y3), (left + cell_size, y3), line_thickness)
        else: # STAIRS_VERTICAL
            # 3 vertical lines for stairs in a horizontal hallway
            spacing = cell_size // 4
            x1 = left + spacing
            x2 = left + 2 * spacing
            x3 = left + 3 * spacing
            pygame.draw.line(surface, line_color, (x1, top), (x1, top + cell_size), line_thickness)
            pygame.draw.line(surface, line_color, (x2, top), (x2, top + cell_size), line_thickness)
            pygame.draw.line(surface, line_color, (x3, top), (x3, top + cell_size), line_thickness)

    elif tile_type == TileType.NOTE:
        # Draw cream floor
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        # Draw grid on floor
        draw_floor_grid(surface, left, top, cell_size)
        # Note indicator (could be enhanced with better graphics)
        note_size = max(2, cell_size // 8)
        note_rect = pygame.Rect(center_x - note_size//2, center_y - note_size//2, note_size, note_size)
        pygame.draw.rect(surface, COLOR_NOTE, note_rect)
    
    # --- PUZZLE ELEMENTS ---
    elif tile_type == TileType.ALTAR:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # Draw altar as a rectangular stone block
        altar_size = int(cell_size * 0.7)
        altar_rect = pygame.Rect(center_x - altar_size // 2, center_y - altar_size // 2, altar_size, altar_size)
        pygame.draw.rect(surface, COLOR_ALTAR, altar_rect)
        pygame.draw.rect(surface, COLOR_WALL, altar_rect, 2)
        
        # Add holy light effect
        light_size = int(cell_size * 0.3)
        light_rect = pygame.Rect(center_x - light_size // 2, center_y - light_size // 2, light_size, light_size)
        pygame.draw.ellipse(surface, COLOR_HOLY_LIGHT, light_rect)
    
    elif tile_type == TileType.BOULDER:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # Draw boulder as a large dark square
        boulder_size = int(cell_size * 0.8)
        boulder_rect = pygame.Rect(center_x - boulder_size // 2, center_y - boulder_size // 2, boulder_size, boulder_size)
        pygame.draw.rect(surface, COLOR_BOULDER, boulder_rect)
        pygame.draw.rect(surface, COLOR_WALL, boulder_rect, 2)
    
    elif tile_type in [TileType.PRESSURE_PLATE, TileType.PRESSURE_PLATE_ACTIVE]:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # Draw pressure plate as a circular element
        plate_radius = int(cell_size * 0.3)
        color = COLOR_PRESSURE_PLATE_ACTIVE if tile_type == TileType.PRESSURE_PLATE_ACTIVE else COLOR_PRESSURE_PLATE
        pygame.draw.circle(surface, color, (center_x, center_y), plate_radius)
        pygame.draw.circle(surface, COLOR_WALL, (center_x, center_y), plate_radius, 2)
    
    elif tile_type in [TileType.GLYPH, TileType.GLYPH_ACTIVE]:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # Draw glyph as a triangular pattern
        color = COLOR_GLYPH_ACTIVE if tile_type == TileType.GLYPH_ACTIVE else COLOR_GLYPH
        glyph_size = int(cell_size * 0.4)
        
        # Draw three dots in triangle formation
        dot_radius = max(2, cell_size // 12)
        offset = glyph_size // 2
        
        # Top dot
        pygame.draw.circle(surface, color, (center_x, center_y - offset), dot_radius)
        # Bottom left dot
        pygame.draw.circle(surface, color, (center_x - offset, center_y + offset // 2), dot_radius)
        # Bottom right dot
        pygame.draw.circle(surface, color, (center_x + offset, center_y + offset // 2), dot_radius)
        
        # If active, add connecting lines
        if tile_type == TileType.GLYPH_ACTIVE:
            line_thickness = max(1, cell_size // 24)
            pygame.draw.line(surface, color, (center_x, center_y - offset), (center_x - offset, center_y + offset // 2), line_thickness)
            pygame.draw.line(surface, color, (center_x, center_y - offset), (center_x + offset, center_y + offset // 2), line_thickness)
            pygame.draw.line(surface, color, (center_x - offset, center_y + offset // 2), (center_x + offset, center_y + offset // 2), line_thickness)
    
    elif tile_type == TileType.BARRIER:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # Draw barrier as vertical red lines
        line_thickness = max(2, cell_size // 12)
        line_spacing = cell_size // 4
        
        for i in range(3):
            line_x = left + line_spacing + (i * line_spacing)
            pygame.draw.line(surface, COLOR_BARRIER, (line_x, top), (line_x, top + cell_size), line_thickness)
    
    elif tile_type == TileType.STAIRS_DOWN:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # Draw stairs down as a square with diagonal lines
        stairs_size = int(cell_size * 0.6)
        stairs_rect = pygame.Rect(center_x - stairs_size // 2, center_y - stairs_size // 2, stairs_size, stairs_size)
        pygame.draw.rect(surface, COLOR_WALL, stairs_rect)
        pygame.draw.rect(surface, COLOR_WHITE, stairs_rect, 2)
        
        # Add downward arrow pattern
        arrow_size = stairs_size // 3
        arrow_points = [
            (center_x, center_y + arrow_size // 2),
            (center_x - arrow_size // 2, center_y - arrow_size // 2),
            (center_x + arrow_size // 2, center_y - arrow_size // 2)
        ]
        pygame.draw.polygon(surface, COLOR_WHITE, arrow_points)
    
    elif tile_type == TileType.CHEST:
        # Draw floor base
        pygame.draw.rect(surface, COLOR_FLOOR, (left, top, cell_size, cell_size))
        draw_floor_grid(surface, left, top, cell_size)
        
        # Draw chest as a brown rectangle
        chest_width = int(cell_size * 0.7)
        chest_height = int(cell_size * 0.5)
        chest_rect = pygame.Rect(center_x - chest_width // 2, center_y - chest_height // 2, chest_width, chest_height)
        pygame.draw.rect(surface, COLOR_CHEST, chest_rect)
        pygame.draw.rect(surface, COLOR_WALL, chest_rect, 2)
        
        # Add lock/handle detail
        handle_size = max(2, cell_size // 16)
        pygame.draw.circle(surface, COLOR_WALL, (center_x, center_y), handle_size)

def draw_puzzle_overlays(surface: pygame.Surface, dungeon: DungeonExplorer, viewport_x: int, viewport_y: int, 
                        cell_size: int, font: pygame.font.Font):
    """Draw puzzle-specific overlays like ASCII symbols"""
    for puzzle in dungeon.puzzle_manager.puzzles.values():
        # Only draw for revealed rooms
        if puzzle.room_id not in dungeon.revealed_rooms:
            continue
        
        # Draw ASCII symbols for puzzle elements
        for element_list in puzzle.elements.values():
            for element in element_list:
                if not dungeon.is_revealed(element.x, element.y):
                    continue
                
                screen_x = (element.x - viewport_x) * cell_size + (cell_size // 2)
                screen_y = (element.y - viewport_y) * cell_size + (cell_size // 2)
                
                # Skip if off-screen
                if (screen_x < -cell_size or screen_x > surface.get_width() + cell_size or
                    screen_y < -cell_size or screen_y > surface.get_height() + cell_size):
                    continue
                
                # Get appropriate symbol and color
                symbol = ""
                color = COLOR_WHITE
                
                if element.element_type == "altar":
                    symbol = UI_ICONS["ALTAR"]
                    color = COLOR_ALTAR
                elif element.element_type == "boulder":
                    symbol = UI_ICONS["BOULDER"]
                    color = COLOR_BOULDER
                elif element.element_type == "pressure_plate":
                    symbol = UI_ICONS["PRESSURE_PLATE"]
                    color = COLOR_PRESSURE_PLATE_ACTIVE if element.active else COLOR_PRESSURE_PLATE
                elif element.element_type == "glyph":
                    symbol = UI_ICONS["GLYPH"]
                    color = COLOR_GLYPH_ACTIVE if element.active else COLOR_GLYPH
                elif element.element_type == "barrier" and element.active:
                    symbol = UI_ICONS["BARRIER"]
                    color = COLOR_BARRIER
                elif element.element_type == "chest":
                    symbol = UI_ICONS["CHEST"]
                    color = COLOR_CHEST
                
                if symbol:
                    # Render the symbol
                    symbol_surf = font.render(symbol, True, color)
                    symbol_rect = symbol_surf.get_rect(center=(screen_x, screen_y))
                    surface.blit(symbol_surf, symbol_rect)

def draw_floor_grid(surface: pygame.Surface, left: int, top: int, cell_size: int):
    """Draw a grid pattern that aligns with character movement"""
    # Very thin lines for the grid
    line_thickness = 1
    
    # The grid should match the cell_size used for character movement
    # Each character movement cell should have its own grid square
    grid_spacing = cell_size  # One grid square = one movement cell
    
    # Draw vertical grid lines at cell boundaries
    # Start from the left edge and draw lines at cell_size intervals
    x = left
    while x <= left + cell_size:
        pygame.draw.line(surface, COLOR_FLOOR_GRID, 
                        (x, top), (x, top + cell_size), line_thickness)
        x += grid_spacing
    
    # Draw horizontal grid lines at cell boundaries
    y = top
    while y <= top + cell_size:
        pygame.draw.line(surface, COLOR_FLOOR_GRID,
                        (left, y), (left + cell_size, y), line_thickness)
        y += grid_spacing

def draw_boundary_walls(surface: pygame.Surface, dungeon: DungeonExplorer, 
                       viewport_x: int, viewport_y: int, cell_size: int,
                       viewport_width_cells: int, viewport_height_cells: int):
    """Draw walls around the perimeter of revealed areas with drop shadow effect"""
    # Make walls much thicker for the hand-drawn aesthetic
    line_thickness = max(4, cell_size // 4)  # Much thicker walls
    shadow_offset = max(2, cell_size // 12)  # Drop shadow offset
    
    # Get all revealed cells  
    revealed_cells = set()
    for room_id in dungeon.revealed_rooms:
        room = dungeon.rooms[room_id]
        for x, y in room.get_cells():
            revealed_cells.add((x, y))
    
    # Also add revealed doors (only if they connect to revealed rooms)
    for door in dungeon.doors:
        # Do not add secret doors to revealed cells for wall drawing purposes
        if door.type == 6 and not door.is_open:
            continue
        if (door.room1_id in dungeon.revealed_rooms or 
            door.room2_id in dungeon.revealed_rooms):
            revealed_cells.add((door.x, door.y))

    # Pre-calculate a set of secret door locations for faster lookup
    secret_horizontal_doors = {(d.x, d.y) for d in dungeon.doors if d.type == 6 and d.is_horizontal and not d.is_open}
    secret_vertical_doors = {(d.x, d.y) for d in dungeon.doors if d.type == 6 and not d.is_horizontal and not d.is_open}
    
    if not revealed_cells:
        return
    
    # Collect all wall segments for both shadow and main walls
    wall_segments = []
    
    # For each revealed cell, check if it's on the boundary and collect wall segments
    for cell_x, cell_y in revealed_cells:
        # Check if this cell is within viewport bounds (with some margin)
        if (cell_x < viewport_x - 1 or cell_x > viewport_x + viewport_width_cells + 1 or
            cell_y < viewport_y - 1 or cell_y > viewport_y + viewport_height_cells + 1):
            continue
        
        # Convert to screen coordinates
        screen_x = (cell_x - viewport_x) * cell_size
        screen_y = (cell_y - viewport_y) * cell_size
        
        # Check each direction for boundaries and collect wall segments
        # Bottom wall (of current cell)
        if (cell_x, cell_y + 1) not in revealed_cells or (cell_x, cell_y + 1) in secret_horizontal_doors:
            start_pos = (screen_x, screen_y + cell_size)
            end_pos = (screen_x + cell_size, screen_y + cell_size)
            wall_segments.append(('horizontal', start_pos, end_pos))
        
        # Top wall (of current cell)
        if (cell_x, cell_y - 1) not in revealed_cells or (cell_x, cell_y) in secret_horizontal_doors:
            start_pos = (screen_x, screen_y)
            end_pos = (screen_x + cell_size, screen_y)
            wall_segments.append(('horizontal', start_pos, end_pos))
        
        # Right wall (of current cell)
        if (cell_x + 1, cell_y) not in revealed_cells or (cell_x + 1, cell_y) in secret_vertical_doors:
            start_pos = (screen_x + cell_size, screen_y)
            end_pos = (screen_x + cell_size, screen_y + cell_size)
            wall_segments.append(('vertical', start_pos, end_pos))
        
        # Left wall (of current cell)
        if (cell_x - 1, cell_y) not in revealed_cells or (cell_x, cell_y) in secret_vertical_doors:
            start_pos = (screen_x, screen_y)
            end_pos = (screen_x, screen_y + cell_size)
            wall_segments.append(('vertical', start_pos, end_pos))
    
    # Extend line segments to fill corners properly
    extended_segments = []
    half_thickness = line_thickness // 2
    
    for orientation, start_pos, end_pos in wall_segments:
        if orientation == 'horizontal':
            # Extend horizontal lines left and right by half thickness
            extended_start = (start_pos[0] - half_thickness, start_pos[1])
            extended_end = (end_pos[0] + half_thickness, end_pos[1])
        else:  # vertical
            # Extend vertical lines up and down by half thickness
            extended_start = (start_pos[0], start_pos[1] - half_thickness)
            extended_end = (end_pos[0], end_pos[1] + half_thickness)
        
        extended_segments.append((extended_start, extended_end))
    
    # Draw drop shadows first (offset down and right)
    for start_pos, end_pos in extended_segments:
        shadow_start = (start_pos[0] + shadow_offset, start_pos[1] + shadow_offset)
        shadow_end = (end_pos[0] + shadow_offset, end_pos[1] + shadow_offset)
        pygame.draw.line(surface, COLOR_WALL_SHADOW, shadow_start, shadow_end, line_thickness)
    
    # Draw main black walls on top
    for start_pos, end_pos in extended_segments:
        pygame.draw.line(surface, COLOR_WALL, start_pos, end_pos, line_thickness)

def draw_terrain_features(surface: pygame.Surface, dungeon: DungeonExplorer,
                         viewport_x: int, viewport_y: int, cell_size: int):
    """Draw water and other terrain features with organic polygon shapes"""
    
    # Collect all visible water tiles
    visible_water = []
    for water in dungeon.water_tiles:
        if dungeon.is_revealed(water.x, water.y):
            screen_x = (water.x - viewport_x) * cell_size
            screen_y = (water.y - viewport_y) * cell_size
            
            # Only include if roughly in viewport (with margin for blob effects)
            if (screen_x > -cell_size * 2 and screen_x < surface.get_width() + cell_size * 2 and
                screen_y > -cell_size * 2 and screen_y < surface.get_height() + cell_size * 2):
                visible_water.append((screen_x + cell_size // 2, screen_y + cell_size // 2, water.x, water.y))
    
    if not visible_water:
        return
    
    # Group connected water tiles into clusters
    water_clusters = group_water_clusters(visible_water, cell_size)
    
    # Draw each cluster as an organic polygon
    for cluster in water_clusters:
        if len(cluster) >= 3:  # Need at least 3 points for a polygon
            draw_organic_water_polygon(surface, cluster, cell_size)
        elif len(cluster) == 2:  # Draw connecting blob for 2 points
            draw_water_connection(surface, cluster, cell_size)
        else:  # Single water tile
            draw_single_water_blob(surface, cluster[0], cell_size)

def group_water_clusters(water_positions: list, cell_size: int):
    """Group nearby water tiles into connected clusters"""
    clusters = []
    unprocessed = water_positions.copy()
    
    while unprocessed:
        # Start new cluster with first unprocessed point
        current_cluster = [unprocessed.pop(0)]
        cluster_changed = True
        
        # Keep adding connected points until no more can be added
        while cluster_changed:
            cluster_changed = False
            to_remove = []
            
            for i, point in enumerate(unprocessed):
                # Check if this point is adjacent to any point in current cluster
                for cluster_point in current_cluster:
                    world_dist = max(abs(point[2] - cluster_point[2]), abs(point[3] - cluster_point[3]))
                    if world_dist <= 1.5:  # Adjacent or diagonal (allowing some tolerance)
                        current_cluster.append(point)
                        to_remove.append(i)
                        cluster_changed = True
                        break
                if cluster_changed:
                    break
            
            # Remove processed points (in reverse order to maintain indices)
            for i in reversed(to_remove):
                unprocessed.pop(i)
        
        clusters.append(current_cluster)
    
    return clusters

def draw_organic_water_polygon(surface: pygame.Surface, cluster: list, cell_size: int):
    """Draw an organic polygon for a cluster of water tiles"""
    if len(cluster) < 3:
        return
    
    # Create organic boundary points around the cluster
    boundary_points = create_organic_boundary(cluster, cell_size)
    
    if len(boundary_points) >= 3:
        # Draw the main water polygon
        pygame.draw.polygon(surface, COLOR_WATER, boundary_points)
        
        # Draw border for depth effect
        border_points = create_organic_boundary(cluster, cell_size, border_offset=3)
        if len(border_points) >= 3:
            pygame.draw.polygon(surface, (80, 120, 160), border_points, 2)

def create_organic_boundary(cluster: list, cell_size: int, border_offset: int = 0):
    """Create organic boundary points around a water cluster using convex hull with organic modifications"""
    if len(cluster) < 3:
        return []
    
    # Extract screen coordinates
    points = [(point[0], point[1]) for point in cluster]
    
    # Calculate the center of the cluster
    center_x = sum(p[0] for p in points) / len(points)
    center_y = sum(p[1] for p in points) / len(points)
    
    # Sort points by angle from center to create a rough hull
    def angle_from_center(point):
        import math
        return math.atan2(point[1] - center_y, point[0] - center_x)
    
    sorted_points = sorted(points, key=angle_from_center)
    
    # Create organic boundary by expanding points outward and adding smoothing
    boundary_points = []
    expansion = cell_size * 0.4 + border_offset  # How much to expand outward
    
    for i, (x, y) in enumerate(sorted_points):
        # Calculate direction from center to this point
        dx = x - center_x
        dy = y - center_y
        dist = (dx * dx + dy * dy) ** 0.5
        
        if dist > 0:
            # Normalize and expand
            nx = dx / dist
            ny = dy / dist
            
            # Add organic variation
            variation = 0.3 + 0.2 * abs((i % 3) - 1)  # Varies between 0.1 and 0.5
            expand_dist = expansion * variation
            
            new_x = x + nx * expand_dist
            new_y = y + ny * expand_dist
            boundary_points.append((int(new_x), int(new_y)))
    
    # Add intermediate points for smoother curves
    smooth_boundary = []
    for i in range(len(boundary_points)):
        current = boundary_points[i]
        next_point = boundary_points[(i + 1) % len(boundary_points)]
        
        smooth_boundary.append(current)
        
        # Add intermediate point for smoother curves
        mid_x = (current[0] + next_point[0]) // 2
        mid_y = (current[1] + next_point[1]) // 2
        smooth_boundary.append((mid_x, mid_y))
    
    return smooth_boundary

def draw_water_connection(surface: pygame.Surface, cluster: list, cell_size: int):
    """Draw connection between two water tiles"""
    if len(cluster) != 2:
        return
    
    point1, point2 = cluster[0], cluster[1]
    
    # Calculate connection parameters
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    dist = (dx * dx + dy * dy) ** 0.5
    
    if dist > 0:
        # Create capsule-like shape
        radius = cell_size * 0.35
        
        # Draw circles at endpoints
        pygame.draw.circle(surface, COLOR_WATER, (point1[0], point1[1]), int(radius))
        pygame.draw.circle(surface, COLOR_WATER, (point2[0], point2[1]), int(radius))
        
        # Draw connecting rectangle
        if dist > radius:
            # Calculate perpendicular vector for rectangle width
            perp_x = -dy / dist * radius
            perp_y = dx / dist * radius
            
            rect_points = [
                (point1[0] + perp_x, point1[1] + perp_y),
                (point1[0] - perp_x, point1[1] - perp_y),
                (point2[0] - perp_x, point2[1] - perp_y),
                (point2[0] + perp_x, point2[1] + perp_y)
            ]
            pygame.draw.polygon(surface, COLOR_WATER, rect_points)

def draw_single_water_blob(surface: pygame.Surface, point, cell_size: int):
    """Draw a single organic water blob"""
    x, y = point[0], point[1]
    radius = int(cell_size * 0.4)
    
    # Draw main blob
    pygame.draw.circle(surface, COLOR_WATER, (x, y), radius)
    
    # Draw border
    pygame.draw.circle(surface, (80, 120, 160), (x, y), radius, 2)