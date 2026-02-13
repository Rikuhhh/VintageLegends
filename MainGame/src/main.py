# src/main.py
import pygame
import threading
import time
import sys
import json
import random
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:
    tk = None
    ttk = None

# Internal imports: try package-style (src.*) first, then fall back to direct module imports
try:
    from src.player import Player
    from src.enemy import Enemy
    from src.ui_manager import UIManager
    from src.battle_system import BattleSystem
    from src.save_manager import SaveManager
    from src.shop import Shop
    from src.crafting_system import CraftingSystem
except Exception:
    from player import Player
    from enemy import Enemy
    from ui_manager import UIManager
    from battle_system import BattleSystem
    from save_manager import SaveManager
    from shop import Shop
    from crafting_system import CraftingSystem

# --- CONFIGURATION DE BASE ---
BASE_PATH = Path(__file__).resolve().parent.parent
ASSETS_PATH = BASE_PATH / "assets"
DATA_PATH = BASE_PATH / "data"
SAVE_PATH = BASE_PATH / "saves"
# --- CHARGEMENT DES PARAMÈTRES ---
def load_json(file_name, default=None):
    """Charge un fichier JSON en toute sécurité"""
    path = DATA_PATH / file_name
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validate that data is a dict
                if not isinstance(data, dict):
                    print(f"[ERREUR] Format invalide dans {file_name}, utilisation des valeurs par défaut")
                    return default or {}
                return data
        except json.JSONDecodeError:
            print(f"[ERREUR] Fichier corrompu : {file_name}, utilisation des valeurs par défaut")
        except Exception as e:
            print(f"[ERREUR] Impossible de charger {file_name}: {e}")
    return default or {}

def load_zones():
    """Load zones from zones.json"""
    try:
        zones_data = load_json('zones.json', {'zones': []})
        return zones_data.get('zones', [])
    except Exception as e:
        print(f"Error loading zones: {e}")
        return []

def select_zone(wave, zones, current_zone=None):
    """Select a zone based on wave number and spawn chances"""
    if not zones:
        return None
    
    # Filter zones by minimum wave
    available_zones = [z for z in zones if z.get('min_wave', 1) <= wave]
    if not available_zones:
        return None
    
    # For wave 1, always select a starting zone
    if wave == 1:
        import random
        # Prefer zones with min_wave=1
        starting_zones = [z for z in available_zones if z.get('min_wave', 1) == 1]
        if starting_zones:
            total_chance = sum(z.get('spawn_chance', 1) for z in starting_zones)
            if total_chance > 0:
                roll = random.random() * total_chance
                current = 0
                for zone in starting_zones:
                    current += zone.get('spawn_chance', 1)
                    if roll <= current:
                        return zone
            return random.choice(starting_zones)
        return random.choice(available_zones)
    
    # Only consider zone changes every 25 waves (not random)
    if wave % 25 != 0:
        return current_zone  # Keep current zone
    
    # At wave 25, 50, 75, etc., roll for zone change based on spawn_chance
    import random
    
    # Roll for each zone: random() * spawn_chance, pick highest
    zone_rolls = []
    for zone in available_zones:
        spawn_chance = zone.get('spawn_chance', 1)
        roll = random.random() * spawn_chance
        zone_rolls.append((roll, zone))
    
    # Sort by roll value (highest first)
    zone_rolls.sort(key=lambda x: x[0], reverse=True)
    
    # Get the highest roll
    highest_roll = zone_rolls[0][0]
    
    # Find all zones with the same highest roll (ties)
    tied_zones = [zone for roll, zone in zone_rolls if roll == highest_roll]
    
    # If multiple zones tied, pick randomly between them
    return random.choice(tied_zones)

def resolve_zone_for_wave(wave, zones):
    """Resolve a stable zone for the current wave when no saved zone is available."""
    if not zones:
        return None
    eligible = [z for z in zones if z.get('min_wave', 1) <= wave]
    if not eligible:
        return None
    # Pick the zone with the highest min_wave to represent the last unlocked zone.
    return max(eligible, key=lambda z: z.get('min_wave', 1))

def load_background_for_zone(zone, screen):
    """Load background image for a specific zone"""
    if not zone:
        # Load default background
        bg_dir = ASSETS_PATH / "images" / "backgrounds"
        flower_bg = bg_dir / "flowerfield.png"
        default_bg = bg_dir / "default_bg.png"
        if flower_bg.exists():
            _bg = pygame.image.load(flower_bg).convert()
            return pygame.transform.smoothscale(_bg, screen.get_size())
        elif default_bg.exists():
            _bg = pygame.image.load(default_bg).convert()
            return pygame.transform.smoothscale(_bg, screen.get_size())
        else:
            bg = pygame.Surface(screen.get_size())
            bg.fill((40, 40, 60))
            return bg
    
    bg_filename = zone.get('background_image', '')
    if bg_filename:
        bg_path = ASSETS_PATH / "images" / "backgrounds" / bg_filename
        if bg_path.exists():
            try:
                _bg = pygame.image.load(bg_path).convert()
                return pygame.transform.smoothscale(_bg, screen.get_size())
            except Exception as e:
                print(f"Error loading zone background {bg_filename}: {e}")
    
    # Fallback to default
    bg = pygame.Surface(screen.get_size())
    bg.fill((40, 40, 60))
    return bg

game_settings = load_json("gamesettings.json", {"width": 1280, "height": 720, "title": "MainGame"})
user_settings = load_json("usersettings.json", {"volume": 0.8, "language": "fr"})

# Validate and sanitize settings
try:
    width = max(640, min(3840, int(user_settings.get("width", 1600))))
    height = max(480, min(2160, int(user_settings.get("height", 900))))
except (ValueError, TypeError):
    width, height = 1600, 900

title = str(game_settings.get("title", "Vintage Legends"))

# --- INITIALISATION PYGAME ---
pygame.init()
# Initialize mixer for music playback
try:
    pygame.mixer.init()
    # Reserve more channels for sound effects (default is 8)
    pygame.mixer.set_num_channels(16)
except Exception:
    pass
# Initialize clock early so it's available for character selection
clock = pygame.time.Clock()
# Utilisation des paramètres validés
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption(title)

def start_music_controller(music_dir, volume=0.2):
    """Launch a small playlist controller window for background music."""
    if tk is None:
        return

    try:
        volume = float(volume)
    except Exception:
        volume = 0.2
    volume = 0.2

    def run():
        root = tk.Tk()
        root.title("Music")
        root.resizable(False, False)
        
        def on_close():
            pygame.mixer.music.stop()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_close)

        try:
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            x = max(0, sw - 280)
            y = max(0, sh // 3)
            root.geometry(f"260x240+{x}+{y}")
        except Exception:
            root.geometry("260x240")

        # Build playlist
        tracks = []
        try:
            if music_dir.exists():
                for p in sorted(music_dir.iterdir()):
                    if p.is_file() and p.suffix.lower() in (".ogg", ".mp3", ".wav", ".flac"):
                        tracks.append(p)
        except Exception:
            tracks = []

        current_index = 0
        paused = False

        def set_status(text):
            status_var.set(text)

        def load_track(index):
            nonlocal current_index, paused
            if not tracks:
                set_status("No tracks found")
                return
            current_index = index % len(tracks)
            try:
                if pygame.mixer.get_init() is None:
                    try:
                        pygame.mixer.init()
                    except Exception as e:
                        set_status(f"Mixer init failed: {e}")
                        return
                pygame.mixer.music.load(str(tracks[current_index]))
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play()
                paused = False
                set_status(f"Playing: {tracks[current_index].stem}")
                playlist.selection_clear(0, tk.END)
                playlist.selection_set(current_index)
                playlist.see(current_index)
            except Exception as e:
                set_status(f"Failed to play: {e}")

        def play_pause():
            nonlocal paused
            if not tracks:
                set_status("No tracks found")
                return
            if pygame.mixer.get_init() is None:
                try:
                    pygame.mixer.init()
                except Exception as e:
                    set_status(f"Mixer init failed: {e}")
                    return
            if pygame.mixer.music.get_busy() and not paused:
                pygame.mixer.music.pause()
                paused = True
                set_status("Paused")
            else:
                if paused:
                    pygame.mixer.music.unpause()
                    paused = False
                    set_status(f"Playing: {tracks[current_index].stem}")
                else:
                    load_track(current_index)

        def stop():
            pygame.mixer.music.stop()
            set_status("Stopped")

        def next_track():
            if tracks:
                load_track(current_index + 1)

        def prev_track():
            if tracks:
                load_track(current_index - 1)

        def on_double_click(event):
            sel = playlist.curselection()
            if sel:
                load_track(sel[0])

        title_lbl = ttk.Label(root, text="Music Player", font=("Arial", 10, "bold"))
        title_lbl.pack(pady=(6, 2))

        status_var = tk.StringVar(value="Ready")
        status_lbl = ttk.Label(root, textvariable=status_var, font=("Arial", 8))
        status_lbl.pack(pady=(0, 6))

        playlist = tk.Listbox(root, height=6, width=32)
        playlist.pack(padx=8, pady=4)
        for t in tracks:
            playlist.insert(tk.END, t.stem)
        playlist.bind("<Double-Button-1>", on_double_click)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=6)

        ttk.Button(btn_frame, text="Prev", command=prev_track, width=6).grid(row=0, column=0, padx=2)
        ttk.Button(btn_frame, text="Play/Pause", command=play_pause, width=10).grid(row=0, column=1, padx=2)
        ttk.Button(btn_frame, text="Next", command=next_track, width=6).grid(row=0, column=2, padx=2)
        ttk.Button(btn_frame, text="Stop", command=stop, width=6).grid(row=0, column=3, padx=2)

        if not tracks:
            set_status("No tracks found")

        root.mainloop()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# --- ZONES SYSTEM ---
