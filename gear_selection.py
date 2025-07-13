import pygame
import random
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum

# Import from existing files
from character_creation import Player, CharCreationState

# --- Gear Data ---
@dataclass
class GearItem:
    name: str
    cost_gp: int = 0
    cost_sp: int = 0
    cost_cp: int = 0
    gear_slots: int = 1
    quantity_per_slot: int = 1
    description: str = ""
    category: str = "General"
    properties: List[str] = field(default_factory=list)

@dataclass
class Weapon(GearItem):
    weapon_type: str = "M"  # M=Melee, R=Ranged, M/R=Both
    range_type: str = "C"   # C=Close, N=Near, F=Far
    damage: str = "1d4"
    weapon_properties: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.category = "Weapon"

@dataclass
class Armor(GearItem):
    ac_bonus: str = "11"
    armor_properties: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.category = "Armor"

@dataclass
class Kit(GearItem):
    contents: List[Tuple[str, int]] = field(default_factory=list)  # (item_name, quantity)
    
    def __post_init__(self):
        self.category = "Kit"

# Define all gear items
GENERAL_GEAR = {
    "Arrows (20)": GearItem("Arrows (20)", cost_gp=1, quantity_per_slot=20, 
                           description="Ammunition for shortbows or longbows"),
    "Backpack": GearItem("Backpack", cost_gp=2, gear_slots=0, 
                        description="Holds all the gear you can carry. Don't lose it. First one is free to carry"),
    "Caltrops": GearItem("Caltrops", cost_sp=5, 
                        description="Tiny iron spikes. Creatures stepping on them take 1 damage and move at half speed for 10 rounds"),
    "Crossbow bolts (20)": GearItem("Crossbow bolts (20)", cost_gp=1, quantity_per_slot=20,
                                   description="Ammunition for crossbows"),
    "Crowbar": GearItem("Crowbar", cost_sp=5, 
                       description="Grants advantage on checks to pry open stuck objects"),
    "Flask or bottle": GearItem("Flask or bottle", cost_sp=3,
                               description="Glass containers that hold one draught of liquid"),
    "Flint and steel": GearItem("Flint and steel", cost_sp=5,
                               description="A small fire starter. Routine attempts to light a fire always succeed"),
    "Gem": GearItem("Gem", cost_gp=10, quantity_per_slot=10,
                   description="Gems come in numerous varieties and are very valuable"),
    "Grappling hook": GearItem("Grappling hook", cost_gp=1,
                              description="A rope anchor with three curved tines"),
    "Iron spikes (10)": GearItem("Iron spikes (10)", cost_gp=1, quantity_per_slot=10,
                                description="Strong spikes with holes for threading rope. Can be hammered in with weapons"),
    "Lantern": GearItem("Lantern", cost_gp=5,
                       description="Casts light up to double near distance. Requires oil. Has a shutter to hide light"),
    "Mirror": GearItem("Mirror", cost_gp=10,
                      description="A small, polished mirror"),
    "Oil flask": GearItem("Oil flask", cost_sp=5,
                         description="Fuels a lantern for one hour. Covers close area and burns for 4 rounds, dealing 1d4 damage each round"),
    "Pole": GearItem("Pole", cost_sp=5,
                    description="Wooden, 10' long"),
    "Rations (3)": GearItem("Rations (3)", cost_sp=5, quantity_per_slot=3,
                           description="Three days of food and water supply for one person"),
    "Rope, 60'": GearItem("Rope, 60'", cost_gp=1,
                         description="Hemp rope, 60 feet long"),
    "Torch": GearItem("Torch", cost_sp=5,
                     description="Sheds light to near distance. Burns for one hour of real time"),
    "Coin": GearItem("Coin", cost_gp=0, quantity_per_slot=100, gear_slots=0,
                    description="Currency. First 100 coins are free to carry")
}

