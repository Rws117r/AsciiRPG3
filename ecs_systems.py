# ecs_systems.py - System implementations for the ECS architecture (Phase 3 Complete)

from typing import List, Set, Tuple, Optional, Dict, Any
import random
import time
from dataclasses import dataclass

from ecs_core import System, World, EntityID
from ecs_components import *

# =============================================================================
# EVENT DEFINITIONS - Events that systems can process
# =============================================================================

@dataclass
class MoveEvent:
    """Entity wants to move"""
    entity: EntityID
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]

@dataclass
class MovementCompletedEvent:
    """Entity successfully moved"""
    entity: EntityID
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]

@dataclass
class EntityPushedEvent:
    """Entity was pushed by another entity"""
    pusher: EntityID
    pushee: EntityID
    new_position: Tuple[int, int]

@dataclass
class DamageEvent:
    """Entity takes damage"""
    target: EntityID
    damage: int
    damage_type: str = "physical"
    source: Optional[EntityID] = None

@dataclass
class DamageAppliedEvent:
    """Damage was applied to entity"""
    target: EntityID
    actual_damage: int
    entity_died: bool

@dataclass
class HealEvent:
    """Entity is healed"""
    target: EntityID
    amount: int
    source: Optional[EntityID] = None

@dataclass
class HealingAppliedEvent:
    """Healing was applied to entity"""
    target: EntityID
    actual_healing: int

@dataclass
class EntityDeathEvent:
    """Entity died"""
    entity: EntityID
    killer: Optional[EntityID] = None

@dataclass
class InteractionEvent:
    """Entity interacts with another entity"""
    actor: EntityID
    target: Optional[EntityID]
    interaction_type: str = "generic"

@dataclass
class InteractionSuccessEvent:
    """Interaction succeeded"""
    actor: EntityID
    target: EntityID
    interaction_type: str

@dataclass
class InteractionFailedEvent:
    """Interaction failed"""
    actor: EntityID
    target: Optional[EntityID]
    reason: str

@dataclass
class ExaminationEvent:
    """Entity examines a position"""
    examiner: EntityID
    target_pos: Tuple[int, int]
    distance: int

@dataclass
class WaitEvent:
    """Entity waits/defends for a turn"""
    entity: EntityID

@dataclass
class UIEvent:
    """Request to open UI screen"""
    ui_type: str  # 'inventory', 'equipment', 'spells'
    entity: EntityID

@dataclass
class ExperienceGainEvent:
    """Entity gains experience"""
    entity: EntityID
    amount: int

# =============================================================================
# CORE SYSTEMS - Essential functionality
# =============================================================================

class RenderSystem(System):
    """Manages rendering of all visible entities"""
    
    def __init__(self):
        self.visible_entities: List[Tuple[EntityID, PositionComponent, RenderableComponent]] = []
        self.camera_x = 0
        self.camera_y = 0
        self.viewport_width = 20
        self.viewport_height = 15
    
    def update(self, world: World, dt: float):
        """Update the list of entities to render"""
        # Get all renderable entities
        entities = world.get_entities_with_components(PositionComponent, RenderableComponent)
        
        self.visible_entities.clear()
        for entity in entities:
            pos = world.get_component(entity, PositionComponent)
            render = world.get_component(entity, RenderableComponent)
            
            # Only include visible entities within viewport
            if (render.visible and 
                self.camera_x <= pos.x < self.camera_x + self.viewport_width and
                self.camera_y <= pos.y < self.camera_y + self.viewport_height):
                self.visible_entities.append((entity, pos, render))
        
        # Sort by render layer (lower layers render first)
        self.visible_entities.sort(key=lambda x: x[2].render_layer)
    
    def set_camera(self, x: int, y: int):
        """Set camera position"""
        self.camera_x = x
        self.camera_y = y
    
    def set_viewport_size(self, width: int, height: int):
        """Set viewport dimensions"""
        self.viewport_width = width
        self.viewport_height = height
    
    def get_renderable_entities(self) -> List[Tuple[EntityID, PositionComponent, RenderableComponent]]:
        """Get sorted list of entities to render"""
        return self.visible_entities.copy()

