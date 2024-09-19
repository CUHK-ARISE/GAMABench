"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json
from statistics import mean, stdev

from server import *

class DivideDollar(GameServer):
    def __init__(self, player_num=10, golds=100, version='v1', name_exp='divide_dollar', round_id=0, models='gpt-3.5-turbo'):
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
        round_msg = f'does not exceeds' if won else f'exceeds'
        
        for player in self.players:
            player_proposal = player.records[-1]
            report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
            received_golds = player_proposal if won else 0
            player.utility.append(received_golds)
            report_list = [self.round_id, player_proposal,
                           total_proposal, round_msg, self.golds, received_golds]
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
    
    
    def analyze(self):
        return 1, [r["total_proposal"] / self.player_num for r in self.round_records]


    def graphical_analysis(self, players_list):
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        player_color = [self.cstm_color(x, 1, self.player_num) for x in range(1,self.player_num+1)]

        # Player
        for pid, player in enumerate(players_list):
            plt.plot(round_numbers, player.records, marker='.', color=player_color[pid], label=f"Player {pid+1}")
        plt.axhline(y=self.golds/self.player_num , color='#000', linestyle='--')
        plt.legend(loc=1)
        plt.title(f'Divide Dollar')
        plt.xlabel('Round')
        plt.ylabel('Proposed Amount')
        plt.xticks(ticks=range(1,21,2))
        plt.savefig(f'figures/{self.name_exp}-player.svg', format="svg", dpi=300)
        plt.clf()
        
        # Average
        responses_list = [r["responses"] for r in self.round_records]
        stdev_list = [stdev(r) for r in responses_list]
        mean_list = [mean(r) for r in responses_list]
        plt.plot(round_numbers, mean_list, marker='.', label='Average', color='b')
        plt.fill_between(
            round_numbers,
            [y - s for y, s in zip(mean_list, stdev_list)],
            [y + s for y, s in zip(mean_list, stdev_list)],
            alpha=0.2, color='b'
        )
        plt.axhline(y=self.golds/self.player_num, color='#000', linestyle='--')
        plt.legend(loc=1)
        plt.title(f'Divide Dollar')
        plt.xlabel('Round')
        plt.ylabel('Average Proposed Amount')
        plt.xticks(ticks=range(1,21,2))
        plt.savefig(f'figures/{self.name_exp}-average.svg', format="svg", dpi=300)
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
        
        cot_msg = get_cot_prompt(self.cot)
        if self.cot:
            output_format = f'{cot_msg} Please provide your thinking process and bid amount in the following JSON format: {{"explanation": "thinking_process", "bid_amount": "integer_between_0_and_{self.golds}"}}'
        else:
            output_format = f'Please provide your bid amount in the following JSON format: {{"bid_amount": "integer_between_0_and_{self.golds}"}}'
        
        request_list = [self.round_id, self.golds, output_format]
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
                    gpt_responses = player.request(self.round_id, player.prompt + request_prompt, request_key="bid_amount")
                try:
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = int(parsered_responses["bid_amount"])
                    player.records.append(parsered_responses)
                    responses.append(parsered_responses)
                    # player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
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
        description_list = [self.player_num, self.round_id+rounds, self.golds, role_msg]
        super().run(rounds, description_file, description_list)
