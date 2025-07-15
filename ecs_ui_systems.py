# ecs_ui_systems.py - UI systems adapted for ECS (Phase 4)

import pygame
from typing import List, Tuple, Dict, Optional
from ecs_core import World, EntityID
from ecs_components import *
from game_constants import *

class ECSUIRenderer:
    """Handles rendering of ECS-based UI elements"""
    
    def __init__(self):
        # Initialize fonts
        try:
            self.title_font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 24)
            self.normal_font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 18)
            self.small_font = pygame.font.Font("JetBrainsMonoNL-Regular.ttf", 14)
        except:
            self.title_font = pygame.font.Font(None, 24)
            self.normal_font = pygame.font.Font(None, 18)
            self.small_font = pygame.font.Font(None, 14)
    
    def render_inventory_screen(self, surface: pygame.Surface, world: World, player_entity: EntityID):
        """Render inventory screen using ECS components"""
        surface.fill((20, 20, 30))
        screen_width, screen_height = surface.get_size()
        
        # Get player components
        name_comp = world.get_component(player_entity, NameComponent)
        inventory_comp = world.get_component(player_entity, InventoryComponent)
        
        if not name_comp or not inventory_comp:
            error_text = self.title_font.render("No inventory data available", True, COLOR_WHITE)
            error_rect = error_text.get_rect(center=(screen_width // 2, screen_height // 2))
            surface.blit(error_text, error_rect)
            return
        
        # Title
        title = f"{name_comp.name}'s Inventory"
        title_surf = self.title_font.render(title, True, COLOR_WHITE)
        title_rect = title_surf.get_rect(centerx=screen_width // 2, top=20)
        surface.blit(title_surf, title_rect)
        
        # Inventory stats
        stats_y = title_rect.bottom + 20
        
        slots_text = f"Slots Used: {inventory_comp.used_slots}/{inventory_comp.max_slots}"
        slots_surf = self.normal_font.render(slots_text, True, COLOR_WHITE)
        surface.blit(slots_surf, (50, stats_y))
        
        gold_text = f"Gold: {inventory_comp.gold:.1f}"
        gold_surf = self.normal_font.render(gold_text, True, (255, 215, 0))
        gold_rect = gold_surf.get_rect(right=screen_width - 50, y=stats_y)
        surface.blit(gold_surf, gold_rect)
        
        # Items list
        items_y = stats_y + 50
        if not inventory_comp.items:
            empty_text = self.normal_font.render("Inventory is empty", True, (150, 150, 150))
            surface.blit(empty_text, (50, items_y))
        else:
            for i, item_entity in enumerate(inventory_comp.items):
                item_name_comp = world.get_component(item_entity, NameComponent)
                if item_name_comp:
                    item_text = f"• {item_name_comp.name}"
                    item_surf = self.normal_font.render(item_text, True, COLOR_WHITE)
                    surface.blit(item_surf, (50, items_y + i * 25))
        
        # Instructions
        instructions = ["ESC: Back to game", "I: Toggle inventory"]
        self._render_instructions(surface, instructions, screen_height - 60)
    
    def render_equipment_screen(self, surface: pygame.Surface, world: World, player_entity: EntityID):
        """Render equipment screen using ECS components"""
        surface.fill((30, 20, 20))
        screen_width, screen_height = surface.get_size()
        
        # Get player components
        name_comp = world.get_component(player_entity, NameComponent)
        equipment_comp = world.get_component(player_entity, EquipmentSlotsComponent)
        
        if not name_comp or not equipment_comp:
            error_text = self.title_font.render("No equipment data available", True, COLOR_WHITE)
            error_rect = error_text.get_rect(center=(screen_width // 2, screen_height // 2))
            surface.blit(error_text, error_rect)
            return
        
        # Title
        title = f"{name_comp.name}'s Equipment"
        title_surf = self.title_font.render(title, True, COLOR_WHITE)
        title_rect = title_surf.get_rect(centerx=screen_width // 2, top=20)
        surface.blit(title_surf, title_rect)
        
        # Equipment slots
        slots_y = title_rect.bottom + 40
        slot_names = {
            'weapon': 'Weapon',
            'armor': 'Armor',
            'shield': 'Shield',
            'light': 'Light Source'
        }
        
        for i, (slot, display_name) in enumerate(slot_names.items()):
            y = slots_y + i * 60
            
            # Slot name
            slot_surf = self.normal_font.render(f"{display_name}:", True, COLOR_WHITE)
            surface.blit(slot_surf, (50, y))
            
            # Equipped item
            equipped_item = equipment_comp.get_equipped_item(slot)
            if equipped_item:
                item_name_comp = world.get_component(equipped_item, NameComponent)
                if item_name_comp:
                    item_text = item_name_comp.name
                    item_color = COLOR_GREEN
                else:
                    item_text = "Unknown Item"
                    item_color = COLOR_RED
            else:
                item_text = "(Nothing equipped)"
                item_color = (150, 150, 150)
            
            item_surf = self.normal_font.render(item_text, True, item_color)
            surface.blit(item_surf, (200, y))
            
            # Item stats if equipped
            if equipped_item:
                self._render_item_stats(surface, world, equipped_item, 200, y + 20)
        
        # Instructions
        instructions = ["ESC: Back to game", "E: Toggle equipment"]
        self._render_instructions(surface, instructions, screen_height - 60)
    
    def render_character_sheet(self, surface: pygame.Surface, world: World, player_entity: EntityID):
        """Render detailed character sheet"""
        surface.fill((20, 30, 20))
        screen_width, screen_height = surface.get_size()
        
        # Get all relevant components
        name_comp = world.get_component(player_entity, NameComponent)
        class_comp = world.get_component(player_entity, ClassComponent)
        stats_comp = world.get_component(player_entity, StatsComponent)
        health_comp = world.get_component(player_entity, HealthComponent)
        exp_comp = world.get_component(player_entity, ExperienceComponent)
        combat_comp = world.get_component(player_entity, CombatStatsComponent)
        
        if not name_comp:
            return
        
        # Character name and title
        title = f"{name_comp.name}"
        if name_comp.title:
            title += f" - {name_comp.title}"
        
        title_surf = self.title_font.render(title, True, COLOR_WHITE)
        title_rect = title_surf.get_rect(centerx=screen_width // 2, top=20)
        surface.blit(title_surf, title_rect)
        
        # Class and level info
        info_y = title_rect.bottom + 20
        if class_comp and exp_comp:
            class_text = f"Level {exp_comp.level} {class_comp.alignment} {class_comp.race} {class_comp.character_class}"
            class_surf = self.normal_font.render(class_text, True, COLOR_WHITE)
            class_rect = class_surf.get_rect(centerx=screen_width // 2, y=info_y)
            surface.blit(class_surf, class_rect)
            info_y = class_rect.bottom + 30
        
        # Stats section
        if stats_comp:
            self._render_character_stats(surface, stats_comp, 50, info_y)
        
        # Vitals section
        vitals_x = screen_width // 2 + 50
        if health_comp:
            self._render_character_vitals(surface, world, player_entity, vitals_x, info_y)
        
        # Instructions
        instructions = ["ESC: Back to game", "C: Toggle character sheet"]
        self._render_instructions(surface, instructions, screen_height - 60)
    
    def _render_character_stats(self, surface: pygame.Surface, stats_comp: StatsComponent, x: int, y: int):
        """Render character statistics"""
        stats_title = self.normal_font.render("Statistics", True, COLOR_WHITE)
        surface.blit(stats_title, (x, y))
        
        stats_list = [
            ("Strength", stats_comp.strength),
            ("Dexterity", stats_comp.dexterity),
            ("Constitution", stats_comp.constitution),
            ("Intelligence", stats_comp.intelligence),
            ("Wisdom", stats_comp.wisdom),
            ("Charisma", stats_comp.charisma)
        ]
        
        stat_y = y + 30
        for stat_name, stat_value in stats_list:
            modifier = stats_comp.get_modifier(stat_name)
            mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
            
            stat_text = f"{stat_name}: {stat_value} ({mod_str})"
            stat_surf = self.small_font.render(stat_text, True, COLOR_WHITE)
            surface.blit(stat_surf, (x + 10, stat_y))
            stat_y += 20
    
    def _render_character_vitals(self, surface: pygame.Surface, world: World, player_entity: EntityID, x: int, y: int):
        """Render character vitals and derived stats"""
        vitals_title = self.normal_font.render("Vitals & Combat", True, COLOR_WHITE)
        surface.blit(vitals_title, (x, y))
        
        vitals_y = y + 30
        
        # Health
        health_comp = world.get_component(player_entity, HealthComponent)
        if health_comp:
            hp_text = f"Hit Points: {health_comp.current_hp}/{health_comp.max_hp}"
            hp_surf = self.small_font.render(hp_text, True, COLOR_WHITE)
            surface.blit(hp_surf, (x + 10, vitals_y))
            vitals_y += 20
        
        # Experience
        exp_comp = world.get_component(player_entity, ExperienceComponent)
        if exp_comp:
            xp_text = f"Experience: {exp_comp.current_xp}/{exp_comp.xp_to_next_level()}"
            xp_surf = self.small_font.render(xp_text, True, COLOR_WHITE)
            surface.blit(xp_surf, (x + 10, vitals_y))
            vitals_y += 20
        
        # Combat stats
        combat_comp = world.get_component(player_entity, CombatStatsComponent)
        if combat_comp:
            ac_text = f"Armor Class: {combat_comp.armor_class}"
            ac_surf = self.small_font.render(ac_text, True, COLOR_WHITE)
            surface.blit(ac_surf, (x + 10, vitals_y))
            vitals_y += 20
            
            if combat_comp.attack_bonus != 0:
                attack_text = f"Attack Bonus: +{combat_comp.attack_bonus}"
                attack_surf = self.small_font.render(attack_text, True, COLOR_WHITE)
                surface.blit(attack_surf, (x + 10, vitals_y))
                vitals_y += 20
        
        # Status effects
        status_effects = []
        if world.has_component(player_entity, BlessedComponent):
            blessed = world.get_component(player_entity, BlessedComponent)
            status_effects.append(f"Blessed ({blessed.duration_remaining} turns)")
        
        if world.has_component(player_entity, CursedComponent):
            cursed = world.get_component(player_entity, CursedComponent)
            status_effects.append(f"Cursed ({cursed.duration_remaining} turns)")
        
        if world.has_component(player_entity, OnFireComponent):
            fire = world.get_component(player_entity, OnFireComponent)
            status_effects.append(f"On Fire ({fire.duration_remaining} turns)")
        
        if world.has_component(player_entity, PoisonedComponent):
            poison = world.get_component(player_entity, PoisonedComponent)
            status_effects.append(f"Poisoned ({poison.duration_remaining} turns)")
        
        if status_effects:
            vitals_y += 10
            status_title = self.small_font.render("Status Effects:", True, (255, 255, 100))
            surface.blit(status_title, (x + 10, vitals_y))
            vitals_y += 20
            
            for effect in status_effects:
                effect_surf = self.small_font.render(f"• {effect}", True, (255, 200, 200))
                surface.blit(effect_surf, (x + 20, vitals_y))
                vitals_y += 16
    
    def _render_item_stats(self, surface: pygame.Surface, world: World, item_entity: EntityID, x: int, y: int):
        """Render statistics for an equipped item"""
        # Check for weapon stats
        weapon_comp = world.get_component(item_entity, WeaponComponent)
        if weapon_comp:
            damage_text = f"Damage: {weapon_comp.damage_dice}"
            damage_surf = self.small_font.render(damage_text, True, (200, 200, 255))
            surface.blit(damage_surf, (x, y))
            return
        
        # Check for armor stats
        armor_comp = world.get_component(item_entity, ArmorComponent)
        if armor_comp:
            ac_text = f"AC Bonus: +{armor_comp.ac_bonus}"
            ac_surf = self.small_font.render(ac_text, True, (200, 255, 200))
            surface.blit(ac_surf, (x, y))
            return
        
        # Check for light source
        light_comp = world.get_component(item_entity, LightSourceComponent)
        if light_comp:
            brightness_text = f"Light: {light_comp.brightness} radius"
            brightness_surf = self.small_font.render(brightness_text, True, (255, 255, 150))
            surface.blit(brightness_surf, (x, y))
            return
    
    def _render_instructions(self, surface: pygame.Surface, instructions: List[str], y: int):
        """Render instruction text at bottom of screen"""
        screen_width = surface.get_width()
        
        for i, instruction in enumerate(instructions):
            inst_surf = self.small_font.render(instruction, True, (200, 200, 200))
            inst_rect = inst_surf.get_rect(centerx=screen_width // 2, y=y + i * 18)
            surface.blit(inst_surf, inst_rect)
    
    def render_action_feedback(self, surface: pygame.Surface, message: str, message_type: str = "info"):
        """Render temporary action feedback messages"""
        screen_width, screen_height = surface.get_size()
        
        # Choose color based on message type
        colors = {
            "success": (100, 255, 100),
            "failure": (255, 100, 100),
            "info": (100, 200, 255),
            "warning": (255, 255, 100)
        }
        color = colors.get(message_type, COLOR_WHITE)
        
        # Render message
        message_surf = self.normal_font.render(message, True, color)
        message_rect = message_surf.get_rect(centerx=screen_width // 2, y=screen_height - 160)
        
        # Background for better visibility
        bg_rect = message_rect.inflate(20, 10)
        pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
        pygame.draw.rect(surface, color, bg_rect, 1)
        
        surface.blit(message_surf, message_rect)
    
    def render_tooltip(self, surface: pygame.Surface, world: World, entity: EntityID, pos: Tuple[int, int]):
        """Render tooltip for an entity"""
        # Get entity information
        name_comp = world.get_component(entity, NameComponent)
        health_comp = world.get_component(entity, HealthComponent)
        
        if not name_comp:
            return
        
        # Build tooltip text
        tooltip_lines = [name_comp.name]
        
        if name_comp.description:
            tooltip_lines.append(name_comp.description)
        
        if health_comp:
            tooltip_lines.append(f"HP: {health_comp.current_hp}/{health_comp.max_hp}")
        
        # Render tooltip
        max_width = max(self.small_font.size(line)[0] for line in tooltip_lines)
        tooltip_height = len(tooltip_lines) * 18 + 10
        
        # Position tooltip near cursor but keep on screen
        tooltip_x = min(pos[0] + 20, surface.get_width() - max_width - 20)
        tooltip_y = max(pos[1] - tooltip_height - 10, 10)
        
        # Background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, max_width + 20, tooltip_height)
        pygame.draw.rect(surface, (0, 0, 0, 200), tooltip_rect)
        pygame.draw.rect(surface, COLOR_WHITE, tooltip_rect, 1)
        
        # Text
        text_y = tooltip_y + 5
        for line in tooltip_lines:
            line_surf = self.small_font.render(line, True, COLOR_WHITE)
            surface.blit(line_surf, (tooltip_x + 10, text_y))
            text_y += 18

# Helper functions for creating UI from ECS data
def get_player_stats_summary(world: World, player_entity: EntityID) -> Dict[str, str]:
    """Get a formatted summary of player statistics"""
    summary = {}
    
    name_comp = world.get_component(player_entity, NameComponent)
    if name_comp:
        summary['name'] = name_comp.name
        summary['title'] = name_comp.title or ""
    
    class_comp = world.get_component(player_entity, ClassComponent)
    if class_comp:
        summary['race'] = class_comp.race
        summary['class'] = class_comp.character_class
        summary['alignment'] = class_comp.alignment
    
    exp_comp = world.get_component(player_entity, ExperienceComponent)
    if exp_comp:
        summary['level'] = str(exp_comp.level)
        summary['xp'] = f"{exp_comp.current_xp}/{exp_comp.xp_to_next_level()}"
    
    health_comp = world.get_component(player_entity, HealthComponent)
    if health_comp:
        summary['hp'] = f"{health_comp.current_hp}/{health_comp.max_hp}"
    
    combat_comp = world.get_component(player_entity, CombatStatsComponent)
    if combat_comp:
        summary['ac'] = str(combat_comp.armor_class)
    
    inventory_comp = world.get_component(player_entity, InventoryComponent)
    if inventory_comp:
        summary['gold'] = f"{inventory_comp.gold:.1f}"
        summary['slots'] = f"{inventory_comp.used_slots}/{inventory_comp.max_slots}"
    
    return summary