class MovementSystem(System):
    """Handles entity movement and collision detection"""
    
    def update(self, world: World, dt: float):
        """Process movement events"""
        for event in world.events:
            if isinstance(event, MoveEvent):
                self.process_movement(world, event)
    
    def process_movement(self, world: World, move_event: MoveEvent):
        """Process a single movement event"""
        entity = move_event.entity
        new_x, new_y = move_event.to_pos
        
        # Get entity's position component
        pos_comp = world.get_component(entity, PositionComponent)
        if not pos_comp:
            return False  # Entity can't move without position
        
        # Check if the entity can move
        if not world.has_component(entity, MovementComponent):
            return False  # Entity can't move
        
        # Check for collision with blocking entities
        if self._is_position_blocked(world, new_x, new_y, entity):
            # Try to handle special cases (pushing, etc.)
            if self._try_special_movement(world, entity, new_x, new_y):
                # Special movement succeeded, update position
                pos_comp.x = new_x
                pos_comp.y = new_y
                return True
            else:
                return False  # Movement blocked
        
        # No collision, update position
        old_pos = (pos_comp.x, pos_comp.y)
        pos_comp.x = new_x
        pos_comp.y = new_y
        
        # Add movement completion event
        world.add_event(MovementCompletedEvent(entity, old_pos, (new_x, new_y)))
        return True
    
    def _is_position_blocked(self, world: World, x: int, y: int, moving_entity: EntityID) -> bool:
        """Check if a position is blocked by other entities"""
        blocking_entities = world.get_entities_with_components(PositionComponent, BlocksMovementComponent)
        
        for blocking_entity in blocking_entities:
            if blocking_entity == moving_entity:
                continue  # Don't block yourself
            
            blocking_pos = world.get_component(blocking_entity, PositionComponent)
            blocking_comp = world.get_component(blocking_entity, BlocksMovementComponent)
            
            if blocking_pos.x == x and blocking_pos.y == y:
                # Check what type of entity is trying to move
                if world.has_component(moving_entity, PlayerControlledComponent):
                    return blocking_comp.blocks_player
                elif world.has_component(moving_entity, MonsterComponent):
                    return blocking_comp.blocks_monsters
                elif world.has_component(moving_entity, ItemComponent):
                    return blocking_comp.blocks_items
                else:
                    return True  # Block unknown entity types
        
        return False
    
    def _try_special_movement(self, world: World, entity: EntityID, x: int, y: int) -> bool:
        """Try special movement like pushing boulders"""
        # Find what's blocking the position
        blocking_entities = world.get_entities_with_components(PositionComponent, BlocksMovementComponent)
        
        for blocking_entity in blocking_entities:
            blocking_pos = world.get_component(blocking_entity, PositionComponent)
            if blocking_pos.x == x and blocking_pos.y == y:
                # Check if this entity can be pushed
                movable = world.get_component(blocking_entity, MovableComponent)
                if movable:
                    return self._try_push_entity(world, entity, blocking_entity, x, y)
        
        return False
    
    def _try_push_entity(self, world: World, pusher: EntityID, pushee: EntityID, target_x: int, target_y: int) -> bool:
        """Try to push one entity with another"""
        pusher_pos = world.get_component(pusher, PositionComponent)
        pushee_pos = world.get_component(pushee, PositionComponent)
        movable = world.get_component(pushee, MovableComponent)
        pusher_stats = world.get_component(pusher, StatsComponent)
        
        if not all([pusher_pos, pushee_pos, movable, pusher_stats]):
            return False
        
        # Calculate push direction
        push_dx = target_x - pusher_pos.x
        push_dy = target_y - pusher_pos.y
        push_target_x = pushee_pos.x + push_dx
        push_target_y = pushee_pos.y + push_dy
        
        # Check if push destination is valid
        if self._is_position_blocked(world, push_target_x, push_target_y, pushee):
            return False
        
        # Check if pusher is strong enough
        strength_mod = pusher_stats.get_modifier('strength')
        push_roll = random.randint(1, 20) + strength_mod
        
        if push_roll >= movable.push_difficulty:
            # Success! Move the pushed entity
            pushee_pos.x = push_target_x
            pushee_pos.y = push_target_y
            world.add_event(EntityPushedEvent(pusher, pushee, (push_target_x, push_target_y)))
            return True
        
        return False

