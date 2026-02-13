# src/skill_manager.py
import json
from pathlib import Path
import random


class SkillManager:
    """Manages skills loading, validation, and execution"""
    
    def __init__(self, data_path=None):
        self.data_path = data_path or Path(__file__).resolve().parents[1] / 'data'
        self.skills = {}
        self.load_skills()
    
    def load_skills(self):
        """Load skills from skills.json"""
        try:
            skills_path = self.data_path / 'skills.json'
            if skills_path.exists():
                with open(skills_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for skill in data.get('skills', []):
                        self.skills[skill['id']] = skill
            else:
                print(f"Warning: skills.json not found at {skills_path}")
        except Exception as e:
            print(f"Error loading skills: {e}")
            self.skills = {}
    
    def get_skill(self, skill_id):
        """Get skill definition by ID"""
        return self.skills.get(skill_id)
    
    def get_skill_level(self, caster, skill_id):
        """Get the level of a skill for the caster (default 1)"""
        if not hasattr(caster, 'skill_levels'):
            return 1
        return caster.skill_levels.get(skill_id, 1)
    
    def can_use_skill(self, caster, skill_id):
        """Check if caster can use this skill (mana, cooldown)"""
        skill = self.get_skill(skill_id)
        if not skill:
            return False, "Skill not found"
        
        # Check mana (scaled by skill level)
        base_mana_cost = skill.get('mana_cost', 0)
        skill_level = self.get_skill_level(caster, skill_id)
        # Mana cost increases by 20% per level
        mana_cost = int(base_mana_cost * (1 + (skill_level - 1) * 0.2))
        current_mana = getattr(caster, 'current_mana', 0)
        if current_mana < mana_cost:
            return False, f"Not enough mana ({current_mana}/{mana_cost})"
        
        # Check cooldown
        cooldowns = getattr(caster, 'skill_cooldowns', {})
        if cooldowns.get(skill_id, 0) > 0:
            return False, f"On cooldown ({cooldowns[skill_id]} turns)"
        
        return True, "OK"
    
    def calculate_skill_damage(self, skill, caster, target, effect_manager=None):
        """Calculate damage for a damage skill"""
        skill_type = skill.get('type')
        if skill_type not in ['damage']:
            return 0
        
        base_power = skill.get('power', 0)
        scaling_stat = skill.get('scaling_stat', 'atk')
        
        # Get skill level and apply damage bonus (25% per level)
        skill_id = skill.get('id')
        skill_level = self.get_skill_level(caster, skill_id)
        level_multiplier = 1 + (skill_level - 1) * 0.25
        
        # Apply active effect modifiers to caster stats
        stat_modifiers = {}
        if effect_manager:
            stat_modifiers = effect_manager.apply_active_effects(caster)
        
        # Get scaling stat value from caster with buffs applied
        if scaling_stat == 'magic_power':
            stat_value = getattr(caster, 'magic_power', 0) + stat_modifiers.get('magic_power', 0)
            # Magic skills scale 1.5x better with magic_power
            stat_value = int(stat_value * 1.5)
        elif scaling_stat == 'atk':
            stat_value = getattr(caster, 'atk', 0) + stat_modifiers.get('atk', 0)
        else:
            stat_value = getattr(caster, scaling_stat, 0) + stat_modifiers.get(scaling_stat, 0)
        
        # Base damage calculation: (base_power + stat_value) * level_multiplier
        raw_damage = int((base_power + stat_value) * level_multiplier)
        
        # Apply effectiveness multiplier
        multiplier = self.get_effectiveness_multiplier(skill, target)
        raw_damage = int(raw_damage * multiplier)
        
        # Apply damage type bonus from equipment
        skill_element = skill.get('element', 'physical')
        damage_type_bonus = self.get_damage_type_bonus(caster, skill_element)
        if damage_type_bonus > 0:
            raw_damage = int(raw_damage * (1 + damage_type_bonus / 100.0))
        
        # Check for critical hit (caster's crit chance with overcrit mechanic)
        is_crit = False
        is_overcrit = False
        try:
            crit_chance = getattr(caster, 'critchance', 0.0)
            base_crit_damage = getattr(caster, 'critdamage', 1.5)
            
            # Overcrit mechanic: crit chance >100%
            if crit_chance > 1.0:
                overcrit_amount = crit_chance - 1.0
                # 1% crit damage per 1% overcrit
                bonus_crit_damage = overcrit_amount
                # 0.5% chance to deal 3x total crit damage
                overcrit_chance = overcrit_amount * 0.5
                effective_crit_chance = 1.0  # Always crit when >100%
                effective_crit_damage = base_crit_damage + bonus_crit_damage
                is_overcrit = random.random() < overcrit_chance
            else:
                effective_crit_chance = crit_chance
                effective_crit_damage = base_crit_damage
            
            if random.random() < effective_crit_chance:
                is_crit = True
                crit_mult = effective_crit_damage * (3.0 if is_overcrit else 1.0)
                raw_damage = int(raw_damage * crit_mult)
        except Exception:
            pass
        
        # Apply penetration and target defense
        penetration = skill.get('penetration', 0.0)
        if scaling_stat == 'magic_power':
            # Magic skill - use magic penetration and magic defense
            caster_pen = getattr(caster, 'magic_penetration', 0) + penetration
            target_def = getattr(target, 'magic_defense', 0)
        else:
            # Physical skill - use physical penetration and defense
            caster_pen = getattr(caster, 'penetration', 0) + penetration
            target_def = getattr(target, 'defense', 0)
        
        # Calculate damage reduction (same formula as regular combat)
        dmg_dealt = self._apply_defense(raw_damage, target_def, caster_pen)
        
        return dmg_dealt, is_crit
    
    def _apply_defense(self, dmg, defense, penetration):
        """Apply defense reduction to damage (same as player/enemy take_damage)"""
        # Calculate effective defense percentage (0-75%)
        def calc_effective_stat(raw_value, soft_cap, hard_cap):
            if raw_value <= soft_cap:
                return raw_value
            elif raw_value <= hard_cap:
                excess = raw_value - soft_cap
                return soft_cap + (excess * 0.5)
            else:
                excess = hard_cap - soft_cap
                return soft_cap + (excess * 0.5)
        
        defense_percent = calc_effective_stat(defense, 30, 75)
        pen_percent = calc_effective_stat(penetration, 50, 75) if penetration > 0 else 0
        
        # Penetration reduces defense effectiveness
        effective_defense = defense_percent * (1.0 - (pen_percent / 100.0))
        
        # Apply damage reduction
        damage_multiplier = 1.0 - (effective_defense / 100.0)
        dmg_taken = max(1, int(dmg * damage_multiplier))
        
        return dmg_taken
    
    def get_effectiveness_multiplier(self, skill, target):
        """Get effectiveness multiplier based on skill element vs target category"""
        effectiveness = skill.get('effectiveness', {})
        strong_vs = effectiveness.get('strong_vs', [])
        weak_vs = effectiveness.get('weak_vs', [])
        
        target_category = getattr(target, 'category', None)
        
        if target_category in strong_vs:
            return 1.5  # 50% bonus damage
        elif target_category in weak_vs:
            return 0.5  # 50% reduced damage
        else:
            return 1.0  # Normal damage
    
    def apply_skill_effects(self, skill, caster, target, effect_manager):
        """Apply skill effects (buffs, debuffs, counters, heal, DoT)"""
        effects = skill.get('effects', [])
        skill_type = skill.get('type')
        
        results = []
        
        # Handle heal skills
        if skill_type == 'heal':
            heal_amount = skill.get('power', 0)
            old_hp = caster.hp
            caster.hp = min(caster.max_hp, caster.hp + heal_amount)
            actual_heal = caster.hp - old_hp
            results.append(('heal', actual_heal, caster))
        
        # Apply all effects
        for effect in effects:
            effect_type = effect.get('type')
            
            if effect_type == 'buff':
                # Apply buff to caster (or target if specified)
                buff_target = caster  # Skills typically buff caster
                effect_manager.add_effect(buff_target, {
                    'type': 'buff',
                    'stat': effect.get('stat'),
                    'value': effect.get('value'),
                    'duration': effect.get('duration'),
                    'source': skill.get('name', skill.get('id'))
                })
                results.append(('buff', effect.get('stat'), effect.get('value'), buff_target))
            
            elif effect_type == 'debuff':
                # Apply debuff to target
                effect_manager.add_effect(target, {
                    'type': 'debuff',
                    'stat': effect.get('stat'),
                    'value': effect.get('value'),
                    'duration': effect.get('duration'),
                    'source': skill.get('name', skill.get('id'))
                })
                results.append(('debuff', effect.get('stat'), effect.get('value'), target))
            
            elif effect_type == 'counter':
                # Apply counter stance to caster - stores the skill info for turn 2
                effect_manager.add_effect(caster, {
                    'type': 'counter',
                    'damage_percent': effect.get('damage_percent', 1.0),  # 100% of damage taken added to counter
                    'duration': 2,  # Always 2 turns
                    'source': skill.get('name', skill.get('id')),
                    'skill_id': skill.get('id'),
                    'skill_power': skill.get('power', 0),
                    'skill_scaling_stat': skill.get('scaling_stat', 'atk'),
                    'damage_stored': 0,  # Will store damage taken during counter stance
                    'turn_count': 0  # Track which turn of counter we're on
                })
                results.append(('counter', effect.get('damage_percent'), caster))
            
            elif effect_type == 'dot':
                # Apply damage over time to target
                # Determine damage type based on skill element
                skill_element = skill.get('element', 'physical')
                damage_type = 'magic' if skill_element in ['fire', 'ice', 'arcane', 'light', 'dark'] else 'physical'
                
                effect_manager.add_effect(target, {
                    'type': 'dot',
                    'damage': effect.get('damage'),
                    'damage_type': damage_type,
                    'duration': effect.get('duration'),
                    'source': skill.get('name', skill.get('id'))
                }, caster=caster)
                results.append(('dot', effect.get('damage'), target))
        
        return results
    
    def use_skill(self, caster, target, skill_id, effect_manager, damage_events=None):
        """Execute a skill: apply damage/effects and set cooldown (mana already consumed by caller)"""
        skill = self.get_skill(skill_id)
        if not skill:
            return None, "Skill not found"
        
        # Get skill level for scaling
        skill_level = self.get_skill_level(caster, skill_id)
        
        # Check for multi-hit skill
        multi_hit_data = skill.get('multi_hit')
        if multi_hit_data and skill.get('type') == 'damage':
            # Execute multi-hit attack
            return self._execute_multi_hit_skill(skill, caster, target, effect_manager, skill_level, damage_events)
        
        # Calculate damage (if applicable)
        damage = 0
        is_crit = False
        if skill.get('type') == 'damage':
            damage, is_crit = self.calculate_skill_damage(skill, caster, target, effect_manager)
            # Apply damage to target
            target.hp = max(0, target.hp - damage)
        
        # Apply effects
        effect_results = self.apply_skill_effects(skill, caster, target, effect_manager)
        
        # Extract healing amount from effect results if present
        healing = 0
        for effect_data in effect_results:
            if effect_data and effect_data[0] == 'heal':
                healing = effect_data[1]
                break
        
        # Set cooldown 
        cooldown = skill.get('cooldown', 0)
        if cooldown > 0:
            if not hasattr(caster, 'skill_cooldowns'):
                caster.skill_cooldowns = {}
            # Use cooldown as-is (no longer tripling since we balanced in skills.json)
            caster.skill_cooldowns[skill_id] = cooldown
        
        # Return result summary
        result = {
            'skill': skill,
            'skill_level': skill_level,
            'damage': damage,
            'is_crit': is_crit,
            'healing': healing,
            'effects': effect_results,
            'mana_used': skill.get('mana_cost', 0)
        }
        
        return result, "Success"
    
    def _execute_multi_hit_skill(self, skill, caster, target, effect_manager, skill_level, damage_events=None):
        """Execute a multi-hit skill with separate damage calculations per hit"""
        import time
        
        multi_hit_data = skill.get('multi_hit', {})
        num_hits = multi_hit_data.get('hits', 3)
        damage_per_hit = multi_hit_data.get('damage_per_hit', 0.4)
        
        total_damage = 0
        crit_count = 0
        hit_count = 0
        
        # Create a copy of the skill to modify power temporarily
        skill_copy = skill.copy()
        original_power = skill.get('power', 0)
        
        # Execute each hit
        for hit_num in range(num_hits):
            if target.hp <= 0:
                break
            
            # Calculate damage for this hit (with reduced power)
            skill_copy['power'] = int(original_power * damage_per_hit)
            
            hit_damage, is_crit = self.calculate_skill_damage(skill_copy, caster, target, effect_manager)
            target.hp = max(0, target.hp - hit_damage)
            
            total_damage += hit_damage
            if is_crit:
                crit_count += 1
            hit_count += 1
            
            # Register damage event for UI if available
            if damage_events is not None:
                try:
                    damage_events.append({
                        'target': 'enemy',
                        'amount': int(hit_damage),
                        'time': time.time(),
                        'is_crit': bool(is_crit),
                    })
                except Exception:
                    pass
        
        # Apply effects only once after all hits
        effect_results = self.apply_skill_effects(skill, caster, target, effect_manager)
        
        # Extract healing amount from effect results if present
        healing = 0
        for effect_data in effect_results:
            if effect_data and effect_data[0] == 'heal':
                healing = effect_data[1]
                break
        
        # Set cooldown
        cooldown = skill.get('cooldown', 0)
        if cooldown > 0:
            if not hasattr(caster, 'skill_cooldowns'):
                caster.skill_cooldowns = {}
            caster.skill_cooldowns[skill.get('id')] = cooldown
        
        result = {
            'skill': skill,
            'skill_level': skill_level,
            'damage': total_damage,
            'is_crit': crit_count > 0,
            'multi_hit': True,
            'hit_count': hit_count,
            'crit_count': crit_count,
            'healing': healing,
            'effects': effect_results,
            'mana_used': skill.get('mana_cost', 0)
        }
        return result, "Success"
    
    def get_damage_type_bonus(self, caster, element):
        """Calculate total damage type bonus from all equipment
        
        Args:
            caster: Entity with equipment
            element: Skill element (fire, ice, dark, etc.)
        
        Returns:
            Total bonus percentage (e.g., 20 for +20%)
        """
        total_bonus = 0.0
        
        if not hasattr(caster, 'equipment'):
            return total_bonus
        
        # Load item data helper
        def load_item_data(item_id):
            if not item_id:
                return None
            try:
                import json
                from pathlib import Path
                base = Path(__file__).resolve().parents[1]
                items_path = base / 'data' / 'items.json'
                with open(items_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get('items', []):
                        if item.get('id') == item_id:
                            return item
            except Exception:
                pass
            return None
        
        # Check all equipment slots
        for slot_name, item_id in caster.equipment.items():
            if not item_id:
                continue
            item_data = load_item_data(item_id)
            if not item_data:
                continue
            
            # Get damage type bonuses from this item
            damage_bonuses = item_data.get('damage_type_bonuses', {})
            if element in damage_bonuses:
                total_bonus += float(damage_bonuses[element])
        
        return total_bonus
