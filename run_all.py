# Import files
from server import *

# Import games
from games.guessing_game import *
from games.bar_game import *
from games.pirate_game import *
from games.diner_dilemma import *
from games.divide_dollar import *
from games.sealed_bid_auction import *
from games.public_goods import *
from games.battle_royale import *

# Load leadboard
from board import *
board = Leaderboard()

# Run Guessing Game
guessing_game = GuessingGame()
guessing_game.run(20)
board.add(game=guessing_game)
board.show()

# Run Bar Game in implicit mode
bargame_implicit = BarGame(mode="implicit")
bargame_implicit.run(20)
board.add(game=bargame_implicit)
board.show()

# Run Divide the Dollar Game
divide_dollar = DivideDollar()
divide_dollar.run(20)
board.add(game=divide_dollar)
board.show()

# Run Public Goods Game
public_goods_game = PublicGoods()
public_goods_game.run(20)
board.add(game=public_goods_game)
board.show()

# Run Diner Dilemma
diner_dilemma = DinerDilemma()
diner_dilemma.run(20)
board.add(game=diner_dilemma)
board.show()

# Run Sealed Bid auction 
sealed_bid_auction = SealedBidAuction()
sealed_bid_auction.run(20)
board.add(game=sealed_bid_auction)
board.show()

# Run Battle Royale
battle_royale = BattleRoyale()
battle_royale.run(20)
board.add(game=battle_royale)
board.show()

# Run Pirate Game
pirate_game = PirateGame()
pirate_game.run(10)
board.add(game=pirate_game)
board.show()