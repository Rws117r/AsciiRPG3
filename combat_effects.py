# combat_effects.py - Visual effects system for combat feedback
import pygame
import math
import random
import time
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Color constants for effects
COLOR_DAMAGE = (220, 20, 60)     # Blood red for damage
COLOR_HEAL = (0, 255, 100)       # Green for healing
COLOR_MISS = (100, 150, 255)     # Blue for miss
COLOR_CRIT = (255, 215, 0)       # Gold for critical hits
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

@dataclass
class FloatingText:
    """Represents floating damage/healing numbers or text"""
    text: str
    x: float
    y: float
    start_x: float
    start_y: float
    color: Tuple[int, int, int]
    font_size: int
    velocity_y: float
    velocity_x: float
    lifetime: float
    max_lifetime: float
    alpha: int = 255
    scale: float = 1.0
    is_critical: bool = False
    bounce_offset: float = 0.0
    
    def update(self, dt: float) -> bool:
        """Update the floating text animation. Returns False when text should be removed."""
        self.lifetime -= dt
        
        if self.lifetime <= 0:
            return False
        
        # Calculate animation progress (0 to 1)
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        
        # Physics-like movement with deceleration (like a bouncing ball slowing down)
        friction = 0.88  # Deceleration factor
        self.velocity_y *= friction
        self.velocity_x *= friction
        
        # Apply gravity-like effect to make it settle down
        self.velocity_y += 5 * dt  # Small downward acceleration
        
        # Update position
        self.y += self.velocity_y * dt
        self.x += self.velocity_x * dt
        
        # Limit maximum distance from start position (stay close to character)
        max_distance = 0.8  # Maximum distance in cell units
        distance_x = abs(self.x - self.start_x)
        distance_y = abs(self.y - self.start_y)
        
        # If too far, pull it back
        if distance_x > max_distance:
            self.x = self.start_x + max_distance * (1 if self.x > self.start_x else -1)
            self.velocity_x *= -0.3  # Bounce back with reduced velocity
        
        if distance_y > max_distance:
            self.y = self.start_y + max_distance * (1 if self.y > self.start_y else -1)
            self.velocity_y *= -0.3  # Bounce back with reduced velocity
        
        # Scale effect for critical hits
        if self.is_critical:
            # Bounce effect for critical hits
            self.bounce_offset = math.sin(progress * math.pi * 6) * 2 * (1 - progress)
            # Scale grows then shrinks
            if progress < 0.25:
                self.scale = 1.0 + progress * 2  # Grow to 1.5x
            else:
                self.scale = 1.5 - (progress - 0.25) * 0.67  # Shrink back
        else:
            # Normal numbers have subtle scale effect
            if progress < 0.2:
                self.scale = 1.0 + progress * 0.5  # Grow slightly
            else:
                self.scale = 1.1 - (progress - 0.2) * 0.125  # Shrink back
        
        # Start fading in the last 40% of lifetime
        fade_start = 0.6
        if progress > fade_start:
            fade_progress = (progress - fade_start) / (1.0 - fade_start)
            self.alpha = int(255 * (1.0 - fade_progress))
        
        return True
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, viewport_x: int, viewport_y: int, cell_size: int):
        """Draw the floating text"""
        if self.alpha <= 0:
            return
        
        # Convert world coordinates to screen coordinates
        screen_x = (self.x - viewport_x) * cell_size
        screen_y = (self.y - viewport_y) * cell_size + self.bounce_offset
        
        # Create font at appropriate size
        scaled_size = max(16, int(self.font_size * self.scale))
        try:
            scaled_font = pygame.font.Font(None, scaled_size)
        except:
            scaled_font = pygame.font.Font(None, 24)  # Fallback
        
        # Create main text surface
        text_surf = scaled_font.render(self.text, True, self.color)
        
        # Apply alpha if needed
        if self.alpha < 255:
            alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((*self.color, self.alpha))
            text_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Create outline for better visibility (no black box, just outline)
        outline_surf = scaled_font.render(self.text, True, COLOR_BLACK)
        if self.alpha < 255:
            alpha_surf = pygame.Surface(outline_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((0, 0, 0, self.alpha))
            outline_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        text_rect = text_surf.get_rect(center=(screen_x, screen_y))
        
        # Draw thin outline (just 1 pixel in each direction)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            outline_rect = text_rect.move(dx, dy)
            surface.blit(outline_surf, outline_rect)
        
        # Draw main text on top
        surface.blit(text_surf, text_rect)

@dataclass
class HitFlash:
    """Represents a hit flash effect on a sprite"""
    target_x: int
    target_y: int
    duration: float
    max_duration: float
    flash_interval: float = 0.1  # How fast to flash
    flash_timer: float = 0.0
    is_visible: bool = True
    
    def update(self, dt: float) -> bool:
        """Update the hit flash. Returns False when effect should be removed."""
        self.duration -= dt
        self.flash_timer += dt
        
        if self.duration <= 0:
            return False
        
        # Toggle visibility based on flash interval
        if self.flash_timer >= self.flash_interval:
            self.is_visible = not self.is_visible
            self.flash_timer = 0.0
        
        return True

@dataclass
class ScreenFlash:
    """Screen-wide flash effect for major hits"""
    color: Tuple[int, int, int]
    duration: float
    max_duration: float
    intensity: int = 100  # Max alpha value
    
    def update(self, dt: float) -> bool:
        """Update screen flash. Returns False when effect should be removed."""
        self.duration -= dt
        return self.duration > 0
    
    def get_alpha(self) -> int:
        """Get current alpha value based on remaining duration"""
        progress = 1.0 - (self.duration / self.max_duration)
        
        # Flash peaks quickly then fades
        if progress < 0.2:
            # Quick rise to peak
            return int(self.intensity * (progress / 0.2))
        else:
            # Slower fade
            fade_progress = (progress - 0.2) / 0.8
            return int(self.intensity * (1.0 - fade_progress))

class CombatEffectsManager:
    """Manages all visual combat effects"""
    
    def __init__(self, font_path: str = None):
        self.floating_texts: List[FloatingText] = []
        self.hit_flashes: List[HitFlash] = []
        self.screen_flash: Optional[ScreenFlash] = None
        
        # Load fonts for different sizes
        try:
            self.font_small = pygame.font.Font(font_path, 16)
            self.font_medium = pygame.font.Font(font_path, 20)
            self.font_large = pygame.font.Font(font_path, 28)
        except:
            # Fallback to default font
            self.font_small = pygame.font.Font(None, 16)
            self.font_medium = pygame.font.Font(None, 20)
            self.font_large = pygame.font.Font(None, 28)
    
    def add_damage_number(self, damage: int, x: int, y: int, is_critical: bool = False, is_heal: bool = False):
        """Add a floating damage number that bounces off the character"""
        color = COLOR_HEAL if is_heal else (COLOR_CRIT if is_critical else COLOR_DAMAGE)
        font_size = 36 if is_critical else (32 if is_heal else 28)  # Much bigger text
        text = f"+{damage}" if is_heal else str(damage)
        
        # Start at the character's position
        offset_x = 0
        offset_y = 0
        
        # Random direction like a ball bouncing off the character's head
        angle = random.uniform(0, 2 * math.pi)  # Random direction in radians
        initial_speed = 25 if is_critical else 20  # Initial "bounce" speed
        
        velocity_x = math.cos(angle) * initial_speed
        velocity_y = math.sin(angle) * initial_speed - 10  # Slight upward bias
        
        # Shorter lifetime since it stays close
        lifetime = 1.2 if is_critical else 1.0
        
        floating_text = FloatingText(
            text=text,
            x=x + offset_x,
            y=y + offset_y,
            start_x=x + offset_x,
            start_y=y + offset_y,
            color=color,
            font_size=font_size,
            velocity_y=velocity_y,
            velocity_x=velocity_x,
            lifetime=lifetime,
            max_lifetime=lifetime,
            is_critical=is_critical
        )
        
        self.floating_texts.append(floating_text)
    
    def add_miss_indicator(self, x: int, y: int):
        """Add a miss indicator that bounces off the character"""
        # Miss text starts at character and bounces in random direction
        offset_x = 0
        offset_y = 0
        
        # Random direction like a ball bouncing off
        angle = random.uniform(0, 2 * math.pi)
        initial_speed = 18
        
        velocity_x = math.cos(angle) * initial_speed
        velocity_y = math.sin(angle) * initial_speed - 8  # Slight upward bias
        
        floating_text = FloatingText(
            text="MISS",
            x=x + offset_x,
            y=y + offset_y,
            start_x=x + offset_x,
            start_y=y + offset_y,
            color=COLOR_MISS,
            font_size=24,  # Bigger miss text
            velocity_y=velocity_y,
            velocity_x=velocity_x,
            lifetime=1.0,
            max_lifetime=1.0,
            is_critical=False
        )
        
        self.floating_texts.append(floating_text)
    
    def add_hit_flash(self, x: int, y: int, duration: float = 0.3):
        """Add a hit flash effect at the target location"""
        hit_flash = HitFlash(
            target_x=x,
            target_y=y,
            duration=duration,
            max_duration=duration
        )
        
        self.hit_flashes.append(hit_flash)
    
    def add_screen_flash(self, color: Tuple[int, int, int] = (255, 0, 0), duration: float = 0.2, intensity: int = 80):
        """Add a screen-wide flash effect"""
        self.screen_flash = ScreenFlash(
            color=color,
            duration=duration,
            max_duration=duration,
            intensity=intensity
        )
    
    def update(self, dt: float):
        """Update all effects"""
        # Update floating texts
        self.floating_texts = [text for text in self.floating_texts if text.update(dt)]
        
        # Update hit flashes
        self.hit_flashes = [flash for flash in self.hit_flashes if flash.update(dt)]
        
        # Update screen flash
        if self.screen_flash and not self.screen_flash.update(dt):
            self.screen_flash = None
    
    def should_flash_sprite(self, x: int, y: int) -> bool:
        """Check if a sprite at given coordinates should be flashed"""
        for flash in self.hit_flashes:
            if flash.target_x == x and flash.target_y == y:
                return flash.is_visible
        return False
    
    def draw_floating_texts(self, surface: pygame.Surface, viewport_x: int, viewport_y: int, cell_size: int):
        """Draw all floating text effects"""
        for text in self.floating_texts:
            text.draw(surface, self.font_medium, viewport_x, viewport_y, cell_size)
    
    def draw_screen_flash(self, surface: pygame.Surface):
        """Draw screen flash effect"""
        if not self.screen_flash:
            return
        
        alpha = self.screen_flash.get_alpha()
        if alpha <= 0:
            return
        
        # Create a surface for the flash effect
        flash_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash_surface.fill((*self.screen_flash.color, alpha))
        
        # Blit with alpha blending
        surface.blit(flash_surface, (0, 0))

# Integration functions for the combat system
def create_combat_effects_manager(font_path: str) -> CombatEffectsManager:
    """Create and return a new combat effects manager"""
    return CombatEffectsManager(font_path)

def apply_damage_effects(effects_manager: CombatEffectsManager, damage: int, target_x: int, target_y: int, 
                        is_critical: bool = False, is_miss: bool = False, is_heal: bool = False):
    """Apply visual effects for damage/healing - only flash the target that gets hit"""
    if is_miss:
        effects_manager.add_miss_indicator(target_x, target_y)
    else:
        effects_manager.add_damage_number(damage, target_x, target_y, is_critical, is_heal)
        # Only add hit flash to the TARGET that gets hit, not the attacker
        effects_manager.add_hit_flash(target_x, target_y)
        
        # Add screen flash for critical hits or high damage
        if is_critical or damage >= 10:
            intensity = 120 if is_critical else min(100, damage * 8)
            color = (255, 215, 0) if is_critical else (255, 0, 0)  # Gold for crit, red for normal
            effects_manager.add_screen_flash(color, 0.15, intensity)

def draw_sprite_with_flash(surface: pygame.Surface, sprite_char: str, font: pygame.font.Font, 
                          pos: Tuple[int, int], color: Tuple[int, int, int], 
                          effects_manager: CombatEffectsManager, world_x: int, world_y: int):
    """Draw a sprite with potential hit flash effect"""
    should_flash = effects_manager.should_flash_sprite(world_x, world_y)
    
    if should_flash:
        # Flash effect: alternate between white and original color
        flash_color = COLOR_WHITE
        sprite_surf = font.render(sprite_char, True, flash_color)
    else:
        sprite_surf = font.render(sprite_char, True, color)
    
    sprite_rect = sprite_surf.get_rect(center=pos)
    surface.blit(sprite_surf, sprite_rect)

# Enhanced attack function with visual effects
def enhanced_make_attack(combat_manager, attacker, target, weapon_damage="1d6", attack_bonus=0, damage_stat_modifier=0, effects_manager=None):
    """Enhanced attack function with visual effects"""
    has_advantage = "surprised" in target.conditions
    attack_roll = combat_manager.roll_d20(advantage=has_advantage)
    total_attack = attack_roll + attack_bonus
    
    combat_manager.log_message(f"{attacker.name} attacks {target.name} (AC {target.ac})")
    combat_manager.log_message(f"Attack roll: {attack_roll} + {attack_bonus} = {total_attack}")
    
    # Check for natural 1 (automatic miss)
    if attack_roll == 1:
        combat_manager.log_message("Natural 1 - automatic miss!")
        if effects_manager:
            apply_damage_effects(effects_manager, 0, target.x, target.y, is_miss=True)
        return False
    
    # Check if attack hits
    if total_attack >= target.ac or attack_roll == 20:
        is_critical = attack_roll == 20
        
        base_damage = combat_manager.roll_damage(weapon_damage)
        if is_critical:
            combat_manager.log_message("Critical hit!")
            # Roll all damage dice twice for a crit
            crit_damage = combat_manager.roll_damage(weapon_damage)
            damage = base_damage + crit_damage + damage_stat_modifier
        else:
            damage = base_damage + damage_stat_modifier
        
        damage = max(1, damage)  # Ensure at least 1 damage
        
        target.hp -= damage
        combat_manager.log_message(f"{target.name} takes {damage} damage! ({target.hp}/{target.max_hp} HP remaining)")
        
        # Apply visual effects
        if effects_manager:
            apply_damage_effects(effects_manager, damage, target.x, target.y, is_critical=is_critical)
        
        if target.hp <= 0:
            target.is_alive = False
            combat_manager.log_message(f"{target.name} falls unconscious!")
        
        if "surprised" in target.conditions:
            target.conditions.remove("surprised")
        
        return True
    else:
        combat_manager.log_message("Miss!")
        if effects_manager:
            apply_damage_effects(effects_manager, 0, target.x, target.y, is_miss=True)
        return False