# src/main.py
import pygame
import time
import sys
import json
from pathlib import Path

# Internal imports: try package-style (src.*) first, then fall back to direct module imports
try:
    from src.player import Player
    from src.enemy import Enemy
    from src.ui_manager import UIManager
    from src.battle_system import BattleSystem
    from src.save_manager import SaveManager
    from src.shop import Shop
except Exception:
    from player import Player
    from enemy import Enemy
    from ui_manager import UIManager
    from battle_system import BattleSystem
    from save_manager import SaveManager
    from shop import Shop

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

game_settings = load_json("gamesettings.json", {"width": 1280, "height": 720, "title": "MainGame"})
user_settings = load_json("usersettings.json", {"volume": 0.8, "language": "fr"})

# Validate and sanitize settings
try:
    width = max(640, min(3840, int(user_settings.get("width", 1280))))
    height = max(480, min(2160, int(user_settings.get("height", 720))))
except (ValueError, TypeError):
    width, height = 1280, 720

title = str(game_settings.get("title", "Vintage Legends"))

# --- INITIALISATION PYGAME ---
pygame.init()
# Initialize clock early so it's available for character selection
clock = pygame.time.Clock()
# Utilisation des paramètres validés
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption(title)

# --- CHARGEMENT DES RESSOURCES ---
# Prefer an explicit 'flowerfield.png' background if present, otherwise fall back to default_bg.png
bg_dir = ASSETS_PATH / "images" / "backgrounds"
flower_bg = bg_dir / "flowerfield.png"
default_bg = bg_dir / "default_bg.png"
if flower_bg.exists():
    _bg = pygame.image.load(flower_bg).convert()
    background = pygame.transform.smoothscale(_bg, screen.get_size())
elif default_bg.exists():
    _bg = pygame.image.load(default_bg).convert()
    background = pygame.transform.smoothscale(_bg, screen.get_size())
else:
    background = pygame.Surface(screen.get_size())
    background.fill((40, 40, 60))  # Couleur par défaut

# Exemple de personnage
mage_path = ASSETS_PATH / "images" / "characters" / "mage.png"
player_sprite = pygame.image.load(mage_path).convert_alpha() if mage_path.exists() else None

# --- CHARACTER SELECTION ---
def choose_character(screen, background, data_path, assets_path):
    """Display a simple character selection screen and return a player data dict.

    Characters are loaded from data/characters.json and mapped to the shape expected by Player.
    """
    chars = load_json('characters.json', {}).get('characters', [])
    font = pygame.font.Font(None, 36)
    small = pygame.font.Font(None, 24)

    if not chars:
        # fallback to a default mage-like template
        return {"name": "Mage", "hp": 100, "atk": 15, "def": 5, 'critchance': 0.05, 'critdamage': 1.5}

    # Simple interactive chooser: show a list of characters and let the player click one
    selected = None
    while selected is None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for i, ch in enumerate(chars):
                    r = pygame.Rect(120, 120 + i * 72, 600, 56)
                    if r.collidepoint((mx, my)):
                        selected = ch
                        break

        screen.blit(background, (0, 0))
        title = font.render("Choose your character", True, (255, 255, 255))
        screen.blit(title, (120, 60))

        for i, ch in enumerate(chars):
            r = pygame.Rect(120, 120 + i * 72, 600, 56)
            pygame.draw.rect(screen, (30, 30, 40), r, border_radius=6)
            name = small.render(ch.get('name', 'Unnamed'), True, (220, 220, 220))
            screen.blit(name, (r.x + 8, r.y + 8))
            desc = small.render(ch.get('description', ''), True, (180, 180, 180))
            screen.blit(desc, (r.x + 8, r.y + 28))

        pygame.display.flip()
        clock.tick(30)

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
    player.xp = saved.get('xp', getattr(player, 'xp', 0))
    player.level = saved.get('level', getattr(player, 'level', 1))
    player.inventory = saved.get('inventory', {})
    player.equipment = saved.get('equipment', {'weapon': None, 'armor': None})
    player.base_atk = saved.get('base_atk', getattr(player, 'base_atk', 0))
    player.base_defense = saved.get('base_defense', getattr(player, 'base_defense', 0))
    player.base_critchance = saved.get('base_critchance', getattr(player, 'base_critchance', 0.0))
    player.base_critdamage = saved.get('base_critdamage', getattr(player, 'base_critdamage', 1.5))
    player.base_penetration = saved.get('base_penetration', getattr(player, 'base_penetration', 0.0))
    player.base_agility = saved.get('base_agility', getattr(player, 'base_agility', 0))
    # restore canonical base max HP (used for deterministic recalculation)
    player.base_max_hp = saved.get('base_max_hp', getattr(player, 'base_max_hp', getattr(player, 'max_hp', 100)))
    player.unspent_points = saved.get('unspent_points', getattr(player, 'unspent_points', 0))
    player.permanent_upgrades = saved.get('permanent_upgrades', getattr(player, 'permanent_upgrades', {}))
    player.challenge_coins = saved.get('challenge_coins', getattr(player, 'challenge_coins', 0))
    player.highest_wave = saved.get('highest_wave', getattr(player, 'highest_wave', 0))
    player.selected_character = saved.get('selected_character')
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
            battle.enemy = Enemy.random_enemy(battle.wave)
            if 'enemy_hp' in saved:
                battle.enemy.hp = int(saved.get('enemy_hp', battle.enemy.hp))
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
    battle = BattleSystem(player)

