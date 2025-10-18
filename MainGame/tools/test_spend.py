from src.player import Player

p = Player({'name':'Test','hp':100,'atk':10,'def':5,'critchance':0.1,'critdamage':1.5})
print('initial base_max_hp, max_hp, hp:', p.base_max_hp, p.max_hp, p.hp)
# Give player a permanent HP upgrade to simulate bought upgrades
p.permanent_upgrades = {'hp_boost': 1}
# Recalc to apply permanent upgrades
p._recalc_stats()
print('after applying permanent upgrades:', p.base_max_hp, p.max_hp, p.hp)
# set unspent and spend atk
p.unspent_points = 1
p.spend_point('atk')
print('after spending atk:', p.base_max_hp, p.max_hp, p.hp, 'base_atk:', p.base_atk)
# spend def
p.unspent_points = 1
p.spend_point('def')
print('after spending def:', p.base_max_hp, p.max_hp, p.hp, 'base_def:', p.base_defense)
# spend hp
p.unspent_points = 1
p.spend_point('hp')
print('after spending hp:', p.base_max_hp, p.max_hp, p.hp)
