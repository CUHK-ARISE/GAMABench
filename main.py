import math
import random
import shutil

from server import *
from games.guessing_game import *
from games.bar_game import *
from games.pirate_game import *
from games.diner_dilemma import *
from games.divide_dollar import *

def load(filename, object, name_exp=None):
    if name_exp:
        shutil.copy2(filename, f'save/{name_exp}.json')
        filename = f'save/{name_exp}.json'
    
    with open(filename, 'r') as json_file:
        loaded_file = json.loads(json_file.read())
        game = object(**loaded_file["meta"])
        game.load(loaded_file["round_records"], loaded_file["player_data"])
    return game


def ratio_randomization(min=1, max=10):
    numerator = random.randint(min, max)
    denominator = random.randint(numerator, max)    # ratio <= 1
    gcd = math.gcd(numerator, denominator)
    numerator = numerator // gcd
    denominator = denominator // gcd
    return numerator/denominator, f"{numerator}/{denominator}"


def dish_randomization(min=10, max=100):
    while True:
        n = random.randint(min, max)
        m = random.randint(n+1, max)
        a = random.randint(m+1, max)
        
        b_min = a + n - m + 1
        if b_min > max:
            continue
        
        b = random.randint(b_min, max)
        
        if b > n:
            return a, b, m, n

player_num = 10

# Guessing Game
min, max, ratio, ratio_str = 0, 100, 2/3, '2/3'
guessing_game = GuessingGame(player_num, min, max, ratio, ratio_str)
guessing_game.run(5)
game = load('save/guessing_game.json', GuessingGame)
game.run(3)
game.show('id', ['player_1', 'player_5'])


# Bar Game
# min_utility, max_utility, home_utility, ratio, ratio_str = 0, 10, 5, 0.6, '60%'
# bargame = BarGame(player_num, min_utility, max_utility, home_utility, ratio, ratio_str, name_exp='bargame_explicit')
# bargame = BarGame(player_num, num_rounds, min_utility, max_utility, home_utility, ratio, ratio_str, 'implicit', 'bargame_implicit')
# bargame.run(5)


# Pirate Game
# pirate_game = PirateGame(player_num=10, rounds=10, gold=100)
# pirate_game.start()


# Divide the Dollar Game
# golds = 100
# golds = 200
# divide_dollar = DivideDollar(player_num, golds)
# divide_dollar.run(5)


# Diner Dilemma
# cheap_cost, cheap_utility, exp_cost, exp_utility = 20, 40, 50, 60
# cheap_cost, cheap_utility, exp_cost, exp_utility = 5, 15, 10, 17
# diner_dilemma = DinerDilemma(player_num, cheap_cost, cheap_utility, exp_cost, exp_utility)
# diner_dilemma.run(5)
