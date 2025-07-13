# presets.py - Preset character builds for quick testing
from character_creation import Player
from gear_selection import WEAPONS, ARMOR, GENERAL_GEAR, InventoryItem
import time

def create_preset_fighter() -> Player:
    """Creates a preset Dwarf Fighter character."""
    bastard_sword = InventoryItem(item=WEAPONS["Bastard sword"], quantity=1)
    chainmail = InventoryItem(item=ARMOR["Chainmail"], quantity=1)
    shield = InventoryItem(item=ARMOR["Shield"], quantity=1)
    rations = InventoryItem(item=GENERAL_GEAR["Rations (3)"], quantity=2)

    fighter = Player(
        name="Grorim",
        title="Stalwart Squire",
        race="Dwarf",
        alignment="Lawful",
        character_class="Fighter",
        level=1,
        hp=14,
        max_hp=14,
        xp=0,
        xp_to_next_level=100,
        ac=17,
        light_duration=3600,
        light_start_time=time.time(),
        strength=16,
        dexterity=14,
        constitution=16,
        intelligence=9,
        wisdom=10,
        charisma=8,
        god="Saint Terragnis",
        inventory=[bastard_sword, chainmail, shield, rations],
        equipment={
            'weapon': bastard_sword,
            'armor': chainmail,
            'shield': shield
        },
        gold=50.0,
        gear_slots_used=5,
        max_gear_slots=16
    )
    return fighter

def create_preset_thief() -> Player:
    """Creates a preset Halfling Thief character."""
    shortsword = InventoryItem(item=WEAPONS["Shortsword"], quantity=1)
    shortbow = InventoryItem(item=WEAPONS["Shortbow"], quantity=1)
    arrows = InventoryItem(item=GENERAL_GEAR["Arrows (20)"], quantity=1)
    leather_armor = InventoryItem(item=ARMOR["Leather armor"], quantity=1)
    
    thief = Player(
        name="Pippin",
        title="Rooftop Runner",
        race="Halfling",
        alignment="Chaotic",
        character_class="Thief",
        level=1,
        hp=7,
        max_hp=7,
        xp=0,
        xp_to_next_level=100,
        ac=15,
        light_duration=3600,
        light_start_time=time.time(),
        strength=10,
        dexterity=17,
        constitution=12,
        intelligence=13,
        wisdom=9,
        charisma=14,
        god="",
        inventory=[shortsword, shortbow, arrows, leather_armor],
        equipment={
            'weapon': shortsword,
            'armor': leather_armor
        },
        gold=75.0,
        gear_slots_used=4,
        max_gear_slots=10
    )
    return thief