zones = load_zones()
current_zone = None

# --- CHARGEMENT DES RESSOURCES ---
# Prefer an explicit 'flowerfield.png' background if present, otherwise fall back to default_bg.png
background = load_background_for_zone(None, screen)

# Music controller removed - zone themes now configured in zones.json
# start_music_controller(ASSETS_PATH / "sounds" / "music", volume=user_settings.get("volume", 0.8))

# Exemple de personnage
mage_path = ASSETS_PATH / "images" / "characters" / "mage.png"
player_sprite = pygame.image.load(mage_path).convert_alpha() if mage_path.exists() else None

# --- CHARACTER SELECTION ---
def choose_character(screen, background, data_path, assets_path):
    """Display a simple character selection screen with seed selection and return a player data dict.

    Characters are loaded from data/characters.json and mapped to the shape expected by Player.
    """
    import time
    chars = load_json('characters.json', {}).get('characters', [])
    font = pygame.font.Font(None, 36)
    small = pygame.font.Font(None, 24)
    tiny = pygame.font.Font(None, 20)

    if not chars:
        # fallback to a default mage-like template
        return {"name": "Mage", "hp": 100, "atk": 15, "def": 5, 'critchance': 0.05, 'critdamage': 1.5, 'game_seed': int(time.time() * 1000) % 1000000000}

    # Simple interactive chooser: show a list of characters and let the player click one
    selected = None
    # Seed selection: "random" or specific seed (string input)
    seed_mode = "random"  # "random" or "custom"
    custom_seed_input = ""
    seed_input_active = False
    
    # UI Rects
    random_seed_rect = pygame.Rect(120, 480, 200, 40)
    custom_seed_rect = pygame.Rect(340, 480, 200, 40)
    seed_input_rect = pygame.Rect(120, 530, 420, 40)
    
    while selected is None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                # Character selection
                for i, ch in enumerate(chars):
                    r = pygame.Rect(120, 120 + i * 72, 600, 56)
                    if r.collidepoint((mx, my)):
                        selected = ch
                        break
                # Seed mode buttons
                if random_seed_rect.collidepoint((mx, my)):
                    seed_mode = "random"
                    seed_input_active = False
                if custom_seed_rect.collidepoint((mx, my)):
                    seed_mode = "custom"
                    seed_input_active = True
                # Seed input field
                if seed_input_rect.collidepoint((mx, my)) and seed_mode == "custom":
                    seed_input_active = True
                else:
                    if not (custom_seed_rect.collidepoint((mx, my)) or seed_input_rect.collidepoint((mx, my))):
                        seed_input_active = False
            
            if ev.type == pygame.KEYDOWN and seed_input_active:
                if ev.key == pygame.K_BACKSPACE:
                    custom_seed_input = custom_seed_input[:-1]
                elif ev.key == pygame.K_RETURN or ev.key == pygame.K_KP_ENTER:
                    seed_input_active = False
                elif ev.unicode.isdigit() and len(custom_seed_input) < 9:
                    custom_seed_input += ev.unicode

        screen.blit(background, (0, 0))
        title = font.render("Choose your character", True, (255, 255, 255))
        screen.blit(title, (120, 60))

        # Character list
        for i, ch in enumerate(chars):
            r = pygame.Rect(120, 120 + i * 72, 600, 56)
            pygame.draw.rect(screen, (30, 30, 40), r, border_radius=6)
            name = small.render(ch.get('name', 'Unnamed'), True, (220, 220, 220))
            screen.blit(name, (r.x + 8, r.y + 8))
            desc = small.render(ch.get('description', ''), True, (180, 180, 180))
            screen.blit(desc, (r.x + 8, r.y + 28))
        
        # Seed selection UI
        seed_title = small.render("Game Seed:", True, (200, 200, 220))
        screen.blit(seed_title, (120, 450))
        
        # Random seed button
        random_color = (70, 120, 180) if seed_mode == "random" else (50, 50, 70)
        pygame.draw.rect(screen, random_color, random_seed_rect, border_radius=6)
        if seed_mode == "random":
            pygame.draw.rect(screen, (100, 160, 220), random_seed_rect, width=2, border_radius=6)
        random_text = tiny.render("Random Seed", True, (255, 255, 255))
        screen.blit(random_text, random_text.get_rect(center=random_seed_rect.center))
        
        # Custom seed button
        custom_color = (70, 120, 180) if seed_mode == "custom" else (50, 50, 70)
        pygame.draw.rect(screen, custom_color, custom_seed_rect, border_radius=6)
        if seed_mode == "custom":
            pygame.draw.rect(screen, (100, 160, 220), custom_seed_rect, width=2, border_radius=6)
        custom_text = tiny.render("Custom Seed", True, (255, 255, 255))
        screen.blit(custom_text, custom_text.get_rect(center=custom_seed_rect.center))
        
        # Seed input field (only visible in custom mode)
        if seed_mode == "custom":
            input_color = (80, 80, 100) if seed_input_active else (50, 50, 70)
            pygame.draw.rect(screen, input_color, seed_input_rect, border_radius=6)
            pygame.draw.rect(screen, (100, 160, 220) if seed_input_active else (70, 70, 90), seed_input_rect, width=2, border_radius=6)
            
            display_text = custom_seed_input if custom_seed_input else "Enter seed (numbers only)"
            text_color = (255, 255, 255) if custom_seed_input else (150, 150, 150)
            input_surf = small.render(display_text, True, text_color)
            screen.blit(input_surf, (seed_input_rect.x + 10, seed_input_rect.y + 10))

        pygame.display.flip()
        clock.tick(30)

    # Determine final seed
    if seed_mode == "random":
        final_seed = int(time.time() * 1000) % 1000000000
    else:
        if custom_seed_input and custom_seed_input.isdigit():
            final_seed = int(custom_seed_input) % 1000000000
        else:
            final_seed = int(time.time() * 1000) % 1000000000
    
    # Map character JSON fields to the Player constructor shape
    return {
        'name': selected.get('name'),
        'hp': selected.get('base_hp', selected.get('hp', 100)),
        'atk': selected.get('base_atk', selected.get('atk', 10)),
        # characters.json uses 'base_def' for defense
        'def': selected.get('base_def', selected.get('base_defense', selected.get('def', 5))),
        # characters.json uses 'base_crit_chance' and 'base_crit_mult'
        'critchance': selected.get('base_crit_chance', selected.get('base_critchance', selected.get('critchance', 0.0))),
        'critdamage': selected.get('base_crit_mult', selected.get('base_critdamage', selected.get('critdamage', 1.5))),
        'game_seed': final_seed,
    }
    

# --- INITIALISATION DU JEU : load save or show chooser ---
save_manager = SaveManager(SAVE_PATH)
saved = save_manager.load()

