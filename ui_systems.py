# ui_systems.py - All UI rendering and inventory/equipment systems
import pygame
import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from game_constants import *
from character_creation import Player

# --- Container/Backpack System ---
@dataclass
class Container:
    """Represents a container that can hold items"""
    name: str
    capacity: int  # Max gear slots it can hold
    contents: List = field(default_factory=list)  # List of InventoryItems
    
    def get_used_capacity(self) -> int:
        """Calculate how many gear slots are used in this container"""
        total = 0
        for inv_item in self.contents:
            try:
                from gear_selection import GearItem
                if hasattr(inv_item.item, 'gear_slots'):
                    slots_per_item = inv_item.item.gear_slots
                    if hasattr(inv_item.item, 'quantity_per_slot') and inv_item.item.quantity_per_slot > 1:
                        # Items that can stack
                        slots_needed = (inv_item.quantity + inv_item.item.quantity_per_slot - 1) // inv_item.item.quantity_per_slot
                        total += slots_needed * slots_per_item
                    else:
                        total += slots_per_item * inv_item.quantity
                else:
                    total += inv_item.quantity
            except ImportError:
                total += inv_item.quantity
        return total
    
    def can_fit_item(self, item, quantity: int = 1) -> bool:
        """Check if item can fit in this container"""
        try:
            from gear_selection import GearItem
            if hasattr(item, 'gear_slots'):
                slots_needed = item.gear_slots * quantity
                if hasattr(item, 'quantity_per_slot') and item.quantity_per_slot > 1:
                    slots_needed = (quantity + item.quantity_per_slot - 1) // item.quantity_per_slot
                return self.get_used_capacity() + slots_needed <= self.capacity
            else:
                return self.get_used_capacity() + quantity <= self.capacity
        except ImportError:
            return self.get_used_capacity() + quantity <= self.capacity

def is_container(item) -> bool:
    """Check if an item is a container"""
    return hasattr(item, 'name') and 'Backpack' in item.name

def get_containers_from_inventory(player: Player) -> List[Container]:
    """Get all containers from player's inventory"""
    containers = []
    
    # Find backpacks and convert them to containers
    for inv_item in player.inventory:
        if is_container(inv_item.item):
            # Create container for each backpack
            for i in range(inv_item.quantity):
                container_name = f"{inv_item.item.name} {i+1}" if inv_item.quantity > 1 else inv_item.item.name
                # Standard backpack holds all items the character can carry
                capacity = player.max_gear_slots
                containers.append(Container(container_name, capacity))
    
    # If no backpacks, create a default "carried items" container
    if not containers:
        containers.append(Container("Carried Items", player.max_gear_slots))
    
    return containers

def organize_inventory_into_containers(player: Player) -> List[Container]:
    """Organize player's inventory into containers"""
    containers = get_containers_from_inventory(player)
    
    if not containers:
        return containers
    
    # For now, put all non-container items in the first container
    main_container = containers[0]
    
    for inv_item in player.inventory:
        if not is_container(inv_item.item):
            # Check if item can fit
            if main_container.can_fit_item(inv_item.item, inv_item.quantity):
                main_container.contents.append(inv_item)
            else:
                # Try other containers or create overflow
                placed = False
                for container in containers[1:]:
                    if container.can_fit_item(inv_item.item, inv_item.quantity):
                        container.contents.append(inv_item)
                        placed = True
                        break
                
                if not placed:
                    # Create overflow container
                    overflow = Container("Overflow (No Backpack)", player.max_gear_slots)
                    overflow.contents.append(inv_item)
                    containers.append(overflow)
    
    return containers

def get_stat_modifier(stat_value: int) -> int:
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

def calculate_armor_class(player: Player) -> int:
    """Calculate player's AC based on equipped armor"""
    base_ac = 10
    dex_modifier = get_stat_modifier(player.dexterity)
    
    # Check for equipped armor
    if 'armor' in player.equipment:
        armor_name = player.equipment['armor'].item.name
        if 'Leather' in armor_name:
            base_ac = 11 + dex_modifier
        elif 'Chainmail' in armor_name:
            base_ac = 13 + dex_modifier
        elif 'Plate' in armor_name:
            base_ac = 15
    else:
        # No armor, just dex bonus
        base_ac = 10 + dex_modifier
    
    # Add shield bonus
    if 'shield' in player.equipment:
        base_ac += 2
    
    return base_ac

