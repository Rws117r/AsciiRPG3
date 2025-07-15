# input_handler.py - Updated version with examination system support
import pygame
from typing import Callable, Optional, Dict
from game_constants import GameState, ExamineMode

class InputHandler:
    """Handles all input processing and maps events to game actions."""
    
    def __init__(self):
        # Callback mappings
        self.movement_callback: Optional[Callable] = None
        self.menu_callbacks: Dict[str, Callable] = {}
        self.system_callbacks: Dict[str, Callable] = {}
        self.navigation_callback: Optional[Callable] = None
        self.selection_callback: Optional[Callable] = None
        self.examination_callback: Optional[Callable] = None
        
        # Key mappings
        self.movement_keys = {
            pygame.K_UP: 'up', pygame.K_w: 'up',
            pygame.K_DOWN: 'down', pygame.K_s: 'down',
            pygame.K_LEFT: 'left', pygame.K_a: 'left',
            pygame.K_RIGHT: 'right', pygame.K_d: 'right'
        }
        
        self.menu_keys = {
            pygame.K_i: 'inventory',
            pygame.K_e: 'equipment', 
            pygame.K_m: 'spells',
            pygame.K_l: 'examine'  # New examination key
        }
        
        self.system_keys = {
            pygame.K_F11: 'fullscreen',
            pygame.K_EQUALS: 'zoom_in', pygame.K_PLUS: 'zoom_in',
            pygame.K_MINUS: 'zoom_out',
            pygame.K_ESCAPE: 'escape'
        }
    
    def set_movement_callback(self, callback: Callable):
        """Set callback for movement actions."""
        self.movement_callback = callback
    
    def set_menu_callback(self, menu_type: str, callback: Callable):
        """Set callback for menu actions."""
        self.menu_callbacks[menu_type] = callback
    
    def set_system_callback(self, system_action: str, callback: Callable):
        """Set callback for system actions."""
        self.system_callbacks[system_action] = callback
    
    def set_navigation_callback(self, callback: Callable):
        """Set callback for UI navigation."""
        self.navigation_callback = callback
    
    def set_selection_callback(self, callback: Callable):
        """Set callback for UI selection."""
        self.selection_callback = callback
    
    def set_examination_callback(self, callback: Callable):
        """Set callback for examination system."""
        self.examination_callback = callback
    
    def handle_event(self, event: pygame.event.Event, game_state: GameState, 
                    examine_mode: ExamineMode = ExamineMode.INACTIVE) -> Optional[str]:
        """Handle a pygame event based on current game state."""
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event, game_state, examine_mode)
        elif event.type == pygame.VIDEORESIZE:
            return self._handle_resize(event)
        
        return None
    
    def _handle_keydown(self, event: pygame.event.Event, game_state: GameState, 
                       examine_mode: ExamineMode) -> Optional[str]:
        """Handle keydown events."""
        key = event.key
        
        # System keys work in all states
        if key in self.system_keys:
            action = self.system_keys[key]
            if action in self.system_callbacks:
                return self.system_callbacks[action]()
        
        # If in examination mode, handle examination input first
        if examine_mode != ExamineMode.INACTIVE:
            if self.examination_callback:
                return self.examination_callback(event, examine_mode)
        
        # State-specific handling
        if game_state == GameState.PLAYING:
            return self._handle_playing_input(key, examine_mode)
        elif game_state == GameState.INVENTORY:
            return self._handle_inventory_input(key)
        elif game_state == GameState.EQUIPMENT:
            return self._handle_equipment_input(key)
        elif game_state == GameState.SPELL_MENU:
            return self._handle_spell_menu_input(key)
        elif game_state == GameState.SPELL_TARGETING:
            return self._handle_spell_targeting_input(key)
        
        return None
    
    def _handle_playing_input(self, key: int, examine_mode: ExamineMode) -> Optional[str]:
        """Handle input during gameplay."""
        # Don't handle movement if in examination mode
        if examine_mode != ExamineMode.INACTIVE:
            return None
        
        # Movement
        if key in self.movement_keys:
            direction = self.movement_keys[key]
            if self.movement_callback:
                self.movement_callback(direction)
            return None
        
        # Menu actions
        if key in self.menu_keys:
            menu_type = self.menu_keys[key]
            if menu_type in self.menu_callbacks:
                self.menu_callbacks[menu_type]()
            return None
        
        # Space key for defend/wait/interact
        if key == pygame.K_SPACE:
            if self.movement_callback:
                return self.movement_callback('defend')
        
        return None
    
    def _handle_inventory_input(self, key: int) -> Optional[str]:
        """Handle inventory screen input."""
        if key == pygame.K_UP:
            if self.navigation_callback:
                self.navigation_callback('inventory', 'up')
        elif key == pygame.K_DOWN:
            if self.navigation_callback:
                self.navigation_callback('inventory', 'down')
        elif key == pygame.K_RETURN:
            if self.selection_callback:
                self.selection_callback('inventory', 'select')
        return None
    
    def _handle_equipment_input(self, key: int) -> Optional[str]:
        """Handle equipment screen input."""
        if key == pygame.K_UP:
            if self.navigation_callback:
                self.navigation_callback('equipment', 'up')
        elif key == pygame.K_DOWN:
            if self.navigation_callback:
                self.navigation_callback('equipment', 'down')
        elif key == pygame.K_RETURN:
            if self.selection_callback:
                self.selection_callback('equipment', 'select')
        return None
    
    def _handle_spell_menu_input(self, key: int) -> Optional[str]:
        """Handle spell menu input."""
        if key == pygame.K_1:
            if self.selection_callback:
                self.selection_callback('spell', 1)
        return None
    
    def _handle_spell_targeting_input(self, key: int) -> Optional[str]:
        """Handle spell targeting input."""
        if key in self.movement_keys:
            direction = self.movement_keys[key]
            if self.navigation_callback:
                self.navigation_callback('spell_target', direction)
        elif key == pygame.K_RETURN:
            if self.selection_callback:
                self.selection_callback('spell_target', 'cast')
        return None
    
    def _handle_resize(self, event: pygame.event.Event) -> Optional[str]:
        """Handle window resize events."""
        return None
    
    def get_movement_direction(self, keys_pressed) -> Optional[str]:
        """Get movement direction from currently pressed keys."""
        for key, direction in self.movement_keys.items():
            if keys_pressed[key]:
                return direction
        return None