# src/main.py
import pygame
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
background_path = ASSETS_PATH / "images" / "backgrounds" / "default_bg.png"
if background_path.exists():
    background = pygame.image.load(background_path).convert()
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
    # load equipment if present
    equip = saved.get('equipment', {})
    if equip:
        player.equipment = equip
        # Note: equipped items' stats are not auto-applied here because we don't have item data;
        # optionally, we can load item definitions and reapply bonuses below
        from shop import Shop
        shop_loader = Shop(DATA_PATH)
        for slot, iid in player.equipment.items():
            it = shop_loader.find_item(iid)
            if it:
                if slot == 'weapon' and it.get('attack'):
                    player.atk += it.get('attack', 0)
                if slot == 'armor' and it.get('defense'):
                    player.defense += it.get('defense', 0)
    # highest wave
    player.highest_wave = saved.get('highest_wave', 0)

# --- BOUCLE PRINCIPALE ---
def main():
    print("🎮 Jeu démarré avec succès !")
    global player, battle
    running = True
    while running:
        # --- ÉVÉNEMENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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
                                    player.add_item(itm)
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
                    p = sf.render(f"{price}g", True, (255, 215, 0))
                    screen.blit(p, (panel_x + 240, by + 8))

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

            while game_over:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        mx, my = ev.pos
                        if retry_rect.collidepoint((mx, my)):
                            # Reinitialize player and battle
                            # save before retry
                            try:
                                player.highest_wave = max(getattr(player, 'highest_wave', 0), battle.wave)
                                save_manager.save(player)
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
                                save_manager.save(player)
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
        save_manager.save(player)
    except Exception:
        pass
    print("👋 Jeu fermé proprement.")
    sys.exit()


if __name__ == "__main__":
    main()
