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
battle_royale = BattleRoyale(player_num=10, version='cot1_Q_begin')
battle_royale.run(20)