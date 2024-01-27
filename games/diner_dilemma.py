"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json

from server import *

class DinerDilemma(GameServer):
    def __init__(self, player_num, cheap_cost, cheap_utility, exp_cost, exp_utility, version, name_exp='diner_dilemma', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'diner_dilemma', models, version)
        self.name_exp = name_exp
        self.cheap_cost = cheap_cost
        self.cheap_utility = cheap_utility
        self.exp_cost = exp_cost
        self.exp_utility = exp_utility
    
    
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
                           round_record["cheap_player"], self.player_num, round_record["cost_msg"], 
                           player.records[-1], player_revenue_msg]
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
        total_cost_list = [r["total_cost"] for r in self.round_records]
        plt.plot(round_numbers, total_cost_list, marker='x', color='b')
        plt.axhline(y=self.cheap_cost * self.player_num, color='r', linestyle='--', label='Cheap')
        plt.axhline(y=self.exp_cost * self.player_num, color='g', linestyle='--', label='Expensive')
        plt.title(f'Diner Dilemma ({self.cheap_cost}:{self.cheap_utility}/{self.exp_cost}:{self.exp_utility})')
        plt.xlabel('Round')
        plt.ylabel('Total Cost')
        plt.ylim(self.cheap_cost * self.player_num - 5, self.exp_cost * self.player_num + 5)
        plt.savefig(f'figures/{self.name_exp}-total-cost.png', dpi=300)
        plt.clf()
        
        # # Choice Analysis
        # os.makedirs("figures", exist_ok=True)
        # round_numbers = [str(i) for i in range(1, self.round_id+1)]
        # avg_cost_list = [r["avg_cost"] for r in self.round_records]
        # plt.plot(round_numbers, avg_cost_list, marker='x', color='b')
        # plt.axhline(y=self.cheap_cost, color='r', linestyle='--', label='Cheap')
        # plt.axhline(y=self.exp_cost, color='g', linestyle='--', label='Expensive')
        # plt.title(f'Diner Dilemma ({self.cheap_cost}:{self.cheap_utility}/{self.exp_cost}:{self.exp_utility})')
        # plt.xlabel('Round')
        # plt.ylabel('Average Cost')
        # plt.ylim(self.cheap_cost - 5, self.exp_cost + 5)
        # plt.savefig(f'figures/{self.name_exp}-cost.png', dpi=300)
        # plt.clf()
        
        # Choice Distribution
        for index, player in enumerate(players_list):
            expensive_dist = [player.records[:i+1].count('expensive') / (i+1) for i in range(len(round_numbers))]
            plt.plot(round_numbers, expensive_dist, marker='x', color=player_color[index], label=player.id)
        plt.title(f'Diner Dilemma ({self.cheap_cost}:{self.cheap_utility}/{self.exp_cost}:{self.exp_utility})')
        plt.xlabel('Round')
        plt.ylabel('Probability of choosing expensive dish')
        plt.ylim(-0.1, 1.1)
        plt.savefig(f'figures/{self.name_exp}-distribution.png', dpi=300)
        plt.clf()
        
        # Utility Received
        for pid, player in enumerate(players_list):
            plt.plot(round_numbers, player.utility, marker='x', color=player_color[pid], label=player.id)
        plt.title(f'Diner Dilemma ({self.cheap_cost}:{self.cheap_utility}/{self.exp_cost}:{self.exp_utility})')
        plt.xlabel('Round')
        plt.ylabel('Utility')
        plt.savefig(f'figures/{self.name_exp}-utility.png', dpi=300)
        plt.clf()
        
        # Utility Tendency
        # for index, player in enumerate(players_list):
        #     player_utility = [sum(player.utility[:i+1]) for i in range(len(round_numbers))]
        #     plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        # plt.title(f'Diner Dilemma ({self.cheap_cost}:{self.cheap_utility}/{self.exp_cost}:{self.exp_utility})')
        # plt.xlabel('Round')
        # plt.ylabel('Total Utility')
        # plt.savefig(f'figures/{self.name_exp}-totalutility.png', dpi=300)
        # plt.clf()
    
    
    def statistic_analysis(self, players_list):
        os.makedirs("results", exist_ok=True)
        with open(f"results/{self.name_exp}-stat_{self.version}.txt", "w") as text_file:
            text_file.write(f"Probability Distribution:\n")
            for player_id, player in enumerate(players_list):
                cheap_ratio = player.records.count('cheap') / self.round_id * 100
                exp_ratio = player.records.count('expensive') / self.round_id * 100
                text_file.write(f"Player {player_id} 'cheap': {cheap_ratio:.1f}%, 'expensive': {exp_ratio:.1f}%\n")
    
    
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
        
        if self.cot:
            output_format = '{"explanation": "<description of your thinking process>", "option": "<expensive or cheap>"}' 
        else:
            output_format = '{"option": "<expensive or cheap>"}'
        cot_msg = get_cot_prompt(self.cot)
        
        request_list = [self.round_id, output_format, cot_msg]
        request_msg = get_prompt(request_file, request_list)
        request_prompt = [{"role": "user", "content": request_msg}]
        responses = []
        
        for player in tqdm(self.players):
            # player.prompt = player.prompt + request_prompt
            while True:
                gpt_responses = player.gpt_request(player.prompt + request_prompt)
                try:
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = parsered_responses["option"].lower()
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
        description_list = [self.player_num, self.exp_cost, self.exp_utility, self.cheap_cost, self.cheap_utility, round_message]
        super().run(rounds, description_file, description_list)
    