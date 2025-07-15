# rendering_coordinator.py - Rendering pipeline coordination with examination system
import pygame
from typing import Optional, List
from game_constants import *
from rendering_engine import *
from ui_systems import *
from dungeon_classes import DungeonExplorer
from character_creation import Player
from combat_coordinator import CombatCoordinator
from combat_effects import draw_sprite_with_flash
from combat_system import draw_combat_ui, draw_health_bars

class RenderingCoordinator:
    """Coordinates all rendering operations and manages the rendering pipeline."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        
        # Initialize fonts
        self._setup_fonts()
        
        # Rendering state
        self.viewport_x = 0
        self.viewport_y = 0
        self.viewport_width_cells = 0
        self.viewport_height_cells = 0
        self.cell_size = 0
        self.player_font = None
        self.spell_cursor_font = None
        
        # Game world references
        self.dungeon: Optional[DungeonExplorer] = None
        self.player: Optional[Player] = None
        self.player_pos = (0, 0)
        
        # UI state for main menu
        self.main_menu_button_rect = None
    
    def _setup_fonts(self):
        """Initialize all fonts used for rendering."""
        self.hud_font_large = pygame.font.Font(FONT_FILE, 28)
        self.hud_font_medium = pygame.font.Font(FONT_FILE, 20)
        self.hud_font_small = pygame.font.Font(FONT_FILE, 14)
        self.coords_font = pygame.font.Font(FONT_FILE, 16)
        self.timer_font = pygame.font.Font(FONT_FILE, 22)
        self.spell_menu_font = pygame.font.Font(FONT_FILE, 20)
    
    def update_screen(self, screen: pygame.Surface):
        """Update screen reference when resolution changes."""
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
    
    def setup_world(self, dungeon: DungeonExplorer, player: Player, player_pos: tuple):
        """Setup world references for rendering."""
        self.dungeon = dungeon
        self.player = player
        self.player_pos = player_pos
    
    def update(self, dt_seconds: float, player_pos: tuple, zoom_level: float):
        """Update rendering state."""
        self.player_pos = player_pos
        
        # Update rendering calculations based on zoom
        self.cell_size = int(BASE_CELL_SIZE * zoom_level)
        self.player_font = pygame.font.Font(FONT_FILE, max(8, int(BASE_FONT_SIZE * zoom_level)))
        self.spell_cursor_font = pygame.font.Font(FONT_FILE, self.cell_size)
        
        # Calculate viewport dimensions
        game_area_height = self.screen_height - HUD_HEIGHT
        self.viewport_width_cells = self.screen_width // self.cell_size
        self.viewport_height_cells = game_area_height // self.cell_size
        
        # Calculate viewport position (centered on player)
        self.viewport_x = player_pos[0] - self.viewport_width_cells // 2
        self.viewport_y = player_pos[1] - self.viewport_height_cells // 2
    
    def render_main_menu(self):
        """Render the main menu."""
        self.main_menu_button_rect = draw_main_menu(self.screen, self.hud_font_large, self.hud_font_medium)
    
    def get_main_menu_button_rect(self):
        """Get the main menu button rect for click detection."""
        return self.main_menu_button_rect
    
    def render_game(self, player: Player, player_pos: tuple, dungeon: DungeonExplorer, 
                   combat_coordinator: CombatCoordinator, zoom_level: float):
        """Render the main game view."""
        self.screen.fill(COLOR_BG)
        
        # Create viewport surface
        game_area_height = self.screen_height - HUD_HEIGHT
        viewport_surface = pygame.Surface((self.screen_width, game_area_height))
        viewport_surface.fill(COLOR_BG)
        
        # Render world
        self._render_world(viewport_surface, dungeon)
        
        # Render entities
        self._render_monsters(viewport_surface, dungeon, combat_coordinator.get_effects_manager())
        self._render_player(viewport_surface, player_pos, combat_coordinator.get_effects_manager())
        
        # Render combat UI
        if combat_coordinator.is_in_combat():
            self._render_combat_elements(viewport_surface, combat_coordinator.get_combat_manager())
        
        # Render effects
        combat_coordinator.get_effects_manager().draw_floating_texts(
            viewport_surface, self.viewport_x, self.viewport_y, self.cell_size
        )
        
        # Blit viewport to screen
        self.screen.blit(viewport_surface, (0, 0))
        
        # Render screen effects
        combat_coordinator.get_effects_manager().draw_screen_flash(self.screen)
        
        # Render UI overlays
        self._render_ui_overlays(player)
        
        # Render combat instructions if in combat
        if combat_coordinator.is_in_combat():
            self._render_combat_instructions()
    
    def render_inventory(self, player: Player, containers: List, selected_index: int):
        """Render inventory screen."""
        draw_inventory_screen(self.screen, player, selected_index, 
                            self.hud_font_medium, self.hud_font_small)
    
    def render_equipment(self, player: Player, selected_slot: str, 
                        selection_mode: bool, selection_index: int):
        """Render equipment screen."""
        if selection_mode:
            draw_equipment_screen(self.screen, player, selected_slot, 
                                self.hud_font_medium, self.hud_font_small)
            show_equipment_selection(self.screen, player, selected_slot, selection_index, 
                                   self.hud_font_medium, self.hud_font_small)
        else:
            draw_equipment_screen(self.screen, player, selected_slot, 
                                self.hud_font_medium, self.hud_font_small)
    
    def render_spell_menu(self, player: Player):
        """Render spell menu."""
        # For now, render a simple spell menu
        spells = ["Fireball", "Magic Missile", "Invisibility"]
        draw_spell_menu(self.screen, self.spell_menu_font, spells)
    
    def render_spell_targeting(self, player: Player, player_pos: tuple, 
                              spell_name: str, target_pos: tuple):
        """Render spell targeting mode."""
        # This would need to be implemented with the main game rendering
        # plus targeting overlay
        pass
    
    def _render_world(self, surface: pygame.Surface, dungeon: DungeonExplorer):
        """Render the dungeon world (tiles, walls, terrain)."""
        # Draw tiles
        for screen_cell_y in range(self.viewport_height_cells + 2):
            for screen_cell_x in range(self.viewport_width_cells + 2):
                world_x = self.viewport_x + screen_cell_x
                world_y = self.viewport_y + screen_cell_y
                
                tile_type = dungeon.tiles.get((world_x, world_y), TileType.VOID)
                
                # Check visibility
                if dungeon.is_revealed(world_x, world_y):
                    draw_tile(surface, tile_type, screen_cell_x, screen_cell_y, self.cell_size)
        
        # Draw terrain features
        draw_terrain_features(surface, dungeon, self.viewport_x, self.viewport_y, self.cell_size)
        
        # Draw walls
        draw_boundary_walls(surface, dungeon, self.viewport_x, self.viewport_y, 
                          self.cell_size, self.viewport_width_cells, self.viewport_height_cells)
    
    def _render_monsters(self, surface: pygame.Surface, dungeon: DungeonExplorer, effects_manager):
        """Render all monsters with effects."""
        for monster in dungeon.monsters:
            if dungeon.is_revealed(monster.x, monster.y):
                monster_screen_x = (monster.x - self.viewport_x) * self.cell_size + (self.cell_size // 2)
                monster_screen_y = (monster.y - self.viewport_y) * self.cell_size + (self.cell_size // 2)
                
                # Get monster character
                if hasattr(monster, 'template') and hasattr(monster.template, 'ascii_char'):
                    monster_char = monster.template.ascii_char
                else:
                    monster_char = UI_ICONS["MONSTER"]
                
                # Draw monster with flash effects
                draw_sprite_with_flash(
                    surface, monster_char, self.player_font,
                    (monster_screen_x, monster_screen_y), COLOR_MONSTER,
                    effects_manager, monster.x, monster.y
                )
    
    def _render_player(self, surface: pygame.Surface, player_pos: tuple, effects_manager):
        """Render the player character with effects."""
        player_screen_x = (self.viewport_width_cells // 2) * self.cell_size + (self.cell_size // 2)
        player_screen_y = (self.viewport_height_cells // 2) * self.cell_size + (self.cell_size // 2)
        
        draw_sprite_with_flash(
            surface, '@', self.player_font,
            (player_screen_x, player_screen_y), COLOR_PLAYER,
            effects_manager, player_pos[0], player_pos[1]
        )
    
    def _render_combat_elements(self, surface: pygame.Surface, combat_manager):
        """Render combat-specific UI elements."""
        draw_health_bars(surface, combat_manager, self.viewport_x, self.viewport_y, 
                        self.cell_size, self.hud_font_small)
        
        # Draw combat UI on main screen (will be rendered later)
        draw_combat_ui(self.screen, combat_manager, self.hud_font_medium, self.hud_font_small)
    
    def _render_ui_overlays(self, player: Player):
        """Render UI overlays (coordinates, timer, HUD)."""
        # Coordinates
        coord_text = f"({self.player_pos[0]}, {self.player_pos[1]})"
        coord_surf = self.coords_font.render(coord_text, True, COLOR_WALL)
        self.screen.blit(coord_surf, (10, 10))
        
        # Timer
        draw_timer_box(self.screen, player, self.timer_font)
        
        # HUD
        draw_hud(self.screen, player, self.hud_font_large, self.hud_font_medium, self.hud_font_small)
    
    def _render_combat_instructions(self):
        """Render combat instruction text."""
        instruction_text = "Move into enemy to attack • SPACE to defend/wait"
        inst_surf = self.hud_font_small.render(instruction_text, True, COLOR_WHITE)
        inst_rect = inst_surf.get_rect(centerx=self.screen_width//2, 
                                     bottom=self.screen_height - HUD_HEIGHT - 10)
        
        # Background for visibility
        bg_rect = inst_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_rect)
        self.screen.blit(inst_surf, inst_rect)