def get_equipped_weapon_damage(player: Player) -> str:
    """Get damage of equipped weapon"""
    if 'weapon' in player.equipment:
        weapon = player.equipment['weapon'].item
        if hasattr(weapon, 'damage'):
            return weapon.damage
    return "1d4"  # Unarmed damage

def can_equip_item(player: Player, item) -> bool:
    """Check if player can equip an item based on class restrictions"""
    # Import here to avoid circular imports
    try:
        from gear_selection import CLASS_WEAPON_RESTRICTIONS, CLASS_ARMOR_RESTRICTIONS, Weapon, Armor
        
        if isinstance(item, Weapon):
            restrictions = CLASS_WEAPON_RESTRICTIONS.get(player.character_class, [])
            if restrictions and item.name not in restrictions:
                return False
        elif isinstance(item, Armor):
            restrictions = CLASS_ARMOR_RESTRICTIONS.get(player.character_class, [])
            if restrictions and item.name not in restrictions:
                return False
    except ImportError:
        pass  # If gear_selection not available, allow all equipment
    
    return True

def get_equipment_slot(item) -> str:
    """Determine which equipment slot an item goes in"""
    try:
        from gear_selection import Weapon, Armor
        
        if isinstance(item, Weapon):
            return 'weapon'
        elif isinstance(item, Armor):
            if 'Shield' in item.name:
                return 'shield'
            else:
                return 'armor'
        elif item.name == 'Torch':
            return 'light'
        elif item.name == 'Lantern':
            return 'light'
    except ImportError:
        pass
    
    return None

def get_available_items_for_slot(player: Player, slot: str):
    """Get inventory items that can be equipped in the given slot"""
    available = []
    for inv_item in player.inventory:
        item_slot = get_equipment_slot(inv_item.item)
        if item_slot == slot and can_equip_item(player, inv_item.item):
            available.append(inv_item)
    return available

def equip_item(player: Player, inv_item, slot: str = None):
    """Equip an item to the appropriate slot"""
    if slot is None:
        slot = get_equipment_slot(inv_item.item)
    
    if slot and can_equip_item(player, inv_item.item):
        # Unequip current item in slot if any
        if slot in player.equipment:
            unequip_item(player, slot)
        
        # Equip new item
        player.equipment[slot] = inv_item
        
        # Update AC if armor/shield equipped
        if slot in ['armor', 'shield']:
            player.ac = calculate_armor_class(player)
        
        return True
    return False

def unequip_item(player: Player, slot: str):
    """Unequip an item from the given slot"""
    if slot in player.equipment:
        del player.equipment[slot]
        
        # Update AC if armor/shield unequipped
        if slot in ['armor', 'shield']:
            player.ac = calculate_armor_class(player)
        
        return True
    return False

def format_item_cost(item) -> str:
    """Format item cost as a readable string"""
    if hasattr(item, 'cost_gp') and item.cost_gp > 0:
        return f"{item.cost_gp} gp"
    elif hasattr(item, 'cost_sp') and item.cost_sp > 0:
        return f"{item.cost_sp} sp"
    elif hasattr(item, 'cost_cp') and item.cost_cp > 0:
        return f"{item.cost_cp} cp"
    else:
        return "Priceless"

def wrap_text(text: str, max_width: int, font: pygame.font.Font) -> List[str]:
    """Wrap text to fit within max_width"""
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = font.size(test_line)[0]
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

