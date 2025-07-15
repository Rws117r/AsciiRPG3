# ecs_input_handler.py - ECS-based input handling (Phase 3 Fixed)

import pygame
from typing import Dict, Callable, Optional
from ecs_core import World, EntityID
from ecs_components import PositionComponent
from ecs_systems import MoveEvent, WaitEvent, InteractionEvent, UIEvent

class ECSInputHandler:
    """Handles input and converts to ECS events"""
    
    def __init__(self, world: World):
        self.world = world
        self.player_entity: Optional[EntityID] = None
        
        # Key mappings
        self.movement_keys = {
            pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)
        }
        
        self.action_keys = {
            pygame.K_SPACE: 'wait',
            pygame.K_i: 'inventory',
            pygame.K_e: 'equipment',
            pygame.K_m: 'spells',
            pygame.K_RETURN: 'interact'
        }
    
    def set_player_entity(self, player_entity: EntityID):
        """Set which entity is the player"""
        self.player_entity = player_entity
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame event and generate ECS events. Returns True if handled."""
        if not self.player_entity:
            return False
        
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
        
        return False
    
    def _handle_keydown(self, event: pygame.event.Event) -> bool:
        """Handle key down events"""
        key = event.key
        
        # Movement
        if key in self.movement_keys:
            dx, dy = self.movement_keys[key]
            
            # Get player position
            player_pos = self.world.get_component(self.player_entity, PositionComponent)
            if player_pos:
                new_pos = (player_pos.x + dx, player_pos.y + dy)
                
                # Create movement event
                move_event = MoveEvent(
                    self.player_entity,
                    (player_pos.x, player_pos.y),
                    new_pos
                )
                self.world.add_event(move_event)
                return True
        
        # Action keys
        elif key in self.action_keys:
            action = self.action_keys[key]
            
            if action == 'wait':
                # Create wait event
                wait_event = WaitEvent(self.player_entity)
                self.world.add_event(wait_event)
                return True
            
            elif action == 'interact':
                # Create interaction event at player position
                player_pos = self.world.get_component(self.player_entity, PositionComponent)
                if player_pos:
                    interact_event = InteractionEvent(
                        self.player_entity,
                        None,  # Will be resolved by system
                        "interact"
                    )
                    self.world.add_event(interact_event)
                    return True
            
            elif action in ['inventory', 'equipment', 'spells']:
                # Create UI event
                ui_event = UIEvent(action, self.player_entity)
                self.world.add_event(ui_event)
                return True
        
        return False