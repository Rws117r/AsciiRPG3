# examination_input_handler.py - Input handling specifically for the examination system
import pygame
from typing import Optional, Dict, Any
from game_constants import ExamineMode, ActionCategory, EXAMINATION_KEYS
from examination_action_system import ExaminationSystem, AvailableAction

class ExaminationInputHandler:
    """Handles input specifically for the examination system"""
    
    def __init__(self, examination_system: ExaminationSystem):
        self.examination_system = examination_system
        
        # Input state tracking
        self.last_key_time = {}
        self.key_repeat_delay = 200  # ms before key repeat starts
        self.key_repeat_rate = 100   # ms between repeats
    
    def handle_event(self, event: pygame.event.Event, player, dungeon) -> Optional[str]:
        """
        Handle examination-specific input events.
        Returns action result string or None.
        """
        if self.examination_system.mode == ExamineMode.INACTIVE:
            return None
        
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event, player, dungeon)
        elif event.type == pygame.MOUSEMOTION:
            return self._handle_mouse_motion(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_click(event, player, dungeon)
        
        return None
    
    def _handle_keydown(self, event: pygame.event.Event, player, dungeon) -> Optional[str]:
        """Handle keydown events during examination"""
        key_name = pygame.key.name(event.key)
        
        if self.examination_system.mode == ExamineMode.LOOKING:
            return self._handle_looking_mode_input(key_name, player, dungeon)
        elif self.examination_system.mode == ExamineMode.ACTION_MENU:
            return self._handle_action_menu_input(key_name, player, dungeon)
        
        return None
    
    def _handle_looking_mode_input(self, key_name: str, player, dungeon) -> Optional[str]:
        """Handle input while in looking mode"""
        # Movement keys
        if key_name in ['w', 'up']:
            self.examination_system.move_cursor(0, -1)
            self._update_examination_at_cursor(player, dungeon)
        elif key_name in ['s', 'down']:
            self.examination_system.move_cursor(0, 1)
            self._update_examination_at_cursor(player, dungeon)
        elif key_name in ['a', 'left']:
            self.examination_system.move_cursor(-1, 0)
            self._update_examination_at_cursor(player, dungeon)
        elif key_name in ['d', 'right']:
            self.examination_system.move_cursor(1, 0)
            self._update_examination_at_cursor(player, dungeon)
        
        # Action selection
        elif key_name == 'return':
            if self.examination_system.examine_current_position(dungeon, player):
                # Entity found and actions available
                pass
            else:
                # No entity or no actions - provide feedback
                print("Nothing special to interact with here.")
        
        # Exit examination mode
        elif key_name == 'escape':
            self.examination_system.deactivate_examine_mode()
            return "examination_ended"
        
        # Quick examine (just show description without entering action menu)
        elif key_name == 'space':
            entity = self._get_entity_at_cursor(dungeon)
            if entity:
                distance = self.examination_system._calculate_distance(
                    player.x, player.y, self.examination_system.cursor_x, self.examination_system.cursor_y
                )
                print(f"You see: {entity.get_examination_text(distance, player)[0]}")
            else:
                print("You don't see anything special there.")
        
        return None
    
    def _handle_action_menu_input(self, key_name: str, player, dungeon) -> Optional[str]:
        """Handle input while in action menu mode"""
        # Navigate menu
        if key_name in ['w', 'up']:
            self.examination_system.navigate_action_menu(-1)
        elif key_name in ['s', 'down']:
            self.examination_system.navigate_action_menu(1)
        
        # Select action
        elif key_name == 'return':
            selected_action = self.examination_system.select_action()
            if selected_action:
                return self._execute_selected_action(selected_action, player, dungeon)
        
        # Go back to looking mode
        elif key_name == 'escape':
            self.examination_system.mode = ExamineMode.LOOKING
            self.examination_system.selected_entity = None
            self.examination_system.available_actions = []
        
        return None
    
    def _handle_mouse_motion(self, event: pygame.event.Event) -> Optional[str]:
        """Handle mouse motion during examination"""
        # Could implement mouse cursor movement here
        # For now, we'll stick to keyboard-only examination
        return None
    
    def _handle_mouse_click(self, event: pygame.event.Event, player, dungeon) -> Optional[str]:
        """Handle mouse clicks during examination"""
        # Could implement click-to-examine here
        # For now, we'll stick to keyboard-only examination
        return None
    
    def _update_examination_at_cursor(self, player, dungeon):
        """Update examination information at current cursor position"""
        entity = self._get_entity_at_cursor(dungeon)
        if entity:
            # Calculate distance
            distance = self.examination_system._calculate_distance(
                player.x, player.y, self.examination_system.cursor_x, self.examination_system.cursor_y
            )
            
            # Update selected entity for potential action menu
            self.examination_system.selected_entity = entity
        else:
            self.examination_system.selected_entity = None
    
    def _get_entity_at_cursor(self, dungeon):
        """Get entity at current cursor position"""
        return self.examination_system._get_entity_at_position(
            self.examination_system.cursor_x, 
            self.examination_system.cursor_y, 
            dungeon
        )
    
    def _execute_selected_action(self, action: AvailableAction, player, dungeon) -> Optional[str]:
        """Execute the selected action and return result"""
        try:
            # Get the entity we're acting on
            entity = self.examination_system.selected_entity
            if not entity:
                return "action_failed:no_target"
            
            # Determine action type and execute accordingly
            action_type = action.action_data.get("action", action.name.lower())
            
            if action_type == "touch":
                return self._execute_touch_action(entity, player)
            elif action_type == "push":
                return self._execute_push_action(entity, player, dungeon, action.action_data)
            elif action_type == "pray":
                return self._execute_pray_action(entity, player)
            elif action_type == "open":
                return self._execute_open_action(entity, player)
            elif action_type == "cast_spell":
                return self._execute_spell_action(entity, player, action.action_data)
            elif action_type == "use_item":
                return self._execute_item_action(entity, player, action.action_data)
            elif action_type == "attack":
                return self._execute_attack_action(entity, player)
            else:
                return f"action_executed:{action_type}"
        
        except Exception as e:
            print(f"Error executing action: {e}")
            return "action_failed:error"
    
    def _execute_touch_action(self, entity, player) -> str:
        """Execute touch/examine action"""
        distance = self.examination_system._calculate_distance(
            player.x, player.y, self.examination_system.cursor_x, self.examination_system.cursor_y
        )
        
        if distance <= 1:
            # Close examination
            if hasattr(entity, 'get_examination_description'):
                description = entity.get_examination_description(distance)
            else:
                description = "You examine it closely. It feels solid and real."
            
            print(description)
            return "action_executed:touch"
        else:
            print("You're too far away to touch that.")
            return "action_failed:out_of_range"
    
    def _execute_push_action(self, entity, player, dungeon, action_data) -> str:
        """Execute push action (mainly for boulders)"""
        if not hasattr(entity, 'element_type') or entity.element_type != "boulder":
            print("You can't push that.")
            return "action_failed:invalid_target"
        
        # Get push direction
        direction = action_data.get("direction")
        if not direction:
            print("No push direction specified.")
            return "action_failed:no_direction"
        
        dx, dy = direction
        new_x = entity.x + dx
        new_y = entity.y + dy
        
        # Try to move the boulder through the dungeon's puzzle system
        if hasattr(dungeon, 'puzzle_manager'):
            walkable_positions = dungeon.get_walkable_positions(for_boulders=True)
            success = dungeon.puzzle_manager.move_boulder(entity, new_x, new_y, walkable_positions)
            
            if success:
                print(f"You push the boulder {self.examination_system._get_direction_name(dx, dy).lower()}.")
                
                # Update dungeon tiles
                dungeon.tiles[(entity.x, entity.y)] = dungeon._get_underlying_tile_type(entity.x, entity.y)
                dungeon.tiles[(new_x, new_y)] = dungeon.tiles.get((new_x, new_y), dungeon.tiles[(entity.x, entity.y)])
                dungeon._update_puzzle_tiles()
                
                return "action_executed:pushed_boulder"
            else:
                print("The boulder won't budge - something is blocking its path.")
                return "action_failed:blocked"
        else:
            print("You can't move the boulder here.")
            return "action_failed:no_puzzle_system"
    
    def _execute_pray_action(self, entity, player) -> str:
        """Execute pray action (mainly for altars)"""
        if not hasattr(entity, 'element_type') or entity.element_type != "altar":
            print("This doesn't seem like an appropriate place for prayer.")
            return "action_failed:invalid_target"
        
        # Simple prayer effect
        print("You kneel before the altar and offer a prayer.")
        print("A warm, comforting presence seems to surround you, and you feel slightly refreshed.")
        
        # Could add actual game effects here (heal HP, etc.)
        
        return "action_executed:prayed"
    
    def _execute_open_action(self, entity, player) -> str:
        """Execute open action (mainly for chests)"""
        if not hasattr(entity, 'element_type') or entity.element_type != "chest":
            print("You can't open that.")
            return "action_failed:invalid_target"
        
        # Try to open through puzzle system
        if hasattr(entity, 'opened') and entity.opened:
            print("The chest is already open and empty.")
            return "action_failed:already_open"
        
        # This would interact with the puzzle system to handle trapped chests, etc.
        print("You attempt to open the chest...")
        # For now, just a simple message
        return "action_executed:opened"
    
    def _execute_spell_action(self, entity, player, action_data) -> str:
        """Execute spell casting action"""
        spell_name = action_data.get("spell")
        if not spell_name:
            print("No spell specified.")
            return "action_failed:no_spell"
        
        if spell_name not in player.starting_spells:
            print(f"You don't know the {spell_name} spell.")
            return "action_failed:unknown_spell"
        
        print(f"You cast {spell_name} on the {entity.element_type if hasattr(entity, 'element_type') else 'target'}!")
        # Spell effects would be implemented here
        
        return "action_executed:cast_spell"
    
    def _execute_item_action(self, entity, player, action_data) -> str:
        """Execute item usage action"""
        item_name = action_data.get("item")
        if not item_name:
            print("No item specified.")
            return "action_failed:no_item"
        
        # Check if player has the item
        has_item = False
        for inv_item in player.inventory:
            if item_name.lower() in inv_item.item.name.lower():
                has_item = True
                break
        
        if not has_item:
            print(f"You don't have a {item_name}.")
            return "action_failed:no_item"
        
        print(f"You use the {item_name} on the {entity.element_type if hasattr(entity, 'element_type') else 'target'}!")
        # Item effects would be implemented here
        
        return "action_executed:used_item"
    
    def _execute_attack_action(self, entity, player) -> str:
        """Execute attack action"""
        if not hasattr(entity, 'name'):
            print("You can't attack that.")
            return "action_failed:invalid_target"
        
        print(f"You attack the {entity.name}!")
        # Combat would be handled by the combat system
        
        return "action_executed:attack"