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
        go_player = responses.count('go')
        go_ratio = go_player / self.player_num
        winner = "go" if go_ratio <= self.ratio else "stay"
        record = {
            "responses": responses,
            "go_num": go_player,
            "go_ratio": go_ratio,
            "winner": winner,
            "utility": self.max if winner == "go" else self.min
        }
        self.round_records.append(record)
        return record


    def report_result(self, round_record):
        for player in self.players:
            player_choice = player.records[-1]
            
            # Compute revieced utility
            if player_choice == "stay":
                player_utility = self.home
            elif player_choice == "go" and round_record["winner"] == "go":
                player_utility = self.max
            elif player_choice == "go" and round_record["winner"] == "stay":
                player_utility = self.min
            player.utility.append(player_utility)
                    
            number_msg = "equal or less" if round_record["winner"] == "go" else "more"
            fun_msg = "more" if round_record["winner"] == "go" else "less"
            if self.mode == 'implicit' and player_choice == "stay":
                report_file = f'prompt_template/{self.prompt_folder}/report_implicit_{self.version}.txt'
                report_list = [self.round_id, player_choice, player_utility]
            else:
                report_file = f'prompt_template/{self.prompt_folder}/report_explicit_{self.version}.txt'
                report_list = [self.round_id, round_record["go_num"], self.player_num - round_record["go_num"],
                               self.player_num, number_msg, fun_msg, self.ratio_str, player_choice, player_utility]

            report_prompts = get_prompt(report_file, report_list)
            gemini_msg = []
            if player.model.startswith('gemini'):
                for i, msg in enumerate(report_prompts):
                    if i == 0:
                        player.prompt[-1]['parts'].append(msg)
                    elif i == 1:
                        player.prompt.append({'role': 'model', 'parts': [msg]})
                    else:         
                        gemini_msg.append(msg)
                player.prompt.append({'role': 'user', 'parts': gemini_msg})
            else:
                report_prompts = [
                    {"role": f"{'assistant' if i == 1 else 'user'}", "content": msg}
                    for i, msg in enumerate(report_prompts)
                ]
                player.prompt = player.prompt + report_prompts
        return


    def graphical_analysis(self, players_list):
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        player_color = [self.cstm_color(x, 1, self.player_num) for x in range(1,self.player_num+1)]
        
        # Single
        for index, player in enumerate(players_list):
            go_dist = [player.records[:i+1].count('go') / (i+1) for i in range(len(round_numbers))]
            plt.plot(round_numbers, go_dist, marker='.', color=player_color[index], label=f"Player {index+1}")
        plt.axhline(y=self.ratio, color='#000', linestyle='--', label='Capacity')
        plt.title(f'El Farol Bar Game (n = {self.player_num})')
        plt.xlabel('Round')
        plt.ylabel('Probability of Go')
        plt.ylim(-0.1, 1.1)
        plt.legend(loc=1).set_zorder(1000)
        plt.xticks(ticks=range(1,21,2))
        plt.savefig(f'figures/{self.name_exp}-single.svg', format="svg", dpi=300)
        plt.clf()
        
        # Average
        go_list = [r["go_num"] for r in self.round_records]
        plt.plot(round_numbers, go_list, marker='.', color='b')
        plt.axhline(y = self.ratio * self.player_num, color='#000', linestyle='--', label='Capacity')
        plt.title(f'El Farol Bar Game (n = {self.player_num})')
        plt.xlabel('Round')
        plt.ylabel('Number of players went to bar')
        plt.ylim(-0.5, self.player_num + 0.5)
        plt.xticks(ticks=range(1,21,2))
        plt.legend()
        plt.savefig(f'figures/{self.name_exp}-average.svg', format="svg", dpi=300)
        plt.clf()
    
    
    def statistic_analysis(self, players_list):
        os.makedirs("results", exist_ok=True)
        with open(f"results/{self.name_exp}.txt", "w") as text_file:
            text_file.write(f"Probability Distribution:\n")
            for player_id, player in enumerate(players_list):
                go_ratio = player.records.count('go') / self.round_id * 100
                stay_ratio = player.records.count('stay') / self.round_id * 100
                text_file.write(f"Player {player_id} 'go': {go_ratio:.1f}%, 'stay': {stay_ratio:.1f}%\n")
    
    
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
        
        cot_msg = get_cot_prompt(self.cot)
        if self.cot:
            output_format = f'{cot_msg} Please provide your thinking process and decision in the following JSON format: {{"explanation": "thinking_process", "decision": "go_or_stay"}}'
        else:
            output_format = f'Please provide your decision in the following JSON format: {{"decision": "go_or_stay"}}'
        
        request_list = [self.round_id, self.ratio_str, output_format]
        request_msg = get_prompt(request_file, request_list)
        request_prompt = [{"role": "user", "content": request_msg}]
        responses = []
        
        for player in tqdm(self.players):
            # player.prompt = player.prompt + request_prompt
            while True:
                if player.model.startswith("gemini"):
                    player.prompt[-1]['parts'].append(request_msg)
                    gpt_responses = player.request(self.round_id, player.prompt)
                else:
                    gpt_responses = player.request(self.round_id, player.prompt + request_prompt)
                try:
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = parsered_responses["decision"].lower()
                    if parsered_responses not in ['go', 'stay']: continue
                    player.records.append(parsered_responses)
                    responses.append(parsered_responses)
                    # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                    break
                except:
                    pass
        round_record = self.compute_result(responses)
        self.report_result(round_record)
    
    
    def run(self, rounds, cot=None, role=None):
        self.cot = cot
        # Update system prompt (number of round)
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        role_msg = get_role_msg(role)
        description_list = [self.player_num, self.round_id+rounds, self.ratio_str, self.max, self.min, self.home, role_msg]
        super().run(rounds, description_file, description_list)