# Create shared UI and shop instances
ui = UIManager(screen, assets_path=ASSETS_PATH, data_path=DATA_PATH)
ui.set_actions(battle)
shop = Shop(DATA_PATH)

# --- BOUCLE PRINCIPALE ---
def main():
    print("🎮 Jeu démarré avec succès !")
    global player, battle
    running = True
    # simple developer console state
    console_open = False
    console_text = ""
    # Auto-save tracking
    last_autosave_wave = 0
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
            offers = shop.get_offers_for_wave(battle.wave)
            # simple shop modal with pagination
            shop_open = True
            shop_page = 0
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
                        # pagination buttons
                        if prev_page_rect.collidepoint((mx, my)) and shop_page > 0:
                            shop_page -= 1
                        if next_page_rect.collidepoint((mx, my)) and shop_page < total_pages - 1:
                            shop_page += 1
                        # iterate current page offers to find clicked buy buttons
                        start_idx = shop_page * items_per_page
                        end_idx = min(start_idx + items_per_page, len(offers))
                        page_offers = offers[start_idx:end_idx]
                        for page_idx, item in enumerate(page_offers):
                            item_y = panel_y + 90 + page_idx * 100
                            buy_rect = pygame.Rect(panel_x + panel_w - 140, item_y + 30, 110, 50)
                            if buy_rect.collidepoint((mx, my)):
                                cost = item.get('_final_cost', item.get('cost', 0))
                                if player.gold >= cost:
                                    player.gold -= cost
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
                
                # Player gold display
                gold_text = sf.render(f"Gold: {player.gold}g", True, (255, 215, 0))
                screen.blit(gold_text, (panel_x + panel_w - 180, panel_y + 20))

                # Close button
                pygame.draw.rect(screen, (220, 80, 80), close_rect, border_radius=8)
                pygame.draw.rect(screen, (255, 120, 120), close_rect, width=2, border_radius=8)
                cr = sf.render("Close", True, (255, 255, 255))
                screen.blit(cr, cr.get_rect(center=close_rect.center))

                # Display current page items
                start_idx = shop_page * items_per_page
                end_idx = min(start_idx + items_per_page, len(offers))
                page_offers = offers[start_idx:end_idx]
                
                for idx, item in enumerate(page_offers):
                    item_y = panel_y + 90 + idx * 100
                    item_h = 85
                    item_rect = pygame.Rect(panel_x + 20, item_y, panel_w - 40, item_h)
                    
                    # Check if mouse is hovering over this item
                    is_hovering = item_rect.collidepoint((mx, my))
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
                    if hover_item.get('critchance'): stats.append(f"Crit: +{int(hover_item['critchance']*100)}%")
                    if hover_item.get('critdamage'): stats.append(f"Crit Dmg: +{hover_item['critdamage']}x")
                    if hover_item.get('penetration'): stats.append(f"Pen: +{hover_item['penetration']}")
                    
                    for stat_text in stats:
                        stat_surf = small_font.render(stat_text, True, (150, 255, 150))
                        screen.blit(stat_surf, (tooltip_x + 10, ty))
                        ty += 25
                
                # Pagination buttons at bottom
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

                pygame.display.flip()
                clock.tick(30)

            # After shop closed, spawn next enemy for the new wave
            battle.in_shop = False
            battle.enemy = Enemy.random_enemy(battle.wave)
            battle.turn = 'player'

        # --- AFFICHAGE ---
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
                                        # iterate upgrades clickable areas
                                        for i, u in enumerate(up_defs):
                                            uy = my0 + 100 + i * 56
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
                                # draw challenge shop
                                screen.blit(background, (0,0))
                                ui.draw(player, battle)
                                pygame.draw.rect(screen, (30,30,40), (mx0, my0, mw, mh))
                                title = pygame.font.Font(None, 40).render('Challenge Shop', True, (255,255,255))
                                screen.blit(title, (mx0 + 16, my0 + 12))
                                # coin count
                                coin_t = pygame.font.Font(None, 28).render(f'Coins: {player.challenge_coins}', True, (255,215,0))
                                screen.blit(coin_t, (mx0 + 16, my0 + 56))
                                # list upgrades
                                for i, u in enumerate(up_defs):
                                    uy = my0 + 100 + i * 56
                                    name = u.get('name')
                                    cur = player.permanent_upgrades.get(u.get('id'), 0)
                                    lvl = pygame.font.Font(None, 28).render(f"{name} (Lv {cur})", True, (220,220,220))
                                    screen.blit(lvl, (mx0 + 16, uy))
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
                            except Exception:
                                pass
                            battle = BattleSystem(player)
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
