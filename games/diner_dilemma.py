"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json

from server import *

class DinerDilemma(GameServer):
    def __init__(self, player_num, rounds, cheap_cost, cheap_utility, exp_cost, exp_utility, name_exp='diner_dilemma'):
        round_message = f" There will be {rounds} rounds." if rounds > 1 else ""
        description_file = 'prompt_template/diner_dilemma_description.txt'
        description_list = [player_num, exp_cost, exp_utility, cheap_cost, cheap_utility, round_message]
        super().__init__(player_num, rounds, description_file, description_list)
        self.name_exp = name_exp
        self.cheap_cost = cheap_cost
        self.cheap_utility = cheap_utility
        self.exp_cost = exp_cost
        self.exp_utility = exp_utility
    
    
    def compute_result(self, responses):
        cheap_player = responses.count('cheap')
        total_cost = cheap_player * self.cheap_cost + (self.n - cheap_player) * self.exp_cost
        avg_cost = total_cost / self.n
        record = {
            "responses": responses,
            "cheap_player": cheap_player,
            "total_cost": total_cost,
            "avg_cost": avg_cost,
        }
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        for player in self.players:
            player_utility = self.cheap_utility if player.records[-1] == "cheap" else self.exp_utility
            player_revenue = player_utility - round_record["avg_cost"]
            player.utility.append(player_revenue)
            report_file = 'prompt_template/diner_dilemma_report.txt'
            report_list = [self.current_round, self.n - round_record["cheap_player"], 
                           round_record["cheap_player"], self.n, round_record["total_cost"], 
                           player_revenue]
            report_prompt = [{"role": "user", "content": self.get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    def graphical_analysis(self, players_list):
        # Choice Analysis
        os.makedirs("results", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.rounds+1)]
        avg_cost_list = [r["avg_cost"] for r in self.round_records]
        plt.plot(round_numbers, avg_cost_list, marker='x', color='b')
        plt.axhline(y=self.cheap_cost, color='r', linestyle='--', label='Cheap')
        plt.axhline(y=self.exp_cost, color='g', linestyle='--', label='Expensive')
        plt.title(f'Diner Dilemma ({self.cheap_cost}/{self.exp_cost})')
        plt.xlabel('Round')
        plt.ylabel('Average Cost')
        plt.ylim(self.cheap_cost - 5, self.exp_cost + 5)
        # plt.legend()
        fig = plt.gcf()
        fig.savefig(f'results/{self.name_exp}-cost.png', dpi=300)
        plt.clf()
        
        # Utility Received
        player_color = []
        for player in players_list:
            player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
            plt.plot(round_numbers, player.utility, marker='x', color=player_color[-1], label=player.id)
        plt.title(f'Diner Dilemma ({self.cheap_cost}/{self.exp_cost})')
        plt.xlabel('Round')
        plt.ylabel('Utility')
        fig = plt.gcf()
        fig.savefig(f'results/{self.name_exp}-utility.png', dpi=300)
        plt.clf()
        
        # Utility Tendency
        for index, player in enumerate(players_list):
            player_utility = [sum(player.utility[:i+1]) for i in range(self.rounds)]
            plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        plt.title(f'Diner Dilemma ({self.cheap_cost}/{self.exp_cost})')
        plt.xlabel('Round')
        plt.ylabel('Total Utility')
        fig = plt.gcf()
        fig.savefig(f'results/{self.name_exp}-totalutility.png', dpi=300)
        plt.clf()
    
    
    def statistic_analysis(self, players_list):
        os.makedirs("results", exist_ok=True)
        with open(f"results/{self.name_exp}-stat.txt", "w") as text_file:
            # print('Probability Distribution:')
            text_file.write(f"Probability Distribution:\n")
            for player_id, player in enumerate(players_list):
                cheap_ratio = player.records.count('cheap') / self.rounds * 100
                exp_ratio = player.records.count('expensive') / self.rounds * 100
                # print(f"Player {player_id} 'yes': {cheap_ratio:.1f}%, 'no': {exp_ratio:.1f}%")
                text_file.write(f"Player {player_id} 'yes': {cheap_ratio:.1f}%, 'no': {exp_ratio:.1f}%\n")
    
    
    def start(self):
        for round in range(1, self.rounds+1):
            print(f"Round {round}: ")
            self.current_round = round
            
            request_file = 'prompt_template/diner_dilemma_request.txt'
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

        savefile = self.save(f'{self.name_exp}.json')
        self.load(savefile)
    
    
    def save(self, savename):
        game_info = {
            "cheap_cost": self.cheap_cost,
            "cheap_utility": self.cheap_utility,
            "exp_cost": self.exp_cost,
            "exp_utility": self.exp_utility,
        }
        return super().save(savename, game_info)


    def load(self, file, attribute=None, metric_list='ALL'):
        super().load(file)
        
        if metric_list == 'ALL':
            players_list = self.players
        else:
            players_list = [player for player in self.players if getattr(player, attribute, None) in metric_list]
        
        self.graphical_analysis(players_list)
        self.statistic_analysis(players_list)