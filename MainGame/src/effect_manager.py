# src/effect_manager.py
import random


class EffectManager:
    """Manages active effects (buffs, debuffs, counters, DoT) on entities"""
    
    def __init__(self):
        # Map of entity -> list of effects
        # entity can be player or enemy (identified by id(entity))
        self.active_effects = {}
    
    def add_effect(self, entity, effect, caster=None):
        """Add an effect to an entity
        
        effect structure:
        {
            'type': 'buff'|'debuff'|'counter'|'dot',
            'stat': 'atk'|'def'|'magic_power'|etc (for buff/debuff),
            'value': int (for buff/debuff),
            'damage': int (for dot),
            'damage_type': 'physical'|'magic' (for dot scaling),
            'damage_percent': float (for counter),
            'duration': int (turns),
            'source': str (skill name),
            'caster_stats': dict (snapshot of caster stats for DoT scaling)
        }
        """
        entity_id = id(entity)
        if entity_id not in self.active_effects:
            self.active_effects[entity_id] = []
        
        # For DoT effects, scale with caster's stats
        if effect.get('type') == 'dot' and caster:
            damage_type = effect.get('damage_type', 'physical')
            base_damage = effect.get('damage', 0)
            
            # Scale DoT with relevant stat
            if damage_type == 'magic':
                scaling_stat = getattr(caster, 'magic_power', 0)
                # Magic DoT scales 30% with magic power
                scaled_damage = base_damage + int(scaling_stat * 0.3)
            else:
                scaling_stat = getattr(caster, 'atk', 0)
                # Physical DoT scales 20% with attack
                scaled_damage = base_damage + int(scaling_stat * 0.2)
            
            effect['damage'] = max(1, scaled_damage)
            effect['damage_type'] = damage_type
        
        # Add effect with internal ID
        effect['_id'] = len(self.active_effects[entity_id])
        self.active_effects[entity_id].append(effect)
    
    def get_effects(self, entity):
        """Get all active effects on an entity"""
        entity_id = id(entity)
        return self.active_effects.get(entity_id, [])
    
    def remove_effect(self, entity, effect_id):
        """Remove a specific effect by ID"""
        entity_id = id(entity)
        if entity_id not in self.active_effects:
            return
        
        self.active_effects[entity_id] = [
            e for e in self.active_effects[entity_id]
            if e.get('_id') != effect_id
        ]
    
    def tick_effects(self, entity):
        """Decrease duration of all effects on entity, remove expired ones
        
        Returns list of expired effects (for logging/feedback)
        """
        entity_id = id(entity)
        if entity_id not in self.active_effects:
            return []
        
        expired = []
        remaining = []
        
        for effect in self.active_effects[entity_id]:
            duration = effect.get('duration', 0)
            duration -= 1
            effect['duration'] = duration
            
            if duration <= 0:
                expired.append(effect)
            else:
                remaining.append(effect)
        
        self.active_effects[entity_id] = remaining
        return expired
    
    def apply_active_effects(self, entity):
        """Apply stat modifiers from active buffs/debuffs
        
        Returns dict of stat modifiers to apply temporarily
        """
        modifiers = {}
        
        for effect in self.get_effects(entity):
            effect_type = effect.get('type')
            
            if effect_type in ['buff', 'debuff']:
                stat = effect.get('stat')
                value = effect.get('value', 0)
                
                if stat:
                    modifiers[stat] = modifiers.get(stat, 0) + value
        
        return modifiers
    
    def process_dot_effects(self, entity):
        """Process damage over time effects
        
        Returns total DoT damage dealt this turn
        """
        total_damage = 0
        
        for effect in self.get_effects(entity):
            if effect.get('type') == 'dot':
                damage = effect.get('damage', 0)
                total_damage += damage
                entity.hp = max(0, entity.hp - damage)
        
        return total_damage
    
    def has_counter_effect(self, entity):
        """Check if entity has an active counter effect"""
        for effect in self.get_effects(entity):
            if effect.get('type') == 'counter':
                return effect
        return None
    
    def trigger_counter(self, entity, attacker, incoming_damage):
        """Trigger counter effect when entity is attacked
        
        Returns counter damage dealt to attacker (or None if no counter)
        """
        counter = self.has_counter_effect(entity)
        if not counter:
            return None
        
        damage_percent = counter.get('damage_percent', 0.5)
        counter_damage = int(incoming_damage * damage_percent)
        
        # Apply counter damage to attacker
        attacker.hp = max(0, attacker.hp - counter_damage)
        
        # Remove counter effect after triggering (one-time use)
        self.remove_effect(entity, counter.get('_id'))
        
        return counter_damage
    
    def clear_entity_effects(self, entity):
        """Remove all effects from an entity (e.g., on death)"""
        entity_id = id(entity)
        if entity_id in self.active_effects:
            del self.active_effects[entity_id]
    
    def get_effect_summary(self, entity):
        """Get human-readable summary of active effects
        
        Returns list of strings describing each effect
        """
        summary = []
        
        for effect in self.get_effects(entity):
            effect_type = effect.get('type')
            duration = effect.get('duration', 0)
            source = effect.get('source', 'Unknown')
            
            if effect_type == 'buff':
                stat = effect.get('stat', '?')
                value = effect.get('value', 0)
                summary.append(f"+{value} {stat.upper()} ({duration}t) [{source}]")
            
            elif effect_type == 'debuff':
                stat = effect.get('stat', '?')
                value = effect.get('value', 0)
                summary.append(f"{value} {stat.upper()} ({duration}t) [{source}]")
            
            elif effect_type == 'counter':
                percent = int(effect.get('damage_percent', 0.5) * 100)
                summary.append(f"Counter {percent}% ({duration}t) [{source}]")
            
            elif effect_type == 'dot':
                damage = effect.get('damage', 0)
                summary.append(f"DoT {damage}dmg/t ({duration}t) [{source}]")
        
        return summary