class PlayerInputSystem(System):
    """Processes player input events"""
    
    def update(self, world: World, dt: float):
        """Process player input events"""
        for event in world.events:
            if isinstance(event, WaitEvent):
                self._process_wait(world, event)
            elif isinstance(event, UIEvent):
                self._process_ui_request(world, event)
    
    def _process_wait(self, world: World, event: WaitEvent):
        """Process wait/defend action"""
        # For now, just add a message
        name_comp = world.get_component(event.entity, NameComponent)
        if name_comp:
            print(f"{name_comp.name} waits and defends.")
        
        # Could add defense bonus or other effects here
    
    def _process_ui_request(self, world: World, event: UIEvent):
        """Process UI screen requests"""
        # This would trigger UI state changes in the game manager
        # For now, just log the request
        name_comp = world.get_component(event.entity, NameComponent)
        name = name_comp.name if name_comp else "Unknown"
        print(f"{name} wants to open {event.ui_type} screen")

class ExperienceSystem(System):
    """Handles experience gain and leveling up"""
    
    def update(self, world: World, dt: float):
        """Process experience events"""
        for event in world.events:
            if isinstance(event, ExperienceGainEvent):
                self._process_experience_gain(world, event)
    
    def _process_experience_gain(self, world: World, event: ExperienceGainEvent):
        """Process experience gain"""
        exp_comp = world.get_component(event.entity, ExperienceComponent)
        if not exp_comp:
            return
        
        exp_comp.current_xp += event.amount
        
        # Check for level up
        while exp_comp.can_level_up():
            self._level_up_entity(world, event.entity, exp_comp)
    
    def _level_up_entity(self, world: World, entity: EntityID, exp_comp: ExperienceComponent):
        """Level up an entity"""
        # Deduct XP for level
        exp_comp.current_xp -= exp_comp.xp_to_next_level()
        exp_comp.level += 1
        
        # Increase health
        health_comp = world.get_component(entity, HealthComponent)
        class_comp = world.get_component(entity, ClassComponent)
        stats_comp = world.get_component(entity, StatsComponent)
        
        if health_comp and class_comp and stats_comp:
            # Calculate HP gain
            con_mod = stats_comp.get_modifier('constitution')
            
            if class_comp.character_class == "Fighter":
                hp_gain = random.randint(1, 8) + con_mod
            elif class_comp.character_class == "Priest":
                hp_gain = random.randint(1, 6) + con_mod
            else:  # Thief, Wizard
                hp_gain = random.randint(1, 4) + con_mod
            
            hp_gain = max(1, hp_gain)
            health_comp.max_hp += hp_gain
            health_comp.current_hp += hp_gain
            
            # Announce level up
            name_comp = world.get_component(entity, NameComponent)
            name = name_comp.name if name_comp else "Unknown"
            print(f"{name} reached level {exp_comp.level}! HP increased by {hp_gain}!")

class HealthSystem(System):
    """Manages entity health and death"""
    
    def update(self, world: World, dt: float):
        """Process health-related events"""
        for event in world.events:
            if isinstance(event, DamageEvent):
                self.process_damage(world, event)
            elif isinstance(event, HealEvent):
                self.process_healing(world, event)
        
        # Check for dead entities
        self._check_for_deaths(world)
    
    def process_damage(self, world: World, damage_event: DamageEvent):
        """Apply damage to an entity"""
        target = damage_event.target
        health = world.get_component(target, HealthComponent)
        
        if not health or not health.is_alive:
            return  # Can't damage dead entities
        
        # Apply damage
        actual_damage = health.damage(damage_event.damage)
        
        # Create damage result event
        world.add_event(DamageAppliedEvent(target, actual_damage, health.current_hp <= 0))
        
        # Check for death
        if health.current_hp <= 0:
            world.add_event(EntityDeathEvent(target, damage_event.source))
    
    def process_healing(self, world: World, heal_event: HealEvent):
        """Apply healing to an entity"""
        target = heal_event.target
        health = world.get_component(target, HealthComponent)
        
        if not health:
            return  # Can't heal entities without health
        
        # Apply healing
        actual_healing = health.heal(heal_event.amount)
        
        # Create healing result event
        world.add_event(HealingAppliedEvent(target, actual_healing))
    
    def _check_for_deaths(self, world: World):
        """Check for entities that should be dead"""
        entities_with_health = world.get_entities_with_components(HealthComponent)
        
        for entity in entities_with_health:
            health = world.get_component(entity, HealthComponent)
            if health and not health.is_alive:
                # Mark entity for death processing
                world.add_event(EntityDeathEvent(entity, None))