# --- Drawing Functions ---
def draw_main_menu(surface: pygame.Surface, large_font, medium_font):
    """Draws the main menu screen."""
    screen_width, screen_height = surface.get_size()
    
    # Background
    surface.fill(COLOR_BG)
    
    # Title
    title_surf = large_font.render("Dungeon Explorer", True, COLOR_BLACK)
    title_rect = title_surf.get_rect(centerx=screen_width/2, top=screen_height * 0.2)
    surface.blit(title_surf, title_rect)

    # Start button
    button_width = 300
    button_height = 60
    start_button_rect = pygame.Rect((screen_width - button_width)/2, screen_height * 0.5, button_width, button_height)
    
    pygame.draw.rect(surface, COLOR_WHITE, start_button_rect, 3)
    
    button_text_surf = medium_font.render("Create New Character", True, COLOR_BLACK)
    button_text_rect = button_text_surf.get_rect(center=start_button_rect.center)
    surface.blit(button_text_surf, button_text_rect)
    
    # Instructions
    inst_text = "Press ESC to quit"
    inst_surf = medium_font.render(inst_text, True, COLOR_BLACK)
    inst_rect = inst_surf.get_rect(centerx=screen_width/2, bottom=screen_height * 0.9)
    surface.blit(inst_surf, inst_rect)
    
    return start_button_rect

def draw_hud(surface: pygame.Surface, player: Player, large_font: pygame.font.Font, 
             medium_font: pygame.font.Font, small_font: pygame.font.Font):
    """Draws the player information HUD at the bottom of the screen."""
    screen_width, screen_height = surface.get_size()
    hud_rect = pygame.Rect(0, screen_height - HUD_HEIGHT, screen_width, HUD_HEIGHT)
    
    # Draw outer black box
    pygame.draw.rect(surface, COLOR_BLACK, hud_rect)
    
    # Draw inner white box
    inner_margin = 4
    inner_rect = hud_rect.inflate(-inner_margin * 2, -inner_margin * 2)
    pygame.draw.rect(surface, COLOR_WHITE, inner_rect, width=1)
    
    # --- Left Section: Character Info ---
    left_padding = inner_rect.left + 20
    name_surf = large_font.render(player.name, True, COLOR_WHITE)
    name_rect = name_surf.get_rect(left=left_padding, top=inner_rect.top + 10)
    surface.blit(name_surf, name_rect)

    title_surf = medium_font.render(player.title, True, COLOR_WHITE)
    title_rect = title_surf.get_rect(left=left_padding, top=name_rect.bottom + 2)
    surface.blit(title_surf, title_rect)

    info_text = f"Lvl {player.level} {player.alignment} {player.race} {player.character_class}"
    info_surf = small_font.render(info_text, True, COLOR_WHITE)
    info_rect = info_surf.get_rect(left=left_padding, bottom=inner_rect.bottom - 10)
    surface.blit(info_surf, info_rect)

    # --- Right Section: Vitals & Resources ---
    right_padding = inner_rect.right - 20
    bar_width = 150 
    bar_height = 15
    
    # HP Bar
    hp_y = inner_rect.top + 15
    
    hp_value_surf = medium_font.render(f"{player.hp}/{player.max_hp}", True, COLOR_WHITE)
    hp_value_rect = hp_value_surf.get_rect(right=right_padding, centery=hp_y + bar_height/2)
    surface.blit(hp_value_surf, hp_value_rect)
    
    hp_bar_rect = pygame.Rect(hp_value_rect.left - bar_width - 10, hp_y, bar_width, bar_height)
    hp_ratio = player.hp / player.max_hp
    hp_bar_fill_width = int(bar_width * hp_ratio)
    pygame.draw.rect(surface, COLOR_BAR_BG, hp_bar_rect)
    pygame.draw.rect(surface, COLOR_HP_BAR, (hp_bar_rect.x, hp_bar_rect.y, hp_bar_fill_width, bar_height))

    hp_text_surf = medium_font.render(f'{UI_ICONS["HEART"]} HP', True, COLOR_HP_BAR)
    hp_text_rect = hp_text_surf.get_rect(right=hp_bar_rect.left - 10, centery=hp_bar_rect.centery)
    surface.blit(hp_text_surf, hp_text_rect)

    # XP Bar
    xp_y = hp_y + bar_height + 10
    
    xp_bar_rect = pygame.Rect(hp_bar_rect.x, xp_y, bar_width, bar_height)
    xp_ratio = player.xp / player.xp_to_next_level
    xp_bar_fill_width = int(bar_width * xp_ratio)
    pygame.draw.rect(surface, COLOR_BAR_BG, xp_bar_rect)
    pygame.draw.rect(surface, COLOR_XP_BAR, (xp_bar_rect.x, xp_bar_rect.y, xp_bar_fill_width, bar_height))

    xp_text_surf = medium_font.render("XP", True, COLOR_XP_BAR)
    xp_text_rect = xp_text_surf.get_rect(right=xp_bar_rect.left - 10, centery=xp_bar_rect.centery)
    surface.blit(xp_text_surf, xp_text_rect)

    # --- Bottom Right: Other Stats ---
    bottom_y = inner_rect.bottom - 10
    
    ac_icon_surf = large_font.render(UI_ICONS["SHIELD"], True, COLOR_WHITE)
    ac_text_surf = medium_font.render(f"{player.ac}", True, COLOR_WHITE)
    ac_text_rect = ac_text_surf.get_rect(right=right_padding, bottom=bottom_y)
    ac_icon_rect = ac_icon_surf.get_rect(right=ac_text_rect.left - 5, centery=ac_text_rect.centery)
    surface.blit(ac_icon_surf, ac_icon_rect)
    surface.blit(ac_text_surf, ac_text_rect)
    
    gold_icon_surf = large_font.render(UI_ICONS["GOLD"], True, (255, 215, 0))
    gold_text_surf = medium_font.render(f"{player.gold:.0f}", True, COLOR_WHITE)
    gold_text_rect = gold_text_surf.get_rect(right=ac_icon_rect.left - 20, bottom=bottom_y)
    gold_icon_rect = gold_icon_surf.get_rect(right=gold_text_rect.left - 5, centery=gold_text_rect.centery)
    surface.blit(gold_icon_surf, gold_icon_rect)
    surface.blit(gold_text_surf, gold_text_rect)

