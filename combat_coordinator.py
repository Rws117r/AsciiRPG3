# combat_coordinator.py - Complete fixed version with proper respawn handling
from typing import Optional, List, Tuple, Dict, Any
from combat_system import (
    CombatManager, CombatState, CombatMonster, 
    calculate_distance, is_adjacent, check_for_combat,
    get_stat_modifier, get_weapon_damage
)
from combat_effects import CombatEffectsManager, enhanced_make_attack
from character_creation import Player
from dungeon_classes import DungeonExplorer
from game_constants import FONT_FILE

class CombatCoordinator:
    """Coordinates combat flow, initiative, and turn management."""
    
    def __init__(self):
        self.combat_manager = CombatManager()
        self.effects_manager = CombatEffectsManager(FONT_FILE)
    
    def update(self, dt_seconds: float):
        """Update combat systems."""
        self.effects_manager.update(dt_seconds)
    
    def is_in_combat(self) -> bool:
        """Check if currently in combat."""
        return self.combat_manager.state != CombatState.NOT_IN_COMBAT
    
    def get_combat_manager(self) -> CombatManager:
        """Get the combat manager for UI rendering."""
        return self.combat_manager
    
    def get_effects_manager(self) -> CombatEffectsManager:
        """Get the effects manager for rendering."""
        return self.effects_manager
    
    def initiate_combat(self, player: Player, player_pos: Tuple[int, int], 
                       target_monster, dungeon: DungeonExplorer, 
                       walkable_positions: set) -> bool:
        """Initiate combat and process first round. Returns True if combat ended."""
        print(f"Combat initiated with {target_monster.name}!")
        
        # Start combat with all adjacent monsters
        monsters_in_combat, surprised_monsters = check_for_combat(player_pos, dungeon.monsters, dungeon)
        self.combat_manager.start_combat(player, player_pos, monsters_in_combat, surprised_monsters, dungeon.monsters)
        
        # Roll initiative
        dex_modifier = get_stat_modifier(player.dexterity)
        self.combat_manager.roll_initiative(dex_modifier)
        
        # Find target monster in combat participants
        target_combat_monster = self._find_combat_monster(target_monster)
        
        # Process full combat round with proper initiative
        return self._process_combat_round(player, player_pos, target_combat_monster, walkable_positions)
    
    def handle_combat_movement(self, player: Player, player_pos: Tuple[int, int], 
                              next_pos: Tuple[int, int], dungeon: DungeonExplorer,
                              walkable_positions: set) -> bool:
        """Handle movement during combat. Returns True if combat ended."""
        from combat_system import attempt_positional_attack
        
        # Check if moving into a monster (attack)
        can_attack, target_monster = attempt_positional_attack(player_pos, next_pos, self.combat_manager, dungeon.monsters)
        
        if can_attack and target_monster:
            # Attack the monster - DON'T log movement
            return self._process_combat_round(player, player_pos, target_monster, walkable_positions)
        
        elif next_pos in walkable_positions:
            # Safe movement - log the movement ONLY when it actually happens
            # The actual position update happens in game_manager
            self.combat_manager.log_message(f"{player.name} moves to {next_pos}")
            return self._process_combat_round(player, next_pos, None, walkable_positions)
        
        else:
            # Can't move there
            self.combat_manager.log_message("Can't move there!")
            return False
    
    def handle_defend_action(self, player: Player, player_pos: Tuple[int, int],
                            walkable_positions: set) -> bool:
        """Handle defend/wait action. Returns True if combat ended."""
        return self._process_combat_round(player, player_pos, None, walkable_positions)
    
    def cleanup_combat(self, player: Player, dungeon: DungeonExplorer):
        """Clean up after combat ends."""
        # Update player HP
        player_participant = self.combat_manager.get_player_in_combat()
        if player_participant:
            player.hp = player_participant.hp
            
            # Don't auto-respawn here - let game_manager handle it
            # This allows for better control over respawn logic
            if player.hp <= 0:
                print(f"{player.name} has been defeated in combat!")
        
        # Update dungeon monsters
        self._update_dungeon_monsters(dungeon)
        
        # Reset combat state
        self.combat_manager.state = CombatState.NOT_IN_COMBAT
    
    def _find_combat_monster(self, target_monster) -> Optional[CombatMonster]:
        """Find the combat participant corresponding to a dungeon monster."""
        for participant in self.combat_manager.participants:
            if (isinstance(participant, CombatMonster) and 
                participant.x == target_monster.x and 
                participant.y == target_monster.y and
                participant.name == target_monster.name):
                return participant
        return None
    
    def _process_combat_round(self, player: Player, player_pos: Tuple[int, int],
                             target_monster: Optional[CombatMonster], 
                             walkable_positions: set) -> bool:
        """Process a complete combat round with proper initiative order."""
        
        # Get turn order (already sorted by initiative)
        turn_order = self.combat_manager.turn_order
        if not turn_order:
            return True  # Combat should end
        
        # Plan all actions first
        combat_actions = []
        
        for participant in turn_order:
            if not participant.is_alive:
                continue
            
            if isinstance(participant, CombatMonster):
                # Plan monster action
                action = self._plan_monster_action(participant, player_pos, walkable_positions)
                combat_actions.append((participant, action))
            else:
                # Plan player action - only if player is alive
                if participant.is_alive:
                    if target_monster and target_monster.is_alive:
                        action = ('attack', target_monster)
                    else:
                        action = ('move_defend', player_pos)
                    combat_actions.append((participant, action))
        
        # Execute all actions in initiative order
        for participant, action in combat_actions:
            if not participant.is_alive:
                continue  # Skip if participant died earlier this round
            
            result = self._execute_combat_action(participant, action, player, walkable_positions)
            
            # Check if target died and mark them as dead for subsequent actions
            if result and result.get('target_died'):
                target = result.get('target')
                if target:
                    target.is_alive = False
                    # End combat immediately if player dies
                    if not isinstance(target, CombatMonster):
                        self.combat_manager.log_message("Player has been defeated! Combat ends.")
                        self.combat_manager.end_combat()
                        return True
        
        # Better combat end condition
        alive_players = [p for p in self.combat_manager.participants 
                        if not isinstance(p, CombatMonster) and p.is_alive]
        alive_monsters = [p for p in self.combat_manager.participants 
                         if isinstance(p, CombatMonster) and p.is_alive and not getattr(p, 'has_fled', False)]
        
        if len(alive_players) == 0:
            self.combat_manager.log_message("All players defeated!")
            self.combat_manager.end_combat()
            return True
        elif len(alive_monsters) == 0:
            self.combat_manager.log_message("All monsters defeated!")
            self.combat_manager.end_combat()
            return True
        
        # Prepare for next round
        self.combat_manager.current_turn_index = 0
        current = self.combat_manager.get_current_participant()
        if current and current.is_alive:
            if isinstance(current, CombatMonster):
                self.combat_manager.state = CombatState.MONSTER_TURN
            else:
                self.combat_manager.state = CombatState.PLAYER_TURN
        
        return False  # Combat continues
    
    def _plan_monster_action(self, monster: CombatMonster, player_pos: Tuple[int, int], 
                            walkable_positions: set) -> Tuple[str, Any]:
        """Plan what a monster will do on their turn."""
        import random
        
        # Check morale first
        morale_threshold = monster.max_hp / 4
        if monster.hp <= morale_threshold and not monster.has_fled:
            morale_roll = random.randint(1, 20)
            if morale_roll < 15:
                monster.has_fled = True
                return ('flee', None)
        
        monster_pos = (monster.x, monster.y)
        
        if monster.has_fled:
            return ('flee', None)
        elif is_adjacent(monster_pos, player_pos):
            return ('attack', 'player')
        else:
            return ('move_toward_player', player_pos)
    
    def _execute_combat_action(self, participant, action: Tuple[str, Any], 
                              player: Player, walkable_positions: set) -> Dict[str, Any]:
        """Execute a combat action and return results."""
        result = {}
        action_type, action_target = action
        
        if isinstance(participant, CombatMonster):
            # Monster action
            if action_type == 'attack':
                player_participant = self.combat_manager.get_player_in_combat()
                if player_participant and player_participant.is_alive:
                    attack_bonus = getattr(participant, 'attack_bonus', 0)
                    damage_bonus = get_stat_modifier(participant.strength)
                    damage = participant.damage
                    
                    hit = enhanced_make_attack(self.combat_manager, participant, player_participant, 
                                             damage, attack_bonus, damage_bonus, self.effects_manager)
                    result['hit'] = hit
                    result['target'] = player_participant
                    
                    # Properly check for player death
                    if player_participant.hp <= 0:
                        player_participant.is_alive = False
                        result['target_died'] = True
                        self.combat_manager.log_message(f"{player_participant.name} has been defeated!")
            
            elif action_type == 'flee':
                self._handle_monster_flee(participant, walkable_positions)
            
            elif action_type == 'move_toward_player':
                self._handle_monster_movement(participant, action_target, walkable_positions)
        
        else:
            # Player action - only act if player is alive
            if not participant.is_alive:
                self.combat_manager.log_message(f"{participant.name} is unconscious and cannot act!")
                return result
                
            if action_type == 'attack':
                target_monster = action_target
                if target_monster and target_monster.is_alive:
                    weapon_damage = get_weapon_damage(player)
                    attack_bonus = get_stat_modifier(player.strength)
                    
                    if player.character_class == "Fighter":
                        attack_bonus += player.level // 2
                    
                    damage_bonus = get_stat_modifier(player.strength)
                    
                    hit = enhanced_make_attack(self.combat_manager, participant, target_monster, 
                                             weapon_damage, attack_bonus, damage_bonus, self.effects_manager)
                    result['hit'] = hit
                    result['target'] = target_monster
                    
                    # Properly check for monster death
                    if target_monster.hp <= 0:
                        target_monster.is_alive = False
                        result['target_died'] = True
            
            elif action_type == 'move_defend':
                self.combat_manager.log_message(f"{participant.name} moves and defends!")
        
        return result
    
    def _handle_monster_flee(self, monster: CombatMonster, walkable_positions: set):
        """Handle monster fleeing behavior."""
        player_participant = self.combat_manager.get_player_in_combat()
        if not player_participant:
            return
        
        player_pos = (player_participant.x, player_participant.y)
        best_flee_spot = None
        max_dist = -1
        
        # Check all 8 directions for best flee spot
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
            new_pos = (monster.x + dx, monster.y + dy)
            
            if new_pos in walkable_positions:
                dist_to_player = calculate_distance(new_pos, player_pos)
                if dist_to_player > max_dist:
                    max_dist = dist_to_player
                    best_flee_spot = new_pos
        
        if best_flee_spot and calculate_distance(best_flee_spot, player_pos) > calculate_distance((monster.x, monster.y), player_pos):
            monster.x, monster.y = best_flee_spot
            self.combat_manager.update_dungeon_monster_position(monster, monster.x, monster.y)
            self.combat_manager.log_message(f"{monster.name} flees to ({monster.x}, {monster.y})!")
        else:
            self.combat_manager.log_message(f"{monster.name} is cornered and can't flee!")
            # If cornered, attack if adjacent
            if is_adjacent((monster.x, monster.y), player_pos):
                player_participant = self.combat_manager.get_player_in_combat()
                if player_participant:
                    attack_bonus = getattr(monster, 'attack_bonus', 0)
                    damage_bonus = get_stat_modifier(monster.strength)
                    damage = monster.damage
                    enhanced_make_attack(self.combat_manager, monster, player_participant, 
                                       damage, attack_bonus, damage_bonus, self.effects_manager)
    
    def _handle_monster_movement(self, monster: CombatMonster, target_pos: Tuple[int, int], 
                                walkable_positions: set):
        """Handle monster movement toward target."""
        best_move = (monster.x, monster.y)
        min_dist = calculate_distance((monster.x, monster.y), target_pos)
        
        # Check 4 cardinal directions
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            new_pos = (monster.x + dx, monster.y + dy)
            if new_pos in walkable_positions:
                dist = calculate_distance(new_pos, target_pos)
                if dist < min_dist:
                    min_dist = dist
                    best_move = new_pos
        
        if best_move != (monster.x, monster.y):
            monster.x, monster.y = best_move
            self.combat_manager.update_dungeon_monster_position(monster, monster.x, monster.y)
            self.combat_manager.log_message(f"{monster.name} moves closer!")
        else:
            self.combat_manager.log_message(f"{monster.name} holds its position.")
    
    def _update_dungeon_monsters(self, dungeon: DungeonExplorer):
        """Update the dungeon's monster list based on combat results."""
        monsters_to_remove = []
        all_combat_monsters = [p for p in self.combat_manager.participants if isinstance(p, CombatMonster)]

        for combat_monster in all_combat_monsters:
            for dungeon_monster in dungeon.monsters:
                if (dungeon_monster.x == combat_monster.x and 
                    dungeon_monster.y == combat_monster.y and
                    dungeon_monster.name == combat_monster.name):
                    if not combat_monster.is_alive:
                        if dungeon_monster not in monsters_to_remove:
                            monsters_to_remove.append(dungeon_monster)
                    else:
                        # Update monster state
                        dungeon_monster.current_hp = combat_monster.hp
                        if hasattr(combat_monster, 'has_fled'):
                            dungeon_monster.fled = combat_monster.has_fled
                    break

        # Remove dead monsters
        for dead_monster in monsters_to_remove:
            dungeon.monsters.remove(dead_monster)