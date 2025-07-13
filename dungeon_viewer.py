# dungeon_viewer.py - Improved combat flow
import pygame
import json
import time
from typing import List, Tuple

# Import all our modules
from game_constants import *
from dungeon_classes import DungeonExplorer
from ui_systems import *
from rendering_engine import *
from character_creation import run_character_creation, Player
from monster_system import get_monster_database
from combat_system import (
    CombatManager, CombatState, CombatActionState, CombatMonster, 
    calculate_distance, is_adjacent, check_for_combat, 
    handle_monster_ai_turn, draw_combat_ui, draw_combat_action_menu, 
    draw_health_bars, get_stat_modifier, get_weapon_damage,
    attempt_positional_attack, execute_positional_attack
)
from combat_effects import CombatEffectsManager, apply_damage_effects, draw_sprite_with_flash, enhanced_make_attack

# --- Combat helper functions ---
def execute_player_attack(combat_manager: CombatManager, player: Player, target_monster: CombatMonster, effects_manager: CombatEffectsManager = None):
    """Execute a player attack with visual effects"""
    player_participant = combat_manager.get_player_in_combat()
    if player_participant:
        weapon_damage = get_weapon_damage(player)
        attack_bonus = get_stat_modifier(player.strength)
        
        # Add weapon mastery bonus for fighters
        if player.character_class == "Fighter":
            attack_bonus += player.level // 2
        
        damage_bonus = get_stat_modifier(player.strength)
        
        # Use enhanced attack with effects
        enhanced_make_attack(combat_manager, player_participant, target_monster, weapon_damage, attack_bonus, damage_bonus, effects_manager)

def execute_positional_attack_with_effects(combat_manager: CombatManager, player: Player, target_monster: CombatMonster, effects_manager: CombatEffectsManager = None):
    """Execute an attack from positional movement with visual effects"""
    player_participant = combat_manager.get_player_in_combat()
    if player_participant:
        weapon_damage = get_weapon_damage(player)
        
        # Calculate attack bonus
        attack_bonus = get_stat_modifier(player.strength)
        if player.character_class == "Fighter":
            attack_bonus += player.level // 2
        
        # Calculate damage bonus
        damage_bonus = get_stat_modifier(player.strength)
        
        # Use enhanced attack with effects
        enhanced_make_attack(combat_manager, player_participant, target_monster, weapon_damage, attack_bonus, damage_bonus, effects_manager)
        return True
    return False

def handle_monster_ai_turn_with_effects(monster, player_pos, combat_manager, walkable_positions, effects_manager=None):
    """Handle AI for monster's turn in combat with visual effects."""
    
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
                 # Use enhanced attack with effects
                 enhanced_make_attack(combat_manager, monster, player_participant, damage, attack_bonus, damage_bonus, effects_manager)
        
        return

    # --- Standard Combat Behavior (Attack or Approach) ---
    if is_adjacent(monster_pos, player_pos):
        # If adjacent, attack the player
        attack_bonus = getattr(monster, 'attack_bonus', 0)
        damage_bonus = get_stat_modifier(monster.strength)
        damage = monster.damage
        # Use enhanced attack with effects
        enhanced_make_attack(combat_manager, monster, player_participant, damage, attack_bonus, damage_bonus, effects_manager)
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

def process_full_combat_round(combat_manager, player, player_pos, target_monster, effects_manager, walkable_positions):
    """Process a complete combat round: initiative, player action, all monster actions, check for end"""
    
    # Step 1: Player acts (attack or move)
    if target_monster:
        # Player is attacking
        execute_positional_attack_with_effects(combat_manager, player, target_monster, effects_manager)
        combat_manager.log_message(f"{player.name} attacks!")
    else:
        # Player is just moving/defending
        combat_manager.log_message(f"{player.name} moves and defends!")
    
    # Step 2: Process all monster turns automatically
    alive_monsters = combat_manager.get_monsters_in_combat()
    for monster in alive_monsters:
        if monster.is_alive and not monster.has_fled:
            handle_monster_ai_turn_with_effects(monster, player_pos, combat_manager, walkable_positions, effects_manager)
            
            # Update player HP in real-time after each monster attack
            player_participant = combat_manager.get_player_in_combat()
            if player_participant:
                player.hp = player_participant.hp
    
    # Step 3: Check if combat should end
    if combat_manager.should_end_combat():
        combat_manager.end_combat()
        return True  # Combat ended
    
    # Step 4: Reset turn order for next round
    combat_manager.current_turn_index = 0
    current = combat_manager.get_current_participant()
    if current:
        if isinstance(current, CombatMonster):
            combat_manager.state = CombatState.MONSTER_TURN
        else:
            combat_manager.state = CombatState.PLAYER_TURN
    
    return False  # Combat continues

