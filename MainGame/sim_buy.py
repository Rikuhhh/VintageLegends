import sys
from pathlib import Path
# ensure we can import src modules regardless of cwd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from src.player import Player
from src.shop import Shop

DATA_PATH = HERE / 'data'

def load_item(item_id):
    shop = Shop(DATA_PATH)
    return shop.find_item(item_id)

def main():
    item_id = 'legendary_staff'
    item = load_item(item_id)
    if not item:
        print('Item not found:', item_id)
        return

    player_data = {'name': 'Sim', 'hp': 100, 'atk': 10, 'def': 5}
    p = Player(player_data)
    print('Initial atk:', p.atk)
    print('Initial equipment:', p.equipment)
    print('Initial inv:', p.inventory)

    # Simulate buying 6 copies
    for i in range(1, 7):
        print('\n-- Purchase', i)
        # emulate buy -> player.add_item
        p.add_item(item)
        print('After add_item: atk=', p.atk, 'equipment=', p.equipment)
        print('Inventory:', p.inventory)

    # Now try equipping from inventory repeatedly
    print('\n-- Now equip from inventory until empty')
    while p.inventory.get(item_id, 0) > 0:
        print('Before equip: atk=', p.atk, 'equipment=', p.equipment, 'inv=', p.inventory.get(item_id))
        ok = p.equip_item_by_id(item_id)
        print('equip_item_by_id returned', ok)
        if ok:
            # remove one from inventory to represent equipping a physical copy
            p.remove_item(item_id, 1)
        print('After equip: atk=', p.atk, 'equipment=', p.equipment, 'inv=', p.inventory.get(item_id))

    print('\nFinal stats: atk=', p.atk)
    print('Final equipment:', p.equipment)
    print('Final inventory:', p.inventory)

if __name__ == '__main__':
    main()
