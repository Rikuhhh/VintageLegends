import json
from pathlib import Path

class Shop:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.items = []
        self.load_items()

    def load_items(self):
        try:
            with open(self.data_path / 'items.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items = data.get('items', [])
        except Exception:
            self.items = []

    def get_offers_for_wave(self, wave=1, player_seed=None, cumulative_increase=0.0, current_zone=None):
        import random
        # Use player seed to create deterministic RNG for this wave's shop
        if player_seed is not None:
            # Create a wave-specific seed from player seed and wave number
            wave_seed = (player_seed + wave * 7919) % 1000000007
            rng = random.Random(wave_seed)
        else:
            rng = random
        
        offers = []
        for i in self.items:
            cost = i.get('cost')
            if cost is None:
                continue
            
            # Filter by zone if item has shop_zones restriction
            shop_zones = i.get('shop_zones', [])
            if shop_zones and current_zone:
                zone_id = current_zone.get('id') if isinstance(current_zone, dict) else current_zone
                if zone_id not in shop_zones:
                    continue
            
            # per-item shop chance (default 1.0)
            sch = float(i.get('shopchance', 1.0))
            if rng.random() > sch:
                continue
            # gold variation: a range like [-0.05, 3.0] or single percentage expressed as -0.05 to 3.0
            gv = i.get('goldvariation')
            final_cost = cost
            if gv is not None:
                # gv can be a single value or a list [min, max]
                if isinstance(gv, list) and len(gv) >= 2:
                    low, high = float(gv[0]), float(gv[1])
                    factor = rng.uniform(low, high)
                else:
                    factor = float(gv)
                # factor interpreted as percentage multiplier (e.g., -0.05 -> reduce by 5%, 0.2 -> increase by 20%)
                final_cost = max(1, int(cost * (1.0 + factor)))
            
            # Apply cumulative price increase from waves (scales all prices)
            # After wave 50, double the price increase every 5 waves
            adjusted_increase = cumulative_increase
            if wave > 50 and wave % 5 == 0:
                adjusted_increase = cumulative_increase * 2
            final_cost = max(1, int(final_cost * (1.0 + adjusted_increase)))

            offers.append({**i, '_final_cost': final_cost})

        return offers

    def find_item(self, item_id):
        for i in self.items:
            if i.get('id') == item_id:
                return i
        return None
