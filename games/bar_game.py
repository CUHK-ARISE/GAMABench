"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json

from server import *
from global_functions import *

class BarGame(GameServer):
    def __init__(self, player_num, min, max, home, ratio, ratio_str, version, mode='explicit', name_exp='bar_game', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'bar_game', models, version)
        self.min = min
        self.max = max
        self.home = home
        self.ratio = ratio
        self.ratio_str = ratio_str
        self.mode = mode
        self.name_exp = name_exp
    
    
    def compute_result(self, responses):
        go_player = responses.count('yes')
        go_ratio = go_player / self.player_num
        winner = "yes" if go_ratio <= self.ratio else "no"
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
            
            # Compute revieced utility
            if player_choice == "not go":
                player_utility = self.home
            elif player_choice == "go" and round_record["winner"] == "yes":
                player_utility = self.max
            elif player_choice == "go" and round_record["winner"] == "no":
                player_utility = self.min
            player.utility.append(player_utility)
                    
            result_msg = "Equal or less" if round_record["winner"] == "yes" else "More"
            if self.mode == 'implicit' and player_choice == "not go":
                report_file = f'prompt_template/{self.prompt_folder}/report_implicit_{self.version}.txt'
                report_list = [self.round_id, player_choice, player_utility]
            else:
                report_file = f'prompt_template/{self.prompt_folder}/report_explicit_{self.version}.txt'
                report_list = [self.round_id, round_record["go_num"], self.player_num - round_record["go_num"],
                               self.player_num, result_msg, self.ratio_str, player_choice, player_utility]

            report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    def graphical_analysis(self, players_list):
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        
        # Specify the representative color for each user
        if my_colors is None:
            player_color = ["#{:06x}".format(random.randint(0, 0xFFFFFF)) for _ in players_list]
        else: 
            player_color = my_colors

        # Choice Analysis
        go_list = [r["go_num"] for r in self.round_records]
        plt.plot(round_numbers, go_list, marker='x', color='b')
        plt.axhline(y=self.ratio * self.player_num, color='r', linestyle='--', label='Capacity')
        plt.title(f'El Farol Bar Game (n = {self.player_num})')
        plt.xlabel('Round')
        plt.ylabel('Number of players went to bar')
        plt.ylim(-0.5, self.player_num + 0.5)
        plt.legend()
        plt.savefig(f'figures/{self.name_exp}-capacity.png', dpi=300)
        plt.clf()
        
        # Choice Distribution
        for index, player in enumerate(players_list):
            go_dist = [player.records[:i+1].count('yes') / (i+1) for i in range(len(round_numbers))]
            plt.plot(round_numbers, go_dist, marker='x', color=player_color[index], label=player.id)
        plt.axhline(y=self.ratio, color='r', linestyle='--', label='Capacity')
        plt.title(f'El Farol Bar Game (n = {self.player_num})')
        plt.xlabel('Round')
        plt.ylabel('Probability of Go')
        plt.ylim(-0.1, 1.1)
        plt.savefig(f'figures/{self.name_exp}-choice-distribution.png', dpi=300)
        plt.clf()

        # # Utility Received
        # for index, player in enumerate(players_list):
        #     plt.plot(round_numbers, player.utility, marker='x', color=player_color[index], label=player.id)
        # plt.title(f'El Farol Bar Game (n = {self.player_num})')
        # plt.xlabel('Round')
        # plt.ylabel('Total Utility')
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}-utility-recieved.png', dpi=300)
        # plt.clf()
        
        # # Utility Tendency
        # for index, player in enumerate(players_list):
        #     player_utility = [sum(player.utility[:i+1]) for i in range(len(round_numbers))]
        #     plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        # plt.title(f'El Farol Bar Game (n = {self.player_num})')
        # plt.xlabel('Round')
        # plt.ylabel('Total Utility')
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}-utility.png', dpi=300)
        # plt.clf()
    
    
    def statistic_analysis(self, players_list):
        os.makedirs("results", exist_ok=True)
        with open(f"results/{self.name_exp}.txt", "w") as text_file:
            text_file.write(f"Probability Distribution:\n")
            for player_id, player in enumerate(players_list):
                yes_ratio = player.records.count('yes') / self.round_id * 100
                no_ratio = player.records.count('no') / self.round_id * 100
                text_file.write(f"Player {player_id} 'yes': {yes_ratio:.1f}%, 'no': {no_ratio:.1f}%\n")
    
    
    def save(self, savename):
        game_info = {
            "min": self.min,
            "max": self.max,
            "home": self.home,
            "ratio": self.ratio,
            "ratio_str": self.ratio_str,
            "mode": self.mode,
        }
        return super().save(savename, game_info)


    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
        self.statistic_analysis(eligible_players)
    
    
    def start(self, round):
        print(f"Round {round}: ")
        self.round_id = round
        
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        
        if self.cot:
            output_format = '{"explanation": "<description of your thinking process>", "option": "<yes or no>"}' 
        else:
            output_format = '{"option": "<yes or no>"}'
        cot_msg = get_cot_prompt(self.cot)
        
        request_list = [self.round_id, output_format, cot_msg]
        request_msg = get_prompt(request_file, request_list)
        request_prompt = [{"role": "user", "content": request_msg}]
        responses = []
        
        for player in tqdm(self.players):
            # player.prompt = player.prompt + request_prompt
            while True:
                gpt_responses = player.request(self.round_id, player.prompt + request_prompt)
                try:
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = parsered_responses["option"].lower()
                    if parsered_responses not in ['yes', 'no']: continue
                    player.records.append(parsered_responses)
                    responses.append(parsered_responses)
                    # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                    break
                except:
                    pass
        round_record = self.compute_result(responses)
        self.report_result(round_record)
    
    
    def run(self, rounds, cot=None):
        self.cot = cot
        # Update system prompt (number of round)
        round_message = f" There will be {self.round_id+rounds} rounds." if rounds > 1 else ""
        round_message = f" There will be 20 rounds."
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        description_list = [self.player_num, self.ratio_str, self.min, self.max, self.home, round_message]
        super().run(rounds, description_file, description_list)