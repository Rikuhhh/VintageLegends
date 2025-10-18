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
from modals import handle_console_event, show_shop_modal, show_challenge_shop_modal, show_game_over_modal

# --- CONFIGURATION DE BASE ---
BASE_PATH = Path(__file__).resolve().parent.parent
ASSETS_PATH = BASE_PATH / "assets"
DATA_PATH = BASE_PATH / "data"
SAVE_PATH = BASE_PATH / "saves"

# --- CHARGEMENT DES PARAMÈTRES ---
from utils import load_json, resource_path

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
# Initialize UI and save manager first
battle = None
ui = UIManager(screen, assets_path=ASSETS_PATH, data_path=DATA_PATH)
save_manager = SaveManager(SAVE_PATH)
shop = Shop(DATA_PATH)

# If a save exists, ask whether to continue or start new. Show class select only when starting a new game.
from modals import show_class_select_modal, show_start_menu_modal
selected_class = None
saved = save_manager.load()
if saved:
    choice = show_start_menu_modal(screen, background, ui, True, clock)
    if choice == 'new' or choice is None:
        # start a new game -> allow class selection
        try:
            selected_class = show_class_select_modal(screen, background, ui, DATA_PATH, clock)
        except Exception:
            selected_class = None
    else:
        # continue -> do not show class selector; saved will be applied below
        selected_class = None
else:
    # no save -> ask for class selection
    try:
        selected_class = show_class_select_modal(screen, background, ui, DATA_PATH, clock)
    except Exception:
        selected_class = None

chars = load_json("characters.json", {}, DATA_PATH).get('characters', [])
default_id = 'mage'
chosen_id = selected_class or default_id

player_data = { 'name': 'Mage', 'hp': 100, 'atk': 15 }
for c in chars:
    if c.get('id') == chosen_id:
        player_data = {
            'name': c.get('name', c.get('id')),
            'hp': int(c.get('base_hp', c.get('hp', 100))),
            'atk': int(c.get('base_atk', c.get('atk', 10))),
            'def': int(c.get('base_def', c.get('def', 5))),
            'critchance': float(c.get('base_crit_chance', c.get('critchance', 0.0))),
            'critdamage': float(c.get('base_crit_mult', c.get('critdamage', 1.5))),
            'id': c.get('id')
        }
        break

player = Player(player_data)
battle = BattleSystem(player)
ui.set_actions(battle)

# Apply save only if player chose to continue (or if no explicit choice variable exists)
if saved and (('choice' not in locals()) or (locals().get('choice') == 'continue')):
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
    console_state = {'open': False, 'text': ''}

    # modal implementations moved to modals.py -> show_shop_modal, show_challenge_shop_modal, show_game_over_modal

    # -- main loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # developer console handling
            if handle_console_event(event, console_state, player, battle, save_manager):
                continue
            ui.handle_event(event)

        battle.update()
        ui.update(player, battle)

        if getattr(battle, 'in_shop', False):
            offers = shop.get_offers_for_wave(battle.wave)
            show_shop_modal(screen, background, ui, player, battle, offers, ASSETS_PATH, clock, save_manager)
            battle.in_shop = False
            battle.enemy = Enemy.random_enemy(battle.wave)
            battle.turn = 'player'

        screen.blit(background, (0, 0))
        if player_sprite:
            screen.blit(player_sprite, (100, 500))
        ui.draw(player, battle)
        # draw dev console if open
        if console_state['open']:
            # simple overlay
            s = pygame.Surface((width, 32))
            s.fill((0,0,0))
            s.set_alpha(200)
            screen.blit(s, (0,0))
            font = pygame.font.Font(None, 24)
            txt = font.render('>' + console_state['text'], True, (255,255,255))
            screen.blit(txt, (8, 6))
        pygame.display.flip()
        clock.tick(60)

        if player.is_dead():
            action = show_game_over_modal(screen, background, ui, player, battle, clock, lambda: show_challenge_shop_modal(screen, background, ui, player, battle, DATA_PATH, clock, save_manager))
            if action == 'retry':
                player = Player(player_data)
                battle = BattleSystem(player)
                ui.set_actions(battle)
                continue
            if action == 'quit':
                break

    pygame.quit()
    try:
        save_manager.save(player, battle=battle)
    except Exception:
        pass
    print("👋 Jeu fermé proprement.")
    sys.exit()


if __name__ == "__main__":
    main()