if saved:
    # Reconstruct a player from saved data and restore persistent fields
    player_template = {
        'name': saved.get('name', 'Player'),
        'hp': saved.get('max_hp', saved.get('hp', 100)),
        'atk': saved.get('base_atk', 10),
        'def': saved.get('base_defense', 5),
        'critchance': saved.get('base_critchance', 0.0),
        'critdamage': saved.get('base_critdamage', 1.5),
    }
    player = Player(player_template)
    # restore persistent fields
    player.gold = saved.get('gold', getattr(player, 'gold', 0))
    player.level = saved.get('level', getattr(player, 'level', 1))
    player.xp = saved.get('xp', getattr(player, 'xp', 0))
    
    # Validate and fix XP - if XP accumulated enough to level up, process it properly
    # This handles cases where save/load might have created inconsistent state
    xp_required = int((player.level ** 1.5) * 100)
    if player.xp >= xp_required:
        # XP is too high for current level - process level ups that should have happened
        print(f'[INFO] Fixing XP overflow: level {player.level}, XP {player.xp}/{xp_required}')
        # Temporarily reduce to safe value, then add back through gain_xp to trigger proper level ups
        excess_xp = player.xp
        player.xp = 0
        player.gain_xp(excess_xp)
    player.inventory = saved.get('inventory', {})
    player.equipment = saved.get('equipment', {'weapon': None, 'armor': None})
    player.base_atk = saved.get('base_atk', getattr(player, 'base_atk', 0))
    player.base_defense = saved.get('base_defense', getattr(player, 'base_defense', 0))
    player.base_critchance = saved.get('base_critchance', getattr(player, 'base_critchance', 0.0))
    player.base_critdamage = saved.get('base_critdamage', getattr(player, 'base_critdamage', 1.5))
    player.base_penetration = saved.get('base_penetration', getattr(player, 'base_penetration', 0.0))
    player.base_agility = saved.get('base_agility', getattr(player, 'base_agility', 0))
    player.base_lifesteal = saved.get('base_lifesteal', getattr(player, 'base_lifesteal', 0.0))
    player.base_hp_regen = saved.get('base_hp_regen', getattr(player, 'base_hp_regen', 0.0))
    # restore canonical base max HP (used for deterministic recalculation)
    player.base_max_hp = saved.get('base_max_hp', getattr(player, 'base_max_hp', getattr(player, 'max_hp', 100)))
    # restore mana stats
    player.current_mana = saved.get('current_mana', getattr(player, 'current_mana', 0))
    player.base_max_mana = saved.get('base_max_mana', getattr(player, 'base_max_mana', 0))
    player.base_mana_regen = saved.get('base_mana_regen', getattr(player, 'base_mana_regen', 0))
    player.base_magic_power = saved.get('base_magic_power', getattr(player, 'base_magic_power', 0))
    player.base_magic_penetration = saved.get('base_magic_penetration', getattr(player, 'base_magic_penetration', 0))
    # restore skills
    player.skills = saved.get('skills', [])
    player.skill_levels = saved.get('skill_levels', {})
    player.equipped_skills = saved.get('equipped_skills', [])
    player.skill_cooldowns = saved.get('skill_cooldowns', {})
    
    # If skills are empty (old save without skills), load starting_skills from character
    if not player.skills:
        try:
            selected_char_id = saved.get('selected_character')
            if selected_char_id:
                characters = load_json('characters.json', {}).get('characters', [])
                for char in characters:
                    if char.get('id') == selected_char_id or char.get('name') == saved.get('name'):
                        starting_skills = char.get('starting_skills', [])
                        player.skills = list(starting_skills)
                        # Initialize skill levels for migrated skills
                        for skill_id in starting_skills:
                            if skill_id not in player.skill_levels:
                                player.skill_levels[skill_id] = 1
                        print(f"✨ Loaded {len(starting_skills)} starting skills for {char.get('name')}")
                        break
        except Exception as e:
            print(f"Warning: Could not load starting skills: {e}")
    
    # Ensure all skills have levels (migration for old saves)
    for skill_id in player.skills:
        if skill_id not in player.skill_levels:
            player.skill_levels[skill_id] = 1
            print(f"🔧 Initialized level for skill: {skill_id}")
    
    player.unspent_points = saved.get('unspent_points', getattr(player, 'unspent_points', 0))
    player.permanent_upgrades = saved.get('permanent_upgrades', getattr(player, 'permanent_upgrades', {}))
    player.challenge_coins = saved.get('challenge_coins', getattr(player, 'challenge_coins', 0))
    player.highest_wave = saved.get('highest_wave', getattr(player, 'highest_wave', 0))
    player.selected_character = saved.get('selected_character')
    # Restore game seed and shop stats
    player.game_seed = saved.get('game_seed', getattr(player, 'game_seed', None))
    player.total_items_bought = saved.get('total_items_bought', getattr(player, 'total_items_bought', 0))
    player.total_gold_spent = saved.get('total_gold_spent', getattr(player, 'total_gold_spent', 0))
    player.cumulative_price_increase = saved.get('cumulative_price_increase', getattr(player, 'cumulative_price_increase', 0.0))
    # restore hp/max_hp
    player.max_hp = saved.get('max_hp', getattr(player, 'max_hp', player.max_hp))
    saved_hp = saved.get('hp', getattr(player, 'hp', player.max_hp))
    
    # Safety check: if saved HP is suspiciously low (less than 10% of max HP or less than 10),
    # it likely means the player died or quit right before death. Restore to full HP.
    if player.max_hp > 0:
        hp_ratio = saved_hp / player.max_hp if saved_hp > 0 else 0
        if saved_hp < 10 or hp_ratio < 0.1:
            print(f'[INFO] Restoring HP to full (was {saved_hp}/{player.max_hp})')
            player.hp = player.max_hp
        else:
            player.hp = saved_hp
    else:
        player.hp = player.max_hp
    
    # If loaded base_max_hp is implausibly larger than saved max_hp (from older corrupted saves),
    # prefer the saved max_hp as the canonical base to avoid sudden jumps when recalculating.
    try:
        bmh = getattr(player, 'base_max_hp', None)
        if bmh is not None and player.max_hp is not None:
            if bmh > max(1000, int(player.max_hp) * 4):
                print('[WARN] Saved base_max_hp unusually large; using saved max_hp as base_max_hp')
                player.base_max_hp = int(player.max_hp)
    except Exception:
        pass
    # Recalculate stats after restoring persistent data
    try:
        player._recalc_stats()
    except Exception:
        pass
    # If there was a saved wave, restore battle state
    battle = BattleSystem(player)
    saved_wave = saved.get('wave')
    if saved_wave:
        try:
            battle.wave = int(saved_wave)
            # Restore saved zone
            saved_zone_id = saved.get('current_zone_id')
            if saved_zone_id and zones:
                for zone in zones:
                    if zone.get('id') == saved_zone_id:
                        battle.current_zone = zone
                        background = load_background_for_zone(zone, screen)
                        print(f"🗺️ Restored zone: {zone.get('name', 'Unknown')}")
                        break
            # If no saved zone or zone not found, select one based on current wave
            if not battle.current_zone and zones:
                loaded_zone = select_zone(battle.wave, zones, None)
                if not loaded_zone:
                    loaded_zone = resolve_zone_for_wave(battle.wave, zones)
                if loaded_zone:
                    battle.current_zone = loaded_zone
                    background = load_background_for_zone(loaded_zone, screen)
            # Get current zone id for enemy spawning
            zone_id = None
            if battle.current_zone:
                zone_id = battle.current_zone.get('id')
            saved_enemy_id = saved.get('enemy_id')
            if saved_enemy_id:
                restored_enemy = Enemy.from_id(saved_enemy_id, battle.wave)
                battle.enemy = restored_enemy or Enemy.random_enemy(battle.wave, current_zone_id=zone_id)
            else:
                battle.enemy = Enemy.random_enemy(battle.wave, current_zone_id=zone_id)

            if 'enemy_hp' in saved and battle.enemy:
                try:
                    saved_enemy_hp = int(saved.get('enemy_hp', battle.enemy.hp))
                    battle.enemy.hp = min(saved_enemy_hp, battle.enemy.max_hp)
                except Exception:
                    pass
        except Exception:
            pass
