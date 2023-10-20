"""
Author: Eric John LI (ejli@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json

from server import *

class PublicGoodsGame(GameServer):
    def __init__(self, player_num, tokens, ratio, name_exp='public_goods_game', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, models)
        self.name_exp = name_exp
        self.tokens = tokens
        self.ratio = ratio
    
    def compute_result(self, responses):
        total_tokens = sum(responses)
        record = {
            "responses": responses,
            "total_tokens": total_tokens,
        }
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        total_tokens = round_record["total_tokens"]
        
        for player in self.players:
            player_contributed_tokens = player.records[-1]
            player.tokens.append(player.tokens[-1] - player_contributed_tokens + total_tokens * self.ratio/self.player_num)
            player.utility.append(player.tokens[-1] - player_contributed_tokens)
            round_msg = f'You currently have {player.tokens[-1]} tokens.'
            report_file = 'prompt_template/public_goods_game_report.txt'
            report_list = [self.round_id, player_contributed_tokens, total_tokens, player.tokens[-1]]
            report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    def graphical_analysis(self, players_list):
        # Choice Analysis
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        proposed_list = [r["total_tokens"] for r in self.round_records]
        plt.plot(round_numbers, proposed_list, marker='x', color='b')
        plt.axhline(y=self.tokens, color='r', linestyle='--', label='tokens')
        plt.title(f'Public Goods Game (tokens = {self.tokens})')
        plt.xlabel('Round')
        plt.ylabel('Total Proposed Amount')
        # plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-proposed.png', dpi=300)
        plt.clf()
        
        # User tokens Tendency
        player_color = []
        for player in players_list:
            player_records = [player.records[i] for i in range(len(round_numbers))]
            player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
            plt.plot(round_numbers, player_records, marker='x', color=player_color[-1], label=player.id)
        plt.title(f'Public Goods Game (tokens = {self.tokens})')
        plt.xlabel('Round')
        plt.ylabel('Proposed Amount')
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-individual-proposed.png', dpi=300)
        plt.clf()
        
        # Player Revenue / Utility
        for index, player in enumerate(players_list):
            player_utility = [sum(player.utility[:i+1]) for i in range(len(round_numbers))]
            plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        plt.title(f'Public Goods Game (tokens = {self.tokens})')
        plt.xlabel('Round')
        plt.ylabel('Revenue')
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-revenue.png', dpi=300)
        plt.clf()
        
    
    def save(self, savename):
        game_info = {
            "tokens": self.tokens,
        }
        return super().save(savename, game_info)

    def save(self, savename, game_info={}):
        save_data = {
            "meta": {
                "name_exp": self.name_exp,
                "player_num": self.player_num,
                **game_info,
                "round_id": self.round_id,
            },
            "round_records": self.round_records,
            "player_data": [],
        }
        
        for player in self.players:
            player_info = {
                "model": player.model,
                "id": player.id,
                "prompt": player.prompt,
                "records": player.records,
                "tokens": player.tokens,
                "utility": player.utility
            }
            save_data["player_data"].append(player_info)
        
        os.makedirs("save", exist_ok=True)
        savepath = f'save/{savename}.json'
        with open(savepath, 'w') as json_file:
            json.dump(save_data, json_file, indent=2)
        return savepath

    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
    

    def start(self, round):
        print(f"Round {round}: ")
        self.round_id = round
        request_file = 'prompt_template/public_goods_game_request.txt'
        responses = []
        
        for player in tqdm(self.players):
            if round == 1: 
                player.tokens.append(self.tokens)
            request_list = [self.round_id, player.tokens[-1]]
            request_msg = get_prompt(request_file, request_list)
            request_prompt = [{"role": "user", "content": request_msg}]
            player.prompt = player.prompt + request_prompt
            while True:
                gpt_responses = player.gpt_request(player.prompt)
                try:
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = int(parsered_responses["Tokens"])
                    player.records.append(parsered_responses)
                    responses.append(parsered_responses)
                    player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
                    break
                except:
                    pass
        round_record = self.compute_result(responses)
        self.report_result(round_record)


    def run(self, rounds):
        # Update system prompt (number of round)
        round_message = f" There will be {self.round_id+rounds} rounds." if rounds > 1 else ""
        description_file = 'prompt_template/public_goods_game_description.txt'
        description_list = [self.player_num, self.ratio, round_message]
        super().run(rounds, description_file, description_list)
