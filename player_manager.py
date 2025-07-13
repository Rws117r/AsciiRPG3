# player_manager.py - Player character management
from character_creation import Player
from ui_systems import calculate_armor_class, get_stat_modifier

class PlayerManager:
    """Manages player character data and actions."""
    
    def __init__(self):
        self.player: Player = None
    
    def setup_player(self, player: Player):
        """Setup a newly created player character."""
        self.player = player
        
        # Calculate AC based on equipment
        player.ac = calculate_armor_class(player)
        
        # Update gear slots if Fighter with Constitution bonus
        if player.character_class == "Fighter":
            constitution_bonus = get_stat_modifier(player.constitution)
            if constitution_bonus > 0:
                player.max_gear_slots += constitution_bonus
        
        # Calculate actual gear slots used from inventory
        self._calculate_gear_slots_used()
        
        print(f"Player setup complete:")
        print(f"  Name: {player.name}")
        print(f"  Class: {player.character_class}")
        print(f"  Items: {len(player.inventory)}")
        print(f"  Gold: {player.gold}")
        print(f"  Gear slots: {player.gear_slots_used}/{player.max_gear_slots}")
        print(f"  AC: {player.ac}")
        print(f"  HP: {player.hp}/{player.max_hp}")
    
    def _calculate_gear_slots_used(self):
        """Calculate how many gear slots are currently used."""
        self.player.gear_slots_used = 0
        
        for inv_item in self.player.inventory:
            item_slots = getattr(inv_item.item, 'gear_slots', 1)
            
            if hasattr(inv_item.item, 'quantity_per_slot') and inv_item.item.quantity_per_slot > 1:
                # Items that can stack (like arrows, rations)
                slots_needed = (inv_item.quantity + inv_item.item.quantity_per_slot - 1) // inv_item.item.quantity_per_slot
                self.player.gear_slots_used += slots_needed * item_slots
            else:
                # Regular items
                self.player.gear_slots_used += item_slots * inv_item.quantity
    
    def update_player_hp(self, new_hp: int):
        """Update player HP and handle death."""
        self.player.hp = max(0, min(new_hp, self.player.max_hp))
        
        if self.player.hp <= 0:
            self._handle_player_death()
    
    def _handle_player_death(self):
        """Handle player character death."""
        print(f"{self.player.name} has fallen!")
        # Death handling logic could go here
    
    def heal_player(self, amount: int) -> int:
        """Heal the player and return actual amount healed."""
        old_hp = self.player.hp
        self.player.hp = min(self.player.hp + amount, self.player.max_hp)
        return self.player.hp - old_hp
    
    def get_attack_bonus(self) -> int:
        """Calculate player's attack bonus."""
        attack_bonus = get_stat_modifier(self.player.strength)
        
        # Class-specific bonuses
        if self.player.character_class == "Fighter":
            attack_bonus += self.player.level // 2
        
        return attack_bonus
    
    def get_damage_bonus(self) -> int:
        """Calculate player's damage bonus."""
        return get_stat_modifier(self.player.strength)
    
    def can_carry_more(self, additional_slots: int = 1) -> bool:
        """Check if player can carry additional gear slots."""
        return (self.player.gear_slots_used + additional_slots) <= self.player.max_gear_slots
    
    def add_experience(self, xp_amount: int):
        """Add experience and handle level ups."""
        self.player.xp += xp_amount
        
        while self.player.xp >= self.player.xp_to_next_level:
            self._level_up()
    
    def _level_up(self):
        """Handle player leveling up."""
        self.player.xp -= self.player.xp_to_next_level
        self.player.level += 1
        
        # Increase XP requirement for next level
        self.player.xp_to_next_level = self._calculate_xp_for_level(self.player.level + 1)
        
        # Roll for HP increase
        hp_increase = self._roll_hp_increase()
        self.player.max_hp += hp_increase
        self.player.hp += hp_increase  # Full heal on level up
        
        print(f"{self.player.name} reached level {self.player.level}!")
        print(f"HP increased by {hp_increase}!")
    
    def _calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP requirement for a given level."""
        # Simple progression: level * 100
        return level * 100
    
    def _roll_hp_increase(self) -> int:
        """Roll HP increase for level up."""
        import random
        
        con_modifier = get_stat_modifier(self.player.constitution)
        
        if self.player.character_class == "Fighter":
            hp_gain = random.randint(1, 8) + con_modifier
        elif self.player.character_class == "Priest":
            hp_gain = random.randint(1, 6) + con_modifier
        else:  # Thief and Wizard
            hp_gain = random.randint(1, 4) + con_modifier
        
        return max(1, hp_gain)  # Minimum 1 HP gain
    
    def get_player_stats_summary(self) -> dict:
        """Get a summary of player statistics."""
        return {
            'name': self.player.name,
            'title': self.player.title,
            'race': self.player.race,
            'class': self.player.character_class,
            'alignment': self.player.alignment,
            'level': self.player.level,
            'hp': f"{self.player.hp}/{self.player.max_hp}",
            'ac': self.player.ac,
            'xp': f"{self.player.xp}/{self.player.xp_to_next_level}",
            'gold': self.player.gold,
            'gear_slots': f"{self.player.gear_slots_used}/{self.player.max_gear_slots}",
            'stats': {
                'strength': self.player.strength,
                'dexterity': self.player.dexterity,
                'constitution': self.player.constitution,
                'intelligence': self.player.intelligence,
                'wisdom': self.player.wisdom,
                'charisma': self.player.charisma
            }
        }