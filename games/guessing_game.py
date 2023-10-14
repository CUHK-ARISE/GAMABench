"""
Author: LAM Man Ho (mhlam@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
from statistics import mean
import json

from server import *

class GuessingGame(GameServer):
    def __init__(self, player_num, rounds, min, max, ratio, ratio_str, name_exp='guessing_game'):
        round_message = f" There will be {rounds} rounds." if rounds > 1 else ""
        description_file = 'prompt_template/guessing_game_description.txt'
        description_list = [player_num, min, max, ratio_str, round_message]
        super().__init__(player_num, rounds, description_file, description_list)
        self.name_exp = name_exp
        self.min = min
        self.max = max
        self.ratio = ratio
        self.ratio_str = ratio_str
      
      
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
            report_file = 'prompt_template/guessing_game_report.txt'
            report_list = [self.current_round, result_str, round_record["mean"],
                            self.ratio_str, f'''{round_record["mean_ratio"]:.2f}''',
                            round_record["winner"], player_choice, won_msg]
            report_prompt = [{"role": "user", "content": self.get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return
    
    
    def graphical_analysis(self):
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.rounds+1)]
        mean_list = [r["mean_ratio"] for r in self.round_records]
        winning_list = [r["winner"] for r in self.round_records]
        for player in self.players:
            plt.plot(round_numbers, player.records, marker='x', color='b')
        for index, winner in enumerate(winning_list):
            if index == 0:
                plt.plot(index, winner, marker='o', color='g', label='Winner')
            else:
                plt.plot(index, winner, marker='o', color='g')
        plt.plot(round_numbers, mean_list, marker='o', label='Average', color='r')
        plt.title(f'Guessing Game (r = {self.ratio_str})')
        plt.xlabel('Round')
        plt.ylabel('Chosen Number')
        plt.ylim(self.min - 10, self.max + 10)
        plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}.png', dpi=300)
        plt.clf()
    
    
    def start(self):
        for round in range(1, self.rounds+1):
            print(f"Round {round}: ")
            self.current_round = round
            
            request_file = 'prompt_template/guessing_game_request.txt'
            request_list = [self.current_round, self.min, self.max]
            request_msg = self.get_prompt(request_file, request_list)
            request_prompt = [{"role": "user", "content": request_msg}]
            responses = []
            
            for player in tqdm(self.players):
                player.prompt = player.prompt + request_prompt
                while True:
                    gpt_responses = player.gpt_request(player.prompt)
                    try:
                        parsered_responses = json.loads(gpt_responses)
                        parsered_responses = int(parsered_responses["option"])
                        player.records.append(parsered_responses)
                        responses.append(parsered_responses)
                        player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                        break
                    except:
                        pass
            round_record = self.compute_result(responses)
            self.report_result(round_record)

        self.graphical_analysis()
