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
    
    def can_use_skill(self, caster, skill_id):
        """Check if caster can use this skill (mana, cooldown)"""
        skill = self.get_skill(skill_id)
        if not skill:
            return False, "Skill not found"
        
        # Check mana
        mana_cost = skill.get('mana_cost', 0)
        current_mana = getattr(caster, 'current_mana', 0)
        if current_mana < mana_cost:
            return False, f"Not enough mana ({current_mana}/{mana_cost})"
        
        # Check cooldown
        cooldowns = getattr(caster, 'skill_cooldowns', {})
        if cooldowns.get(skill_id, 0) > 0:
            return False, f"On cooldown ({cooldowns[skill_id]} turns)"
        
        return True, "OK"
    
    def calculate_skill_damage(self, skill, caster, target):
        """Calculate damage for a damage skill"""
        skill_type = skill.get('type')
        if skill_type not in ['damage']:
            return 0
        
        base_power = skill.get('power', 0)
        scaling_stat = skill.get('scaling_stat', 'atk')
        
        # Get scaling stat value from caster
        if scaling_stat == 'magic_power':
            stat_value = getattr(caster, 'magic_power', 0)
        elif scaling_stat == 'atk':
            stat_value = getattr(caster, 'atk', 0)
        else:
            stat_value = getattr(caster, scaling_stat, 0)
        
        # Base damage calculation: base_power + stat_value
        raw_damage = base_power + stat_value
        
        # Apply effectiveness multiplier
        multiplier = self.get_effectiveness_multiplier(skill, target)
        raw_damage = int(raw_damage * multiplier)
        
        # Check for critical hit (caster's crit chance)
        is_crit = False
        try:
            crit_chance = getattr(caster, 'critchance', 0.0)
            if random.random() < crit_chance:
                is_crit = True
                crit_mult = getattr(caster, 'critdamage', 1.5)
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
                # Apply counter stance to caster
                effect_manager.add_effect(caster, {
                    'type': 'counter',
                    'damage_percent': effect.get('damage_percent', 0.5),
                    'duration': effect.get('duration'),
                    'source': skill.get('name', skill.get('id'))
                })
                results.append(('counter', effect.get('damage_percent'), caster))
            
            elif effect_type == 'dot':
                # Apply damage over time to target
                effect_manager.add_effect(target, {
                    'type': 'dot',
                    'damage': effect.get('damage'),
                    'duration': effect.get('duration'),
                    'source': skill.get('name', skill.get('id'))
                })
                results.append(('dot', effect.get('damage'), target))
        
        return results
    
    def use_skill(self, caster, target, skill_id, effect_manager):
        """Execute a skill: apply damage/effects and set cooldown (mana already consumed by caller)"""
        skill = self.get_skill(skill_id)
        if not skill:
            return None, "Skill not found"
        
        # Calculate damage (if applicable)
        damage = 0
        is_crit = False
        if skill.get('type') == 'damage':
            damage, is_crit = self.calculate_skill_damage(skill, caster, target)
            # Apply damage to target
            target.hp = max(0, target.hp - damage)
        
        # Apply effects
        effect_results = self.apply_skill_effects(skill, caster, target, effect_manager)
        
        # Set cooldown
        cooldown = skill.get('cooldown', 0)
        if cooldown > 0:
            if not hasattr(caster, 'skill_cooldowns'):
                caster.skill_cooldowns = {}
            caster.skill_cooldowns[skill_id] = cooldown
        
        # Return result summary
        result = {
            'skill': skill,
            'damage': damage,
            'is_crit': is_crit,
            'effects': effect_results,
            'mana_used': skill.get('mana_cost', 0)
        }
        
        return result, "Success"
