import json
import random
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

    def _compute_final_cost(self, item):
        """Compute the final displayed cost for a shop item.
        Supports numeric 'goldvariation' which may be a single number or [min, max].
        Returns an int >= 0.
        """
        try:
            cost = int(item.get('cost', 0))
            gv = item.get('goldvariation')
            if gv is None:
                return cost
            if isinstance(gv, list) and len(gv) >= 2:
                low, high = float(gv[0]), float(gv[1])
                factor = random.uniform(low, high)
            else:
                factor = float(gv)
            return max(0, int(cost * factor))
        except Exception:
            return int(item.get('cost', 0))

    def get_offers_for_wave(self, wave=1):
        offers = []
        for item in self.items:
            cost = item.get('cost')
            if cost is None:
                continue
            sch = float(item.get('shopchance', 1.0))
            if random.random() > sch:
                continue
            final_cost = self._compute_final_cost(item)
            offers.append({**item, '_final_cost': final_cost})
        return offers

    def find_item(self, item_id):
        for i in self.items:
            if i.get('id') == item_id:
                return i
        return None
