# src/main.py
import pygame
import time
import sys
import json
from pathlib import Path

# Import interne
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
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[ERREUR] Fichier corrompu : {file_name}")
    return default or {}

game_settings = load_json("gamesettings.json", {"width": 1280, "height": 720, "title": "MainGame"})
user_settings = load_json("usersettings.json", {"volume": 0.8, "language": "fr"})

# --- INITIALISATION PYGAME ---
pygame.init()
# Vérification des paramètres de largeur et hauteur
width = user_settings.get("width", 1280)
height = user_settings.get("height", 720)
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("" + game_settings.get("title", "MainGame"))
clock = pygame.time.Clock()

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

# --- INSTANCIATION DU JEU ---
player_data = load_json("characters.json").get("mage", {"name": "Mage", "hp": 100, "atk": 15})
player = Player(player_data)
battle = BattleSystem(player)
ui = UIManager(screen, assets_path=ASSETS_PATH, data_path=DATA_PATH)
ui.set_actions(battle)
save_manager = SaveManager(SAVE_PATH)
shop = Shop(DATA_PATH)

# Load save if present
saved = save_manager.load()
if saved:
    # apply simple fields
    player.gold = saved.get('gold', player.gold)
    player.xp = saved.get('xp', player.xp)
    player.level = saved.get('level', player.level)
    inv = saved.get('inventory', {})
    player.inventory = inv
    # restore base stats and hp/max_hp
    player.base_atk = saved.get('base_atk', getattr(player, 'base_atk', player.base_atk))
    player.base_defense = saved.get('base_defense', getattr(player, 'base_defense', player.base_defense))
    player.max_hp = saved.get('max_hp', getattr(player, 'max_hp', player.max_hp))
    player.hp = saved.get('hp', getattr(player, 'hp', player.max_hp))
    # load equipment if present
    equip = saved.get('equipment', {})
    if equip:
        player.equipment = equip
        # Reapply equipment bonuses correctly by recalculating stats
        from shop import Shop
        shop_loader = Shop(DATA_PATH)
        # ensure base stats exist
        if not hasattr(player, 'base_atk'):
            player.base_atk = getattr(player, 'atk', 0)
        if not hasattr(player, 'base_defense'):
            player.base_defense = getattr(player, 'defense', 0)
        # recalc stats from base + equipment
        player._recalc_stats()
    # highest wave
    player.highest_wave = saved.get('highest_wave', 0)
    # restore saved wave and enemy hp if present
    saved_wave = saved.get('wave')
    if saved_wave:
        # set battle to saved wave and create enemy with matching HP if possible
        battle.wave = int(saved_wave)
        try:
            battle.enemy = Enemy.random_enemy(battle.wave)
            if 'enemy_hp' in saved:
                battle.enemy.hp = int(saved.get('enemy_hp', battle.enemy.hp))
        except Exception:
            pass

