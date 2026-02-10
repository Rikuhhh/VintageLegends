# src/battle_system.py
import time
try:
    from enemy import Enemy
except Exception:
    from .enemy import Enemy
try:
    from skill_manager import SkillManager
except Exception:
    from .skill_manager import SkillManager
try:
    from effect_manager import EffectManager
except Exception:
    from .effect_manager import EffectManager
import random

class BattleSystem:
    def __init__(self, player, data_path=None):
        self.player = player
        self.wave = 1
        self.current_zone = None
        self.enemy = Enemy.random_enemy(self.wave)
        self.turn = "player"
        self.last_action_time = 0
        self.action_delay = 0.9  # petit délai visuel — make turns less instant
        # Block player action for a short time after certain events (e.g., new wave)
        self.player_action_cooldown_until = 0.0
        # Whether the next wave is a shop instead of a fight
        self.in_shop = False
        # Queue of recent damage events for UI (list of dicts: target, amount, time, is_crit)
        self.damage_events = []
        # Combat log messages (list of strings)
        self.combat_log = []
        # Blocking state: temporary defense bonus for next enemy turn
        self.block_defense_bonus = 0
        self.combat_log = []
        # Skill and effect managers
        self.skill_manager = SkillManager(data_path=data_path)
        self.effect_manager = EffectManager()
        # Track if turn start effects have been processed
        self.turn_processed = False
        self.enemy_turn_processed = False
    
    def add_log(self, message, category='info'):
        """Add a message to combat log"""
        self.combat_log.append({
            'message': message,
            'category': category,
            'time': time.time()
        })
        # Keep only last 100 messages
        if len(self.combat_log) > 100:
            self.combat_log = self.combat_log[-100:]
    
    def start_player_turn(self):
        """Process turn start effects: mana regen, cooldown reduction, effect ticking"""
        if self.turn != "player":
            return
        
        # Only process once per turn
        if self.turn_processed:
            return
        self.turn_processed = True
        
        # Regenerate mana (only if no skill was used last turn)
        skill_used_last_turn = getattr(self, 'skill_used_this_turn', False)
        if not skill_used_last_turn:
            if hasattr(self.player, 'regenerate_mana'):
                mana_gained = self.player.regenerate_mana()
                if mana_gained and mana_gained > 0:
                    self.add_log(f"+{mana_gained} mana", 'buff')
        else:
            # Reset the flag for next turn
            self.skill_used_this_turn = False
        
        # Reduce skill cooldowns
        if hasattr(self.player, 'skill_cooldowns'):
            expired_skills = []
            for skill_id, remaining in list(self.player.skill_cooldowns.items()):
                new_cooldown = remaining - 1
                if new_cooldown <= 0:
                    expired_skills.append(skill_id)
                    del self.player.skill_cooldowns[skill_id]
                else:
                    self.player.skill_cooldowns[skill_id] = new_cooldown
            
            # Log skills coming off cooldown
            for skill_id in expired_skills:
                skill = self.skill_manager.get_skill(skill_id)
                skill_name = skill.get('name', skill_id) if skill else skill_id
                self.add_log(f"{skill_name} ready!", 'info')
        
        # Tick player effects
        if hasattr(self, 'effect_manager') and self.effect_manager:
            try:
                self.effect_manager.tick_effects(self.player)
            except Exception as e:
                print(f"Warning: Failed to tick player effects: {e}")

        # Process player DoT effects at start of player turn
        if hasattr(self, 'effect_manager') and self.effect_manager:
            try:
                dot_damage = self.effect_manager.process_dot_effects(self.player)
                if dot_damage > 0:
                    self.add_log(f"{dot_damage} DoT damage", 'debuff')
                    try:
                        self.damage_events.append({
                            'target': 'player',
                            'amount': int(dot_damage),
                            'time': time.time(),
                            'is_crit': False,
                        })
                    except Exception:
                        pass
            except Exception as e:
                print(f"Warning: Failed to process player DoT: {e}")
        
        # Apply HP regeneration at turn start
        player_hp_regen = getattr(self.player, 'hp_regen', 0.0)
        if player_hp_regen > 0:
            regen_amount = int(player_hp_regen)
            if regen_amount > 0:
                old_hp = self.player.hp
                self.player.hp = min(self.player.max_hp, self.player.hp + regen_amount)
                actual_regen = self.player.hp - old_hp
                if actual_regen > 0:
                    self.add_log(f"+{actual_regen} HP (regen)", 'heal')
                    # Add healing counter
                    try:
                        self.damage_events.append({
                            'target': 'player',
                            'amount': actual_regen,
                            'time': time.time(),
                            'is_heal': True,
                        })
                    except Exception:
                        pass
        
        # Enemy effects are processed at the start of the enemy's turn

    def player_attack(self):
        """Action du joueur via un bouton."""
        if self.turn != "player":
            return  # ignore si ce n'est pas ton tour

        if time.time() < self.player_action_cooldown_until:
            return
        
        # Process turn start effects (mana regen, cooldowns, etc.)
        self.start_player_turn()
        
        # Safety check: ensure enemy exists
        if not self.enemy or self.enemy.is_dead():
            print("No enemy to attack!")
            return
        
        # Apply active effect modifiers to player stats
        player_modifiers = self.effect_manager.apply_active_effects(self.player)
        
        # base damage with buffs applied
        base_dmg = getattr(self.player, 'atk', 0) + player_modifiers.get('atk', 0)
        
        # Overcrit mechanic: crit chance >100% converts to bonuses
        crit_chance = float(getattr(self.player, 'critchance', 0.0))
        base_crit_damage = float(getattr(self.player, 'critdamage', 1.5))
        
        # Calculate overcrit bonuses
        is_overcrit = False
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
        
        # Roll for critical hit
        try:
            is_crit = random.random() < effective_crit_chance
        except Exception:
            is_crit = False

        if is_crit:
            crit_mult = effective_crit_damage * (3.0 if is_overcrit else 1.0)
            dmg = int(round(base_dmg * crit_mult))
        else:
            dmg = int(base_dmg)

        # apply damage to enemy (pass player penetration and effect manager)
        player_pen = getattr(self.player, 'penetration', 0)
        enemy_modifiers = self.effect_manager.apply_active_effects(self.enemy)
        # Apply defense debuffs to enemy
        dmg_dealt = self.enemy.take_damage(dmg, player_pen, self.effect_manager)
        
        # Apply lifesteal if player has it
        player_lifesteal = getattr(self.player, 'lifesteal', 0.0)
        if player_lifesteal > 0 and dmg_dealt > 0:
            lifesteal_amount = int(dmg_dealt * (player_lifesteal / 100.0))
            if lifesteal_amount > 0:
                old_hp = self.player.hp
                self.player.hp = min(self.player.max_hp, self.player.hp + lifesteal_amount)
                actual_heal = self.player.hp - old_hp
                if actual_heal > 0:
                    self.add_log(f"Lifesteal: +{actual_heal} HP", 'heal')
                    # Add healing counter
                    try:
                        self.damage_events.append({
                            'target': 'player',
                            'amount': actual_heal,
                            'time': time.time(),
                            'is_heal': True,
                        })
                    except Exception:
                        pass
        # register damage event for UI
        try:
            self.damage_events.append({
                'target': 'enemy',
                'amount': int(dmg_dealt),
                'time': time.time(),
                'is_crit': bool(is_crit),
            })
        except Exception:
            pass
        if is_crit:
            crit_label = "OVERCRIT!!!" if is_overcrit else "CRIT!"
            print(f"{crit_label} {self.player.name} inflige {dmg_dealt} (x{crit_mult:.1f}) à {self.enemy.name} !")
            self.add_log(f"{crit_label} {dmg_dealt} damage!", 'damage')
        else:
            print(f"{self.player.name} inflige {dmg_dealt} à {self.enemy.name} !")
            self.add_log(f"Dealt {dmg_dealt} damage", 'damage')

        if self.enemy.is_dead():
            print(f"{self.enemy.name} est vaincu !")
            self.add_log(f"{self.enemy.name} defeated!", 'info')
            # Apply gold modifier from upgrades/items
            gold_gained = int(self.enemy.gold * getattr(self.player, 'gold_modifier', 1.0))
            self.player.gold += gold_gained
            self.player.gain_xp(self.enemy.xp)
            # Handle boss skill unlock chance
            if self.enemy.is_boss:
                self._try_boss_skill_unlock()
            # handle potential drops before moving to next wave
            self._process_drops(self.enemy)
            self.next_wave()
            # Short delay after killing enemy (less than other actions)
            self.action_delay = 0.3
        else:
            self.turn = "enemy"
            self.last_action_time = time.time()
            # Standard action delay
            self.action_delay = 0.9
            self.enemy_turn_processed = False
    
    def player_block(self):
        """Player blocks, adding +300 defense for the next enemy turn"""
        if self.turn != "player":
            return

        if time.time() < self.player_action_cooldown_until:
            return
        
        # Process turn start effects (mana regen, cooldowns, etc.)
        self.start_player_turn()
        
        if not self.enemy or self.enemy.is_dead():
            print("No enemy to block!")
            return
        
        # Add temporary defense bonus
        self.block_defense_bonus = 300
        self.add_log("Blocking! +300 defense this turn", 'buff')
        print(f"{self.player.name} is blocking! (+300 defense)")
        
        # Pass turn to enemy
        self.turn = "enemy"
        self.last_action_time = time.time()
        self.action_delay = 0.9
        self.enemy_turn_processed = False
    
    def player_use_skill(self, skill_id):
        """Player uses a skill"""
        if self.turn != "player":
            return

        if time.time() < self.player_action_cooldown_until:
            return
        
        # Process turn start effects (mana regen, cooldowns, etc.)
        self.start_player_turn()
        
        if not self.enemy or self.enemy.is_dead():
            print("No enemy to target!")
            return
        
        # Check if skill manager exists
        if not hasattr(self, 'skill_manager') or self.skill_manager is None:
            print("Skill system not initialized!")
            return
        
        # Get skill data
        skill = self.skill_manager.get_skill(skill_id)
        if not skill:
            print(f"Skill {skill_id} not found!")
            return
        
        # Check if player has the skill
        if not hasattr(self.player, 'skills') or skill_id not in self.player.skills:
            print(f"Player doesn't know {skill_id}!")
            return
        
        # Check if skill can be used (cooldown check)
        can_use, msg = self.skill_manager.can_use_skill(self.player, skill_id)
        if not can_use:
            print(f"Cannot use skill: {msg}")
            self.add_log(msg, 'debuff')
            return
        
        # Check mana cost (scaled by skill level)
        base_mana_cost = skill.get('mana_cost', 0)
        skill_level = self.skill_manager.get_skill_level(self.player, skill_id)
        mana_cost = int(base_mana_cost * (1 + (skill_level - 1) * 0.2))
        if not self.player.consume_mana(mana_cost):
            print(f"Not enough mana! Need {mana_cost}, have {self.player.current_mana}")
            self.add_log(f"Not enough mana for {skill_id}!", 'debuff')
            return
        
        # Use the skill
        result, msg = self.skill_manager.use_skill(self.player, self.enemy, skill_id, self.effect_manager)
        
        # Mark that a skill was used this turn (prevents mana regen)
        self.skill_used_this_turn = True
        
        # Log the skill usage
        if result:
            damage = result.get('damage', 0)
            healing = result.get('healing', 0)
            effects = result.get('effects', [])
            skill_name = skill.get('name', skill_id)
            
            # Log skill activation (for buff/support skills without damage)
            if damage == 0 and healing == 0 and effects:
                self.add_log(f"Used {skill_name}!", 'skill')
            
            if damage > 0:
                self.add_log(f"Used {skill_name}: {damage} damage!", 'skill')
                print(f"{self.player.name} used {skill_id} for {damage} damage!")
                
                # Register damage event for UI
                try:
                    self.damage_events.append({
                        'target': 'enemy',
                        'amount': int(damage),
                        'time': time.time(),
                        'is_crit': result.get('is_crit', False),
                    })
                except Exception:
                    pass
            
            if healing > 0:
                self.add_log(f"Used {skill_name}: healed {healing}!", 'heal')
                print(f"{self.player.name} healed {healing} HP!")
                # Add healing counter
                try:
                    self.damage_events.append({
                        'target': 'player',
                        'amount': int(healing),
                        'time': time.time(),
                        'is_heal': True,
                    })
                except Exception:
                    pass
            
            # Log buff/debuff effects
            for effect_data in effects:
                effect_type = effect_data[0] if effect_data else None
                if effect_type == 'buff':
                    stat, value = effect_data[1], effect_data[2]
                    self.add_log(f"Buff: +{value} {stat.upper()}!", 'buff')
                elif effect_type == 'debuff':
                    stat, value = effect_data[1], effect_data[2]
                    self.add_log(f"Debuff: {value} {stat.upper()} on enemy!", 'debuff')
                elif effect_type == 'counter':
                    self.add_log(f"Counter stance activated!", 'buff')
                elif effect_type == 'dot':
                    damage_per_turn = effect_data[1]
                    self.add_log(f"DoT: {damage_per_turn} dmg/turn!", 'skill')
            
            # Check if enemy died
            if self.enemy.is_dead():
                print(f"{self.enemy.name} est vaincu !")
                gold_gained = int(self.enemy.gold * getattr(self.player, 'gold_modifier', 1.0))
                self.add_log(f"{self.enemy.name} defeated! +{gold_gained}g", 'info')
                self.player.gold += gold_gained
                self.player.gain_xp(self.enemy.xp)
                if self.enemy.is_boss:
                    self._try_boss_skill_unlock()
                self._process_drops(self.enemy)
                self.next_wave()
                # Short delay after killing enemy (less than other actions)
                self.player_action_cooldown_until = time.time() + 0.3
            else:
                # Pass turn to enemy
                self.turn = "enemy"
                self.last_action_time = time.time()
                # Standard action delay
                self.action_delay = 0.9
                self.enemy_turn_processed = False
        else:
            print(f"Failed to use skill: {msg}")
            self.add_log(f"Skill failed: {msg}", 'debuff')

    def update(self):
        """Tour automatique de l’ennemi après ton attaque."""
        if self.turn == "enemy":
            # Safety check: ensure enemy exists before attacking
            if not self.enemy or self.enemy.is_dead():
                self.turn = "player"
                self.turn_processed = False  # Reset for next player turn
                return
            
            if time.time() - self.last_action_time >= self.action_delay:
                # Process enemy turn start effects once
                if not self.enemy_turn_processed:
                    self.enemy_turn_processed = True
                    if hasattr(self, 'effect_manager') and self.effect_manager:
                        try:
                            self.effect_manager.tick_effects(self.enemy)
                        except Exception as e:
                            print(f"Warning: Failed to tick enemy effects: {e}")

                        # Process enemy DoT effects at start of enemy turn
                        try:
                            dot_damage = self.effect_manager.process_dot_effects(self.enemy)
                            if dot_damage > 0:
                                self.add_log(f"{dot_damage} DoT damage to enemy", 'skill')
                                try:
                                    self.damage_events.append({
                                        'target': 'enemy',
                                        'amount': int(dot_damage),
                                        'time': time.time(),
                                        'is_crit': False,
                                    })
                                except Exception:
                                    pass
                        except Exception as e:
                            print(f"Warning: Failed to process enemy DoT: {e}")

                    # If enemy dies from DoT, resolve defeat and skip attack
                    if self.enemy and self.enemy.is_dead():
                        gold_gained = int(self.enemy.gold * getattr(self.player, 'gold_modifier', 1.0))
                        self.add_log(f"{self.enemy.name} defeated by DoT! +{gold_gained}g", 'info')
                        self.player.gold += gold_gained
                        self.player.gain_xp(self.enemy.xp)
                        if self.enemy.is_boss:
                            self._try_boss_skill_unlock()
                        self._process_drops(self.enemy)
                        self.next_wave()
                        self.player_action_cooldown_until = time.time() + 0.3
                        return

                # Check if player dodges the attack
                player_dodge = getattr(self.player, 'dodge_chance', 0.0)
                dodged = random.random() < player_dodge
                
                if dodged:
                    # Player dodged the attack!
                    try:
                        self.damage_events.append({
                            'target': 'player',
                            'amount': 0,
                            'time': time.time(),
                            'is_crit': False,
                            'dodged': True,
                        })
                    except Exception:
                        pass
                    print(f"{self.player.name} esquive l'attaque de {self.enemy.name}!")
                    self.add_log("Dodged enemy attack!", 'buff')
                else:
                    dmg = self.enemy.atk
                    # Apply block defense bonus temporarily
                    original_defense = self.player.defense
                    if self.block_defense_bonus > 0:
                        self.player.defense += self.block_defense_bonus
                        print(f"Block reduces damage! (Defense: {original_defense} -> {self.player.defense})")
                    
                    # Enemies don't have penetration (for now), pass 0
                    enemy_pen = getattr(self.enemy, 'penetration', 0)
                    # apply damage and capture the actual damage taken after defense
                    dmg_taken = self.player.take_damage(dmg, enemy_pen, self.effect_manager)
                    
                    # Restore original defense and clear block bonus
                    if self.block_defense_bonus > 0:
                        self.player.defense = original_defense
                        self.block_defense_bonus = 0
                    
                    # register damage event for UI with post-defense damage
                    try:
                        self.damage_events.append({
                            'target': 'player',
                            'amount': int(dmg_taken),
                            'time': time.time(),
                            'is_crit': False,
                        })
                    except Exception:
                        pass
                    print(f"{self.enemy.name} inflige {dmg_taken} à {self.player.name} !")
                    self.add_log(f"Took {dmg_taken} damage!", 'debuff')

                    if self.player.is_dead():
                        print(f"{self.player.name} est vaincu... 💀")
                    # Do not auto-respawn here; main loop will handle game over

                self.turn = "player"
                self.turn_processed = False  # Reset for next player turn
                self.enemy_turn_processed = False
                # Slight pause after enemy turn before player can act
                self.player_action_cooldown_until = time.time() + 0.2

    def next_wave(self):
        self.wave += 1
        # Award challenge coins with scaling: +1 every 10 waves, +1 extra every 20 waves
        # Plus bonus scaling: +1 per 10 waves for every 50 waves reached
        try:
            reward = 0
            if self.wave % 10 == 0:
                # Base reward: 1 coin every 10 waves
                reward += 1
                # Scaling bonus: +1 coin per 10 waves for every 50 waves reached
                # e.g., at wave 50-100: +1, at wave 100-150: +2, etc.
                scaling_bonus = self.wave // 50
                reward += scaling_bonus
            if self.wave % 20 == 0:
                # Extra coin every 20 waves
                reward += 1
            if reward > 0 and hasattr(self.player, 'challenge_coins'):
                self.player.challenge_coins = getattr(self.player, 'challenge_coins', 0) + reward
                # Add a short notification event to be displayed by UI
                try:
                    self.damage_events.append({'type': 'coin_reward', 'amount': reward, 'time': time.time()})
                except Exception:
                    pass
        except Exception:
            pass
        
        # Apply wave-based price increase (1-15% per wave, seeded)
        try:
            if hasattr(self.player, 'game_seed') and self.player.game_seed is not None:
                # Use player seed + wave to determine this wave's price increase
                import random
                wave_seed = (self.player.game_seed + self.wave * 9973) % 1000000007
                rng = random.Random(wave_seed)
                # Random increase between 0.01 (1%) and 0.15 (15%)
                wave_increase = rng.uniform(0.01, 0.15)
                # Add to cumulative price increase
                if hasattr(self.player, 'cumulative_price_increase'):
                    self.player.cumulative_price_increase = getattr(self.player, 'cumulative_price_increase', 0.0) + wave_increase
        except Exception as e:
            print(f"Error calculating price increase: {e}")
        
        # Update highest wave
        if hasattr(self.player, 'highest_wave'):
            self.player.highest_wave = max(getattr(self.player, 'highest_wave', 0), self.wave)
        
        # Decide whether next wave is a shop — guaranteed every 10th wave, otherwise 10% chance
        import random
        if self.wave % 10 == 0:
            self.in_shop = True
        else:
            self.in_shop = random.random() < 0.10
        if not self.in_shop:
            # Get allowed categories from current zone
            allowed_categories = None
            if self.current_zone:
                enemy_types = self.current_zone.get('enemy_types', {})
                allowed_categories = [cat for cat, allowed in enemy_types.items() if allowed]
            
            self.enemy = Enemy.random_enemy(self.wave, allowed_categories=allowed_categories)
            print(f"👹 Nouvelle vague : {self.enemy.name}")
            self.turn = "player"
            self.turn_processed = False  # Reset for new wave
            # Brief pause before the player can act after a new enemy appears
            self.player_action_cooldown_until = time.time() + 0.3
        else:
            self.enemy = None
            print(f"🛒 Shop opens at wave {self.wave}")
    
    
    def _try_boss_skill_unlock(self):
        """Try to unlock a random locked skill when killing a boss (15% chance)"""
        import json
        import random
        from pathlib import Path
        
        # 15% chance to unlock a skill from boss
        if random.random() > 0.15:
            return
        
        try:
            base = Path(__file__).resolve().parents[1]
            skills_path = base / 'data' / 'skills.json'
            if not skills_path.exists():
                return
            
            with open(skills_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both dict and array formats
            if isinstance(data, dict) and 'skills' in data:
                all_skills = data['skills']
            elif isinstance(data, list):
                all_skills = data
            else:
                all_skills = []
            
            # Get list of locked skills (not yet unlocked)
            player_skills = getattr(self.player, 'skills', [])
            locked_skills = [skill.get('id') for skill in all_skills if skill.get('id') and skill.get('id') not in player_skills]
            
            # If no locked skills, try to level up an existing skill instead
            if not locked_skills:
                if player_skills:
                    # Pick a random unlocked skill to level up
                    skill_id = random.choice(player_skills)
                    result, level = self.player.unlock_skill(skill_id)
                    if result == 'levelup':
                        # Get skill name for better display
                        skill_name = skill_id
                        for skill in all_skills:
                            if skill.get('id') == skill_id:
                                skill_name = skill.get('name', skill_id)
                                break
                        self.add_log(f"Boss upgraded skill: {skill_name} -> Lv{level}!", 'buff')
                else:
                    self.add_log("No skills available!", 'info')
                return
            
            # Randomly pick one locked skill
            skill_id = random.choice(locked_skills)
            result, level = self.player.unlock_skill(skill_id)
            if result == 'new':
                # Get skill name for better display
                skill_name = skill_id
                for skill in all_skills:
                    if skill.get('id') == skill_id:
                        skill_name = skill.get('name', skill_id)
                        break
                self.add_log(f"Boss dropped skill: {skill_name}!", 'buff')
        except Exception as e:
            print(f"Warning: Failed to process boss skill drop: {e}")
    
    def _process_drops(self, enemy):
        """Check items.json for droppable items matching the enemy category and roll.
        Adds items to player.inventory via player.add_item on success.
        """
        try:
            from pathlib import Path
            import json
            import random

            base = Path(__file__).resolve().parents[1]
            items_path = base / 'data' / 'items.json'
            if not items_path.exists():
                items = []
            else:
                with open(items_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                items = data.get('items', [])

            # global droppable items table
            for it in items:
                if not it.get('droppable'):
                    continue
                dropped_by = it.get('dropped_by')
                # if dropped_by not set, skip
                if not dropped_by:
                    continue
                # allow lists or single string
                if isinstance(dropped_by, list):
                    ok = enemy.category in dropped_by
                else:
                    ok = (enemy.category == dropped_by)
                if not ok:
                    continue
                # compute chance
                chance = float(it.get('drop_chance', 0.25))
                if random.random() < chance:
                    # grant the item
                    print(f"Loot trouvé: {it.get('name')} de {enemy.name}")
                    # call add_item with auto_equip=False so drops go to inventory
                    self.player.add_item(it, auto_equip=False)

            # Also check per-monster drops in monsters.json if present (supports qty ranges)
            monsters_path = base / 'data' / 'monsters.json'
            if monsters_path.exists():
                with open(monsters_path, 'r', encoding='utf-8') as f:
                    mdata = json.load(f)
                for mon in mdata.get('enemies', []):
                    if mon.get('id') == getattr(enemy, 'id', None):
                        for drop in mon.get('drops', []):
                            chance = float(drop.get('chance', 0.0))
                            if random.random() < chance:
                                iid = drop.get('item_id')
                                qmin = int(drop.get('qty_min', 1))
                                qmax = int(drop.get('qty_max', qmin))
                                qty = random.randint(qmin, qmax)
                                # find item def in items.json
                                item_def = None
                                for it in items:
                                    if it.get('id') == iid:
                                        item_def = it
                                        break
                                if not item_def:
                                    item_def = {'id': iid, 'name': iid, 'type': 'misc'}
                                print(f"Loot (monster table): {item_def.get('name')} x{qty} from {enemy.name}")
                                for _ in range(qty):
                                    self.player.add_item(item_def, auto_equip=False)
                        break
        except Exception as e:
            print("Erreur lors du traitement des drops:", e)
