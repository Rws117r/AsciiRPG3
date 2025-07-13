# combat_system.py - Updated version with combat effects integration
import pygame
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

class CombatState(Enum):
    NOT_IN_COMBAT = 0
    INITIATIVE_ROLL = 1
    PLAYER_TURN = 2
    MONSTER_TURN = 3
    COMBAT_OVER = 4

class CombatActionState(Enum):
    SELECTING_ACTION = 0
    SELECTING_TARGET = 1
    SELECTING_MOVEMENT = 2
    POSITIONAL_COMBAT = 3

@dataclass
class CombatParticipant:
    """Base class for anything that can participate in combat"""
    name: str
    x: int
    y: int
    hp: int
    max_hp: int
    ac: int
    initiative: int = 0
    is_alive: bool = True
    conditions: List[str] = field(default_factory=list)
    # Add stats to the combat participant to calculate bonuses
    strength: int = 10
    dexterity: int = 10


@dataclass 
class CombatMonster(CombatParticipant):
    """Monster in combat"""
    damage: str = "1d6"
    attack_bonus: int = 0
    has_fled: bool = False
    room_id: int = -1

class CombatManager:
    """Manages combat state and turn order"""
    
    def __init__(self):
        self.state = CombatState.NOT_IN_COMBAT
        self.participants = []
        self.turn_order = []
        self.current_turn_index = 0
        self.combat_log = []
        self.surprise_participants = []
        # Add reference to dungeon monsters for position updates
        self.dungeon_monsters = []
        
    def start_combat(self, player, player_pos, monsters, surprised_monsters=None, dungeon_monsters=None):
        """Initialize combat with player and monsters"""
        self.state = CombatState.INITIATIVE_ROLL
        self.participants = []
        self.combat_log = []
        self.surprise_participants = []
        # Store reference to the dungeon monsters list for position updates
        self.dungeon_monsters = dungeon_monsters if dungeon_monsters else monsters
        
        # Add player to combat
        player_combat = CombatParticipant(
            name=player.name,
            x=player_pos[0],
            y=player_pos[1],
            hp=player.hp,
            max_hp=player.max_hp,
            ac=player.ac,
            strength=player.strength,
            dexterity=player.dexterity
        )
        self.participants.append(player_combat)
        
        # Add monsters to combat - now using MonsterInstance data
        for monster in monsters:
            # Check if it's a MonsterInstance (new system) or old Monster
            if hasattr(monster, 'template'):
                # New MonsterInstance
                monster_combat = CombatMonster(
                    name=monster.name,
                    x=monster.x,
                    y=monster.y,
                    hp=monster.current_hp,
                    max_hp=monster.max_hp,
                    ac=monster.template.ac,
                    damage=monster.get_damage_dice(),
                    attack_bonus=monster.get_attack_bonus(),
                    room_id=monster.room_id,
                    has_fled=monster.fled,
                    strength=monster.template.stats.get("strength", 10),
                    dexterity=monster.template.stats.get("dexterity", 10)
                )
            else:
                # Old Monster (fallback)
                monster_combat = CombatMonster(
                    name="Monster",
                    x=monster.x,
                    y=monster.y,
                    hp=8,
                    max_hp=8,
                    ac=12,
                    damage="1d6",
                    attack_bonus=2,
                    room_id=getattr(monster, 'room_id', -1)
                )
            
            self.participants.append(monster_combat)
        
        # Handle surprise
        if surprised_monsters:
            for surprised in surprised_monsters:
                for participant in self.participants:
                    if isinstance(participant, CombatMonster) and participant.x == surprised.x and participant.y == surprised.y:
                        participant.conditions.append("surprised")
                        self.surprise_participants.append(participant)
        
        self.log_message("Combat begins!")
    
    def roll_initiative(self, player_dex_modifier=0):
        """Roll initiative for all participants"""
        for participant in self.participants:
            if not isinstance(participant, CombatMonster):
                participant.initiative = self.roll_d20() + player_dex_modifier
            else: # Is a monster
                participant.initiative = self.roll_d20() + 1
        
        self.turn_order = sorted(self.participants, key=lambda p: p.initiative, reverse=True)
        self.current_turn_index = 0
        
        for i, participant in enumerate(self.turn_order):
            self.log_message(f"Initiative {i+1}: {participant.name} ({participant.initiative})")

        # Set initial turn state
        current = self.get_current_participant()
        if current:
            if isinstance(current, CombatMonster):
                self.state = CombatState.MONSTER_TURN
            else:
                self.state = CombatState.PLAYER_TURN
        return self.turn_order
    
    def get_current_participant(self):
        """Get the participant whose turn it is"""
        if not self.turn_order or self.current_turn_index >= len(self.turn_order):
            return None
        return self.turn_order[self.current_turn_index]
    
    def advance_turn(self):
        """Move to the next participant's turn"""
        self.current_turn_index += 1
        
        # Skip dead participants
        while (self.current_turn_index < len(self.turn_order) and 
               not self.turn_order[self.current_turn_index].is_alive):
            self.current_turn_index += 1
        
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.log_message("--- New Round ---")
        
        current = self.get_current_participant()
        if current:
            if isinstance(current, CombatMonster):
                self.state = CombatState.MONSTER_TURN
            else:
                self.state = CombatState.PLAYER_TURN
        
        if self.should_end_combat():
            self.end_combat()
    
    def should_end_combat(self):
        """Check if combat should end"""
        alive_players = [p for p in self.participants if not isinstance(p, CombatMonster) and p.is_alive]
        alive_monsters = [p for p in self.participants if isinstance(p, CombatMonster) and p.is_alive and not getattr(p, 'has_fled', False)]
        return len(alive_players) == 0 or len(alive_monsters) == 0
    
    def end_combat(self):
        """End combat and clean up"""
        self.state = CombatState.COMBAT_OVER
        self.log_message("Combat ends!")
    
    def log_message(self, message):
        """Add a message to the combat log"""
        self.combat_log.append(message)
        print(f"Combat: {message}")
    
    def roll_d20(self, advantage=False, disadvantage=False):
        """Roll a d20 with advantage/disadvantage"""
        if advantage and disadvantage:
            return random.randint(1, 20)
        elif advantage:
            return max(random.randint(1, 20), random.randint(1, 20))
        elif disadvantage:
            return min(random.randint(1, 20), random.randint(1, 20))
        else:
            return random.randint(1, 20)
    
    def roll_damage(self, damage_dice):
        """Roll damage dice (e.g., '1d6', '2d8+3')"""
        # Handle versatile weapon strings like "1d8/1d10" by taking the first part
        if "/" in damage_dice:
            damage_dice = damage_dice.split('/')[0]

        try:
            if '+' in damage_dice:
                dice_part, bonus = damage_dice.split('+')
                bonus = int(bonus)
            elif '-' in damage_dice:
                dice_part, penalty = damage_dice.split('-')
                bonus = -int(penalty)
            else:
                dice_part = damage_dice
                bonus = 0
            
            if 'd' in dice_part:
                num_dice, die_size = dice_part.split('d')
                num_dice = int(num_dice)
                die_size = int(die_size)
                total = sum(random.randint(1, die_size) for _ in range(num_dice))
                return max(1, total + bonus)
            else:
                return max(1, int(dice_part) + bonus)
        except:
            return 1
    
    def make_attack(self, attacker, target, weapon_damage="1d6", attack_bonus=0, damage_stat_modifier=0):
        """Make an attack roll and apply damage if hit"""
        has_advantage = "surprised" in target.conditions
        attack_roll = self.roll_d20(advantage=has_advantage)
        total_attack = attack_roll + attack_bonus
        
        self.log_message(f"{attacker.name} attacks {target.name} (AC {target.ac})")
        self.log_message(f"Attack roll: {attack_roll} + {attack_bonus} = {total_attack}")
        
        if attack_roll == 1:
            self.log_message("Natural 1 - automatic miss!")
            return False
        
        if total_attack >= target.ac or attack_roll == 20:
            is_critical = attack_roll == 20
            
            base_damage = self.roll_damage(weapon_damage)
            if is_critical:
                self.log_message("Critical hit!")
                # Roll all damage dice twice for a crit
                crit_damage = self.roll_damage(weapon_damage)
                damage = base_damage + crit_damage + damage_stat_modifier
            else:
                damage = base_damage + damage_stat_modifier
            
            damage = max(1, damage) # Ensure at least 1 damage
            
            target.hp -= damage
            self.log_message(f"{target.name} takes {damage} damage! ({target.hp}/{target.max_hp} HP remaining)")
            
            if target.hp <= 0:
                target.is_alive = False
                self.log_message(f"{target.name} falls unconscious!")
            
            if "surprised" in target.conditions:
                target.conditions.remove("surprised")
            
            return True
        else:
            self.log_message("Miss!")
            return False
    
    def check_morale(self, monster):
        """Check if monster flees due to low morale (when at or below 25% HP)."""
        morale_threshold = monster.max_hp / 4
        if monster.hp <= morale_threshold and not monster.has_fled:
            morale_roll = random.randint(1, 20)
            if morale_roll < 15:
                monster.has_fled = True
                self.log_message(f"{monster.name} flees in terror!")
                return True
        return False
    
    def update_dungeon_monster_position(self, combat_monster, new_x, new_y):
        """Update position of corresponding monster in dungeon list"""
        for dungeon_monster in self.dungeon_monsters:
            if (dungeon_monster.x == combat_monster.x and 
                dungeon_monster.y == combat_monster.y and 
                dungeon_monster.name == combat_monster.name):
                dungeon_monster.x = new_x
                dungeon_monster.y = new_y
                break
    
    def get_monsters_in_combat(self):
        """Get all monsters currently in combat"""
        return [p for p in self.participants if isinstance(p, CombatMonster) and p.is_alive and not p.has_fled]
    
    def get_player_in_combat(self):
        """Get the player participant"""
        for p in self.participants:
            if not isinstance(p, CombatMonster):
                return p
        return None

