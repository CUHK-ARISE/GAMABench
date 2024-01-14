"""
Author: LI, Eric John (ejli@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json
import numpy as np
from random import seed
from random import randint
import random
from server import *

class SealedBidAuction(GameServer):
    def __init__(self, player_num, valuation, version, mode = 'second-highest bid', name_exp='sealed_bid_auction', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'sealed_bid_auction', models, version)
        self.version = version
        self.mode = mode
        self.name_exp = name_exp
        self.valuation = valuation
    
    
    def compute_result(self, responses):
        winning_bid = max(responses)
        bid_winner_pay = 0
        # Different modes
        if self.mode == 'second-highest bid':
            print(self.mode)
            bid_winner_pay = sorted(list(set(responses)))[-2]
        elif self.mode == 'highest bid':
            bid_winner_pay = sorted(list(set(responses)))[-1]
        print(f"bid_winner: {winning_bid}, bid_winner_pay: {bid_winner_pay}, responses: {responses}") #bid_winner_pay: {bid_winner_pay)

        record = {
            "responses": responses,
            "bid_winner_proposed": winning_bid,
            "bid_winner_payment": bid_winner_pay
        }
        
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        for player in self.players:
            player_bid = player.records[-1]
            report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
            if player_bid == round_record['bid_winner']:             
                player_util = player.valuation[-1] - round_record['bid_winner_payment']
            else:
                player_util = player.valuation[-1]
            player.utility.append(player_util)
            result = 'won' if round_record["bid_winner"] == player_bid else 'lost'
            report_msg = 'You pay ' + str(round_record["bid_winner_payment"]) + ". " if result == 'won' else ''
            report_list = [self.current_round, player.valuation[-1], player_bid, result, report_msg, player.valuation[-1] - round_record["bid_winner_payment"]]
            report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    def plot_v_b(self, players_list):
        round_numbers = [str(i+1) for i in range(self.round_id)]
        for player in players_list:
            valuations = np.array(player.valuation)
            bids = np.array(player.records)
            differences = bids - valuations
            plt.plot(round_numbers, differences, label=player.id, marker='o')
            
            for i, diff in enumerate(differences):
                plt.annotate(player.id, (round_numbers[i], diff), textcoords="offset points", xytext=(0,10), ha='center')

        plt.axhline(0, color='black', linewidth=0.5, linestyle='--')

        plt.title('Difference between Bids and Valuations Over Rounds')
        plt.xlabel('Round')
        plt.ylabel('Difference')
        plt.legend()
        # plt.grid(True)
        plt.savefig(f'figures/{self.name_exp}-v-b-plot-{self.mode}-{self.version}.png', dpi=300)
        # plt.show()

    def graphical_analysis(self, players_list):
        plt.figure(figsize=(15, 10))  # Increase figure size 
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        # Choice Analysis
        
        # User Proposal Tendency
        player_color = []
        for player in players_list:
            player_records = [player.records[i] for i in range(len(round_numbers))]
            player_valuation_records = [player.valuation[i] for i in range(len(round_numbers))]
            player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
            plt.plot(round_numbers, player_records, marker='x', color=player_color[-1], label=player.id)
                # plt.plot(round_numbers, player_valuation_records, marker='o', color=player_color[-1], label=player.id)
        plt.title(f'Sealed Bid Auction (valuations = {self.valuation})')
        plt.xlabel('Round')
        plt.ylabel('Bid')
        plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-individual-proposed-{self.mode}-{self.version}.png', dpi=300)
        plt.clf()
        
        # Player Revenue / Utility
        for index, player in enumerate(players_list):
            player_utility = [sum(player.utility[:i+1]) for i in range(len(round_numbers))]
            plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        plt.title(f'Sealed Bid Auction (valuations = {self.valuation})')
        plt.xlabel('Round')
        plt.ylabel('Utility')
        plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}-utility-{self.mode}-{self.version}.png', dpi=300)
        plt.clf()
        
        self.plot_v_b(players_list)
    
        plt.close()
        
    def save(self, savename):
        game_info = {
            "valuation": self.valuation,
        }
        return super().save(savename, game_info)


    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
    

    def start(self, round):
        print(f"Round {round}: ")
        self.round_id = round
        
        self.current_round = round
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        # valuation of item should be randomized here
        responses = []
        round_valuation = []

        for player in tqdm(self.players):
            rand_valuation = randint(0, self.valuation)
            while(rand_valuation in round_valuation):
                rand_valuation = randint(0, self.valuation)
            round_valuation.append(rand_valuation)

            player.valuation.append(rand_valuation)
            request_list = [self.current_round, player.valuation[-1]]
            request_msg = get_prompt(request_file, request_list)
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
        # savefile = self.save(f'{self.name_exp}.json')
        # self.load(savefile)


    def run(self, rounds):
        # Update system prompt (number of round)
        round_message = f" There will be {rounds} rounds." if rounds > 1 else ""
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        description_list = [self.player_num, self.mode, round_message]
        super().run(rounds, description_file, description_list)