WEAPONS = {
    "Bastard sword": Weapon("Bastard sword", cost_gp=10, gear_slots=2, weapon_type="M", 
                           range_type="C", damage="1d8/1d10", weapon_properties=["V"]),
    "Club": Weapon("Club", cost_cp=5, weapon_type="M", range_type="C", damage="1d4"),
    "Crossbow": Weapon("Crossbow", cost_gp=8, weapon_type="R", range_type="F", 
                      damage="1d6", weapon_properties=["2H", "L"]),
    "Dagger": Weapon("Dagger", cost_gp=1, weapon_type="M/R", range_type="C/N", 
                    damage="1d4", weapon_properties=["F", "Th"]),
    "Greataxe": Weapon("Greataxe", cost_gp=10, gear_slots=2, weapon_type="M", 
                      range_type="C", damage="1d8/1d10", weapon_properties=["V"]),
    "Greatsword": Weapon("Greatsword", cost_gp=12, gear_slots=2, weapon_type="M", 
                        range_type="C", damage="1d12", weapon_properties=["2H"]),
    "Javelin": Weapon("Javelin", cost_sp=5, weapon_type="M/R", range_type="C/F", 
                     damage="1d4", weapon_properties=["Th"]),
    "Longbow": Weapon("Longbow", cost_gp=8, weapon_type="R", range_type="F", 
                     damage="1d8", weapon_properties=["2H"]),
    "Longsword": Weapon("Longsword", cost_gp=9, weapon_type="M", range_type="C", damage="1d8"),
    "Mace": Weapon("Mace", cost_gp=5, weapon_type="M", range_type="C", damage="1d6"),
    "Shortbow": Weapon("Shortbow", cost_gp=6, weapon_type="R", range_type="F", 
                      damage="1d4", weapon_properties=["2H"]),
    "Shortsword": Weapon("Shortsword", cost_gp=7, weapon_type="M", range_type="C", damage="1d6"),
    "Spear": Weapon("Spear", cost_sp=5, weapon_type="M/R", range_type="C/N", 
                   damage="1d6", weapon_properties=["Th"]),
    "Staff": Weapon("Staff", cost_sp=5, weapon_type="M", range_type="C", 
                   damage="1d4", weapon_properties=["2H"]),
    "Warhammer": Weapon("Warhammer", cost_gp=10, weapon_type="M", range_type="C", 
                       damage="1d10", weapon_properties=["2H"])
}

ARMOR = {
    "Leather armor": Armor("Leather armor", cost_gp=10, ac_bonus="11 + DEX mod"),
    "Chainmail": Armor("Chainmail", cost_gp=60, gear_slots=2, ac_bonus="13 + DEX mod", 
                      armor_properties=["Disadv on stealth, swim"]),
    "Plate mail": Armor("Plate mail", cost_gp=130, gear_slots=3, ac_bonus="15", 
                       armor_properties=["No swim, disadv stealth"]),
    "Shield": Armor("Shield", cost_gp=10, ac_bonus="+2", 
                   armor_properties=["Occupies one hand"]),
    "Mithral": Armor("Mithral upgrade", cost_gp=0, gear_slots=-1,
                    description="Upgrade for metal armor. x4 cost, -1 gear slot, no penalty stealth/swim")
}

KITS = {
    "Crawling Kit": Kit("Crawling Kit", cost_gp=7, gear_slots=7,
                       description="Essential dungeon exploration gear",
                       contents=[
                           ("Backpack", 1), ("Flint and steel", 1), ("Torch", 2),
                           ("Rations (3)", 1), ("Iron spikes (10)", 1),
                           ("Grappling hook", 1), ("Rope, 60'", 1)
                       ])
}

# Class starting gear restrictions
CLASS_WEAPON_RESTRICTIONS = {
    "Fighter": [],  # Can use all weapons
    "Priest": ["Club", "Crossbow", "Dagger", "Mace", "Longsword", "Staff", "Warhammer"],
    "Thief": ["Club", "Crossbow", "Dagger", "Shortbow", "Shortsword"],
    "Wizard": ["Dagger", "Staff"]
}

CLASS_ARMOR_RESTRICTIONS = {
    "Fighter": [],  # Can use all armor
    "Priest": [],   # Can use all armor
    "Thief": ["Leather armor", "Shield"],  # + Mithral chainmail
    "Wizard": ["Shield"]  # No armor except shields
}

# Starting gold by class
STARTING_GOLD = {
    "Fighter": 120,
    "Priest": 90,
    "Thief": 60,
    "Wizard": 40
}

# Colors
COLOR_BG = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_CREAM = (240, 236, 224)
COLOR_BUTTON_NORMAL = (140, 134, 125)
COLOR_BUTTON_HOVER = (162, 160, 154)
COLOR_BUTTON_SELECTED = (100, 150, 100)
COLOR_GOLD = (255, 215, 0)
COLOR_RED = (255, 100, 100)
COLOR_GREEN = (100, 255, 100)

class GearSelectionState(Enum):
    CATEGORY_SELECTION = 0
    ITEM_SELECTION = 1
    QUANTITY_SELECTION = 2
    CONFIRM_PURCHASE = 3
    REVIEW_GEAR = 4
    COMPLETE = 5

@dataclass
class InventoryItem:
    item: GearItem
    quantity: int = 1