# Combat helper functions
def get_stat_modifier(stat_value):
    """Calculate ability modifier from stat value"""
    if stat_value <= 3:
        return -4
    elif stat_value <= 5:
        return -3
    elif stat_value <= 7:
        return -2
    elif stat_value <= 9:
        return -1
    elif stat_value <= 11:
        return 0
    elif stat_value <= 13:
        return +1
    elif stat_value <= 15:
        return +2
    elif stat_value <= 17:
        return +3
    else:
        return +4

def calculate_distance(pos1, pos2):
    """Calculate distance between two positions"""
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

def is_adjacent(pos1, pos2):
    """Check if two positions are adjacent"""
    return calculate_distance(pos1, pos2) <= 1

def get_weapon_damage(player):
    """Get damage string for player's equipped weapon"""
    if hasattr(player, 'equipment') and 'weapon' in player.equipment:
        weapon = player.equipment['weapon'].item
        if hasattr(weapon, 'damage'):
            return weapon.damage
    return "1d4"

def check_for_combat(player_pos, monsters, dungeon):
    """Check if player has encountered monsters and determine surprise"""
    adjacent_monsters = []
    surprised_monsters = []
    
    for monster in monsters:
        if dungeon.is_revealed(monster.x, monster.y):
            distance = calculate_distance(player_pos, (monster.x, monster.y))
            
            if distance == 1:
                adjacent_monsters.append(monster)
                
                if random.randint(1, 6) <= 2:
                    surprised_monsters.append(monster)
    
    return adjacent_monsters, surprised_monsters