def draw_timer_box(surface: pygame.Surface, player: Player, font: pygame.font.Font):
    """Draws the torch timer in its own box in the top right corner."""
    margin = 10
    screen_width, _ = surface.get_size()
    
    time_left = max(0, player.light_duration - (time.time() - player.light_start_time))
    minutes, seconds = divmod(int(time_left), 60)
    light_text = f'{UI_ICONS["SUN"]} {minutes:02d}:{seconds:02d}'
    
    light_surf = font.render(light_text, True, COLOR_TORCH_ICON)
    
    box_width = light_surf.get_width() + 20
    box_height = light_surf.get_height() + 10
    
    box_rect = pygame.Rect(screen_width - box_width - margin, margin, box_width, box_height)
    pygame.draw.rect(surface, COLOR_BLACK, box_rect)
    
    inner_rect = box_rect.inflate(-4, -4)
    pygame.draw.rect(surface, COLOR_WHITE, inner_rect, 1)
    
    light_rect = light_surf.get_rect(center=box_rect.center)
    surface.blit(light_surf, light_rect)

def draw_spell_menu(surface: pygame.Surface, font: pygame.font.Font, spells: List[str]):
    """Draws the spell selection menu."""
    menu_width = 300
    menu_height = 200
    screen_width, screen_height = surface.get_size()
    
    menu_rect = pygame.Rect((screen_width - menu_width) / 2, (screen_height - HUD_HEIGHT - menu_height) / 2, menu_width, menu_height)
    
    # Draw a solid black background box
    pygame.draw.rect(surface, COLOR_BLACK, menu_rect)
    
    # Draw border
    pygame.draw.rect(surface, COLOR_WHITE, menu_rect, 1)
    
    # Draw title
    title_surf = font.render("Choose a Spell", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=menu_rect.centerx, top=menu_rect.top + 10)
    surface.blit(title_surf, title_rect)
    
    # Draw spell options
    for i, spell_name in enumerate(spells):
        text = f"{i+1}. {spell_name}"
        spell_surf = font.render(text, True, COLOR_WHITE)
        spell_rect = spell_surf.get_rect(left=menu_rect.left + 20, top=title_rect.bottom + 10 + (i * 30))
        surface.blit(spell_surf, spell_rect)