# --- BOUCLE PRINCIPALE ---
def main():
    print("🎮 Jeu démarré avec succès !")
    global player, battle
    running = True
    # simple developer console state
    console_open = False
    console_text = ""
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

        # If battle indicates a shop wave, open shop modal before spawning next enemy
        if getattr(battle, 'in_shop', False):
            offers = shop.get_offers_for_wave(battle.wave)
            # simple shop modal
            shop_open = True
            sf = pygame.font.Font(None, 36)
            # panel layout
            panel_x, panel_y, panel_w, panel_h = 180, 100, 520, 360
            close_rect = pygame.Rect(panel_x + panel_w - 70, panel_y + 10, 60, 30)

            while shop_open:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        mx, my = ev.pos
                        # iterate offers to find clicked buy buttons
                        # close button
                        if close_rect.collidepoint((mx, my)):
                            shop_open = False
                        for idx, item in enumerate(offers):
                            by = 150 + idx * 64
                            buy_rect = pygame.Rect(panel_x + 340, by, 80, 48)
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

                # Draw shop panel center-left
                pygame.draw.rect(screen, (30, 30, 40), (panel_x, panel_y, panel_w, panel_h))
                title = sf.render(f"Shop - Wave {battle.wave}", True, (255, 255, 255))
                screen.blit(title, (panel_x + 20, panel_y + 10))

                # Close button
                pygame.draw.rect(screen, (200, 80, 80), close_rect, border_radius=6)
                cr = sf.render("Close", True, (0, 0, 0))
                screen.blit(cr, cr.get_rect(center=close_rect.center))

                for idx, item in enumerate(offers):
                    by = 150 + idx * 64
                    # icon if exists in assets
                    icon_rect = pygame.Rect(panel_x + 20, by, 48, 48)
                    # try to load icon path assets/images/items/{id}.png
                    icon_path = ASSETS_PATH / 'images' / 'items' / f"{item.get('id')}.png"
                    if icon_path.exists():
                        ico = pygame.image.load(str(icon_path)).convert_alpha()
                        ico = pygame.transform.smoothscale(ico, (48, 48))
                        screen.blit(ico, icon_rect)
                    else:
                        # draw name if no icon
                        t = sf.render(item.get('name', item.get('id')), True, (220, 220, 220))
                        screen.blit(t, (panel_x + 80, by + 8))

                    # price
                    price = item.get('_final_cost', item.get('cost', 0))
                    price_text = f"{price}g"
                    p = sf.render(price_text, True, (255, 215, 0))
                    # Draw name but ensure it doesn't overlap price by truncating if necessary
                    name = item.get('name', item.get('id'))
                    # compute available width between icon/name start and price start
                    name_x = panel_x + 80
                    price_x = panel_x + 240
                    max_name_w = max(16, price_x - name_x - 12)
                    # truncate with ellipsis if needed
                    rendered = sf.render(name, True, (220, 220, 220))
                    if rendered.get_width() > max_name_w:
                        # shorten the string
                        truncated = name
                        while truncated and sf.render(truncated + '...', True, (0,0,0)).get_width() > max_name_w:
                            truncated = truncated[:-1]
                        name = (truncated + '...') if truncated else name[:8]
                    n = sf.render(name, True, (220, 220, 220))
                    screen.blit(n, (name_x, by + 8))
                    screen.blit(p, (price_x, by + 8))

                    # buy button
                    buy_rect = pygame.Rect(panel_x + 340, by, 80, 48)
                    pygame.draw.rect(screen, (80, 160, 80), buy_rect, border_radius=6)
                    bt = sf.render("Buy", True, (0, 0, 0))
                    screen.blit(bt, bt.get_rect(center=buy_rect.center))

                pygame.display.flip()
                clock.tick(30)

            # After shop closed, spawn next enemy for the new wave
            battle.in_shop = False
            battle.enemy = Enemy.random_enemy(battle.wave)
            battle.turn = 'player'

        # --- AFFICHAGE ---
        screen.blit(background, (0, 0))
        if player_sprite:
            screen.blit(player_sprite, (100, 500))
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
                                                cost = int(u.get('cost', 1))
                                                uid = u.get('id')
                                                cur = player.permanent_upgrades.get(uid, 0)
                                                if player.challenge_coins >= cost and cur < int(u.get('max_level', 99)):
                                                    player.challenge_coins -= cost
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
                                    # cost and buy
                                    cost = int(u.get('cost', 1))
                                    cost_t = pygame.font.Font(None, 24).render(f"{cost}c", True, (255,215,0))
                                    screen.blit(cost_t, (mx0 + 360, uy))
                                    buy_rect = pygame.Rect(mx0 + 420, uy, 100, 40)
                                    pygame.draw.rect(screen, (80,160,80), buy_rect, border_radius=6)
                                    bt = pygame.font.Font(None, 28).render('Buy', True, (0,0,0))
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
                            # Reinitialize player and battle
                            # save before retry
                            try:
                                player.highest_wave = max(getattr(player, 'highest_wave', 0), battle.wave)
                                save_manager.save(player, battle=battle)
                            except Exception:
                                pass
                            player = Player(player_data)
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
                    screen.blit(player_sprite, (100, 500))
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
        save_manager.save(player, battle=battle)
    except Exception:
        pass
    print("👋 Jeu fermé proprement.")
    sys.exit()


if __name__ == "__main__":
    main()
