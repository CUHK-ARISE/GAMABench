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

# Public Goods Game
sealed_bid_auction = SealedBidAuction(player_num=3, mode="second-highest bid", valuation=100, version='v1')
sealed_bid_auction.run(3)