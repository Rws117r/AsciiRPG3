# ecs_render_coordinator.py - ECS-based rendering coordinator (Phase 4)

import pygame
from typing import Dict, List, Tuple, Optional
from ecs_core import World, EntityID, System
from ecs_components import *
from game_constants import *

class ECSRenderCoordinator:
    """Coordinates all ECS-based rendering operations"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        
        # Initialize fonts
        self._setup_fonts()
        
        # Camera and viewport
        self.camera_x = 0
        self.camera_y = 0
        self.cell_size = 32
        self.viewport_width_cells = 20
        self.viewport_height_cells = 15
        
        # Rendering layers (sorted by render_layer component)
        self.renderable_entities: List[Tuple[EntityID, PositionComponent, RenderableComponent]] = []
        
        # UI state
        self.show_debug_info = False
        
        # Performance tracking
        self.last_render_time = 0.0
        self.frame_count = 0
        
    def _setup_fonts(self):
        """Initialize fonts for rendering"""
        try:
            self.entity_font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 24)
            self.hud_font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 20)
            self.debug_font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 16)
        except:
            self.entity_font = pygame.font.Font(None, 24)
            self.hud_font = pygame.font.Font(None, 20)
            self.debug_font = pygame.font.Font(None, 16)
    
    def update_screen(self, screen: pygame.Surface):
        """Update screen reference when resolution changes"""
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        
        # Recalculate viewport
        self.viewport_width_cells = self.screen_width // self.cell_size
        self.viewport_height_cells = (self.screen_height - 120) // self.cell_size  # Account for HUD
    
    def set_camera(self, x: int, y: int):
        """Set camera position"""
        self.camera_x = x
        self.camera_y = y
    
    def center_camera_on_entity(self, world: World, entity: EntityID):
        """Center camera on a specific entity (usually the player)"""
        pos = world.get_component(entity, PositionComponent)
        if pos:
            self.camera_x = pos.x - self.viewport_width_cells // 2
            self.camera_y = pos.y - self.viewport_height_cells // 2
    
    def update_renderable_entities(self, world: World):
        """Update the list of entities to render, sorted by layer"""
        entities = world.get_entities_with_components(PositionComponent, RenderableComponent)
        
        self.renderable_entities.clear()
        for entity in entities:
            pos = world.get_component(entity, PositionComponent)
            render = world.get_component(entity, RenderableComponent)
            
            # Only include visible entities within viewport
            if (render.visible and 
                self.camera_x <= pos.x < self.camera_x + self.viewport_width_cells and
                self.camera_y <= pos.y < self.camera_y + self.viewport_height_cells):
                self.renderable_entities.append((entity, pos, render))
        
        # Sort by render layer (lower layers render first)
        self.renderable_entities.sort(key=lambda x: x[2].render_layer)
    
    def render_world(self, world: World):
        """Render the entire game world"""
        # Clear screen
        self.screen.fill(COLOR_BG)
        
        # Update entities to render
        self.update_renderable_entities(world)
        
        # Render background/floor tiles first
        self._render_background()
        
        # Render all entities
        self._render_entities(world)
        
        # Render UI overlays
        self._render_ui_overlays(world)
        
        # Render debug info if enabled
        if self.show_debug_info:
            self._render_debug_info(world)
    
    def render_main_menu(self, world: World):
        """Render main menu screen"""
        self.screen.fill((20, 20, 40))
        
        # Title
        title_text = self.entity_font.render("ECS Dungeon Crawler", True, COLOR_WHITE)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, self.screen_height // 3))
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        instructions = [
            "Phase 4: ECS Rendering System",
            "",
            "SPACE/ENTER: Start Game",
            "ESC: Quit",
            "",
            f"Entities: {world.get_entity_count()}"
        ]
        
        y_offset = title_rect.bottom + 50
        for instruction in instructions:
            if instruction:
                inst_text = self.hud_font.render(instruction, True, COLOR_WHITE)
                inst_rect = inst_text.get_rect(center=(self.screen_width // 2, y_offset))
                self.screen.blit(inst_text, inst_rect)
            y_offset += 30
    
    def _render_background(self):
        """Render background tiles/floor"""
        # For now, render a simple grid background
        grid_color = (40, 40, 60)
        
        # Draw grid lines
        for x in range(0, self.screen_width, self.cell_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.screen_height - 120), 1)
        
        for y in range(0, self.screen_height - 120, self.cell_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.screen_width, y), 1)
    
    def _render_entities(self, world: World):
        """Render all game entities"""
        for entity, pos, render in self.renderable_entities:
            self._render_single_entity(world, entity, pos, render)
    
    def _render_single_entity(self, world: World, entity: EntityID, pos: PositionComponent, render: RenderableComponent):
        """Render a single entity"""
        # Calculate screen position
        screen_x = (pos.x - self.camera_x) * self.cell_size + (self.cell_size // 2)
        screen_y = (pos.y - self.camera_y) * self.cell_size + (self.cell_size // 2)
        
        # Skip if off-screen
        if (screen_x < -self.cell_size or screen_x > self.screen_width + self.cell_size or
            screen_y < -self.cell_size or screen_y > self.screen_height + self.cell_size):
            return
        
        # Apply any visual effects
        final_color = render.color
        
        # Check for status effects that change appearance
        if world.has_component(entity, OnFireComponent):
            final_color = (255, 100, 100)  # Red tint for fire
        elif world.has_component(entity, BlessedComponent):
            final_color = (255, 255, 200)  # Light yellow for blessed
        elif world.has_component(entity, CursedComponent):
            final_color = (150, 100, 150)  # Purple tint for cursed
        
        # Render the entity character
        char_surface = self.entity_font.render(render.ascii_char, True, final_color)
        char_rect = char_surface.get_rect(center=(screen_x, screen_y))
        self.screen.blit(char_surface, char_rect)
        
        # Render additional overlays
        self._render_entity_overlays(world, entity, screen_x, screen_y)
    
    def _render_entity_overlays(self, world: World, entity: EntityID, screen_x: int, screen_y: int):
        """Render overlays for entities (health bars, status icons, etc.)"""
        overlays_y = screen_y - self.cell_size // 2 - 5
        
        # Health bar for entities with health
        health = world.get_component(entity, HealthComponent)
        if health and health.max_hp > 1:  # Don't show health bar for 1 HP entities
            self._render_health_bar(health, screen_x, overlays_y)
            overlays_y -= 8
        
        # Status effect icons
        status_icons = []
        if world.has_component(entity, OnFireComponent):
            status_icons.append(("🔥", (255, 100, 0)))
        if world.has_component(entity, BlessedComponent):
            status_icons.append(("✨", (255, 255, 100)))
        if world.has_component(entity, CursedComponent):
            status_icons.append(("💀", (150, 100, 150)))
        if world.has_component(entity, PoisonedComponent):
            status_icons.append(("☠", (100, 255, 100)))
        
        # Render status icons
        icon_x = screen_x - len(status_icons) * 8
        for icon, color in status_icons:
            icon_surface = self.debug_font.render(icon, True, color)
            self.screen.blit(icon_surface, (icon_x, overlays_y))
            icon_x += 16
    
    def _render_health_bar(self, health: HealthComponent, center_x: int, y: int):
        """Render a health bar above an entity"""
        bar_width = 24
        bar_height = 4
        
        # Background
        bg_rect = pygame.Rect(center_x - bar_width // 2, y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (50, 50, 50), bg_rect)
        
        # Health fill
        health_ratio = health.current_hp / health.max_hp
        fill_width = int(bar_width * health_ratio)
        
        if health_ratio > 0.6:
            health_color = (0, 255, 0)
        elif health_ratio > 0.3:
            health_color = (255, 255, 0)
        else:
            health_color = (255, 0, 0)
        
        if fill_width > 0:
            fill_rect = pygame.Rect(center_x - bar_width // 2, y, fill_width, bar_height)
            pygame.draw.rect(self.screen, health_color, fill_rect)
        
        # Border
        pygame.draw.rect(self.screen, COLOR_WHITE, bg_rect, 1)
    
    def _render_ui_overlays(self, world: World):
        """Render UI overlays (HUD, etc.)"""
        # Find player entity for HUD
        player_entities = world.get_entities_with_components(PlayerControlledComponent, NameComponent, HealthComponent)
        
        if player_entities:
            player_entity = next(iter(player_entities))
            self._render_player_hud(world, player_entity)
        
        # Render camera coordinates
        coord_text = f"Camera: ({self.camera_x}, {self.camera_y})"
        coord_surface = self.debug_font.render(coord_text, True, COLOR_WHITE)
        self.screen.blit(coord_surface, (10, 10))
        
        # Render entity count
        entity_count_text = f"Entities: {len(self.renderable_entities)}/{world.get_entity_count()}"
        count_surface = self.debug_font.render(entity_count_text, True, COLOR_WHITE)
        self.screen.blit(count_surface, (10, 30))
    
    def _render_player_hud(self, world: World, player_entity: EntityID):
        """Render player HUD at bottom of screen"""
        hud_y = self.screen_height - 110
        hud_rect = pygame.Rect(0, hud_y, self.screen_width, 110)
        
        # HUD background
        pygame.draw.rect(self.screen, (20, 20, 20), hud_rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, hud_rect, 2)
        
        # Get player components
        name = world.get_component(player_entity, NameComponent)
        health = world.get_component(player_entity, HealthComponent)
        class_comp = world.get_component(player_entity, ClassComponent)
        exp = world.get_component(player_entity, ExperienceComponent)
        stats = world.get_component(player_entity, StatsComponent)
        combat_stats = world.get_component(player_entity, CombatStatsComponent)
        inventory = world.get_component(player_entity, InventoryComponent)
        
        # Left side - Character info
        if name:
            name_text = self.hud_font.render(name.name, True, COLOR_WHITE)
            self.screen.blit(name_text, (20, hud_y + 10))
            
            if name.title:
                title_text = self.debug_font.render(name.title, True, (200, 200, 200))
                self.screen.blit(title_text, (20, hud_y + 35))
        
        if class_comp:
            class_text = f"L{exp.level if exp else 1} {class_comp.character_class}"
            class_surface = self.debug_font.render(class_text, True, COLOR_WHITE)
            self.screen.blit(class_surface, (20, hud_y + 55))
        
        # Center - Health and XP bars
        if health:
            # Health bar
            hp_text = f"HP: {health.current_hp}/{health.max_hp}"
            hp_surface = self.hud_font.render(hp_text, True, COLOR_WHITE)
            hp_rect = hp_surface.get_rect(centerx=self.screen_width // 2, y=hud_y + 15)
            self.screen.blit(hp_surface, hp_rect)
            
            # HP bar visual
            bar_width = 150
            bar_height = 12
            bar_rect = pygame.Rect(hp_rect.centerx - bar_width // 2, hp_rect.bottom + 5, bar_width, bar_height)
            pygame.draw.rect(self.screen, (50, 50, 50), bar_rect)
            
            hp_ratio = health.current_hp / health.max_hp
            fill_width = int(bar_width * hp_ratio)
            if fill_width > 0:
                fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_height)
                pygame.draw.rect(self.screen, (220, 20, 60), fill_rect)
            
            pygame.draw.rect(self.screen, COLOR_WHITE, bar_rect, 1)
        
        if exp:
            # XP bar
            xp_text = f"XP: {exp.current_xp}/{exp.xp_to_next_level()}"
            xp_surface = self.debug_font.render(xp_text, True, COLOR_WHITE)
            xp_rect = xp_surface.get_rect(centerx=self.screen_width // 2, y=hud_y + 60)
            self.screen.blit(xp_surface, xp_rect)
            
            # XP bar visual
            bar_width = 120
            bar_height = 8
            bar_rect = pygame.Rect(xp_rect.centerx - bar_width // 2, xp_rect.bottom + 2, bar_width, bar_height)
            pygame.draw.rect(self.screen, (50, 50, 50), bar_rect)
            
            xp_ratio = exp.current_xp / exp.xp_to_next_level()
            fill_width = int(bar_width * xp_ratio)
            if fill_width > 0:
                fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_height)
                pygame.draw.rect(self.screen, (135, 206, 250), fill_rect)
            
            pygame.draw.rect(self.screen, COLOR_WHITE, bar_rect, 1)
        
        # Right side - Stats
        right_x = self.screen_width - 150
        
        if combat_stats:
            ac_text = f"AC: {combat_stats.armor_class}"
            ac_surface = self.debug_font.render(ac_text, True, COLOR_WHITE)
            self.screen.blit(ac_surface, (right_x, hud_y + 15))
        
        if inventory:
            gold_text = f"Gold: {inventory.gold:.0f}"
            gold_surface = self.debug_font.render(gold_text, True, (255, 215, 0))
            self.screen.blit(gold_surface, (right_x, hud_y + 35))
            
            inv_text = f"Items: {inventory.used_slots}/{inventory.max_slots}"
            inv_surface = self.debug_font.render(inv_text, True, COLOR_WHITE)
            self.screen.blit(inv_surface, (right_x, hud_y + 55))
        
        # Controls
        controls = ["WASD: Move", "ESC: Menu", "F1: Debug"]
        for i, control in enumerate(controls):
            control_surface = self.debug_font.render(control, True, (150, 150, 150))
            self.screen.blit(control_surface, (right_x, hud_y + 75 + i * 12))
    
    def _render_debug_info(self, world: World):
        """Render debug information"""
        debug_y = 50
        
        # ECS debug info
        debug_info = world.debug_info()
        
        debug_lines = [
            f"Systems: {debug_info['system_count']}",
            f"Component Types: {debug_info['component_types']}",
            f"Events: {debug_info['event_count']}",
            f"Cache Size: {debug_info['cache_size']}",
        ]
        
        for line in debug_lines:
            debug_surface = self.debug_font.render(line, True, (255, 255, 0))
            self.screen.blit(debug_surface, (10, debug_y))
            debug_y += 15
        
        # Component counts
        debug_y += 10
        counts_title = self.debug_font.render("Component Counts:", True, (255, 255, 0))
        self.screen.blit(counts_title, (10, debug_y))
        debug_y += 15
        
        for comp_type, count in debug_info['component_counts'].items():
            if count > 0:  # Only show components that exist
                count_line = f"  {comp_type}: {count}"
                count_surface = self.debug_font.render(count_line, True, (200, 200, 200))
                self.screen.blit(count_surface, (10, debug_y))
                debug_y += 12
    
    def toggle_debug_info(self):
        """Toggle debug information display"""
        self.show_debug_info = not self.show_debug_info
    
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.camera_x) * self.cell_size
        screen_y = (world_y - self.camera_y) * self.cell_size
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to world coordinates"""
        world_x = self.camera_x + (screen_x // self.cell_size)
        world_y = self.camera_y + (screen_y // self.cell_size)
        return (world_x, world_y)
    
    def is_position_visible(self, world_x: int, world_y: int) -> bool:
        """Check if a world position is currently visible on screen"""
        return (self.camera_x <= world_x < self.camera_x + self.viewport_width_cells and
                self.camera_y <= world_y < self.camera_y + self.viewport_height_cells)
    
    def get_viewport_bounds(self) -> Tuple[int, int, int, int]:
        """Get viewport bounds as (min_x, min_y, max_x, max_y)"""
        return (self.camera_x, self.camera_y, 
                self.camera_x + self.viewport_width_cells, 
                self.camera_y + self.viewport_height_cells)