else:
    # No save — show chooser and create a fresh player
    player_template = choose_character(screen, background, DATA_PATH, ASSETS_PATH)
    # map chosen template back to an id if possible
    try:
        chs = load_json('characters.json', {}).get('characters', [])
        sel_id = None
        for ch in chs:
            if ch.get('name') == player_template.get('name'):
                sel_id = ch.get('id') or ch.get('name')
                break
        if not sel_id and chs:
            sel_id = player_template.get('name')
    except Exception:
        sel_id = player_template.get('name')

    player = Player(player_template)
    player.selected_character = sel_id
    
    # Load starting skills from character data
    starting_skills = player_template.get('starting_skills', [])
    if starting_skills:
        player.skills = list(starting_skills)
        # Initialize skill levels for starting skills
        if not hasattr(player, 'skill_levels'):
            player.skill_levels = {}
        for skill_id in starting_skills:
            player.skill_levels[skill_id] = 1
        print(f"✨ Learned {len(starting_skills)} starting skills")
        for skill_id in starting_skills:
            print(f"  - {skill_id}")
    else:
        player.skills = []
        player.skill_levels = {}
    
    battle = BattleSystem(player)
    # Initialize starting zone for new game
    if zones:
        starting_zone = select_zone(1, zones)
        if starting_zone:
            battle.current_zone = starting_zone
            background = load_background_for_zone(starting_zone, screen)
            print(f"🗺️ Starting in zone: {starting_zone.get('name', 'Unknown')}")

# Create shared instances
shop = Shop(DATA_PATH)
crafting_system = CraftingSystem(DATA_PATH)

# Attach crafting system to battle so UI can access it
battle.crafting_system = crafting_system

# Create UI after battle is set up
ui = UIManager(screen, assets_path=ASSETS_PATH, data_path=DATA_PATH)
ui.set_actions(battle)

