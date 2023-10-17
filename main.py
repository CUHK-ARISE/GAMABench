import math
import random

from server import *
from games.guessing_game import *
from games.bar_game import *
from games.pirate_game import *

def ratio_randomization(min=1, max=10):
    numerator = random.randint(min, max)
    denominator = random.randint(numerator, max)    # ratio <= 1
    gcd = math.gcd(numerator, denominator)
    numerator = numerator // gcd
    denominator = denominator // gcd
    return numerator/denominator, f"{numerator}/{denominator}"

num_players = 10
num_rounds = 10

# Guessing Game
# min, max, ratio, ratio_str = 0, 100, 2/3, '2/3'
# guessing_game = GuessingGame(num_players, num_rounds, min, max, ratio, ratio_str)
# guessing_game.start()

# Bar Game
min_utility, max_utility, home_utility, ratio, ratio_str = 0, 10, 5, 0.6, '60%'
bargame = BarGame(num_players, num_rounds, min_utility, max_utility, home_utility, ratio, ratio_str)
# bargame.start()

print("Select model = gpt-3.5-turbo")
attribute = 'model'
model_list = ['gpt-3.5-turbo']
bargame.load('save/bar_game.json', attribute, model_list)

print("Select id = 1,2,3,4")
attribute = 'id'
players_list = [f"player_{i}" for i in [1,2,3,4]]
bargame.load('save/bar_game.json', attribute, players_list)


# Pirate Game
# pirate_game = PirateGame(player_num=10, rounds=10, gold=100)
# pirate_game.start()