def attempt_positional_attack(player_pos, target_pos, combat_manager, dungeon_monsters):
    """
    Attempt to attack a monster at the target position.
    Returns (True, monster) if an attack was made, (False, None) if movement should proceed normally.
    """
    target_monster = None
    for monster in dungeon_monsters:
        if (monster.x, monster.y) == target_pos:
            # Search all combat participants, not just ones that haven't fled
            for combat_participant in combat_manager.participants:
                if isinstance(combat_participant, CombatMonster) and combat_participant.x == monster.x and combat_participant.y == monster.y:
                    target_monster = combat_participant
                    break
            break
    
    if target_monster:
        return True, target_monster
    
    return False, None

def execute_positional_attack(combat_manager, player, target_monster):
    """Execute an attack from positional movement"""
    player_participant = combat_manager.get_player_in_combat()
    if player_participant:
        weapon_damage = get_weapon_damage(player)
        
        # Calculate attack bonus
        attack_bonus = get_stat_modifier(player.strength)
        if player.character_class == "Fighter":
            attack_bonus += 1 # Weapon Mastery
        
        # Calculate damage bonus
        damage_bonus = get_stat_modifier(player.strength)
        
        combat_manager.make_attack(player_participant, target_monster, weapon_damage, attack_bonus, damage_bonus)
        combat_manager.advance_turn()
        return True
    return False

