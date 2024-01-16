from server import *
from prompt_template.prompt_rephrase import *
from global_functions import *

from games.guessing_game import *
from games.bar_game import *
from games.pirate_game import *
from games.diner_dilemma import *
from games.divide_dollar import *
from games.sealed_bid_auction import *
from games.public_goods import *
from games.battle_royale import *

# Battle Royale
for i in range(2):
    for j in range(5):
        if i == 0: 
            current_version = f"cot{j+1}_Q_begin"
        elif i == 1:
            current_version = f"cot{j+1}_Q_end"
        # public_goods = PublicGoods(player_num=10, tokens=100, ratio=random.randint(1, 10 / 2), version=current_version)
        # public_goods.run(20)
        battle_royale = BattleRoyale(player_num=10, version=current_version)
        battle_royale.run(20)
        # sealed_bid_auction = SealedBidAuction(player_num=10, mode="second-highest bid", valuation=100, version=current_version)
        # sealed_bid_auction.run(20)
        # pirate_game = PirateGame(player_num=10, gold=100, version=current_version)
        # pirate_game.run(10)