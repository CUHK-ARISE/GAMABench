from server import *
from global_functions import *

from games.guessing_game import *
from games.bar_game import *
from games.pirate_game import *
from games.diner_dilemma import *
from games.divide_dollar import *
from games.sealed_bid_auction import *
from games.public_goods import *
from games.battle_royale import *

class Leaderboard():
    def __init__(self):
        self.data = {}
        self.load()
    
    
    def add(self, name: str = "User", game: GameServer = None, filepath=None):
        if filepath:
            game = load(filepath, game)
        
        game_name = game.game_name
        score = game.compute_score()

        # If the model (name) does not exist in the data, initialize it
        if name not in self.data:
            self.data[name] = {}
        
        # If the game_name for the model already exists, append the score to a list
        if game_name in self.data[name]:
            self.data[name][game_name].append(score)
        else:
            self.data[name][game_name] = [score]
            
    
    def to_dataframe(self):
        avg_data = {}

        for model, games in self.data.items():
            avg_data[model] = {}
            for game, scores in games.items():
                avg_data[model][game] = sum(scores) / len(scores)

        df = pd.DataFrame.from_dict(avg_data, orient='index')
        
        # Overall Column
        df['Overall'] = df.mean(axis=1)
        columns = ['Overall'] + [col for col in df.columns if col != 'Overall']
        df = df[columns]
        df = df.sort_values(by='Overall', ascending=False)
        
        # 👑👑👑
        first_index = df.index[0]
        df.rename(index={first_index: f"👑**{first_index}**"}, inplace=True)

        return df.round(1)
    
    
    def show(self, name="leadboard"):
        df = self.to_dataframe()
        with open(f"{name}.md", "w") as file:
            file.write(df.to_markdown())
        return df

        
    def load(self):
        games_object = [GuessingGame, BarGame, DivideDollar, PublicGoods, DinerDilemma, SealedBidAuction, BattleRoyale, PirateGame]
        
        games_name = ["Guessing", "Bar", "Dollar", "Goods", "Diner", "Auction", "Battle", "Pirate"]

        games_folder = ["guessing_game", "bar_game_implicit", "divide_dollar", "public_goods",
                        "diner_dilemma", "sealed_bid_auction/first_price", "battle_royale", "pirate_game"]
        
        games_path = ["guessing_game", "bar_game_implicit", "divide_dollar", "public_goods",
                      "diner_dilemma", "sealed_bid_auction", "battle_royale", "pirate_game"]
        
        models_name = ["GPT-3.5-0125", "GPT-3.5-1106", "GPT-3.5-0613", "GPT-4t-0125", "GPT-4o-0806",
                       "Gemini-1.0-Pro", "Gemini-1.5-Pro", "LLaMA-3.1-8B", "LLaMA-3.1-70B",
                       "LLaMA-3.1-405B", "Mixtral-8x7B", "Mixtral-8x22B", "Qwen-2-72B"]
        
        models_path = ["", "gpt-3.5-turbo-1106_", "gpt-3.5-turbo-0613_", "gpt-4-0125-preview_", "gpt-4o_",
                       "gemini-1.0-pro_", "gemini-1.5-pro_",
                       "llama-3.1-8b_", "llama-3.1-70b_", "llama-3.1-405b_",
                       "mixtral-8x7b_", "mixtral-8x22b_", "qwen2-72b_"]
        
        version = "v1"
        
        for game_index, game in enumerate(games_name):
            for model_index, model in enumerate(models_name):
                for i in range(1, 6):
                    path = f"./raw_results/{games_folder[game_index]}/{models_path[model_index]}{games_path[game_index]}_{version}_{i}.json"
                    self.add(model, games_object[game_index], path)
