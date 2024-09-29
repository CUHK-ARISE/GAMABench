"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
from statistics import mean, stdev
import json

from server import *

class GuessingGame(GameServer):
    def __init__(self, player_num=10, min=0, max=100, ratio=2/3, ratio_str='2/3', version='v1', name_exp='guessing_game', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'guessing_game', models, version)
        self.game_name = "Guessing"
        self.min = min
        self.max = max
        self.ratio = ratio
        self.ratio_str = ratio_str
        self.name_exp = name_exp
      
    
    def compute_score(self):
        S = mean(self.analyze()[1])
        D = self.max - self.min
        if self.ratio < 1:
            return (self.max - S) / D * 100
        elif self.ratio == 1:
            return (2 * S - D) / D * 100
        else:
            return S / D * 100
    
      
    def compute_result(self, responses):
        winner = min(responses, key=lambda x: abs(x - mean(responses) * self.ratio))
        record = {
            "responses": responses,
            "mean": mean(responses),
            "mean_ratio": mean(responses) * self.ratio,
            "winner": winner,
            "winner_num": responses.count(winner)
        }
        self.round_records.append(record)
        return record


    def report_result(self, round_record):
        result_list = round_record["responses"]
        random.shuffle(result_list)
        result_str = ', '.join(map(str, result_list))
        for player in self.players:
            player_choice = player.records[-1]
            won = player_choice == round_record["winner"]
            won_msg = "Congratulation you won" if won else "Unfortunately you lost"
            report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
            report_list = [self.round_id, round_record["mean"], self.ratio_str,
                           f'''{round_record["mean_ratio"]:.2f}''',
                           round_record["winner"], player_choice, won_msg]
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
        return 1, [r["mean"] - self.min for r in self.round_records]
    
    
    def graphical_analysis(self, players_list):
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        player_color = [self.cstm_color(x, 1, self.player_num) for x in range(1,self.player_num+1)]
        
        # Player
        for pid, player in enumerate(players_list):
            plt.plot(round_numbers, player.records, marker='.', color=player_color[pid], label=f"Player {pid+1}")
        plt.legend(loc=1).set_zorder(1000)
        plt.title(f'Guessing Game)')
        plt.xlabel('Round')
        plt.ylabel('Chosen Number')
        plt.xticks(ticks=range(1,21,2))
        plt.savefig(f'figures/{self.name_exp}-player.svg', format="svg", dpi=300)
        plt.clf()
        
        # Average
        winning_list = [r["winner"] for r in self.round_records]
        plt.plot(round_numbers, winning_list, marker='.', label='Winner', color='r')
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
        plt.title(f'Guessing Game')
        plt.xlabel('Round')
        plt.ylabel('Chosen Number')
        plt.xticks(ticks=range(1,21,2))
        plt.legend(loc=1)
        plt.savefig(f"figures/{self.name_exp}-average.svg", format="svg", dpi=300)
        plt.clf()
    
    
    def save(self, savename):
        game_info = {
            "min": self.min,
            "max": self.max,
            "ratio": self.ratio,
            "ratio_str": self.ratio_str,
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
            output_format = f'{cot_msg} Please provide your thinking process and chosen number in the following JSON format: {{"explanation": "thinking_process", "chosen_number": "integer_between_{self.min}_and_{self.max}"}}'
        else:
            output_format = f'Please provide your chosen number in the following JSON format: {{"chosen_number": "integer_between_{self.min}_and_{self.max}"}}'
        
        request_list = [self.round_id, self.ratio_str, self.min, self.max, output_format]
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
                    parsered_responses = int(parsered_responses["chosen_number"])
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
        description_list = [self.player_num, self.round_id+rounds, self.min, self.max, self.ratio_str, role_msg]
        super().run(rounds, description_file, description_list)