def handle_monster_ai_turn(monster, player_pos, combat_manager, walkable_positions):
    """Handle AI for monster's turn in combat."""
    
    # Decide if the monster should start fleeing this turn.
    combat_manager.check_morale(monster)

    player_participant = combat_manager.get_player_in_combat()
    if not player_participant:
        return 

    player_pos = (player_participant.x, player_participant.y)
    monster_pos = (monster.x, monster.y)

    # --- Fleeing Behavior ---
    if monster.has_fled:
        best_flee_spot = None
        max_dist = -1

        # Check all 8 directions for a valid spot to flee to
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
            new_pos = (monster.x + dx, monster.y + dy)
            
            if new_pos in walkable_positions:
                dist_to_player = calculate_distance(new_pos, player_pos)
                if dist_to_player > max_dist:
                    max_dist = dist_to_player
                    best_flee_spot = new_pos
        
        if best_flee_spot and calculate_distance(best_flee_spot, player_pos) > calculate_distance(monster_pos, player_pos):
            # Update position AND sync with dungeon monsters
            old_x, old_y = monster.x, monster.y
            monster.x, monster.y = best_flee_spot
            # Update corresponding dungeon monster position
            combat_manager.update_dungeon_monster_position(monster, monster.x, monster.y)
            combat_manager.log_message(f"{monster.name} flees to ({monster.x}, {monster.y})!")
        else:
            combat_manager.log_message(f"{monster.name} is cornered and can't flee!")
            if is_adjacent(monster_pos, player_pos):
                 attack_bonus = getattr(monster, 'attack_bonus', 0)
                 damage_bonus = get_stat_modifier(monster.strength)
                 damage = monster.damage
                 combat_manager.make_attack(monster, player_participant, damage, attack_bonus, damage_bonus)
        
        return

    # --- Standard Combat Behavior (Attack or Approach) ---
    if is_adjacent(monster_pos, player_pos):
        # If adjacent, attack the player
        attack_bonus = getattr(monster, 'attack_bonus', 0)
        damage_bonus = get_stat_modifier(monster.strength)
        damage = monster.damage
        combat_manager.make_attack(monster, player_participant, damage, attack_bonus, damage_bonus)
    else:
        # If not adjacent, move towards the player
        best_move = monster_pos
        min_dist = calculate_distance(monster_pos, player_pos)

        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]: 
            new_pos = (monster.x + dx, monster.y + dy)
            if new_pos in walkable_positions:
                dist = calculate_distance(new_pos, player_pos)
                if dist < min_dist:
                    min_dist = dist
                    best_move = new_pos
        
        if best_move != monster_pos:
            # Update position AND sync with dungeon monsters
            old_x, old_y = monster.x, monster.y
            monster.x, monster.y = best_move
            # Update corresponding dungeon monster position
            combat_manager.update_dungeon_monster_position(monster, monster.x, monster.y)
            combat_manager.log_message(f"{monster.name} moves closer!")
        else:
            combat_manager.log_message(f"{monster.name} holds its position.")

# Combat UI functions
def draw_combat_ui(surface, combat_manager, font, small_font):
    """Draw combat UI elements"""
    if combat_manager.state == CombatState.NOT_IN_COMBAT:
        return
    
    screen_width, screen_height = surface.get_size()
    
    current = combat_manager.get_current_participant()
    if current:
        turn_text = f"{current.name}'s Turn"
        turn_surf = font.render(turn_text, True, (255, 255, 0))
        turn_rect = turn_surf.get_rect(centerx=screen_width//2, top=10)
        
        bg_rect = turn_rect.inflate(20, 10)
        pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect)
        surface.blit(turn_surf, turn_rect)
    
    draw_combat_log(surface, combat_manager, font, small_font)