class StatusEffectSystem(System):
    """Manages temporary status effects"""
    
    def update(self, world: World, dt: float):
        """Update all status effects"""
        # Process each type of status effect
        self._process_poison(world, dt)
        self._process_fire(world, dt)
        self._process_blessings(world, dt)
        self._process_curses(world, dt)
        
        # Decrement durations and remove expired effects
        self._update_effect_durations(world)
    
    def _process_poison(self, world: World, dt: float):
        """Process poison damage"""
        poisoned_entities = world.get_entities_with_components(PoisonedComponent, HealthComponent)
        
        for entity in poisoned_entities:
            poison = world.get_component(entity, PoisonedComponent)
            if poison and not poison.is_expired:
                # Apply poison damage
                world.add_event(DamageEvent(entity, poison.damage_per_turn, "poison", poison.source))
    
    def _process_fire(self, world: World, dt: float):
        """Process fire damage and spreading"""
        burning_entities = world.get_entities_with_components(OnFireComponent, HealthComponent)
        
        for entity in burning_entities:
            fire = world.get_component(entity, OnFireComponent)
            if fire and not fire.is_expired:
                # Apply fire damage
                world.add_event(DamageEvent(entity, fire.fire_damage, "fire", fire.source))
                
                # Try to spread fire
                if random.random() < fire.spread_chance:
                    self._try_spread_fire(world, entity, fire)
    
    def _try_spread_fire(self, world: World, burning_entity: EntityID, fire_component: OnFireComponent):
        """Try to spread fire to nearby flammable entities"""
        pos = world.get_component(burning_entity, PositionComponent)
        if not pos:
            return
        
        # Check adjacent positions for flammable entities
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                check_x, check_y = pos.x + dx, pos.y + dy
                nearby_entities = world.get_entities_with_components(PositionComponent, FlammableComponent)
                
                for nearby_entity in nearby_entities:
                    nearby_pos = world.get_component(nearby_entity, PositionComponent)
                    flammable = world.get_component(nearby_entity, FlammableComponent)
                    
                    if (nearby_pos.x == check_x and nearby_pos.y == check_y and
                        not world.has_component(nearby_entity, OnFireComponent)):
                        
                        # Check if entity catches fire
                        if random.random() < flammable.ignition_chance:
                            world.add_component(nearby_entity, OnFireComponent(
                                duration_remaining=5,
                                fire_damage=flammable.burn_damage,
                                source=burning_entity
                            ))
    
    def _process_blessings(self, world: World, dt: float):
        """Process blessing effects"""
        # Blessings are mostly passive, but we could add periodic effects here
        pass
    
    def _process_curses(self, world: World, dt: float):
        """Process curse effects"""
        # Curses are mostly passive, but we could add periodic effects here
        pass
    
    def _update_effect_durations(self, world: World):
        """Update durations and remove expired effects"""
        status_components = [PoisonedComponent, OnFireComponent, BlessedComponent, CursedComponent, WetComponent]
        
        for component_type in status_components:
            entities = world.get_entities_with_components(component_type)
            for entity in entities:
                effect = world.get_component(entity, component_type)
                if effect and not effect.is_permanent:
                    effect.duration_remaining -= 1
                    if effect.is_expired:
                        world.remove_component(entity, component_type)

