"""
Author: LI, Eric John (ejli@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json
from random import seed
from random import randint

from server import *

seed(99)

class VickreyAuction(GameServer):
    def __init__(self, player_num, rounds, valuation, name_exp='vickrey_auction'):
        # display the round message in the description file only when round > 1
        round_message = f" There will be {rounds} rounds." if rounds > 1 else ""
        description_file = 'prompt_template/vickrey_auction_description.txt'
        # input appropriate value for the description file
        description_list = [player_num, round_message]
        super().__init__(player_num, rounds, description_file, description_list)
        self.name_exp = name_exp
        self.valuation = valuation
    
    
    def compute_result(self, responses):
        bid_winner = max(responses)
        bid_winner_pay = sorted(list(set(responses)))[-2]
        record = {
            "responses": responses,
            "bid_winner": bid_winner,
            "bid_winner_payment": bid_winner_pay
        }
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        for player in self.players:
            player_bid = player.records[-1]
            report_file = 'prompt_template/vickrey_auction_report.txt'
            player_util = player_bid - player.valuation[-1]
            player.utility.append(player_util)
            result = 'won' if round_record["bid_winner"] == player_bid else 'lost'
            report_msg = 'You pay ' + str(round_record["bid_winner_payment"]) if result == 'won' else ''
            report_list = [self.current_round, player.valuation[-1], player_bid, result, 
                           report_msg, player.valuation[-1] - round_record["bid_winner_payment"]]
            report_prompt = [{"role": "user", "content": self.get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    # def graphical_analysis(self, players_list):
    #     # Choice Analysis
    #     os.makedirs("results", exist_ok=True)
    #     round_numbers = [str(i) for i in range(1, self.rounds+1)]
    #     proposed_list = [r["total_proposal"] for r in self.round_records]
    #     plt.plot(round_numbers, proposed_list, marker='x', color='b')
    #     plt.axhline(y=self.golds, color='r', linestyle='--', label='Golds')
    #     plt.title(f'Divide Dollar (golds = {self.golds})')
    #     plt.xlabel('Round')
    #     plt.ylabel('Total Proposed Amount')
    #     # plt.legend()
    #     fig = plt.gcf()
    #     fig.savefig(f'results/{self.name_exp}-proposed.png', dpi=300)
    #     plt.clf()
        
    #     # User Proposal Tendency
    #     player_color = []
    #     for player in players_list:
    #         player_records = [player.records[i] for i in range(self.rounds)]
    #         player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
    #         plt.plot(round_numbers, player_records, marker='x', color=player_color[-1], label=player.id)
    #     plt.title(f'Divide Dollar (golds = {self.golds})')
    #     plt.xlabel('Round')
    #     plt.ylabel('Proposed Amount')
    #     fig = plt.gcf()
    #     fig.savefig(f'results/{self.name_exp}-individual-proposed.png', dpi=300)
    #     plt.clf()
        
    #     # Player Revenue / Utility
    #     for index, player in enumerate(players_list):
    #         player_utility = [sum(player.utility[:i+1]) for i in range(self.rounds)]
    #         plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
    #     plt.title(f'Divide Dollar (golds = {self.golds})')
    #     plt.xlabel('Round')
    #     plt.ylabel('Revenue')
    #     fig = plt.gcf()
    #     fig.savefig(f'results/{self.name_exp}-revenue.png', dpi=300)
    #     plt.clf()
    
    
    # def statistic_analysis(self, players_list):
    #     os.makedirs("results", exist_ok=True)
    #     with open(f"results/{self.name_exp}-stat.txt", "w") as text_file:
    #         # print('Probability Distribution:')
    #         text_file.write(f"Probability Distribution:\n")
    #         for player_id, player in enumerate(players_list):
    #             cheap_ratio = player.records.count('cheap') / self.rounds * 100
    #             exp_ratio = player.records.count('expensive') / self.rounds * 100
    #             text_file.write(f"Player {player_id} 'cheap': {cheap_ratio:.1f}%, 'expensive': {exp_ratio:.1f}%\n")
    
    
    def start(self):
        for round in range(1, self.rounds+1):
            print(f"Round {round}: ")
            self.current_round = round
            request_file = 'prompt_template/vickrey_auction_request.txt'
            # valuation of item should be randomized here
            responses = []
            for player in tqdm(self.players):
                rand_valuation = randint(0, self.valuation)
                player.valuation.append(rand_valuation)
                request_list = [self.current_round, player.valuation[-1]]
                request_msg = self.get_prompt(request_file, request_list)
                request_prompt = [{"role": "user", "content": request_msg}]
                player.prompt = player.prompt + request_prompt
                while True:
                    gpt_responses = player.gpt_request(player.prompt)
                    try:
                        parsered_responses = json.loads(gpt_responses)
                        parsered_responses = int(parsered_responses["bid"])
                        player.records.append(parsered_responses)
                        responses.append(parsered_responses)
                        player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
                        break
                    except:
                        pass
            round_record = self.compute_result(responses)
            self.report_result(round_record)

        savefile = self.save(f'{self.name_exp}.json')
        self.load(savefile)
    
    
    def save(self, savename):
        game_info = {
            "valuation": self.valuation,
        }
        return super().save(savename, game_info)


    def load(self, file, attribute=None, metric_list='ALL'):
        super().load(file)
        
        if metric_list == 'ALL':
            players_list = self.players
        else:
            players_list = [player for player in self.players if getattr(player, attribute, None) in metric_list]
        
        # self.graphical_analysis(players_list)
        # self.statistic_analysis(players_list)