class GearSelector:
    def __init__(self, player: Player, screen_width: int, screen_height: int, font_file: str):
        self.player = player
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fonts
        self.title_font = pygame.font.Font(font_file, 36)
        self.large_font = pygame.font.Font(font_file, 24)
        self.medium_font = pygame.font.Font(font_file, 20)
        self.small_font = pygame.font.Font(font_file, 16)
        self.tiny_font = pygame.font.Font(font_file, 14)
        
        # State
        self.state = GearSelectionState.CATEGORY_SELECTION
        self.selected_index = 0
        
        # Layout
        self.list_width = screen_width // 3
        self.detail_width = (screen_width * 2) // 3
        self.list_x = 20
        self.detail_x = self.list_width + 40
        
        # Player data
        self.gold = STARTING_GOLD.get(player.character_class, 60)
        self.used_gear_slots = 0
        self.max_gear_slots = max(player.strength, 10)
        
        # Inventory
        self.inventory: List[InventoryItem] = []
        
        # Selection state
        self.current_category = "General"
        self.selected_item = None
        self.selected_quantity = 1
        
        # Add constitution bonus to gear slots for Fighters
        if player.character_class == "Fighter":
            constitution_bonus = self._get_stat_modifier(player.constitution)
            if constitution_bonus > 0:
                self.max_gear_slots += constitution_bonus
        
        # Start with a free backpack
        backpack = GENERAL_GEAR["Backpack"]
        self.inventory.append(InventoryItem(backpack, 1))
    
    def _get_stat_modifier(self, stat_value: int) -> int:
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
    
    def _get_categories(self) -> List[str]:
        return ["General", "Weapons", "Armor", "Kits", "Review & Finish"]
    
    def _get_items_for_category(self, category: str) -> Dict[str, GearItem]:
        if category == "General":
            return GENERAL_GEAR
        elif category == "Weapons":
            # Filter weapons by class restrictions
            restrictions = CLASS_WEAPON_RESTRICTIONS.get(self.player.character_class, [])
            if not restrictions:  # Fighter - no restrictions
                return WEAPONS
            return {name: weapon for name, weapon in WEAPONS.items() if name in restrictions}
        elif category == "Armor":
            # Filter armor by class restrictions
            restrictions = CLASS_ARMOR_RESTRICTIONS.get(self.player.character_class, [])
            if not restrictions:  # Fighter/Priest - no restrictions
                return ARMOR
            return {name: armor for name, armor in ARMOR.items() if name in restrictions}
        elif category == "Kits":
            return KITS
        return {}
    
    def _get_current_options(self) -> List[str]:
        if self.state == GearSelectionState.CATEGORY_SELECTION:
            return self._get_categories()
        elif self.state == GearSelectionState.ITEM_SELECTION:
            items = self._get_items_for_category(self.current_category)
            return list(items.keys())
        return []
    
    def _calculate_total_cost(self, item: GearItem, quantity: int) -> int:
        """Calculate total cost in copper pieces"""
        cost_cp = item.cost_cp + (item.cost_sp * 10) + (item.cost_gp * 100)
        return cost_cp * quantity
    
    def _can_afford_item(self, item: GearItem, quantity: int) -> bool:
        total_cost = self._calculate_total_cost(item, quantity)
        player_wealth_cp = self.gold * 100  # Convert gold to copper
        return total_cost <= player_wealth_cp
    
    def _get_gear_slots_needed(self, item: GearItem, quantity: int) -> int:
        if item.quantity_per_slot == 1:
            return item.gear_slots * quantity
        else:
            # Items that can stack (like arrows, rations)
            slots_needed = (quantity + item.quantity_per_slot - 1) // item.quantity_per_slot
            return slots_needed * item.gear_slots
    
    def _can_carry_item(self, item: GearItem, quantity: int) -> bool:
        needed_slots = self._get_gear_slots_needed(item, quantity)
        return (self.used_gear_slots + needed_slots) <= self.max_gear_slots
    
    def _add_item_to_inventory(self, item: GearItem, quantity: int):
        # Handle kits specially - expand them into individual items
        if isinstance(item, Kit):
            # Add kit contents instead of the kit itself
            for content_name, content_quantity in item.contents:
                # Find the actual item from our gear database
                content_item = self._find_item_by_name(content_name)
                if content_item:
                    # Add each content item to inventory
                    total_content_quantity = content_quantity * quantity
                    
                    # Check if item already exists in inventory
                    existing_item = None
                    for inv_item in self.inventory:
                        if inv_item.item.name == content_item.name:
                            existing_item = inv_item
                            break
                    
                    if existing_item:
                        existing_item.quantity += total_content_quantity
                    else:
                        self.inventory.append(InventoryItem(content_item, total_content_quantity))
                    
                    # Update used gear slots for content items
                    self.used_gear_slots += self._get_gear_slots_needed(content_item, total_content_quantity)
        else:
            # Regular item handling
            # Check if item already exists in inventory
            for inv_item in self.inventory:
                if inv_item.item.name == item.name:
                    inv_item.quantity += quantity
                    break
            else:
                self.inventory.append(InventoryItem(item, quantity))
            
            # Update used gear slots
            self.used_gear_slots += self._get_gear_slots_needed(item, quantity)
        
        # Deduct cost
        total_cost_cp = self._calculate_total_cost(item, quantity)
        cost_in_gold = total_cost_cp / 100
        self.gold -= cost_in_gold
    
    def _find_item_by_name(self, item_name: str) -> Optional[GearItem]:
        """Find an item by name from all available gear"""
        # Search in all gear categories
        all_gear = {}
        all_gear.update(GENERAL_GEAR)
        all_gear.update(WEAPONS)
        all_gear.update(ARMOR)
        all_gear.update(KITS)
        
        return all_gear.get(item_name)
    
    def _get_max_affordable_quantity(self, item: GearItem) -> int:
        cost_per_item_cp = self._calculate_total_cost(item, 1)
        if cost_per_item_cp == 0:
            return 999  # Free items
        player_wealth_cp = self.gold * 100
        return int(player_wealth_cp // cost_per_item_cp)
    
    def _get_max_carryable_quantity(self, item: GearItem) -> int:
        available_slots = self.max_gear_slots - self.used_gear_slots
        if item.gear_slots == 0:
            return 999  # Items that don't take slots
        
        if item.quantity_per_slot == 1:
            return available_slots // item.gear_slots
        else:
            return available_slots * item.quantity_per_slot
    
    def handle_event(self, event: pygame.event.Event) -> Optional[bool]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == GearSelectionState.CATEGORY_SELECTION:
                    return None  # Cancel gear selection
                else:
                    self._previous_state()
            
            elif event.key == pygame.K_RETURN:
                if self.state == GearSelectionState.CATEGORY_SELECTION:
                    categories = self._get_categories()
                    if self.selected_index < len(categories):
                        selected_cat = categories[self.selected_index]
                        if selected_cat == "Review & Finish":
                            self.state = GearSelectionState.REVIEW_GEAR
                        else:
                            self.current_category = selected_cat
                            self.state = GearSelectionState.ITEM_SELECTION
                        self.selected_index = 0
                
                elif self.state == GearSelectionState.ITEM_SELECTION:
                    items = self._get_items_for_category(self.current_category)
                    item_names = list(items.keys())
                    if self.selected_index < len(item_names):
                        item_name = item_names[self.selected_index]
                        self.selected_item = items[item_name]
                        self.selected_quantity = 1
                        self.state = GearSelectionState.QUANTITY_SELECTION
                
                elif self.state == GearSelectionState.QUANTITY_SELECTION:
                    if (self._can_afford_item(self.selected_item, self.selected_quantity) and 
                        self._can_carry_item(self.selected_item, self.selected_quantity)):
                        self.state = GearSelectionState.CONFIRM_PURCHASE
                
                elif self.state == GearSelectionState.CONFIRM_PURCHASE:
                    self._add_item_to_inventory(self.selected_item, self.selected_quantity)
                    self.state = GearSelectionState.ITEM_SELECTION
                
                elif self.state == GearSelectionState.REVIEW_GEAR:
                    return True  # Complete gear selection
            
            elif event.key == pygame.K_UP:
                if self.state in [GearSelectionState.CATEGORY_SELECTION, GearSelectionState.ITEM_SELECTION]:
                    options = self._get_current_options()
                    if options:
                        self.selected_index = (self.selected_index - 1) % len(options)
                elif self.state == GearSelectionState.QUANTITY_SELECTION:
                    max_qty = min(
                        self._get_max_affordable_quantity(self.selected_item),
                        self._get_max_carryable_quantity(self.selected_item),
                        99
                    )
                    if self.selected_quantity < max_qty:
                        self.selected_quantity += 1
            
            elif event.key == pygame.K_DOWN:
                if self.state in [GearSelectionState.CATEGORY_SELECTION, GearSelectionState.ITEM_SELECTION]:
                    options = self._get_current_options()
                    if options:
                        self.selected_index = (self.selected_index + 1) % len(options)
                elif self.state == GearSelectionState.QUANTITY_SELECTION:
                    if self.selected_quantity > 1:
                        self.selected_quantity -= 1
        
        return False
    
    def _previous_state(self):
        if self.state == GearSelectionState.ITEM_SELECTION:
            self.state = GearSelectionState.CATEGORY_SELECTION
        elif self.state == GearSelectionState.QUANTITY_SELECTION:
            self.state = GearSelectionState.ITEM_SELECTION
        elif self.state == GearSelectionState.CONFIRM_PURCHASE:
            self.state = GearSelectionState.QUANTITY_SELECTION
        elif self.state == GearSelectionState.REVIEW_GEAR:
            self.state = GearSelectionState.CATEGORY_SELECTION
        
        self.selected_index = 0
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)
        
        # Title
        title = "Select Your Gear"
        title_surf = self.title_font.render(title, True, COLOR_WHITE)
        title_rect = title_surf.get_rect(centerx=self.screen_width // 2, top=20)
        surface.blit(title_surf, title_rect)
        
        # Draw separator line
        separator_x = self.list_width + 30
        pygame.draw.line(surface, COLOR_WHITE, (separator_x, 80), (separator_x, self.screen_height - 100), 2)
        
        # Draw main content based on state
        if self.state == GearSelectionState.CATEGORY_SELECTION:
            self._draw_category_selection(surface)
        elif self.state == GearSelectionState.ITEM_SELECTION:
            self._draw_item_selection(surface)
        elif self.state == GearSelectionState.QUANTITY_SELECTION:
            self._draw_quantity_selection(surface)
        elif self.state == GearSelectionState.CONFIRM_PURCHASE:
            self._draw_confirm_purchase(surface)
        elif self.state == GearSelectionState.REVIEW_GEAR:
            self._draw_review_gear(surface)
        
        # Always draw player stats and inventory summary
        self._draw_player_info(surface)
        self._draw_instructions(surface)
    
    def _draw_category_selection(self, surface: pygame.Surface):
        categories = self._get_categories()
        
        # Left side - categories
        start_y = 120
        for i, category in enumerate(categories):
            y = start_y + i * 50
            
            if i == self.selected_index:
                highlight_rect = pygame.Rect(self.list_x - 5, y - 5, self.list_width - 30, 40)
                pygame.draw.rect(surface, COLOR_BUTTON_HOVER, highlight_rect)
                pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
            
            color = COLOR_BLACK if i == self.selected_index else COLOR_WHITE
            cat_surf = self.large_font.render(category, True, color)
            surface.blit(cat_surf, (self.list_x, y))
        
        # Right side - category description
        if self.selected_index < len(categories):
            selected_cat = categories[self.selected_index]
            descriptions = {
                "General": "Basic adventuring equipment and supplies",
                "Weapons": "Combat equipment for your class",
                "Armor": "Protective gear and shields",
                "Kits": "Pre-assembled equipment packages",
                "Review & Finish": "Review your selections and complete"
            }
            
            desc = descriptions.get(selected_cat, "")
            desc_surf = self.medium_font.render(desc, True, COLOR_WHITE)
            surface.blit(desc_surf, (self.detail_x, 150))
    
    def _draw_item_selection(self, surface: pygame.Surface):
        items = self._get_items_for_category(self.current_category)
        item_names = list(items.keys())
        
        # Left side - item list
        start_y = 120
        for i, item_name in enumerate(item_names):
            y = start_y + i * 50
            item = items[item_name]
            
            if i == self.selected_index:
                highlight_rect = pygame.Rect(self.list_x - 5, y - 5, self.list_width - 30, 40)
                pygame.draw.rect(surface, COLOR_BUTTON_HOVER, highlight_rect)
                pygame.draw.rect(surface, COLOR_WHITE, highlight_rect, 2)
            
            color = COLOR_BLACK if i == self.selected_index else COLOR_WHITE
            name_surf = self.medium_font.render(item_name, True, color)
            surface.blit(name_surf, (self.list_x, y))
            
            # Show cost
            cost_text = self._format_cost(item)
            cost_surf = self.small_font.render(cost_text, True, COLOR_GOLD)
            surface.blit(cost_surf, (self.list_x, y + 22))
        
        # Right side - item details
        if self.selected_index < len(item_names):
            selected_item = items[item_names[self.selected_index]]
            self._draw_item_details(surface, selected_item)
    
    def _draw_quantity_selection(self, surface: pygame.Surface):
        # Center the quantity selection
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # Item name
        name_surf = self.large_font.render(self.selected_item.name, True, COLOR_WHITE)
        name_rect = name_surf.get_rect(centerx=center_x, y=center_y - 100)
        surface.blit(name_surf, name_rect)
        
        # Quantity selector
        qty_text = f"Quantity: {self.selected_quantity}"
        qty_surf = self.large_font.render(qty_text, True, COLOR_WHITE)
        qty_rect = qty_surf.get_rect(centerx=center_x, y=center_y - 40)
        surface.blit(qty_surf, qty_rect)
        
        # Cost calculation
        total_cost = self._calculate_total_cost(self.selected_item, self.selected_quantity)
        cost_text = f"Total Cost: {self._format_cost_cp(total_cost)}"
        cost_surf = self.medium_font.render(cost_text, True, COLOR_GOLD)
        cost_rect = cost_surf.get_rect(centerx=center_x, y=center_y)
        surface.blit(cost_surf, cost_rect)
        
        # Gear slots needed
        slots_needed = self._get_gear_slots_needed(self.selected_item, self.selected_quantity)
        slots_text = f"Gear Slots: {slots_needed}"
        slots_surf = self.medium_font.render(slots_text, True, COLOR_WHITE)
        slots_rect = slots_surf.get_rect(centerx=center_x, y=center_y + 30)
        surface.blit(slots_surf, slots_rect)
        
        # Affordability check
        can_afford = self._can_afford_item(self.selected_item, self.selected_quantity)
        can_carry = self._can_carry_item(self.selected_item, self.selected_quantity)
        
        if not can_afford:
            afford_surf = self.medium_font.render("Cannot afford this quantity!", True, COLOR_RED)
            afford_rect = afford_surf.get_rect(centerx=center_x, y=center_y + 60)
            surface.blit(afford_surf, afford_rect)
        
        if not can_carry:
            carry_surf = self.medium_font.render("Not enough carrying capacity!", True, COLOR_RED)
            carry_rect = carry_surf.get_rect(centerx=center_x, y=center_y + 90)
            surface.blit(carry_surf, carry_rect)
    
    def _draw_confirm_purchase(self, surface: pygame.Surface):
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        confirm_text = "Confirm Purchase?"
        confirm_surf = self.large_font.render(confirm_text, True, COLOR_WHITE)
        confirm_rect = confirm_surf.get_rect(centerx=center_x, y=center_y - 60)
        surface.blit(confirm_surf, confirm_rect)
        
        item_text = f"{self.selected_quantity}x {self.selected_item.name}"
        item_surf = self.medium_font.render(item_text, True, COLOR_WHITE)
        item_rect = item_surf.get_rect(centerx=center_x, y=center_y - 20)
        surface.blit(item_surf, item_rect)
        
        total_cost = self._calculate_total_cost(self.selected_item, self.selected_quantity)
        cost_text = f"Cost: {self._format_cost_cp(total_cost)}"
        cost_surf = self.medium_font.render(cost_text, True, COLOR_GOLD)
        cost_rect = cost_surf.get_rect(centerx=center_x, y=center_y + 20)
        surface.blit(cost_surf, cost_rect)
    
    def _draw_review_gear(self, surface: pygame.Surface):
        # Show complete inventory
        inv_title = self.large_font.render("Your Equipment", True, COLOR_WHITE)
        surface.blit(inv_title, (50, 100))
        
        y = 140
        for inv_item in self.inventory:
            item_text = f"{inv_item.quantity}x {inv_item.item.name}"
            item_surf = self.medium_font.render(item_text, True, COLOR_WHITE)
            surface.blit(item_surf, (50, y))
            
            # Show item properties for weapons/armor
            if hasattr(inv_item.item, 'damage'):
                prop_text = f"  Damage: {inv_item.item.damage}"
                prop_surf = self.small_font.render(prop_text, True, COLOR_WHITE)
                surface.blit(prop_surf, (70, y + 20))
                y += 20
            elif hasattr(inv_item.item, 'ac_bonus'):
                prop_text = f"  AC: {inv_item.item.ac_bonus}"
                prop_surf = self.small_font.render(prop_text, True, COLOR_WHITE)
                surface.blit(prop_surf, (70, y + 20))
                y += 20
            
            y += 35
        
        # Show remaining gold
        gold_text = f"Remaining Gold: {self.gold:.1f} gp"
        gold_surf = self.large_font.render(gold_text, True, COLOR_GOLD)
        surface.blit(gold_surf, (50, y + 20))
        
        # Show gear slots used
        slots_text = f"Gear Slots: {self.used_gear_slots}/{self.max_gear_slots}"
        slots_surf = self.large_font.render(slots_text, True, COLOR_WHITE)
        surface.blit(slots_surf, (50, y + 50))
    
    def _draw_item_details(self, surface: pygame.Surface, item: GearItem):
        detail_y = 120
        
        # Item name
        name_surf = self.large_font.render(item.name, True, COLOR_WHITE)
        surface.blit(name_surf, (self.detail_x, detail_y))
        detail_y += 35
        
        # Cost
        cost_text = f"Cost: {self._format_cost(item)}"
        cost_surf = self.medium_font.render(cost_text, True, COLOR_GOLD)
        surface.blit(cost_surf, (self.detail_x, detail_y))
        detail_y += 25
        
        # Gear slots
        slots_text = f"Gear Slots: {item.gear_slots}"
        if item.quantity_per_slot > 1:
            slots_text += f" (up to {item.quantity_per_slot} per slot)"
        slots_surf = self.medium_font.render(slots_text, True, COLOR_WHITE)
        surface.blit(slots_surf, (self.detail_x, detail_y))
        detail_y += 25
        
        # Weapon-specific details
        if isinstance(item, Weapon):
            damage_text = f"Damage: {item.damage}"
            damage_surf = self.medium_font.render(damage_text, True, COLOR_WHITE)
            surface.blit(damage_surf, (self.detail_x, detail_y))
            detail_y += 25
            
            type_text = f"Type: {item.weapon_type} | Range: {item.range_type}"
            type_surf = self.small_font.render(type_text, True, COLOR_WHITE)
            surface.blit(type_surf, (self.detail_x, detail_y))
            detail_y += 20
            
            if item.weapon_properties:
                props_text = f"Properties: {', '.join(item.weapon_properties)}"
                props_surf = self.small_font.render(props_text, True, COLOR_WHITE)
                surface.blit(props_surf, (self.detail_x, detail_y))
                detail_y += 20
        
        # Armor-specific details
        elif isinstance(item, Armor):
            ac_text = f"Armor Class: {item.ac_bonus}"
            ac_surf = self.medium_font.render(ac_text, True, COLOR_WHITE)
            surface.blit(ac_surf, (self.detail_x, detail_y))
            detail_y += 25
            
            if item.armor_properties:
                props_text = f"Properties: {', '.join(item.armor_properties)}"
                props_surf = self.small_font.render(props_text, True, COLOR_WHITE)
                surface.blit(props_surf, (self.detail_x, detail_y))
                detail_y += 20
        
        # Kit contents
        elif isinstance(item, Kit):
            contents_title = self.medium_font.render("Contents:", True, COLOR_WHITE)
            surface.blit(contents_title, (self.detail_x, detail_y))
            detail_y += 25
            
            for content_name, quantity in item.contents:
                content_text = f"  {quantity}x {content_name}"
                content_surf = self.small_font.render(content_text, True, COLOR_WHITE)
                surface.blit(content_surf, (self.detail_x, detail_y))
                detail_y += 18
        
        detail_y += 10
        
        # Description
        if item.description:
            wrapped_lines = self._wrap_text(item.description, self.detail_width - 40, self.small_font)
            for line in wrapped_lines:
                line_surf = self.small_font.render(line, True, COLOR_WHITE)
                surface.blit(line_surf, (self.detail_x, detail_y))
                detail_y += 18
    
    def _draw_player_info(self, surface: pygame.Surface):
        # Calculate dynamic positioning based on screen size
        info_width = min(280, self.screen_width // 4)
        info_height = 140
        info_x = self.screen_width - info_width - 20
        info_y = 80
        
        # Adjust detail area to not overlap with player info
        self.detail_width = self.screen_width - self.detail_x - info_width - 60
        
        # Background
        info_rect = pygame.Rect(info_x, info_y, info_width, info_height)
        pygame.draw.rect(surface, (20, 20, 20), info_rect)
        pygame.draw.rect(surface, COLOR_WHITE, info_rect, 2)
        
        # Player name and class
        name_text = f"{self.player.name}"
        name_surf = self.medium_font.render(name_text, True, COLOR_WHITE)
        surface.blit(name_surf, (info_x + 10, info_y + 10))
        
        class_text = f"{self.player.character_class}"
        class_surf = self.small_font.render(class_text, True, COLOR_WHITE)
        surface.blit(class_surf, (info_x + 10, info_y + 30))
        
        # Gold
        gold_text = f"Gold: {self.gold:.1f} gp"
        gold_surf = self.small_font.render(gold_text, True, COLOR_GOLD)
        surface.blit(gold_surf, (info_x + 10, info_y + 55))
        
        # Gear slots with visual indicator
        slots_text = f"Gear Slots: {self.used_gear_slots}/{self.max_gear_slots}"
        color = COLOR_RED if self.used_gear_slots > self.max_gear_slots else COLOR_WHITE
        slots_surf = self.small_font.render(slots_text, True, color)
        surface.blit(slots_surf, (info_x + 10, info_y + 75))
        
        # Visual gear slots bar
        bar_width = min(200, info_width - 20)
        bar_height = 8
        bar_x = info_x + 10
        bar_y = info_y + 95
        
        # Background bar
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Filled portion
        if self.max_gear_slots > 0:
            fill_ratio = min(self.used_gear_slots / self.max_gear_slots, 1.0)
            fill_width = int(bar_width * fill_ratio)
            fill_color = COLOR_RED if self.used_gear_slots > self.max_gear_slots else COLOR_GREEN
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, fill_width, bar_height))
        
        # Items carried
        items_text = f"Items: {len(self.inventory)}"
        items_surf = self.small_font.render(items_text, True, COLOR_WHITE)
        surface.blit(items_surf, (info_x + 10, info_y + 110))
    
    def _draw_instructions(self, surface: pygame.Surface):
        instructions = []
        
        if self.state == GearSelectionState.CATEGORY_SELECTION:
            instructions = ["UP/DOWN: Navigate categories", "ENTER: Select category", "ESC: Cancel"]
        elif self.state == GearSelectionState.ITEM_SELECTION:
            instructions = ["UP/DOWN: Browse items", "ENTER: Select item", "ESC: Back to categories"]
        elif self.state == GearSelectionState.QUANTITY_SELECTION:
            instructions = ["UP/DOWN: Adjust quantity", "ENTER: Confirm quantity", "ESC: Back to items"]
        elif self.state == GearSelectionState.CONFIRM_PURCHASE:
            instructions = ["ENTER: Purchase item", "ESC: Cancel purchase"]
        elif self.state == GearSelectionState.REVIEW_GEAR:
            instructions = ["ENTER: Complete gear selection", "ESC: Continue shopping"]
        
        y = self.screen_height - 60
        for instruction in instructions:
            inst_surf = self.small_font.render(instruction, True, COLOR_WHITE)
            inst_rect = inst_surf.get_rect(centerx=self.screen_width // 2, y=y)
            surface.blit(inst_surf, inst_rect)
            y += 18
    
    def _format_cost(self, item: GearItem) -> str:
        """Format item cost as a readable string"""
        if item.cost_gp > 0:
            return f"{item.cost_gp} gp"
        elif item.cost_sp > 0:
            return f"{item.cost_sp} sp"
        elif item.cost_cp > 0:
            return f"{item.cost_cp} cp"
        else:
            return "Free"
    
    def _format_cost_cp(self, cost_cp: int) -> str:
        """Format cost in copper pieces as gold/silver/copper"""
        if cost_cp >= 100:
            gp = cost_cp // 100
            remainder = cost_cp % 100
            if remainder >= 10:
                sp = remainder // 10
                cp = remainder % 10
                if cp > 0:
                    return f"{gp} gp, {sp} sp, {cp} cp"
                else:
                    return f"{gp} gp, {sp} sp"
            elif remainder > 0:
                return f"{gp} gp, {remainder} cp"
            else:
                return f"{gp} gp"
        elif cost_cp >= 10:
            sp = cost_cp // 10
            cp = cost_cp % 10
            if cp > 0:
                return f"{sp} sp, {cp} cp"
            else:
                return f"{sp} sp"
        elif cost_cp > 0:
            return f"{cost_cp} cp"
        else:
            return "Free"
    
    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> List[str]:
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
    
    def get_final_inventory(self) -> List[InventoryItem]:
        """Get the final inventory for the player"""
        return self.inventory.copy()
    
    def get_remaining_gold(self) -> float:
        """Get remaining gold after purchases"""
        return self.gold

# Integration function to add gear selection to character creation
def run_gear_selection(player: Player, screen_width: int, screen_height: int, font_file: str) -> Optional[Player]:
    """Run gear selection after character creation"""
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Gear Selection")
    clock = pygame.time.Clock()
    
    gear_selector = GearSelector(player, screen_width, screen_height, font_file)
    
    running = True
    while running:
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            
            result = gear_selector.handle_event(event)
            if result is True:
                # Gear selection complete - update player with final inventory
                player.gold = gear_selector.get_remaining_gold()
                player.inventory = gear_selector.get_final_inventory()
                return player
            elif result is None:
                return None  # Cancelled
        
        gear_selector.draw(screen)
        pygame.display.flip()
    
    return None

# Property descriptions for tooltips
WEAPON_PROPERTIES = {
    "F": "Finesse - Use STR or DEX for attacks",
    "L": "Loading - Must forgo moving to reload",
    "Th": "Thrown - Can throw for ranged attack using STR or DEX", 
    "2H": "Two-handed - Must use with two hands",
    "V": "Versatile - Can use one or two handed (higher damage with two)"
}

# Add this to the main game integration
def integrate_gear_selection_with_character_creation():
    """
    To integrate this with your existing character creation:
    
    1. Add gear selection state to CharCreationState enum:
       GEAR_SELECTION = 9
    
    2. In character_creation.py, modify the _next_state method to include gear selection:
       elif self.state == CharCreationState.STATS_REVIEW:
           self.state = CharCreationState.GEAR_SELECTION
       elif self.state == CharCreationState.GEAR_SELECTION:
           self.state = CharCreationState.COMPLETE
    
    3. Add gear selection handling in the main character creation loop:
       elif self.state == CharCreationState.GEAR_SELECTION:
           # Run gear selection
           gear_result = run_gear_selection(self.create_player(), screen_width, screen_height, font_file)
           if gear_result:
               return gear_result
           else:
               self.state = CharCreationState.STATS_REVIEW
    
    4. Add inventory field to Player dataclass:
       inventory: List[InventoryItem] = field(default_factory=list)
       gold: float = 0.0
    """
    pass