# --- BOUCLE PRINCIPALE ---
def main():
    print("🎮 Jeu démarré avec succès !")
    global player, battle, background
    running = True
    # simple developer console state
    console_open = False
    console_text = ""
    # Auto-save tracking
    last_autosave_wave = 0
    # Zone change tracking
    last_zone_check_wave = 0
    while running:
        # --- ÉVÉNEMENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Toggle developer console with backquote (`)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                console_open = not console_open
                # clear text when opening
                if console_open:
                    console_text = ""
                continue
            
            # Manual save with 'S' key
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s and not console_open:
                try:
                    save_manager.save(player, battle=battle)
                    print("💾 Manual save complete!")
                    # Add UI notification
                    try:
                        battle.damage_events.append({'type': 'note', 'msg': 'Game Saved', 'time': time.time()})
                    except Exception:
                        pass
                except Exception as e:
                    print(f"Save failed: {e}")
                continue

            # If console is open, capture text input and handle Enter
            if console_open:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        cmd = console_text.strip()
                        # developer commands
                        if cmd == 'reset_challenges':
                            try:
                                player.challenge_coins = 0
                                player.permanent_upgrades = {}
                                player._recalc_stats()
                                save_manager.save(player)
                                print('Developer: challenges reset')
                                # add UI notification
                                try:
                                    battle.damage_events.append({'type': 'note', 'msg': 'Challenges reset', 'time': time.time()})
                                except Exception:
                                    pass
                            except Exception as e:
                                print('reset_challenges failed', e)
                        # close console after executing
                        console_open = False
                        console_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        console_text = console_text[:-1]
                    else:
                        # append printable character
                        ch = getattr(event, 'unicode', '')
                        if ch:
                            console_text += ch
                # when console is open we don't forward events to UI
                continue

            ui.handle_event(event)

        # --- MISE À JOUR ---
        battle.update()
        ui.update(player, battle)
        
        # Check for zone changes every 25 waves (only once when wave changes)
        try:
            current_wave = getattr(battle, 'wave', 0)
            if current_wave % 25 == 0 and current_wave > 0 and current_wave != last_zone_check_wave:
                new_zone = select_zone(current_wave, zones, battle.current_zone)
                # Only change if we got a different zone
                if new_zone and new_zone != battle.current_zone:
                    old_zone_name = battle.current_zone.get('name', 'Unknown') if battle.current_zone else 'Unknown'
                    battle.current_zone = new_zone
                    background = load_background_for_zone(new_zone, screen)
                    print(f"🗺️ Zone changed: {old_zone_name} → {new_zone.get('name', 'Unknown')}")
                    # Add notification
                    try:
                        battle.damage_events.append({
                            'type': 'note',
                            'msg': f"Entering {new_zone.get('name', 'Unknown')}",
                            'time': time.time()
                        })
                    except Exception:
                        pass
                elif new_zone and new_zone == battle.current_zone:
                    print(f"🗺️ Staying in {new_zone.get('name', 'Unknown')}")
                last_zone_check_wave = current_wave
        except Exception as e:
            print(f"Zone change error: {e}")
        
        # Auto-save every 10 waves (on wave completion, not during combat)
        try:
            current_wave = getattr(battle, 'wave', 0)
            if current_wave > 0 and current_wave % 10 == 0 and current_wave != last_autosave_wave:
                # Only autosave when not in combat and not in shop
                if getattr(battle, 'turn', '') == 'player' and not getattr(battle, 'in_shop', False):
                    enemy = getattr(battle, 'enemy', None)
                    # Save after defeating wave enemy (enemy is ready for next wave)
                    if enemy and enemy.hp == enemy.max_hp:
                        save_manager.save(player, battle=battle)
                        last_autosave_wave = current_wave
                        print(f"💾 Auto-saved at wave {current_wave}")
        except Exception as e:
            print(f"Auto-save error: {e}")

        # If battle indicates a shop wave, open shop modal before spawning next enemy
        if getattr(battle, 'in_shop', False):
            offers = shop.get_offers_for_wave(
                battle.wave,
                player_seed=getattr(player, 'game_seed', None),
                cumulative_increase=getattr(player, 'cumulative_price_increase', 0.0),
                current_zone=battle.current_zone
            )
            # simple shop modal with pagination and tabs
            shop_open = True
            shop_page = 0
            shop_tab = "items"  # "items" or "stats"
            items_per_page = 4
            total_pages = max(1, (len(offers) + items_per_page - 1) // items_per_page)
            title_font = pygame.font.Font(None, 48)
            sf = pygame.font.Font(None, 32)
            small_font = pygame.font.Font(None, 26)
            # Larger panel layout centered
            panel_w, panel_h = 700, 520
            panel_x = (width - panel_w) // 2
            panel_y = (height - panel_h) // 2
            close_rect = pygame.Rect(panel_x + panel_w - 90, panel_y + 10, 80, 40)
            # Tab buttons
            items_tab_rect = pygame.Rect(panel_x + 20, panel_y + 70, 120, 35)
            stats_tab_rect = pygame.Rect(panel_x + 150, panel_y + 70, 120, 35)
            prev_page_rect = pygame.Rect(panel_x + 30, panel_y + panel_h - 60, 120, 45)
            next_page_rect = pygame.Rect(panel_x + panel_w - 150, panel_y + panel_h - 60, 120, 45)
            # Track mouse position for hover tooltips
            hover_item = None

            while shop_open:
                # Get mouse position for hover detection
                mx, my = pygame.mouse.get_pos()
                hover_item = None
                
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        mx, my = ev.pos
                        # close button
                        if close_rect.collidepoint((mx, my)):
                            shop_open = False
                        # Tab switching
                        if items_tab_rect.collidepoint((mx, my)):
                            shop_tab = "items"
                            shop_page = 0
                        if stats_tab_rect.collidepoint((mx, my)):
                            shop_tab = "stats"
                        # pagination buttons (only for items tab)
                        if shop_tab == "items":
                            if prev_page_rect.collidepoint((mx, my)) and shop_page > 0:
                                shop_page -= 1
                            if next_page_rect.collidepoint((mx, my)) and shop_page < total_pages - 1:
                                shop_page += 1
                            # iterate current page offers to find clicked buy buttons
                            start_idx = shop_page * items_per_page
                            end_idx = min(start_idx + items_per_page, len(offers))
                            page_offers = offers[start_idx:end_idx]
                            for page_idx, item in enumerate(page_offers):
                                item_y = panel_y + 120 + page_idx * 95
                                buy_rect = pygame.Rect(panel_x + panel_w - 140, item_y + 30, 110, 50)
                                if buy_rect.collidepoint((mx, my)):
                                    cost = item.get('_final_cost', item.get('cost', 0))
                                    if player.gold >= cost:
                                        player.gold -= cost
                                        # Track shop statistics
                                        player.total_gold_spent = getattr(player, 'total_gold_spent', 0) + cost
                                        player.total_items_bought = getattr(player, 'total_items_bought', 0) + 1
                                        # remove _final_cost before adding to inventory
                                        itm = {k: v for k, v in item.items() if not k.startswith('_')}
                                        # Purchases should go to inventory only and NOT auto-equip to avoid duplication
                                        player.add_item(itm, auto_equip=False)
                                    else:
                                        print("Not enough gold")
                    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                        shop_open = False

                screen.blit(background, (0, 0))
                ui.draw(player, battle)

                # Draw shop panel with border and shadow effect
                shadow_offset = 5
                pygame.draw.rect(screen, (10, 10, 15), (panel_x + shadow_offset, panel_y + shadow_offset, panel_w, panel_h), border_radius=10)
                pygame.draw.rect(screen, (35, 35, 50), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
                pygame.draw.rect(screen, (80, 80, 120), (panel_x, panel_y, panel_w, panel_h), width=3, border_radius=10)
                
                # Title with background
                title_bg = pygame.Rect(panel_x, panel_y, panel_w, 65)
                pygame.draw.rect(screen, (50, 50, 70), title_bg, border_top_left_radius=10, border_top_right_radius=10)
                title = title_font.render(f"Shop - Wave {battle.wave}", True, (255, 255, 100))
                screen.blit(title, (panel_x + 20, panel_y + 15))
                
                # Close button
                pygame.draw.rect(screen, (220, 80, 80), close_rect, border_radius=8)
                pygame.draw.rect(screen, (255, 120, 120), close_rect, width=2, border_radius=8)
                cr = sf.render("Close", True, (255, 255, 255))
                screen.blit(cr, cr.get_rect(center=close_rect.center))
                
                # Tab buttons
                items_tab_color = (70, 120, 180) if shop_tab == "items" else (50, 50, 70)
                stats_tab_color = (70, 120, 180) if shop_tab == "stats" else (50, 50, 70)
                pygame.draw.rect(screen, items_tab_color, items_tab_rect, border_radius=6)
                pygame.draw.rect(screen, stats_tab_color, stats_tab_rect, border_radius=6)
                if shop_tab == "items":
                    pygame.draw.rect(screen, (100, 160, 220), items_tab_rect, width=2, border_radius=6)
                else:
                    pygame.draw.rect(screen, (100, 160, 220), stats_tab_rect, width=2, border_radius=6)
                items_text = small_font.render("Items", True, (255, 255, 255))
                stats_text = small_font.render("Shop Stats", True, (255, 255, 255))
                screen.blit(items_text, items_text.get_rect(center=items_tab_rect.center))
                screen.blit(stats_text, stats_text.get_rect(center=stats_tab_rect.center))
                
                # Conditional rendering based on active tab
                if shop_tab == "items":
                    # Player gold display
                    gold_bg = pygame.Rect(panel_x + panel_w - 200, panel_y + 70, 180, 35)
                    pygame.draw.rect(screen, (40, 40, 55), gold_bg, border_radius=6)
                    pygame.draw.rect(screen, (255, 215, 0), gold_bg, width=2, border_radius=6)
                    gold_text = small_font.render(f"Gold: {player.gold}g", True, (255, 215, 0))
                    screen.blit(gold_text, (panel_x + panel_w - 190, panel_y + 77))

                    # Display current page items
                    start_idx = shop_page * items_per_page
                    end_idx = min(start_idx + items_per_page, len(offers))
                    page_offers = offers[start_idx:end_idx]
                    
                    for idx, item in enumerate(page_offers):
                        item_y = panel_y + 120 + idx * 95
                        item_h = 85
                        item_rect = pygame.Rect(panel_x + 20, item_y, panel_w - 40, item_h)
                        
                        # Check if mouse is hovering over this item (but not over pagination buttons)
                        is_hovering = item_rect.collidepoint((mx, my))
                        # Don't show tooltip if hovering over pagination buttons
                        if prev_page_rect.collidepoint((mx, my)) or next_page_rect.collidepoint((mx, my)):
                            is_hovering = False
                        if is_hovering:
                            hover_item = item
                        
                        # Item background with hover effect
                        bg_color = (60, 70, 90) if is_hovering else (45, 50, 65)
                        pygame.draw.rect(screen, bg_color, item_rect, border_radius=8)
                        pygame.draw.rect(screen, (100, 110, 140), item_rect, width=2, border_radius=8)
                        
                        # Icon with larger size
                        icon_size = 64
                        icon_rect = pygame.Rect(panel_x + 30, item_y + 10, icon_size, icon_size)
                        icon_path = ASSETS_PATH / 'images' / 'items' / f"{item.get('id')}.png"
                        if icon_path.exists():
                            try:
                                ico = pygame.image.load(str(icon_path)).convert_alpha()
                                ico = pygame.transform.smoothscale(ico, (icon_size, icon_size))
                                screen.blit(ico, icon_rect)
                            except:
                                # Draw placeholder if image fails to load
                                pygame.draw.rect(screen, (80, 80, 100), icon_rect, border_radius=4)
                        else:
                            # Draw placeholder box for missing icon
                            pygame.draw.rect(screen, (80, 80, 100), icon_rect, border_radius=4)
                        
                        # Item name (full, no truncation)
                        name = item.get('name', item.get('id'))
                        name_surf = sf.render(name, True, (255, 255, 255))
                        screen.blit(name_surf, (panel_x + 110, item_y + 12))
                        
                        # Item type/description on second line
                        item_type = item.get('type', '').capitalize()
                        desc = item.get('desc', '')
                        if item_type:
                            type_surf = small_font.render(f"[{item_type}]", True, (150, 200, 255))
                            screen.blit(type_surf, (panel_x + 110, item_y + 42))
                        
                        # Price with larger font
                        price = item.get('_final_cost', item.get('cost', 0))
                        price_color = (100, 255, 100) if player.gold >= price else (255, 100, 100)
                        price_surf = sf.render(f"{price}g", True, price_color)
                        price_x = panel_x + panel_w - 270
                        screen.blit(price_surf, (price_x, item_y + 25))
                        
                        # Buy button with better styling
                        buy_rect = pygame.Rect(panel_x + panel_w - 140, item_y + 17, 110, 50)
                        can_afford = player.gold >= price
                        button_color = (80, 180, 80) if can_afford else (100, 100, 100)
                        pygame.draw.rect(screen, button_color, buy_rect, border_radius=8)
                        if can_afford:
                            pygame.draw.rect(screen, (120, 220, 120), buy_rect, width=2, border_radius=8)
                        bt = sf.render("Buy", True, (255, 255, 255) if can_afford else (150, 150, 150))
                        screen.blit(bt, bt.get_rect(center=buy_rect.center))
                    
                    # Draw hover tooltip if hovering over an item
                    if hover_item:
                        tooltip_w, tooltip_h = 350, 200
                        tooltip_x = min(mx + 20, width - tooltip_w - 10)
                        tooltip_y = min(my + 20, height - tooltip_h - 10)
                        
                        # Tooltip background with shadow
                        pygame.draw.rect(screen, (10, 10, 15), (tooltip_x + 3, tooltip_y + 3, tooltip_w, tooltip_h), border_radius=8)
                        pygame.draw.rect(screen, (25, 25, 40), (tooltip_x, tooltip_y, tooltip_w, tooltip_h), border_radius=8)
                        pygame.draw.rect(screen, (120, 120, 180), (tooltip_x, tooltip_y, tooltip_w, tooltip_h), width=2, border_radius=8)
                        
                        # Tooltip content
                        ty = tooltip_y + 10
                        tip_name = small_font.render(hover_item.get('name', ''), True, (255, 255, 100))
                        screen.blit(tip_name, (tooltip_x + 10, ty))
                        ty += 30
                        
                        # Description
                        desc = hover_item.get('desc', 'No description')
                        # Word wrap description
                        words = desc.split()
                        lines = []
                        current_line = ""
                        for word in words:
                            test_line = current_line + (" " if current_line else "") + word
                            if small_font.size(test_line)[0] < tooltip_w - 20:
                                current_line = test_line
                            else:
                                if current_line:
                                    lines.append(current_line)
                                current_line = word
                        if current_line:
                            lines.append(current_line)
                        
                        for line in lines[:3]:  # Max 3 lines
                            desc_surf = small_font.render(line, True, (200, 200, 200))
                            screen.blit(desc_surf, (tooltip_x + 10, ty))
                            ty += 25
                        
                        ty += 5
                        # Stats display
                        stats = []
                        if hover_item.get('attack'): stats.append(f"Attack: +{hover_item['attack']}")
                        if hover_item.get('defense'): stats.append(f"Defense: +{hover_item['defense']}")
                        if hover_item.get('hp'): stats.append(f"HP: +{hover_item['hp']}")
                        if hover_item.get('max_hp'): stats.append(f"Max HP: +{hover_item['max_hp']}")
                        if hover_item.get('critchance'): stats.append(f"Crit: +{int(hover_item['critchance']*100)}%")
                        if hover_item.get('critdamage'): stats.append(f"Crit Dmg: +{hover_item['critdamage']}x")
                        if hover_item.get('penetration'): stats.append(f"Pen: +{hover_item['penetration']}")
                        
                        # Magic stats
                        if hover_item.get('magic_power'): stats.append(f"Magic Power: +{hover_item['magic_power']}")
                        if hover_item.get('magic_penetration'): stats.append(f"Magic Pen: +{hover_item['magic_penetration']}")
                        if hover_item.get('max_mana'): stats.append(f"Max Mana: +{hover_item['max_mana']}")
                        if hover_item.get('mana_regen'): stats.append(f"Mana Regen: +{hover_item['mana_regen']}")
                        
                        for stat_text in stats:
                            stat_surf = small_font.render(stat_text, True, (150, 255, 150))
                            screen.blit(stat_surf, (tooltip_x + 10, ty))
                            ty += 25
                    
                    # Pagination buttons at bottom (only for items tab)
                    if shop_page > 0:
                        pygame.draw.rect(screen, (80, 120, 200), prev_page_rect, border_radius=8)
                    else:
                        pygame.draw.rect(screen, (50, 50, 70), prev_page_rect, border_radius=8)
                    prev_text = sf.render("< Prev", True, (255, 255, 255) if shop_page > 0 else (120, 120, 120))
                    screen.blit(prev_text, prev_text.get_rect(center=prev_page_rect.center))

                    if shop_page < total_pages - 1:
                        pygame.draw.rect(screen, (80, 120, 200), next_page_rect, border_radius=8)
                    else:
                        pygame.draw.rect(screen, (50, 50, 70), next_page_rect, border_radius=8)
                    next_text = sf.render("Next >", True, (255, 255, 255) if shop_page < total_pages - 1 else (120, 120, 120))
                    screen.blit(next_text, next_text.get_rect(center=next_page_rect.center))

                    # Page indicator
                    page_text = sf.render(f"Page {shop_page + 1}/{total_pages}", True, (200, 200, 220))
                    screen.blit(page_text, page_text.get_rect(center=(panel_x + panel_w // 2, panel_y + panel_h - 35)))
                
                elif shop_tab == "stats":
                    # Shop Stats Tab - display shop statistics
                    stats_y = panel_y + 130
                    line_height = 40
                    
                    # Display various shop statistics
                    stats_data = [
                        ("Game Seed:", str(getattr(player, 'game_seed', 'N/A'))),
                        ("Total Items Bought:", str(getattr(player, 'total_items_bought', 0))),
                        ("Total Gold Spent:", f"{getattr(player, 'total_gold_spent', 0)}g"),
                        ("Current Gold:", f"{player.gold}g"),
                        ("Price Increase:", f"+{getattr(player, 'cumulative_price_increase', 0.0) * 100:.1f}%"),
                        ("Current Wave:", str(battle.wave)),
                        ("Highest Wave:", str(getattr(player, 'highest_wave', 0))),
                    ]
                    
                    for label, value in stats_data:
                        # Label
                        label_surf = sf.render(label, True, (180, 180, 200))
                        screen.blit(label_surf, (panel_x + 50, stats_y))
                        # Value
                        value_surf = sf.render(value, True, (255, 255, 100))
                        screen.blit(value_surf, (panel_x + 350, stats_y))
                        stats_y += line_height
                    
                    # Additional info
                    info_y = stats_y + 20
                    info_text = small_font.render("Prices increase by 1-15% per wave (seeded)", True, (150, 150, 170))
                    screen.blit(info_text, (panel_x + 50, info_y))

                pygame.display.flip()
                clock.tick(30)

            # After shop closed, spawn next enemy for the new wave
            battle.in_shop = False
            # Get current zone id for enemy spawning
            zone_id = None
            if battle.current_zone:
                zone_id = battle.current_zone.get('id')
            battle.enemy = Enemy.random_enemy(battle.wave, current_zone_id=zone_id)
            # Reset enemy hit time so new enemy doesn't appear with red/shake effect
            battle.enemy_hit_time = 0
            battle.turn = 'player'

        # --- AFFICHAGE ---
        screen.blit(background, (0, 0))
        
        # Display current zone name at top right (visible area)
        if battle.current_zone:
            zone_font = pygame.font.Font(None, 32)
            zone_name = battle.current_zone.get('name', 'Unknown Zone')
            zone_text = zone_font.render(zone_name, True, (255, 255, 150))
            
            # Position at top right, away from left panel
            zone_x = width - zone_text.get_width() - 40
            zone_y = 20
            
            # Draw background box for better visibility
            box_padding = 15
            box_rect = pygame.Rect(zone_x - box_padding, zone_y - box_padding // 2,
                                  zone_text.get_width() + box_padding * 2,
                                  zone_text.get_height() + box_padding)
            pygame.draw.rect(screen, (20, 20, 30, 200), box_rect, border_radius=8)
            pygame.draw.rect(screen, (100, 255, 100), box_rect, 2, border_radius=8)
            
            # Draw text
            screen.blit(zone_text, (zone_x, zone_y))
        
        if player_sprite:
            # Scale down player sprite to 30% of original size
            scaled_width = int(player_sprite.get_width() * 0.3)
            scaled_height = int(player_sprite.get_height() * 0.3)
            scaled_sprite = pygame.transform.smoothscale(player_sprite, (scaled_width, scaled_height))
            
            # Check if player was recently hit for visual effect
            hit_effect_duration = 0.3  # seconds
            time_since_hit = time.time() - battle.player_hit_time
            is_hit = time_since_hit < hit_effect_duration
            
            # Apply red tint if hit
            if is_hit:
                # Create red overlay
                red_overlay = scaled_sprite.copy()
                red_overlay.fill((255, 50, 50, 128), special_flags=pygame.BLEND_RGBA_MULT)
                scaled_sprite.blit(red_overlay, (0, 0))
            
            # Center the player sprite horizontally, keep it at bottom
            sprite_x = (width - scaled_width) // 2
            sprite_y = height - scaled_height - 50
            
            # Apply shake effect if hit
            if is_hit:
                shake_intensity = 5
                shake_x = random.randint(-shake_intensity, shake_intensity)
                shake_y = random.randint(-shake_intensity, shake_intensity)
                sprite_x += shake_x
                sprite_y += shake_y
            
            screen.blit(scaled_sprite, (sprite_x, sprite_y))
            
            # Draw player health bar above sprite
            bar_width = 200
            bar_height = 20
            bar_x = (width - bar_width) // 2
            bar_y = sprite_y - 35
            
            # Background bar (red)
            pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
            
            # Health bar (green)
            hp_ratio = max(0, min(1, player.hp / player.max_hp)) if player.max_hp > 0 else 0
            health_width = int(bar_width * hp_ratio)
            if health_width > 0:
                # Color changes based on health percentage
                if hp_ratio > 0.6:
                    health_color = (0, 200, 0)
                elif hp_ratio > 0.3:
                    health_color = (255, 200, 0)
                else:
                    health_color = (255, 50, 50)
                pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height), border_radius=4)
            
            # Border
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=4)
            
            # HP Text
            hp_font = pygame.font.Font(None, 18)
            hp_text = hp_font.render(f"{player.hp}/{player.max_hp}", True, (255, 255, 255))
            hp_text_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
            # Draw text shadow for better visibility
            shadow_text = hp_font.render(f"{player.hp}/{player.max_hp}", True, (0, 0, 0))
            screen.blit(shadow_text, (hp_text_rect.x + 1, hp_text_rect.y + 1))
            screen.blit(hp_text, hp_text_rect)
            
            # Mana bar below HP bar
            current_mana = getattr(player, 'current_mana', 0)
            max_mana = getattr(player, 'max_mana', 0)
            if max_mana > 0:
                mana_bar_y = bar_y + bar_height + 5
                
                # Background bar (dark blue)
                pygame.draw.rect(screen, (0, 0, 80), (bar_x, mana_bar_y, bar_width, bar_height), border_radius=4)
                
                # Mana bar (blue)
                mana_ratio = max(0, min(1, current_mana / max_mana)) if max_mana > 0 else 0
                mana_width = int(bar_width * mana_ratio)
                if mana_width > 0:
                    mana_color = (100, 150, 255)
                    pygame.draw.rect(screen, mana_color, (bar_x, mana_bar_y, mana_width, bar_height), border_radius=4)
                
                # Border
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, mana_bar_y, bar_width, bar_height), width=2, border_radius=4)
                
                # Mana Text
                mana_text = hp_font.render(f"{current_mana}/{max_mana}", True, (255, 255, 255))
                mana_text_rect = mana_text.get_rect(center=(bar_x + bar_width // 2, mana_bar_y + bar_height // 2))
                # Draw text shadow
                mana_shadow = hp_font.render(f"{current_mana}/{max_mana}", True, (0, 0, 0))
                screen.blit(mana_shadow, (mana_text_rect.x + 1, mana_text_rect.y + 1))
                screen.blit(mana_text, mana_text_rect)
        
        ui.draw(player, battle)
        pygame.display.flip()

        clock.tick(60)  # Limite à 60 FPS
        # Vérification de la condition de mort
        if player.is_dead():
            # Interactive Game Over modal: show highest wave and Retry/Quit
            game_over = True
            modal_font = pygame.font.Font(None, 96)
            small_font = pygame.font.Font(None, 36)

            # Precompute button rects
            btn_w, btn_h = 160, 48
            spacing = 20
            total_w = btn_w * 2 + spacing
            bx = width // 2 - total_w // 2
            by = height // 2 + 40
            retry_rect = pygame.Rect(bx, by, btn_w, btn_h)
            quit_rect = pygame.Rect(bx + btn_w + spacing, by, btn_w, btn_h)
            # Challenge Shop button (to spend challenge coins)
            cs_rect = pygame.Rect(bx - btn_w - spacing, by, btn_w, btn_h)

            while game_over:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        mx, my = ev.pos
                        # challenge shop
                        if cs_rect.collidepoint((mx, my)):
                            # open challenge shop modal
                            open_challenge_shop = True
                            # load upgrades
                            up_defs = load_json('upgrades.json', {'upgrades': []}).get('upgrades', [])
                            # modal geometry
                            mw, mh = 560, 420
                            mx0 = width//2 - mw//2
                            my0 = height//2 - mh//2
                            # precompute static rects for buttons
                            close_c_rect = pygame.Rect(mx0 + mw - 90, my0 + mh - 44, 80, 32)
                            # filter + scroll state
                            challenge_filter = 'all'
                            scroll_offset = 0
                            visible_count = 5
                            filter_buttons = [
                                ('all', 'ALL'),
                                ('offense', 'OFFENSE'),
                                ('defense', 'DEFENSE'),
                                ('magic', 'MAGIC'),
                                ('utility', 'UTILITY'),
                            ]
                            # enter modal loop
                            while open_challenge_shop:
                                for ce in pygame.event.get():
                                    if ce.type == pygame.QUIT:
                                        pygame.quit(); sys.exit()
                                    if ce.type == pygame.MOUSEBUTTONDOWN and ce.button == 1:
                                        mx2, my2 = ce.pos
                                        # close button
                                        if close_c_rect.collidepoint((mx2, my2)):
                                            open_challenge_shop = False
                                            break
                                        # filter buttons
                                        fbx = mx0 + 16
                                        fby = my0 + 86
                                        fbw = 90
                                        fbh = 26
                                        fbgap = 8
                                        for i, (fkey, flabel) in enumerate(filter_buttons):
                                            frect = pygame.Rect(fbx + i * (fbw + fbgap), fby, fbw, fbh)
                                            if frect.collidepoint((mx2, my2)):
                                                challenge_filter = fkey
                                                scroll_offset = 0
                                                break
                                        # scroll up/down
                                        up_rect = pygame.Rect(mx0 + mw - 50, my0 + 100, 30, 30)
                                        down_rect = pygame.Rect(mx0 + mw - 50, my0 + 100 + (visible_count * 56) - 10, 30, 30)
                                        if up_rect.collidepoint((mx2, my2)):
                                            scroll_offset = max(0, scroll_offset - 1)
                                        if down_rect.collidepoint((mx2, my2)):
                                            scroll_offset += 1
                                        # iterate upgrades clickable areas
                                        # filter upgrades list
                                        if challenge_filter == 'all':
                                            filtered_defs = up_defs
                                        else:
                                            filtered_defs = [u for u in up_defs if u.get('category') == challenge_filter]
                                        max_scroll = max(0, len(filtered_defs) - visible_count)
                                        scroll_offset = max(0, min(scroll_offset, max_scroll))
                                        visible_defs = filtered_defs[scroll_offset:scroll_offset + visible_count]

                                        for i, u in enumerate(visible_defs):
                                            uy = my0 + 120 + i * 56
                                            buy_rect = pygame.Rect(mx0 + 420, uy, 100, 40)
                                            if buy_rect.collidepoint((mx2, my2)):
                                                base_cost = int(u.get('cost', 1))
                                                uid = u.get('id')
                                                cur = player.permanent_upgrades.get(uid, 0)
                                                # Dynamic cost: base_cost * (current_level + 1)
                                                # Example: if base is 3 and cur is 0, cost is 3. If cur is 1, cost is 6. If cur is 2, cost is 9
                                                dynamic_cost = base_cost * (cur + 1)
                                                if player.challenge_coins >= dynamic_cost and cur < int(u.get('max_level', 99)):
                                                    player.challenge_coins -= dynamic_cost
                                                    player.permanent_upgrades[uid] = cur + 1
                                                    player._recalc_stats()
                                                    try:
                                                        save_manager.save(player)
                                                    except Exception:
                                                        pass
                                    if ce.type == pygame.MOUSEBUTTONDOWN and ce.button in (4, 5):
                                        if ce.button == 4:
                                            scroll_offset = max(0, scroll_offset - 1)
                                        elif ce.button == 5:
                                            scroll_offset += 1
                                # draw challenge shop
                                screen.blit(background, (0,0))
                                ui.draw(player, battle)
                                pygame.draw.rect(screen, (30,30,40), (mx0, my0, mw, mh))
                                title = pygame.font.Font(None, 40).render('Challenge Shop', True, (255,255,255))
                                screen.blit(title, (mx0 + 16, my0 + 12))
                                # coin count
                                coin_t = pygame.font.Font(None, 28).render(f'Coins: {player.challenge_coins}', True, (255,215,0))
                                screen.blit(coin_t, (mx0 + 16, my0 + 56))
                                # filter buttons
                                fbx = mx0 + 16
                                fby = my0 + 86
                                fbw = 90
                                fbh = 26
                                fbgap = 8
                                for i, (fkey, flabel) in enumerate(filter_buttons):
                                    frect = pygame.Rect(fbx + i * (fbw + fbgap), fby, fbw, fbh)
                                    active = (challenge_filter == fkey)
                                    fcolor = (90, 120, 180) if active else (60, 60, 80)
                                    pygame.draw.rect(screen, fcolor, frect, border_radius=6)
                                    pygame.draw.rect(screen, (160, 160, 200), frect, 2, border_radius=6)
                                    ftext = pygame.font.Font(None, 20).render(flabel, True, (255,255,255))
                                    screen.blit(ftext, ftext.get_rect(center=frect.center))

                                # list upgrades (filtered + paged)
                                if challenge_filter == 'all':
                                    filtered_defs = up_defs
                                else:
                                    filtered_defs = [u for u in up_defs if u.get('category') == challenge_filter]
                                max_scroll = max(0, len(filtered_defs) - visible_count)
                                scroll_offset = max(0, min(scroll_offset, max_scroll))
                                visible_defs = filtered_defs[scroll_offset:scroll_offset + visible_count]

                                for i, u in enumerate(visible_defs):
                                    uy = my0 + 120 + i * 56
                                    name = u.get('name')
                                    desc = u.get('desc', '')
                                    cur = player.permanent_upgrades.get(u.get('id'), 0)
                                    lvl = pygame.font.Font(None, 26).render(f"{name} (Lv {cur})", True, (220,220,220))
                                    screen.blit(lvl, (mx0 + 16, uy))
                                    if desc:
                                        desc_text = pygame.font.Font(None, 20).render(desc[:38], True, (160,160,180))
                                        screen.blit(desc_text, (mx0 + 16, uy + 24))
                                    # cost and buy - dynamic cost based on current level
                                    base_cost = int(u.get('cost', 1))
                                    dynamic_cost = base_cost * (cur + 1)
                                    cost_t = pygame.font.Font(None, 24).render(f"{dynamic_cost}c", True, (255,215,0))
                                    screen.blit(cost_t, (mx0 + 360, uy))
                                    buy_rect = pygame.Rect(mx0 + 420, uy, 100, 40)
                                    # Gray out button if can't afford or at max level
                                    can_buy = player.challenge_coins >= dynamic_cost and cur < int(u.get('max_level', 99))
                                    btn_color = (80,160,80) if can_buy else (100,100,100)
                                    pygame.draw.rect(screen, btn_color, buy_rect, border_radius=6)
                                    bt = pygame.font.Font(None, 28).render('Buy', True, (255,255,255) if can_buy else (150,150,150))
                                    screen.blit(bt, bt.get_rect(center=buy_rect.center))

                                # scroll buttons
                                up_rect = pygame.Rect(mx0 + mw - 50, my0 + 100, 30, 30)
                                down_rect = pygame.Rect(mx0 + mw - 50, my0 + 100 + (visible_count * 56) - 10, 30, 30)
                                pygame.draw.rect(screen, (80, 80, 100), up_rect, border_radius=4)
                                pygame.draw.rect(screen, (80, 80, 100), down_rect, border_radius=4)
                                up_t = pygame.font.Font(None, 26).render('^', True, (255,255,255))
                                down_t = pygame.font.Font(None, 26).render('v', True, (255,255,255))
                                screen.blit(up_t, up_t.get_rect(center=up_rect.center))
                                screen.blit(down_t, down_t.get_rect(center=down_rect.center))
                                # close button
                                pygame.draw.rect(screen, (200,80,80), close_c_rect, border_radius=6)
                                ct = pygame.font.Font(None, 28).render('Close', True, (0,0,0))
                                screen.blit(ct, ct.get_rect(center=close_c_rect.center))
                                pygame.display.flip()
                                clock.tick(30)
                            # end challenge shop
                            continue
                        # normal retry/quit handling
                        if retry_rect.collidepoint((mx, my)):
                            # Reinitialize player and battle; allow player to choose character again
                            # Preserve persistent challenge progression before reinitializing
                            old_perms = getattr(player, 'permanent_upgrades', {}).copy()
                            old_coins = getattr(player, 'challenge_coins', 0)
                            try:
                                player.highest_wave = max(getattr(player, 'highest_wave', 0), battle.wave)
                                save_manager.save(player, battle=battle)
                            except Exception:
                                pass
                            # ask for character choice
                            new_template = choose_character(screen, background, DATA_PATH, ASSETS_PATH)
                            player = Player(new_template)
                            # restore persistent challenge data so permanent upgrades carry to the new run
                            player.permanent_upgrades = old_perms.copy()
                            player.challenge_coins = old_coins
                            try:
                                player._recalc_stats()
                                # Ensure player starts at full HP with upgraded max_hp
                                player.hp = player.max_hp
                            except Exception:
                                pass
                            battle = BattleSystem(player)
                            # Reset starting zone and background on respawn
                            if zones:
                                starting_zone = select_zone(1, zones)
                                if starting_zone:
                                    battle.current_zone = starting_zone
                                    background = load_background_for_zone(starting_zone, screen)
                                    print(f"🗺️ Starting in zone: {starting_zone.get('name', 'Unknown')}")
                                else:
                                    battle.current_zone = None
                                    background = load_background_for_zone(None, screen)
                            else:
                                battle.current_zone = None
                                background = load_background_for_zone(None, screen)
                            battle.crafting_system = crafting_system  # Attach crafting system
                            ui.set_actions(battle)
                            game_over = False
                            break
                        if quit_rect.collidepoint((mx, my)):
                            try:
                                player.highest_wave = max(getattr(player, 'highest_wave', 0), battle.wave)
                                save_manager.save(player, battle=battle)
                            except Exception:
                                pass
                            pygame.quit()
                            sys.exit()

                # Draw underlying frame
                screen.blit(background, (0, 0))
                if player_sprite:
                    # Scale down player sprite to 30% of original size
                    scaled_width = int(player_sprite.get_width() * 0.3)
                    scaled_height = int(player_sprite.get_height() * 0.3)
                    scaled_sprite = pygame.transform.smoothscale(player_sprite, (scaled_width, scaled_height))
                    
                    # Center the player sprite horizontally, keep it at bottom
                    sprite_x = (width - scaled_width) // 2
                    sprite_y = height - scaled_height - 50
                    screen.blit(scaled_sprite, (sprite_x, sprite_y))
                    
                    # Draw player health bar above sprite
                    bar_width = 200
                    bar_height = 20
                    bar_x = (width - bar_width) // 2
                    bar_y = sprite_y - 35
                    
                    # Background bar (red)
                    pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
                    
                    # Health bar (green)
                    hp_ratio = max(0, min(1, player.hp / player.max_hp)) if player.max_hp > 0 else 0
                    health_width = int(bar_width * hp_ratio)
                    if health_width > 0:
                        # Color changes based on health percentage
                        if hp_ratio > 0.6:
                            health_color = (0, 200, 0)
                        elif hp_ratio > 0.3:
                            health_color = (255, 200, 0)
                        else:
                            health_color = (255, 50, 50)
                        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height), border_radius=4)
                    
                    # Border
                    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=4)
                    
                    # HP Text
                    hp_font = pygame.font.Font(None, 18)
                    hp_text = hp_font.render(f"{player.hp}/{player.max_hp}", True, (255, 255, 255))
                    hp_text_rect = hp_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
                    # Draw text shadow for better visibility
                    shadow_text = hp_font.render(f"{player.hp}/{player.max_hp}", True, (0, 0, 0))
                    screen.blit(shadow_text, (hp_text_rect.x + 1, hp_text_rect.y + 1))
                    screen.blit(hp_text, hp_text_rect)
                
                ui.draw(player, battle)

                # Dark overlay
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))

                # Modal text
                go_text = modal_font.render("Game Over", True, (255, 50, 50))
                go_rect = go_text.get_rect(center=(width // 2, height // 2 - 80))
                screen.blit(go_text, go_rect)

                wave_text = small_font.render(f"Highest Wave: {battle.wave}", True, (255, 255, 255))
                wave_rect = wave_text.get_rect(center=(width // 2, height // 2 - 20))
                screen.blit(wave_text, wave_rect)

                # Buttons
                # Challenge Shop button
                pygame.draw.rect(screen, (120, 100, 200), cs_rect, border_radius=8)
                cs_t = small_font.render('Challenge Shop', True, (255,255,255))
                screen.blit(cs_t, cs_t.get_rect(center=cs_rect.center))
                pygame.draw.rect(screen, (80, 160, 80), retry_rect, border_radius=8)
                pygame.draw.rect(screen, (200, 80, 80), quit_rect, border_radius=8)
                rt = small_font.render("Retry", True, (0, 0, 0))
                qt = small_font.render("Quit", True, (0, 0, 0))
                screen.blit(rt, rt.get_rect(center=retry_rect.center))
                screen.blit(qt, qt.get_rect(center=quit_rect.center))

                pygame.display.flip()
                clock.tick(30)

            # After retry, continue main loop with new player/battle
            continue

    pygame.quit()
    try:
        # Only save if player has reasonable HP (not dead or nearly dead)
        if player.hp > 0 and player.max_hp > 0:
            hp_ratio = player.hp / player.max_hp
            if hp_ratio < 0.1:
                # Player is nearly dead, restore to full HP before saving
                print(f'[INFO] Restoring HP before quit save (was {player.hp}/{player.max_hp})')
                player.hp = player.max_hp
        save_manager.save(player, battle=battle)
    except Exception:
        pass
    print("👋 Jeu fermé proprement.")
    sys.exit()


if __name__ == "__main__":
    main()
