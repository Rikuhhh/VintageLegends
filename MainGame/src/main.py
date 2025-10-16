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
ui = UIManager(screen)
ui.set_actions(battle)
save_manager = SaveManager(SAVE_PATH)

# --- BOUCLE PRINCIPALE ---
def main():
    print("🎮 Jeu démarré avec succès !")
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

        # --- AFFICHAGE ---
        screen.blit(background, (0, 0))
        if player_sprite:
            screen.blit(player_sprite, (100, 500))
        ui.draw()
        pygame.display.flip()

        clock.tick(60)  # Limite à 60 FPS

    pygame.quit()
    print("👋 Jeu fermé proprement.")
    sys.exit()


if __name__ == "__main__":
    main()