def draw_combat_log(surface, combat_manager, font, small_font):
    """Draw combat log on screen"""
    if combat_manager.state == CombatState.NOT_IN_COMBAT:
        return
    
    screen_width, screen_height = surface.get_size()
    log_width = 400
    log_height = 200
    log_x = screen_width - log_width - 10
    log_y = 10
    
    log_rect = pygame.Rect(log_x, log_y, log_width, log_height)
    pygame.draw.rect(surface, (0, 0, 0, 200), log_rect)
    pygame.draw.rect(surface, (255, 255, 255), log_rect, 2)
    
    title_surf = font.render("Combat Log", True, (255, 255, 255))
    surface.blit(title_surf, (log_x + 10, log_y + 10))
    
    start_y = log_y + 40
    line_height = 18
    max_lines = 8
    
    recent_log = combat_manager.combat_log[-max_lines:] if len(combat_manager.combat_log) > max_lines else combat_manager.combat_log
    
    for i, message in enumerate(recent_log):
        if len(message) > 50:
            message = message[:47] + "..."
        
        message_surf = small_font.render(message, True, (255, 255, 255))
        surface.blit(message_surf, (log_x + 10, start_y + i * line_height))

def draw_combat_action_menu(surface, selected_action, font, small_font):
    """Draw the combat action selection menu"""
    actions = ["Attack", "Defend", "Move"]
    
    menu_width = 200
    menu_height = len(actions) * 30 + 40
    screen_width, screen_height = surface.get_size()
    
    menu_x = 20
    menu_y = screen_height - menu_height - 140
    
    menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
    pygame.draw.rect(surface, (0, 0, 0, 200), menu_rect)
    pygame.draw.rect(surface, (255, 255, 255), menu_rect, 2)
    
    title_surf = font.render("Combat Actions", True, (255, 255, 255))
    surface.blit(title_surf, (menu_x + 10, menu_y + 10))
    
    for i, action in enumerate(actions):
        y = menu_y + 35 + i * 25
        
        if i == selected_action:
            highlight_rect = pygame.Rect(menu_x + 5, y - 2, menu_width - 10, 20)
            pygame.draw.rect(surface, (100, 100, 200), highlight_rect)
        
        color = (255, 255, 255) if i == selected_action else (200, 200, 200)
        action_surf = small_font.render(f"{i+1}. {action}", True, color)
        surface.blit(action_surf, (menu_x + 10, y))

def draw_health_bars(surface, combat_manager, viewport_x, viewport_y, cell_size, small_font):
    """Draw health bars above combat participants"""
    for participant in combat_manager.participants:
        if not participant.is_alive:
            continue
        
        if isinstance(participant, CombatMonster):
            screen_x = (participant.x - viewport_x) * cell_size + (cell_size // 2)
            screen_y = (participant.y - viewport_y) * cell_size - 10
            
            bar_width = cell_size
            bar_height = 6
            bar_x = screen_x - bar_width // 2
            bar_y = screen_y - bar_height
            
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            
            health_ratio = participant.hp / participant.max_hp
            fill_width = int(bar_width * health_ratio)
            health_color = (255, 0, 0) if health_ratio < 0.3 else (255, 255, 0) if health_ratio < 0.7 else (0, 255, 0)
            pygame.draw.rect(surface, health_color, (bar_x, bar_y, fill_width, bar_height))
            
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
            
            hp_text = f"{participant.hp}/{participant.max_hp}"
            hp_surf = small_font.render(hp_text, True, (255, 255, 255))
            hp_rect = hp_surf.get_rect(centerx=screen_x, bottom=bar_y - 2)
            
            text_bg = hp_rect.inflate(4, 2)
            pygame.draw.rect(surface, (0, 0, 0, 150), text_bg)
            surface.blit(hp_surf, hp_rect)