def main():
    pygame.init()
    
    # Load data
    try:
        with open(JSON_FILE, 'r') as f:
            dungeon_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{JSON_FILE}' not found.")
        pygame.quit()
        return
    
    # Initialize game variables
    player = None
    dungeon = None
    
    # Display setup
    zoom_level = DEFAULT_ZOOM
    cell_size = int(BASE_CELL_SIZE * zoom_level)
    
    initial_width = INITIAL_VIEWPORT_WIDTH * cell_size
    initial_height = INITIAL_VIEWPORT_HEIGHT * cell_size

    screen = pygame.display.set_mode((initial_width, initial_height + HUD_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption(f"{dungeon_data.get('title', 'Dungeon')}")
    
    # Create fonts for the UI
    hud_font_large = pygame.font.Font(FONT_FILE, 28)
    hud_font_medium = pygame.font.Font(FONT_FILE, 20)
    hud_font_small = pygame.font.Font(FONT_FILE, 14)
    coords_font = pygame.font.Font(FONT_FILE, 16)
    timer_font = pygame.font.Font(FONT_FILE, 22)
    spell_menu_font = pygame.font.Font(FONT_FILE, 20)

    # Initialize combat effects manager
    effects_manager = CombatEffectsManager(FONT_FILE)

    # Game state
    game_state = GameState.MAIN_MENU
    spell_target_pos = (0, 0)
    player_pos = (0, 0)
    walkable_positions = set()
    fullscreen = False
    current_spell = ""
    
    # Combat state
    combat_manager = CombatManager()
    combat_action_state = CombatActionState.SELECTING_ACTION
    selected_combat_action = 0
    combat_target_cursor = (0, 0)
    
    # Inventory/Equipment state
    inventory_selected_index = 0
    equipment_selected_slot = 'weapon'
    equipment_selection_mode = False
    equipment_selection_index = 0
    container_selected_index = 0
    container_view_selected_index = 0
    item_action_selected_index = 0
    current_container = None
    current_containers = []
    
    # Initialize viewport variables
    viewport_width_cells = 0
    viewport_height_cells = 0
    viewport_x = 0
    viewport_y = 0
    player_font = None
    spell_cursor_font = None
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Calculate delta time for smooth animations
        dt = clock.tick(60)
        dt_seconds = dt / 1000.0
        
        # Update combat effects
        effects_manager.update(dt_seconds)
        
        # Get current screen dimensions
        screen_width, screen_height = screen.get_size()
        game_area_height = screen_height - HUD_HEIGHT
        
        # Update rendering values based on zoom (only when playing)
        if game_state == GameState.PLAYING and player is not None and dungeon is not None:
            cell_size = int(BASE_CELL_SIZE * zoom_level)
            player_font = pygame.font.Font(FONT_FILE, max(8, int(BASE_FONT_SIZE * zoom_level)))
            spell_cursor_font = pygame.font.Font(FONT_FILE, cell_size)
            
            # Calculate dynamic viewport dimensions in cells
            viewport_width_cells = screen_width // cell_size
            viewport_height_cells = game_area_height // cell_size

            # Calculate world coordinates of the top-left corner of the viewport
            viewport_x = player_pos[0] - viewport_width_cells // 2
            viewport_y = player_pos[1] - viewport_height_cells // 2
        
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == GameState.PLAYING and combat_manager.state == CombatState.NOT_IN_COMBAT:
                        running = False
                    elif game_state in [GameState.SPELL_MENU, GameState.SPELL_TARGETING]:
                        game_state = GameState.PLAYING
                    elif game_state == GameState.INVENTORY:
                        game_state = GameState.PLAYING
                    elif game_state == GameState.CONTAINER_VIEW:
                        game_state = GameState.INVENTORY
                    elif game_state == GameState.ITEM_ACTION:
                        game_state = GameState.CONTAINER_VIEW
                    elif game_state == GameState.EQUIPMENT:
                        if equipment_selection_mode:
                            equipment_selection_mode = False
                        else:
                            game_state = GameState.PLAYING
                    else:
                        running = False

                # Game controls
                if game_state == GameState.PLAYING:
                    if event.key == pygame.K_F11:
                        fullscreen = not fullscreen
                        if fullscreen:
                            info = pygame.display.Info()
                            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((initial_width, initial_height + HUD_HEIGHT), pygame.RESIZABLE)
                        
                        screen_width, screen_height = screen.get_size()
                    elif event.key in [pygame.K_PLUS, pygame.K_EQUALS]:
                        zoom_level = min(zoom_level + ZOOM_STEP, MAX_ZOOM)
                    elif event.key == pygame.K_MINUS:
                        zoom_level = max(zoom_level - ZOOM_STEP, MIN_ZOOM)
                    elif event.key == pygame.K_m:
                        if combat_manager.state == CombatState.NOT_IN_COMBAT:
                            game_state = GameState.SPELL_MENU
                            spell_target_pos = player_pos
                    elif event.key == pygame.K_i:
                        if combat_manager.state == CombatState.NOT_IN_COMBAT:
                            game_state = GameState.INVENTORY
                            inventory_selected_index = 0
                            current_containers = organize_inventory_into_containers(player)
                    elif event.key == pygame.K_e:
                        if combat_manager.state == CombatState.NOT_IN_COMBAT:
                            game_state = GameState.EQUIPMENT
                            equipment_selected_slot = 'weapon'
                            equipment_selection_mode = False
                    
                    # Movement and combat handling
                    if combat_manager.state == CombatState.NOT_IN_COMBAT:
                        # Normal movement - check for combat initiation
                        next_pos = player_pos
                        moved = False
                        if event.key in [pygame.K_UP, pygame.K_w]:
                            next_pos = (player_pos[0], player_pos[1] - 1)
                            moved = True
                        elif event.key in [pygame.K_DOWN, pygame.K_s]:
                            next_pos = (player_pos[0], player_pos[1] + 1)
                            moved = True
                        elif event.key in [pygame.K_LEFT, pygame.K_a]:
                            next_pos = (player_pos[0] - 1, player_pos[1])
                            moved = True
                        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                            next_pos = (player_pos[0] + 1, player_pos[1])
                            moved = True
                        
                        if moved:
                            monster_at_target = None
                            for m in dungeon.monsters:
                                if (m.x, m.y) == next_pos and dungeon.is_revealed(m.x, m.y):
                                    monster_at_target = m
                                    break
                            
                            if monster_at_target:
                                # IMPROVED: Initiate combat and immediately process first round
                                print(f"Combat initiated with {monster_at_target.name}!")
                                
                                # Start combat with all monsters adjacent to the player's CURRENT position
                                monsters_in_combat, surprised_monsters = check_for_combat(player_pos, dungeon.monsters, dungeon)
                                combat_manager.start_combat(player, player_pos, monsters_in_combat, surprised_monsters, dungeon.monsters)
                                
                                # Roll initiative
                                dex_modifier = get_stat_modifier(player.dexterity)
                                combat_manager.roll_initiative(dex_modifier)
                                
                                # Find the target monster in combat participants
                                target_combat_monster = None
                                for combat_participant in combat_manager.participants:
                                    if (isinstance(combat_participant, CombatMonster) and 
                                        combat_participant.x == monster_at_target.x and 
                                        combat_participant.y == monster_at_target.y):
                                        target_combat_monster = combat_participant
                                        break
                                
                                # Process the full combat round immediately
                                combat_ended = process_full_combat_round(
                                    combat_manager, player, player_pos, target_combat_monster, 
                                    effects_manager, walkable_positions
                                )
                                
                                if combat_ended:
                                    # Handle combat end immediately
                                    player_participant = combat_manager.get_player_in_combat()
                                    if player_participant:
                                        player.hp = player_participant.hp
                                    
                                    # Update dungeon monsters
                                    monsters_to_remove = []
                                    all_combat_monsters = [p for p in combat_manager.participants if isinstance(p, CombatMonster)]

                                    for combat_monster in all_combat_monsters:
                                        for dungeon_monster in dungeon.monsters:
                                            if (dungeon_monster.x == combat_monster.x and 
                                                dungeon_monster.y == combat_monster.y):
                                                if not combat_monster.is_alive:
                                                    if dungeon_monster not in monsters_to_remove:
                                                        monsters_to_remove.append(dungeon_monster)
                                                else:
                                                    dungeon_monster.current_hp = combat_monster.hp
                                                    if hasattr(combat_monster, 'has_fled'):
                                                        dungeon_monster.fled = combat_monster.has_fled
                                                break

                                    for dead in monsters_to_remove:
                                        dungeon.monsters.remove(dead)
                                    
                                    combat_manager.state = CombatState.NOT_IN_COMBAT

                            elif next_pos in walkable_positions:
                                # Safe movement, no monster at destination
                                player_pos = next_pos
                                
                                # Auto-open doors
                                tile_at_pos = dungeon.tiles.get(player_pos)
                                if tile_at_pos in [TileType.DOOR_HORIZONTAL, TileType.DOOR_VERTICAL]:
                                    if dungeon.open_door_at_position(player_pos[0], player_pos[1]):
                                        walkable_positions = dungeon.get_walkable_positions(for_monster=False)
                                
                                # Move monsters (existing code)
                                occupied_tiles = {(m.x, m.y) for m in dungeon.monsters}
                                occupied_tiles.add(player_pos)
                                monster_walkable = dungeon.get_walkable_positions(for_monster=True)

                                for monster in dungeon.monsters:
                                    if monster.room_id in dungeon.revealed_rooms:
                                        dx = player_pos[0] - monster.x
                                        dy = player_pos[1] - monster.y
                                        
                                        next_monster_pos = monster.x, monster.y
                                        if abs(dx) > abs(dy):
                                            next_monster_pos = (monster.x + (1 if dx > 0 else -1), monster.y)
                                        else:
                                            next_monster_pos = (monster.x, monster.y + (1 if dy > 0 else -1))
                                        
                                        if next_monster_pos in monster_walkable and next_monster_pos not in occupied_tiles:
                                            monster.x, monster.y = next_monster_pos
                    
                    # IMPROVED: Positional combat during player's turn
                    elif combat_manager.state == CombatState.PLAYER_TURN:
                        # In combat, movement = attack if moving into monster, or movement + full round processing
                        next_pos = player_pos
                        moved = False
                        
                        if event.key in [pygame.K_UP, pygame.K_w]:
                            next_pos = (player_pos[0], player_pos[1] - 1)
                            moved = True
                        elif event.key in [pygame.K_DOWN, pygame.K_s]:
                            next_pos = (player_pos[0], player_pos[1] + 1)
                            moved = True
                        elif event.key in [pygame.K_LEFT, pygame.K_a]:
                            next_pos = (player_pos[0] - 1, player_pos[1])
                            moved = True
                        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                            next_pos = (player_pos[0] + 1, player_pos[1])
                            moved = True
                        elif event.key == pygame.K_SPACE:
                            # Space = skip turn / defend - process full round with no target
                            combat_ended = process_full_combat_round(
                                combat_manager, player, player_pos, None, 
                                effects_manager, walkable_positions
                            )
                            
                            if combat_ended:
                                # Handle combat end
                                player_participant = combat_manager.get_player_in_combat()
                                if player_participant:
                                    player.hp = player_participant.hp
                                
                                # Update dungeon monsters (same code as above)
                                monsters_to_remove = []
                                all_combat_monsters = [p for p in combat_manager.participants if isinstance(p, CombatMonster)]

                                for combat_monster in all_combat_monsters:
                                    for dungeon_monster in dungeon.monsters:
                                        if (dungeon_monster.x == combat_monster.x and 
                                            dungeon_monster.y == combat_monster.y):
                                            if not combat_monster.is_alive:
                                                if dungeon_monster not in monsters_to_remove:
                                                    monsters_to_remove.append(dungeon_monster)
                                            else:
                                                dungeon_monster.current_hp = combat_monster.hp
                                                if hasattr(combat_monster, 'has_fled'):
                                                    dungeon_monster.fled = combat_monster.has_fled
                                            break

                                for dead in monsters_to_remove:
                                    dungeon.monsters.remove(dead)
                                
                                combat_manager.state = CombatState.NOT_IN_COMBAT
                            moved = False
                        
                        if moved:
                            # Check if moving into a monster (= attack)
                            can_attack, target_monster = attempt_positional_attack(player_pos, next_pos, combat_manager, dungeon.monsters)
                            
                            if can_attack and target_monster:
                                # Process full combat round with this attack
                                combat_ended = process_full_combat_round(
                                    combat_manager, player, player_pos, target_monster, 
                                    effects_manager, walkable_positions
                                )
                                
                                if combat_ended:
                                    # Handle combat end (same code as above)
                                    player_participant = combat_manager.get_player_in_combat()
                                    if player_participant:
                                        player.hp = player_participant.hp
                                    
                                    monsters_to_remove = []
                                    all_combat_monsters = [p for p in combat_manager.participants if isinstance(p, CombatMonster)]

                                    for combat_monster in all_combat_monsters:
                                        for dungeon_monster in dungeon.monsters:
                                            if (dungeon_monster.x == combat_monster.x and 
                                                dungeon_monster.y == combat_monster.y):
                                                if not combat_monster.is_alive:
                                                    if dungeon_monster not in monsters_to_remove:
                                                        monsters_to_remove.append(dungeon_monster)
                                                else:
                                                    dungeon_monster.current_hp = combat_monster.hp
                                                    if hasattr(combat_monster, 'has_fled'):
                                                        dungeon_monster.fled = combat_monster.has_fled
                                                break

                                    for dead in monsters_to_remove:
                                        dungeon.monsters.remove(dead)
                                    
                                    combat_manager.state = CombatState.NOT_IN_COMBAT
                                    
                            elif next_pos in walkable_positions:
                                # Safe movement in combat - process full round with movement
                                player_pos = next_pos
                                combat_manager.log_message(f"{player.name} moves to {next_pos}")
                                
                                combat_ended = process_full_combat_round(
                                    combat_manager, player, player_pos, None, 
                                    effects_manager, walkable_positions
                                )
                                
                                if combat_ended:
                                    # Handle combat end (same code as above)
                                    player_participant = combat_manager.get_player_in_combat()
                                    if player_participant:
                                        player.hp = player_participant.hp
                                    
                                    monsters_to_remove = []
                                    all_combat_monsters = [p for p in combat_manager.participants if isinstance(p, CombatMonster)]

                                    for combat_monster in all_combat_monsters:
                                        for dungeon_monster in dungeon.monsters:
                                            if (dungeon_monster.x == combat_monster.x and 
                                                dungeon_monster.y == combat_monster.y):
                                                if not combat_monster.is_alive:
                                                    if dungeon_monster not in monsters_to_remove:
                                                        monsters_to_remove.append(dungeon_monster)
                                                else:
                                                    dungeon_monster.current_hp = combat_monster.hp
                                                    if hasattr(combat_monster, 'has_fled'):
                                                        dungeon_monster.fled = combat_monster.has_fled
                                                break

                                    for dead in monsters_to_remove:
                                        dungeon.monsters.remove(dead)
                                    
                                    combat_manager.state = CombatState.NOT_IN_COMBAT
                            else:
                                # Can't move there
                                combat_manager.log_message("Can't move there!")
                        
                        elif event.key == pygame.K_SPACE:
                            # Open doors (only when not in combat)
                            if combat_manager.state == CombatState.NOT_IN_COMBAT:
                                for dx, dy in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
                                    if dungeon.open_door_at_position(player_pos[0] + dx, player_pos[1] + dy):
                                        walkable_positions = dungeon.get_walkable_positions(for_monster=False)
                                        break

                # Spell menu controls
                elif game_state == GameState.SPELL_MENU:
                    if event.key == pygame.K_1:
                        current_spell = "Burning Hands"
                        game_state = GameState.SPELL_TARGETING

                # Spell targeting controls
                elif game_state == GameState.SPELL_TARGETING:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        new_target = (spell_target_pos[0], spell_target_pos[1] - 1)
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        new_target = (spell_target_pos[0], spell_target_pos[1] + 1)
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        new_target = (spell_target_pos[0] - 1, spell_target_pos[1])
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        new_target = (spell_target_pos[0] + 1, spell_target_pos[1])
                        if is_valid_spell_target(player_pos, new_target, current_spell):
                            spell_target_pos = new_target
                    elif event.key == pygame.K_RETURN:
                        print(f"Casting {current_spell} at {spell_target_pos}!")
                        game_state = GameState.PLAYING

                # Inventory controls
                elif game_state == GameState.INVENTORY:
                    if event.key == pygame.K_UP:
                        if current_containers:
                            inventory_selected_index = (inventory_selected_index - 1) % len(current_containers)
                    elif event.key == pygame.K_DOWN:
                        if current_containers:
                            inventory_selected_index = (inventory_selected_index + 1) % len(current_containers)
                    elif event.key == pygame.K_RETURN:
                        if current_containers and 0 <= inventory_selected_index < len(current_containers):
                            current_container = current_containers[inventory_selected_index]
                            container_view_selected_index = 0
                            game_state = GameState.CONTAINER_VIEW

                # Equipment controls  
                elif game_state == GameState.EQUIPMENT:
                    if not equipment_selection_mode:
                        equipment_slots = ['weapon', 'armor', 'shield', 'light']
                        if event.key == pygame.K_UP:
                            current_index = equipment_slots.index(equipment_selected_slot)
                            equipment_selected_slot = equipment_slots[(current_index - 1) % len(equipment_slots)]
                        elif event.key == pygame.K_DOWN:
                            current_index = equipment_slots.index(equipment_selected_slot)
                            equipment_selected_slot = equipment_slots[(current_index + 1) % len(equipment_slots)]
                        elif event.key == pygame.K_RETURN:
                            equipment_selection_mode = True
                            equipment_selection_index = 0
                    else:
                        # Equipment selection mode
                        available_items = get_available_items_for_slot(player, equipment_selected_slot)
                        available_items.insert(0, None)  # Add unequip option
                        
                        if event.key == pygame.K_UP:
                            equipment_selection_index = (equipment_selection_index - 1) % len(available_items)
                        elif event.key == pygame.K_DOWN:
                            equipment_selection_index = (equipment_selection_index + 1) % len(available_items)
                        elif event.key == pygame.K_RETURN:
                            selected_item = available_items[equipment_selection_index]
                            
                            if selected_item is None:
                                unequip_item(player, equipment_selected_slot)
                            else:
                                equip_item(player, selected_item, equipment_selected_slot)
                            
                            equipment_selection_mode = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == GameState.MAIN_MENU:
                    if 'start_button_rect' in locals() and start_button_rect.collidepoint(event.pos):
                        # Start character creation
                        pygame.display.quit()
                        created_player = run_character_creation(screen_width, screen_height, FONT_FILE)
                        
                        if created_player is None:
                            running = False
                            break
                        
                        # Character creation successful
                        if fullscreen:
                            info = pygame.display.Info()  
                            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                        pygame.display.set_caption(f"{dungeon_data.get('title', 'Dungeon')}")
                        
                        player = created_player
                        player.ac = calculate_armor_class(player)
                        
                        # Update gear slots if Fighter with Constitution bonus
                        if player.character_class == "Fighter":
                            constitution_bonus = get_stat_modifier(player.constitution)
                            if constitution_bonus > 0:
                                player.max_gear_slots += constitution_bonus
                        
                        # Calculate actual gear slots used from inventory
                        player.gear_slots_used = 0
                        for inv_item in player.inventory:
                            item_slots = getattr(inv_item.item, 'gear_slots', 1)
                            if hasattr(inv_item.item, 'quantity_per_slot') and inv_item.item.quantity_per_slot > 1:
                                slots_needed = (inv_item.quantity + inv_item.item.quantity_per_slot - 1) // inv_item.item.quantity_per_slot
                                player.gear_slots_used += slots_needed * item_slots
                            else:
                                player.gear_slots_used += item_slots * inv_item.quantity
                        
                        print(f"Player created with {len(player.inventory)} items")
                        print(f"Player gold: {player.gold}")
                        print(f"Gear slots: {player.gear_slots_used}/{player.max_gear_slots}")
                        
                        dungeon = DungeonExplorer(dungeon_data)
                        player_pos = dungeon.get_starting_position()
                        walkable_positions = dungeon.get_walkable_positions(for_monster=False)
                        game_state = GameState.PLAYING

        # --- RENDER ---
        if game_state == GameState.MAIN_MENU:
            start_button_rect = draw_main_menu(screen, hud_font_large, hud_font_medium)
        
        elif game_state == GameState.INVENTORY:
            draw_inventory_screen(screen, player, inventory_selected_index, hud_font_medium, hud_font_small)
        
        elif game_state == GameState.EQUIPMENT:
            if equipment_selection_mode:
                draw_equipment_screen(screen, player, equipment_selected_slot, hud_font_medium, hud_font_small)
                show_equipment_selection(screen, player, equipment_selected_slot, equipment_selection_index, hud_font_medium, hud_font_small)
            else:
                draw_equipment_screen(screen, player, equipment_selected_slot, hud_font_medium, hud_font_small)
        
        elif game_state == GameState.PLAYING and player is not None and dungeon is not None:
            # Ensure fonts are available for rendering
            if player_font is None:
                cell_size = int(BASE_CELL_SIZE * zoom_level)
                player_font = pygame.font.Font(FONT_FILE, max(8, int(BASE_FONT_SIZE * zoom_level)))
                spell_cursor_font = pygame.font.Font(FONT_FILE, cell_size)
                
                viewport_width_cells = screen_width // cell_size
                viewport_height_cells = game_area_height // cell_size
                viewport_x = player_pos[0] - viewport_width_cells // 2
                viewport_y = player_pos[1] - viewport_height_cells // 2
            
            screen.fill(COLOR_BG)
            
            # Create viewport surface
            viewport_surface = pygame.Surface((screen_width, game_area_height))
            viewport_surface.fill(COLOR_BG)
            
            # Draw tiles
            for screen_cell_y in range(viewport_height_cells + 2):
                for screen_cell_x in range(viewport_width_cells + 2):
                    world_x = viewport_x + screen_cell_x
                    world_y = viewport_y + screen_cell_y
                    
                    tile_type = dungeon.tiles.get((world_x, world_y), TileType.VOID)
                    
                    # Check visibility - fog of war rules
                    if dungeon.is_revealed(world_x, world_y):
                        draw_tile(viewport_surface, tile_type, screen_cell_x, screen_cell_y, cell_size)
            
            # Draw terrain features (water) on top of tiles but under walls
            draw_terrain_features(viewport_surface, dungeon, viewport_x, viewport_y, cell_size)
            
            # Draw walls using proper marching squares
            draw_boundary_walls(viewport_surface, dungeon, viewport_x, viewport_y, cell_size, viewport_width_cells, viewport_height_cells)
            
            # Draw spell range indicator if targeting
            if game_state == GameState.SPELL_TARGETING:
                draw_spell_range_indicator(viewport_surface, player_pos, current_spell, viewport_x, viewport_y, cell_size, viewport_width_cells, viewport_height_cells)
            
            # Draw monsters with flash effects
            for monster in dungeon.monsters:
                if dungeon.is_revealed(monster.x, monster.y):
                    monster_screen_x = (monster.x - viewport_x) * cell_size + (cell_size // 2)
                    monster_screen_y = (monster.y - viewport_y) * cell_size + (cell_size // 2)
                    
                    # Use monster's ASCII character if available, otherwise default icon
                    if hasattr(monster, 'template') and hasattr(monster.template, 'ascii_char'):
                        monster_char = monster.template.ascii_char
                    else:
                        monster_char = UI_ICONS["MONSTER"]
                    
                    # Draw monster with flash effects
                    draw_sprite_with_flash(
                        viewport_surface, 
                        monster_char, 
                        player_font, 
                        (monster_screen_x, monster_screen_y), 
                        COLOR_MONSTER, 
                        effects_manager, 
                        monster.x, 
                        monster.y
                    )

            # Draw combat elements if in combat
            if combat_manager.state != CombatState.NOT_IN_COMBAT:
                draw_health_bars(viewport_surface, combat_manager, viewport_x, viewport_y, cell_size, hud_font_small)

            # Draw player with flash effects
            player_screen_x = (viewport_width_cells // 2) * cell_size + (cell_size // 2)
            player_screen_y = (viewport_height_cells // 2) * cell_size + (cell_size // 2)
            
            draw_sprite_with_flash(
                viewport_surface, 
                '@', 
                player_font, 
                (player_screen_x, player_screen_y), 
                COLOR_PLAYER, 
                effects_manager, 
                player_pos[0], 
                player_pos[1]
            )
            
            # Draw spell cursor if targeting
            if game_state == GameState.SPELL_TARGETING:
                cursor_screen_x = (spell_target_pos[0] - viewport_x) * cell_size + (cell_size // 2)
                cursor_screen_y = (spell_target_pos[1] - viewport_y) * cell_size + (cell_size // 2)
                cursor_surf = spell_cursor_font.render(UI_ICONS["SPELL_CURSOR"], True, COLOR_SPELL_CURSOR)
                cursor_rect = cursor_surf.get_rect(center=(cursor_screen_x, cursor_screen_y))
                viewport_surface.blit(cursor_surf, cursor_rect)

            # Draw floating damage numbers and effects
            effects_manager.draw_floating_texts(viewport_surface, viewport_x, viewport_y, cell_size)

            # Blit viewport to screen
            screen.blit(viewport_surface, (0, 0))
            
            # Draw screen flash effects (after blitting viewport)
            effects_manager.draw_screen_flash(screen)
            
            # Display coordinates and timer
            coord_text = f"({player_pos[0]}, {player_pos[1]})"
            coord_surf = coords_font.render(coord_text, True, COLOR_WALL)
            screen.blit(coord_surf, (10, 10))
            
            draw_timer_box(screen, player, timer_font)

            # Draw HUD
            draw_hud(screen, player, hud_font_large, hud_font_medium, hud_font_small)

            # Draw combat UI if in combat (simplified)
            if combat_manager.state != CombatState.NOT_IN_COMBAT:
                draw_combat_ui(screen, combat_manager, hud_font_medium, hud_font_small)
                
                # Show simple instructions for positional combat
                if combat_manager.state == CombatState.PLAYER_TURN:
                    instruction_text = "Move into enemy to attack • SPACE to defend/wait"
                    inst_surf = hud_font_small.render(instruction_text, True, COLOR_WHITE)
                    inst_rect = inst_surf.get_rect(centerx=screen_width//2, bottom=screen_height - HUD_HEIGHT - 10)
                    
                    # Background for visibility
                    bg_rect = inst_rect.inflate(20, 10)
                    pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect)
                    screen.blit(inst_surf, inst_rect)

            # Draw spell menu if active
            if game_state == GameState.SPELL_MENU:
                draw_spell_menu(screen, spell_menu_font, ["Fireball", "Magic Missile", "Invisibility"])
        else:
            # Fallback for any other state
            screen.fill(COLOR_BG)

        pygame.display.flip()
    
    pygame.quit()

if __name__ == '__main__':
    main()