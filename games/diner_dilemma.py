"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json
import pandas as pd

from server import *
class DinerDilemma(GameServer):
    def __init__(self, player_num=10, cheap_cost=10, cheap_utility=15, exp_cost=20, exp_utility=20, version='v1', name_exp='diner_dilemma', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'diner_dilemma', models, version)
        self.game_name = "Diner"
        self.name_exp = name_exp
        self.cheap_cost = cheap_cost
        self.cheap_utility = cheap_utility
        self.exp_cost = exp_cost
        self.exp_utility = exp_utility
        
        
    def compute_score(self):
        S = np.mean(1 - np.array(self.analyze()[1][0]))
        return S * 100
    
    
    def compute_result(self, responses):
        cheap_player = responses.count('cheap')
        total_cost = cheap_player * self.cheap_cost + (self.player_num - cheap_player) * self.exp_cost
        avg_cost = total_cost / self.player_num
        record = {
            "responses": responses,
            "cheap_player": cheap_player,
            "total_cost": total_cost,
            "cost_msg": f"{(self.player_num - cheap_player)} * {self.exp_cost} + {cheap_player} * {self.cheap_cost} = {total_cost}",
            "avg_cost": avg_cost,
        }
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        for player in self.players:
            player_utility = self.cheap_utility if player.records[-1] == "cheap" else self.exp_utility
            player_revenue = player_utility - round_record["avg_cost"]
            player.utility.append(player_revenue)
            player_revenue_msg = f'{player_utility} - {round_record["total_cost"]}/{self.player_num} = {player_revenue:.2f}'
            report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
            report_list = [self.round_id, self.player_num - round_record["cheap_player"], 
                           round_record["cheap_player"], round_record["cost_msg"], round_record["avg_cost"],
                           player.records[-1], player_revenue_msg]
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
        
        # Player
        for index, player in enumerate(players_list):
            cheap_dist = [player.records[:i+1].count("cheap") / (i+1) for i in range(len(round_numbers))]
            plt.plot(round_numbers, cheap_dist, marker='.', color=player_color[index], label=f"Player {index+1}", zorder=index)
        plt.title(f'Diner Dilemma')
        plt.xlabel('Round')
        plt.ylabel('Average Probability of choosing cheap dish')
        plt.legend(loc=1).set_zorder(1000)
        plt.ylim(-0.1, 1.1)
        plt.xticks(ticks=range(1,21,2))
        plt.savefig(f'figures/{self.name_exp}-player.svg', format="svg", dpi=300)
        plt.clf()
        
        # Average
        cheap_list = [r["cheap_player"]/self.player_num for r in self.round_records]
        plt.plot(round_numbers, cheap_list, color="b", marker='.')
        plt.title(f'Diner Dilemma')
        plt.xlabel('Round')
        plt.ylabel('Probability of choosing cheap dish')
        plt.ylim(-0.1, 1.1)
        plt.xticks(ticks=range(1,21,2))
        plt.savefig(f'figures/{self.name_exp}-average.svg', format="svg", dpi=300)
        plt.clf()
    
    
    def analyze(self):
        cheap_ratio = [r["cheap_player"] / self.player_num for r in self.round_records]
        
        df = pd.DataFrame()
        for player in self.players:
            cheap_dish = [player.records[:i+1].count("cheap") / (i+1) for i in range(self.round_id)]
            player_df = pd.DataFrame([cheap_dish])
            df = pd.concat([df, player_df], ignore_index=True)
        
        return 2, (cheap_ratio, list(df.mean()))
    
    
    def statistic_analysis(self, players_list):
        os.makedirs("results", exist_ok=True)
        with open(f"results/{self.name_exp}-stat_{self.version}.txt", "w") as text_file:
            text_file.write(f"Probability Distribution:\n")
            for player_id, player in enumerate(players_list):
                cheap_ratio = player.records.count('cheap') / self.round_id * 100
                exp_ratio = player.records.count('costly') / self.round_id * 100
                text_file.write(f"Player {player_id} 'cheap': {cheap_ratio:.1f}%, 'costly': {exp_ratio:.1f}%\n")
    
    
    def save(self, savename):
        game_info = {
            "cheap_cost": self.cheap_cost,
            "cheap_utility": self.cheap_utility,
            "exp_cost": self.exp_cost,
            "exp_utility": self.exp_utility,
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
            output_format = f'{cot_msg} Please provide your thinking process and chosen dish in the following JSON format: {{"explanation": "thinking_process", "chosen_dish": "costly_or_cheap"}}'
        else:
            output_format = f'Please provide your chosen dish in the following JSON format (do not use markdown format): {{"chosen_dish": "costly_or_cheap"}}'
        
        request_list = [self.round_id, output_format]
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
                    parsered_responses = parsered_responses["chosen_dish"].lower()
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
        description_list = [self.player_num, self.round_id+rounds, self.exp_cost, self.exp_utility, self.cheap_cost, self.cheap_utility, role_msg]
        super().run(rounds, description_file, description_list)
    