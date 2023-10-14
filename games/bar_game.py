"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json

from server import *

class BarGame(GameServer):
    def __init__(self, player_num, rounds, min, max, home, ratio, ratio_str, name_exp='bar game'):
        round_message = f" There will be {rounds} rounds." if rounds > 1 else ""
        description_file = 'prompt_template/bar_game_description.txt'
        description_list = [player_num, ratio_str, max, min, home, round_message]
        super().__init__(player_num, rounds, description_file, description_list)
        self.name_exp = name_exp
        self.min = min
        self.max = max
        self.home = home
        self.ratio = ratio
        self.ratio_str = ratio_str
        for player in self.players:
            player.utility = []
    
    
    def compute_result(self, responses):
        go_player = responses.count('yes')
        go_ratio = go_player / self.n
        winner = "yes" if go_ratio < self.ratio else "no"
        record = {
            "responses": responses,
            "go_num": go_player,
            "go_ratio": go_ratio,
            "winner": winner,
            "utility": self.max if winner == "yes" else self.min
        }
        self.round_records.append(record)
        return record


    def report_result(self, round_record):
        for player in self.players:
            player_choice = "go" if player.records[-1] == "yes" else "not go"
            
            if player_choice == "not go":
                player.utility.append(self.home)
            elif player_choice == "go" and round_record["winner"] == "yes":
                    player.utility.append(self.max)
            elif player_choice == "go" and round_record["winner"] == "no":
                    player.utility.append(self.min)
                    
            result_msg = "Less" if round_record["winner"] == "yes" else "Equal or more"
            report_file = 'prompt_template/bar_game_report.txt'
            report_list = [self.current_round, round_record["go_num"], self.n - round_record["go_num"], self.n, 
                        result_msg, self.ratio_str, player_choice, player.utility[-1]]
            report_prompt = [{"role": "user", "content": self.get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    def graphical_analysis(self):
        # Choice Analysis
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.rounds+1)]
        go_list = [r["go_num"] for r in self.round_records]
        plt.plot(round_numbers, go_list, marker='x', color='b')
        plt.axhline(y=self.ratio * self.n, color='r', linestyle='--', label='Capacity')
        plt.title(f'El Farol Bar Game (n = {self.n})')
        plt.xlabel('Round')
        plt.ylabel('Number of players went to bar')
        plt.ylim(-0.5, self.n + 0.5)
        plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-capacity.png', dpi=300)
        plt.clf()
        
        # Utility Tendency
        for player in self.players:
            player_utility = [sum(player.utility[:i+1]) for i in range(self.rounds)]
            plt.plot(round_numbers, player_utility, marker='x', color='b')
        plt.title(f'El Farol Bar Game (n = {self.n})')
        plt.xlabel('Round')
        plt.ylabel('Total Utility')
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-utility.png', dpi=300)
        plt.clf()
    
    
    def statistic_analysis(self):
        print('Probability Distribution:')
        for player_id, player in enumerate(self.players):
            yes_ratio = player.records.count('yes') / self.rounds * 100
            no_ratio = player.records.count('no') / self.rounds * 100
            print(f"Player {player_id} 'yes': {yes_ratio:.1f}%, 'no': {no_ratio:.1f}%")
    
    
    def start(self):
        for round in range(1, self.rounds+1):
            print(f"Round {round}: ")
            self.current_round = round
            
            request_file = 'prompt_template/bar_game_request.txt'
            request_list = [self.current_round]
            request_msg = self.get_prompt(request_file, request_list)
            request_prompt = [{"role": "user", "content": request_msg}]
            responses = []
            
            for player in tqdm(self.players):
                player.prompt = player.prompt + request_prompt
                while True:
                    gpt_responses = player.gpt_request(player.prompt)
                    try:
                        parsered_responses = json.loads(gpt_responses)
                        parsered_responses = parsered_responses["option"].lower()
                        player.records.append(parsered_responses)
                        responses.append(parsered_responses)
                        player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                        break
                    except:
                        pass
            round_record = self.compute_result(responses)
            self.report_result(round_record)

        self.graphical_analysis()
        self.statistic_analysis()
