import math
import random
import shutil
import json
import numpy as np

def addnoise(value, epsilon=0.02):
    noise = np.random.normal(0, epsilon)
    return value + noise

def load(filepath, object, newfile=None):
    if newfile:
        shutil.copy2(filepath, f'save/{newfile}.json')
        filepath = f'save/{newfile}.json'
    
    with open(filepath, 'r') as json_file:
        loaded_file = json.loads(json_file.read())
        if newfile:
            loaded_file["meta"]["name_exp"] = newfile
        game = object(**loaded_file["meta"])
        game.load(loaded_file["round_records"], loaded_file["player_data"])
        
    with open(filepath, 'w') as json_file:
        json.dump(loaded_file, json_file, indent=4)
    return game


def ratio_randomization(min=1, max=10):
    numerator = random.randint(min, max)
    denominator = random.randint(numerator, max)    # ratio <= 1
    gcd = math.gcd(numerator, denominator)
    numerator = numerator // gcd
    denominator = denominator // gcd
    return denominator, numerator, f"{denominator}/{numerator}"


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
