# ecs_core.py - Core Entity-Component-System implementation

from typing import Dict, Set, Any, Type, Optional, List, TypeVar, Generic
import uuid
from abc import ABC, abstractmethod

# Type hints for better IDE support
ComponentType = TypeVar('ComponentType')
EntityType = 'EntityID'

class EntityID:
    """Unique identifier for entities in the ECS world"""
    
    def __init__(self):
        self.id = uuid.uuid4()
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, EntityID) and self.id == other.id
    
    def __repr__(self):
        return f"Entity({str(self.id)[:8]})"

class Component:
    """Base class for all components - pure data containers"""
    pass

class System(ABC):
    """Base class for all systems - pure logic processors"""
    
    @abstractmethod
    def update(self, world: 'World', dt: float):
        """Override this method to implement system logic"""
        pass
    
    def on_entity_added(self, world: 'World', entity: EntityID):
        """Called when an entity matching this system's requirements is added"""
        pass
    
    def on_entity_removed(self, world: 'World', entity: EntityID):
        """Called when an entity matching this system's requirements is removed"""
        pass

class World:
    """The ECS world that manages entities, components, and systems"""
    
    def __init__(self):
        self.entities: Set[EntityID] = set()
        self.components: Dict[Type[Component], Dict[EntityID, Component]] = {}
        self.systems: List[System] = []
        self.events: List[Any] = []
        self._entity_cache: Dict[frozenset, Set[EntityID]] = {}
        self._next_update_id = 0
    
    def create_entity(self) -> EntityID:
        """Create a new entity and return its ID"""
        entity = EntityID()
        self.entities.add(entity)
        self._invalidate_cache()
        return entity
    
    def destroy_entity(self, entity: EntityID) -> bool:
        """Remove an entity and all its components"""
        if entity not in self.entities:
            return False
        
        # Notify systems before removal
        for system in self.systems:
            system.on_entity_removed(self, entity)
        
        # Remove from all component stores
        for component_dict in self.components.values():
            component_dict.pop(entity, None)
        
        # Remove from entity set
        self.entities.discard(entity)
        self._invalidate_cache()
        return True
    
    def add_component(self, entity: EntityID, component: Component):
        """Add a component to an entity"""
        if entity not in self.entities:
            raise ValueError(f"Entity {entity} does not exist")
        
        component_type = type(component)
        if component_type not in self.components:
            self.components[component_type] = {}
        
        # Remove old component of same type if exists
        old_component = self.components[component_type].get(entity)
        
        # Add new component
        self.components[component_type][entity] = component
        
        # Invalidate cache and notify systems
        self._invalidate_cache()
        if old_component is None:  # Only notify if this is a new component type
            for system in self.systems:
                system.on_entity_added(self, entity)
    
    def remove_component(self, entity: EntityID, component_type: Type[Component]) -> bool:
        """Remove a component from an entity"""
        if component_type not in self.components:
            return False
        
        removed = self.components[component_type].pop(entity, None)
        if removed:
            self._invalidate_cache()
            for system in self.systems:
                system.on_entity_removed(self, entity)
        
        return removed is not None
    
    def get_component(self, entity: EntityID, component_type: Type[ComponentType]) -> Optional[ComponentType]:
        """Get a component from an entity"""
        if component_type not in self.components:
            return None
        return self.components[component_type].get(entity)
    
    def has_component(self, entity: EntityID, component_type: Type[Component]) -> bool:
        """Check if entity has a specific component"""
        return (component_type in self.components and 
                entity in self.components[component_type])
    
    def has_components(self, entity: EntityID, *component_types: Type[Component]) -> bool:
        """Check if entity has ALL the specified components"""
        return all(self.has_component(entity, comp_type) for comp_type in component_types)
    
    def get_entities_with_components(self, *component_types: Type[Component]) -> Set[EntityID]:
        """Get all entities that have ALL the specified components"""
        if not component_types:
            return set()
        
        # Use cache for performance
        cache_key = frozenset(component_types)
        if cache_key in self._entity_cache:
            return self._entity_cache[cache_key].copy()
        
        # Start with entities that have the first component
        if component_types[0] not in self.components:
            result = set()
        else:
            result = set(self.components[component_types[0]].keys())
        
        # Intersect with entities that have each subsequent component
        for component_type in component_types[1:]:
            if component_type not in self.components:
                result = set()
                break
            result &= set(self.components[component_type].keys())
        
        # Cache the result
        self._entity_cache[cache_key] = result.copy()
        return result
    
    def get_entities_with_any_components(self, *component_types: Type[Component]) -> Set[EntityID]:
        """Get all entities that have ANY of the specified components"""
        result = set()
        for component_type in component_types:
            if component_type in self.components:
                result |= set(self.components[component_type].keys())
        return result
    
    def add_system(self, system: System):
        """Add a system to the world"""
        if system not in self.systems:
            self.systems.append(system)
    
    def remove_system(self, system: System) -> bool:
        """Remove a system from the world"""
        try:
            self.systems.remove(system)
            return True
        except ValueError:
            return False
    
    def add_event(self, event: Any):
        """Add an event to be processed this frame"""
        self.events.append(event)
    
    def clear_events(self):
        """Clear all events (usually called after processing)"""
        self.events.clear()
    
    def update(self, dt: float):
        """Update all systems"""
        self._next_update_id += 1
        
        # Update all systems
        for system in self.systems:
            try:
                system.update(self, dt)
            except Exception as e:
                print(f"Error in system {type(system).__name__}: {e}")
                # Continue with other systems even if one fails
        
        # Clear events after all systems have processed them
        self.clear_events()
    
    def _invalidate_cache(self):
        """Clear the entity query cache when entities/components change"""
        self._entity_cache.clear()
    
    def get_entity_count(self) -> int:
        """Get the total number of entities"""
        return len(self.entities)
    
    def get_component_count(self, component_type: Type[Component]) -> int:
        """Get the number of entities with a specific component"""
        return len(self.components.get(component_type, {}))
    
    def debug_info(self) -> Dict[str, Any]:
        """Get debug information about the world state"""
        component_counts = {}
        for comp_type, comp_dict in self.components.items():
            component_counts[comp_type.__name__] = len(comp_dict)
        
        return {
            'entity_count': len(self.entities),
            'system_count': len(self.systems),
            'component_types': len(self.components),
            'component_counts': component_counts,
            'event_count': len(self.events),
            'cache_size': len(self._entity_cache)
        }

# Utility functions for common ECS patterns
def create_archetype_matcher(*required_components: Type[Component]):
    """Create a function that checks if an entity matches an archetype"""
    def matches(world: World, entity: EntityID) -> bool:
        return world.has_components(entity, *required_components)
    return matches

def query_entities(world: World, *component_types: Type[Component]) -> List[tuple]:
    """Query entities and return tuples of (entity, component1, component2, ...)"""
    entities = world.get_entities_with_components(*component_types)
    results = []
    
    for entity in entities:
        components = []
        for comp_type in component_types:
            component = world.get_component(entity, comp_type)
            components.append(component)
        results.append((entity, *components))
    
    return results

def for_each_entity(world: World, *component_types: Type[Component]):
    """Decorator to iterate over entities with specific components"""
    def decorator(func):
        def wrapper():
            entities = world.get_entities_with_components(*component_types)
            for entity in entities:
                components = [world.get_component(entity, comp_type) for comp_type in component_types]
                func(entity, *components)
        return wrapper
    return decorator