# Inventory UI functions
def draw_inventory_screen(surface: pygame.Surface, player: Player, selected_index: int, 
                         font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw inventory management screen showing containers"""
    surface.fill(COLOR_BLACK)
    
    screen_width, screen_height = surface.get_size()
    
    # Title
    title_surf = font.render(f"{player.name}'s Inventory", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=screen_width//2, top=20)
    surface.blit(title_surf, title_rect)
    
    # Draw separator line
    separator_x = screen_width // 3 + 30
    pygame.draw.line(surface, COLOR_WHITE, (separator_x, 80), (separator_x, screen_height - 100), 2)
    
    # Get containers
    containers = organize_inventory_into_containers(player)
    
    # Left side - container list
    list_x = 20
    list_width = screen_width // 3
    y = 100
    
    if not containers:
        empty_surf = font.render("No containers found", True, COLOR_WHITE)
        surface.blit(empty_surf, (list_x, y))
    else:
        for i, container in enumerate(containers):
            # Highlight selected container
            if i == selected_index:
                highlight_rect = pygame.Rect(list_x - 5, y - 5, list_width - 30, 60)
                pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
                pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
            
            color = COLOR_BLACK if i == selected_index else COLOR_WHITE
            
            # Container name
            container_surf = font.render(container.name, True, color)
            surface.blit(container_surf, (list_x, y))
            
            # Container capacity info
            used_capacity = container.get_used_capacity()
            capacity_text = f"{used_capacity}/{container.capacity} slots"
            capacity_color = COLOR_RED if used_capacity > container.capacity else color
            capacity_surf = small_font.render(capacity_text, True, capacity_color)
            surface.blit(capacity_surf, (list_x, y + 25))
            
            # Item count
            item_count_text = f"{len(container.contents)} items"
            item_surf = small_font.render(item_count_text, True, color)
            surface.blit(item_surf, (list_x, y + 40))
            
            y += 70
    
    # Right side - container contents
    detail_x = separator_x + 20
    detail_width = screen_width - detail_x - 20
    
    if containers and 0 <= selected_index < len(containers):
        selected_container = containers[selected_index]
        draw_container_contents(surface, selected_container, detail_x, 100, detail_width, font, small_font)
    
    # Instructions
    instructions = ["UP/DOWN: Navigate containers", "ENTER: View container contents", "ESC: Back to game"]
    inst_y = screen_height - 60
    for instruction in instructions:
        inst_surf = small_font.render(instruction, True, COLOR_WHITE)
        inst_rect = inst_surf.get_rect(centerx=screen_width//2, y=inst_y)
        surface.blit(inst_surf, inst_rect)
        inst_y += 15

def draw_container_contents(surface: pygame.Surface, container: Container, x: int, y: int, width: int,
                           font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw the contents of a container"""
    current_y = y
    
    # Container header
    header_surf = font.render(f"Contents of {container.name}", True, COLOR_WHITE)
    surface.blit(header_surf, (x, current_y))
    current_y += 30
    
    # Capacity bar
    used_capacity = container.get_used_capacity()
    capacity_text = f"Capacity: {used_capacity}/{container.capacity}"
    capacity_surf = small_font.render(capacity_text, True, COLOR_WHITE)
    surface.blit(capacity_surf, (x, current_y))
    current_y += 20
    
    # Visual capacity bar
    bar_width = min(200, width - 20)
    bar_height = 8
    pygame.draw.rect(surface, (50, 50, 50), (x, current_y, bar_width, bar_height))
    
    if container.capacity > 0:
        fill_ratio = min(used_capacity / container.capacity, 1.0)
        fill_width = int(bar_width * fill_ratio)
        fill_color = COLOR_RED if used_capacity > container.capacity else COLOR_GREEN
        pygame.draw.rect(surface, fill_color, (x, current_y, fill_width, bar_height))
    
    current_y += 25
    
    # Contents list
    if not container.contents:
        empty_surf = small_font.render("(Empty)", True, (150, 150, 150))
        surface.blit(empty_surf, (x, current_y))
    else:
        for inv_item in container.contents:
            item_name = getattr(inv_item.item, 'name', 'Unknown Item')
            quantity = getattr(inv_item, 'quantity', 1)
            
            item_text = f"• {quantity}x {item_name}"
            item_surf = small_font.render(item_text, True, COLOR_WHITE)
            surface.blit(item_surf, (x, current_y))
            current_y += 18
            
            # Show item properties briefly
            if hasattr(inv_item.item, 'damage'):
                prop_text = f"    Damage: {inv_item.item.damage}"
                prop_surf = small_font.render(prop_text, True, (150, 150, 150))
                surface.blit(prop_surf, (x, current_y))
                current_y += 15
            elif hasattr(inv_item.item, 'ac_bonus'):
                prop_text = f"    AC: {inv_item.item.ac_bonus}"
                prop_surf = small_font.render(prop_text, True, (150, 150, 150))
                surface.blit(prop_surf, (x, current_y))
                current_y += 15
            
            current_y += 5

def draw_equipment_screen(surface: pygame.Surface, player: Player, selected_slot: str,
                         font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw equipment management screen"""
    surface.fill(COLOR_BLACK)
    
    screen_width, screen_height = surface.get_size()
    
    # Title
    title_surf = font.render(f"{player.name}'s Equipment", True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=screen_width//2, top=20)
    surface.blit(title_surf, title_rect)
    
    # Draw separator line
    separator_x = screen_width // 3 + 30
    pygame.draw.line(surface, COLOR_WHITE, (separator_x, 80), (separator_x, screen_height - 100), 2)
    
    # Equipment slots
    equipment_slots = ['weapon', 'armor', 'shield', 'light']
    slot_names = {
        'weapon': 'Weapon',
        'armor': 'Armor', 
        'shield': 'Shield',
        'light': 'Light Source'
    }
    
    list_x = 20
    list_width = screen_width // 3
    y = 100
    
    for slot in equipment_slots:
        # Highlight selected slot
        if slot == selected_slot:
            highlight_rect = pygame.Rect(list_x - 5, y - 5, list_width - 30, 60)
            pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)
            pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
        
        color = COLOR_BLACK if slot == selected_slot else COLOR_WHITE
        
        # Slot name
        slot_surf = font.render(slot_names[slot], True, color)
        surface.blit(slot_surf, (list_x, y))
        
        # Equipped item
        if slot in player.equipment:
            item_name = player.equipment[slot].item.name
            item_surf = small_font.render(f"  {item_name}", True, color)
            surface.blit(item_surf, (list_x, y + 25))
        else:
            empty_surf = small_font.render("  (Empty)", True, (150, 150, 150))
            surface.blit(empty_surf, (list_x, y + 25))
        
        y += 70
    
    # Right side - item details or available equipment
    detail_x = separator_x + 20
    detail_width = screen_width - detail_x - 20
    
    if selected_slot in player.equipment:
        # Show equipped item details
        equipped_item = player.equipment[selected_slot]
        draw_item_details(surface, equipped_item.item, detail_x, 100, detail_width, font, small_font)
    else:
        # Show available items for this slot
        available_items = get_available_items_for_slot(player, selected_slot)
        if available_items:
            avail_title = small_font.render("Available to equip:", True, COLOR_WHITE)
            surface.blit(avail_title, (detail_x, 100))
            
            item_y = 130
            for inv_item in available_items:
                item_surf = small_font.render(f"• {inv_item.item.name}", True, COLOR_WHITE)
                surface.blit(item_surf, (detail_x, item_y))
                item_y += 20
        else:
            no_items_surf = small_font.render("No items available for this slot", True, (150, 150, 150))
            surface.blit(no_items_surf, (detail_x, 100))
    
    # Instructions
    instructions = ["UP/DOWN: Navigate slots", "ENTER: Change equipment", "ESC: Back to game"]
    inst_y = screen_height - 60
    for instruction in instructions:
        inst_surf = small_font.render(instruction, True, COLOR_WHITE)
        inst_rect = inst_surf.get_rect(centerx=screen_width//2, y=inst_y)
        surface.blit(inst_surf, inst_rect)
        inst_y += 15

def show_equipment_selection(surface: pygame.Surface, player: Player, slot: str, selected_index: int,
                            font: pygame.font.Font, small_font: pygame.font.Font):
    """Draws the pop-up menu for selecting an item to equip."""
    screen_width, screen_height = surface.get_size()
    
    # Get available items for the slot, plus an "Unequip" option
    available_items = get_available_items_for_slot(player, slot)
    available_items.insert(0, None)  # None represents "Unequip"

    # Define menu dimensions
    menu_width = 350
    item_height = 30
    menu_height = (len(available_items) * item_height) + 50
    menu_x = (screen_width - menu_width) // 2
    menu_y = (screen_height - HUD_HEIGHT - menu_height) // 2
    
    menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)

    # Draw menu background (semi-transparent)
    bg_surface = pygame.Surface(menu_rect.size, pygame.SRCALPHA)
    bg_surface.fill(COLOR_SPELL_MENU_BG)
    surface.blit(bg_surface, menu_rect.topleft)

    # Draw menu border
    pygame.draw.rect(surface, COLOR_WHITE, menu_rect, 2)
    
    # Draw title
    title_text = f"Equip to {slot.capitalize()}"
    title_surf = font.render(title_text, True, COLOR_WHITE)
    title_rect = title_surf.get_rect(centerx=menu_rect.centerx, top=menu_rect.top + 10)
    surface.blit(title_surf, title_rect)
    
    # Draw item list
    list_y = title_rect.bottom + 10
    for i, inv_item in enumerate(available_items):
        item_y = list_y + (i * item_height)
        
        # Highlight the selected item
        if i == selected_index:
            highlight_rect = pygame.Rect(menu_rect.left + 5, item_y, menu_width - 10, item_height)
            pygame.draw.rect(surface, COLOR_SELECTED_ITEM, highlight_rect)

        # Get item name
        if inv_item is None:
            item_name = "(Unequip)"
        else:
            item_name = inv_item.item.name
            
        color = COLOR_BLACK if i == selected_index else COLOR_WHITE
        item_surf = small_font.render(item_name, True, color)
        item_rect = item_surf.get_rect(left=menu_rect.left + 15, centery=item_y + item_height / 2)
        surface.blit(item_surf, item_rect)

def draw_item_details(surface: pygame.Surface, item, x: int, y: int, width: int,
                     font: pygame.font.Font, small_font: pygame.font.Font):
    """Draw detailed information about an item"""
    current_y = y
    
    # Item name
    item_name = getattr(item, 'name', 'Unknown Item')
    name_surf = font.render(item_name, True, COLOR_WHITE)
    surface.blit(name_surf, (x, current_y))
    current_y += 35
    
    # Item type/category
    category = getattr(item, 'category', 'General')
    category_surf = small_font.render(f"Category: {category}", True, (200, 200, 200))
    surface.blit(category_surf, (x, current_y))
    current_y += 25
    
    # Weapon-specific details
    if hasattr(item, 'damage'):
        damage_surf = small_font.render(f"Damage: {item.damage}", True, COLOR_WHITE)
        surface.blit(damage_surf, (x, current_y))
        current_y += 20
        
        if hasattr(item, 'weapon_properties') and item.weapon_properties:
            props_surf = small_font.render(f"Properties: {', '.join(item.weapon_properties)}", True, COLOR_WHITE)
            surface.blit(props_surf, (x, current_y))
            current_y += 20
    
    # Armor-specific details
    elif hasattr(item, 'ac_bonus'):
        ac_surf = small_font.render(f"Armor Class: {item.ac_bonus}", True, COLOR_WHITE)
        surface.blit(ac_surf, (x, current_y))
        current_y += 20
        
        if hasattr(item, 'armor_properties') and item.armor_properties:
            props_surf = small_font.render(f"Properties: {', '.join(item.armor_properties)}", True, COLOR_WHITE)
            surface.blit(props_surf, (x, current_y))
            current_y += 20
    
    # Gear slots
    gear_slots = getattr(item, 'gear_slots', 1)
    slots_surf = small_font.render(f"Gear Slots: {gear_slots}", True, COLOR_WHITE)
    surface.blit(slots_surf, (x, current_y))
    current_y += 20
    
    # Cost (if available)
    cost_text = format_item_cost(item)
    if cost_text != "Priceless":
        cost_surf = small_font.render(f"Value: {cost_text}", True, (255, 215, 0))
        surface.blit(cost_surf, (x, current_y))
        current_y += 25
    
    # Description
    description = getattr(item, 'description', '')
    if description:
        desc_lines = wrap_text(description, width - 20, small_font)
        for line in desc_lines:
            line_surf = small_font.render(line, True, COLOR_WHITE)
            surface.blit(line_surf, (x, current_y))
            current_y += 18