"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json

from server import *

class DivideDollar(GameServer):
    def __init__(self, player_num, golds, version, name_exp='divide_dollar', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'divide_dollar', models, version)
        self.name_exp = name_exp
        self.golds = golds
    
    
    def compute_result(self, responses):
        total_proposal = sum(responses)
        record = {
            "responses": responses,
            "total_proposal": total_proposal,
        }
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        total_proposal = round_record["total_proposal"]
        all_proposals = round_record["responses"]
        random.shuffle(all_proposals)
        all_proposals_msg = ', '.join(map(str, all_proposals))
        won = total_proposal <= self.golds
        round_msg = f'Luckily {total_proposal} <= {self.golds}' if won else f'Unfortunately {total_proposal} > {self.golds}'
        
        for player in self.players:
            player_proposal = player.records[-1]
            report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
            recieved_golds = player_proposal if won else 0
            player.utility.append(recieved_golds)
            report_list = [self.round_id, player_proposal, all_proposals_msg,
                           total_proposal, round_msg, recieved_golds]
            report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    def graphical_analysis(self, players_list):
        # Choice Analysis
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        proposed_list = [r["total_proposal"] for r in self.round_records]
        plt.plot(round_numbers, proposed_list, marker='x', color='b')
        plt.axhline(y=self.golds, color='r', linestyle='--', label='Golds')
        plt.title(f'Divide Dollar (golds = {self.golds})')
        plt.xlabel('Round')
        plt.ylabel('Total Proposed Amount')
        # plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-proposed.png', dpi=300)
        plt.clf()
        
        # User Proposal Tendency
        player_color = []
        for player in players_list:
            player_records = [player.records[i] for i in range(len(round_numbers))]
            player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
            plt.plot(round_numbers, player_records, marker='x', color=player_color[-1], label=player.id)
        plt.title(f'Divide Dollar (golds = {self.golds})')
        plt.xlabel('Round')
        plt.ylabel('Proposed Amount')
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-individual-proposed.png', dpi=300)
        plt.clf()
        
        # Player Revenue / Utility
        for index, player in enumerate(players_list):
            player_utility = [sum(player.utility[:i+1]) for i in range(len(round_numbers))]
            plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        plt.title(f'Divide Dollar (golds = {self.golds})')
        plt.xlabel('Round')
        plt.ylabel('Revenue')
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-revenue.png', dpi=300)
        plt.clf()
        
    
    def save(self, savename):
        game_info = {
            "golds": self.golds,
        }
        return super().save(savename, game_info)


    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
    

    def start(self, round):
        print(f"Round {round}: ")
        self.round_id = round
        
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        
        if self.cot:
            output_format = '{"explanation": "<description of your thinking process>", "option": "<amount>"}' 
        else:
            output_format = '{"option": "<amount>"}'
        cot_msg = get_cot_prompt(self.cot)
        
        request_list = [self.round_id, self.golds, output_format, cot_msg]
        request_msg = get_prompt(request_file, request_list)
        request_prompt = [{"role": "user", "content": request_msg}]
        responses = []
        
        for player in tqdm(self.players):
            # player.prompt = player.prompt + request_prompt
            while True:
                gpt_responses = player.gpt_request(player.prompt + request_prompt)
                try:
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = int(parsered_responses["propose"])
                    player.records.append(parsered_responses)
                    responses.append(parsered_responses)
                    # player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
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
        description_list = [self.player_num, self.golds, round_message]
        super().run(rounds, description_file, description_list)