class InteractionSystem(System):
    """Handles entity interactions"""
    
    def update(self, world: World, dt: float):
        """Process interaction events"""
        for event in world.events:
            if isinstance(event, InteractionEvent):
                self.process_interaction(world, event)
    
    def process_interaction(self, world: World, interaction_event: InteractionEvent):
        """Process a single interaction"""
        actor = interaction_event.actor
        target = interaction_event.target
        
        # If no specific target, find nearby interactable entities
        if target is None:
            target = self._find_nearby_interactable(world, actor)
            if target is None:
                world.add_event(InteractionFailedEvent(actor, None, "Nothing to interact with"))
                return False
        
        # Check if target is interactable
        interactable = world.get_component(target, InteractableComponent)
        if not interactable:
            world.add_event(InteractionFailedEvent(actor, target, "Not interactable"))
            return False
        
        # Check distance if required
        if interactable.requires_adjacent:
            if not self._are_adjacent(world, actor, target):
                world.add_event(InteractionFailedEvent(actor, target, "Too far away"))
                return False
        
        # Check interaction limits
        if (interactable.max_interactions >= 0 and 
            interactable.interaction_count >= interactable.max_interactions):
            world.add_event(InteractionFailedEvent(actor, target, "No more uses"))
            return False
        
        # Process interaction based on type
        success = self._process_specific_interaction(world, actor, target, interactable)
        
        if success:
            interactable.interaction_count += 1
            world.add_event(InteractionSuccessEvent(actor, target, interactable.interaction_type))
        
        return success
    
    def _find_nearby_interactable(self, world: World, actor: EntityID) -> Optional[EntityID]:
        """Find nearby interactable entities"""
        actor_pos = world.get_component(actor, PositionComponent)
        if not actor_pos:
            return None
        
        interactable_entities = world.get_entities_with_components(PositionComponent, InteractableComponent)
        
        for entity in interactable_entities:
            entity_pos = world.get_component(entity, PositionComponent)
            if entity_pos and actor_pos.distance_to(entity_pos) <= 1:
                return entity
        
        return None
    
    def _are_adjacent(self, world: World, entity1: EntityID, entity2: EntityID) -> bool:
        """Check if two entities are adjacent"""
        pos1 = world.get_component(entity1, PositionComponent)
        pos2 = world.get_component(entity2, PositionComponent)
        
        if not pos1 or not pos2:
            return False
        
        return pos1.distance_to(pos2) <= 1
    
    def _process_specific_interaction(self, world: World, actor: EntityID, target: EntityID, 
                                    interactable: InteractableComponent) -> bool:
        """Process specific interaction types"""
        interaction_type = interactable.interaction_type
        
        if interaction_type == "door":
            return self._interact_with_door(world, actor, target)
        elif interaction_type == "container":
            return self._interact_with_container(world, actor, target)
        elif interaction_type == "light_source":
            return self._interact_with_light(world, actor, target)
        elif interaction_type == "altar":
            return self._interact_with_altar(world, actor, target)
        else:
            # Generic interaction
            return True
    
    def _interact_with_door(self, world: World, actor: EntityID, door: EntityID) -> bool:
        """Handle door interaction"""
        door_comp = world.get_component(door, DoorComponent)
        if not door_comp:
            return False
        
        if door_comp.locked:
            # Check if actor has key
            # TODO: Implement key checking
            world.add_event(InteractionFailedEvent(actor, door, "Door is locked"))
            return False
        
        # Toggle door state
        door_comp.is_open = not door_comp.is_open
        
        # Update renderable if present
        renderable = world.get_component(door, RenderableComponent)
        if renderable:
            renderable.ascii_char = '-' if door_comp.is_open else '+'
        
        return True
    
    def _interact_with_container(self, world: World, actor: EntityID, container: EntityID) -> bool:
        """Handle container interaction"""
        container_comp = world.get_component(container, ContainerComponent)
        if not container_comp:
            return False
        
        if container_comp.requires_key:
            # TODO: Implement key checking
            world.add_event(InteractionFailedEvent(actor, container, "Container is locked"))
            return False
        
        # Toggle container state
        container_comp.is_open = not container_comp.is_open
        return True
    
    def _interact_with_light(self, world: World, actor: EntityID, light_source: EntityID) -> bool:
        """Handle light source interaction"""
        light = world.get_component(light_source, LightSourceComponent)
        if not light:
            return False
        
        # Toggle light state
        light.lit = not light.lit
        
        # Update renderable color
        renderable = world.get_component(light_source, RenderableComponent)
        if renderable:
            if light.lit:
                renderable.color = light.light_color
            else:
                renderable.color = (100, 100, 100)  # Dim gray when unlit
        
        return True
    
    def _interact_with_altar(self, world: World, actor: EntityID, altar: EntityID) -> bool:
        """Handle altar interaction"""
        # Add blessing to actor
        world.add_component(actor, BlessedComponent(duration_remaining=10, bonus_amount=1))
        return True

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_basic_systems() -> List[System]:
    """Create the basic systems needed for a functioning game"""
    return [
        RenderSystem(),
        MovementSystem(),
        HealthSystem(),
        StatusEffectSystem(),
        InteractionSystem(),
    ]