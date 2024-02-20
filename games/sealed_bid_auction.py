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
    def __init__(self, player_num, valuation_min=0, valuation_max=200, interval=10, version="v1", mode = 'second highest bid', name_exp='sealed_bid_auction', seed=42, round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'sealed_bid_auction', models, version)
        self.version = version
        self.mode = mode
        self.name_exp = name_exp
        self.valuation_min = valuation_min
        self.valuation_max = valuation_max
        self.interval = interval
        self.round_valuation = []
        self.seed = seed
        
    def compute_result(self, responses):
        player_utilities = []
        winning_bid = max(responses)
        bid_winner_pay = 0
        # Different modes
        if self.mode == 'second highest bid':
            bid_winner_pay = sorted(list((responses)))[-2]
        elif self.mode == 'highest bid':
            bid_winner_pay = sorted(list(responses))[-1]
        winning_player = [player for player in self.players if player.records[-1] == winning_bid]
        print(winning_player)
        if len(winning_player) > 1:
            winning_player = winning_player[randint(0, len(winning_player) - 1)].id
        else:
            winning_player = winning_player[0].id
        print(f"bid_winner: {winning_player}, bid_winner_pay: {bid_winner_pay}, responses: {responses}") #bid_winner_pay: {bid_winner_pay)
        for player in self.players:
            if player.records[-1] == winning_bid and player.id == winning_player:        
                player_util = player.valuation[-1] - bid_winner_pay
            else:
                player_util = 0
            player.utility.append(player_util)
            player_utilities.append(player_util)
        record = {
            "responses": responses,
            "bid_winner": winning_player,
            "bid_winner_proposed": winning_bid,
            "bid_winner_payment": bid_winner_pay,
            "utility": player_utilities,
            "valuations": self.round_valuation
        }
        
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        for player in self.players:
            player_bid = player.records[-1]
            report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
            result = 'won' if round_record["bid_winner"] == player.id else 'lost'
            report_msg = 'You paid ' + str(round_record["bid_winner_payment"]) + ". " if result == 'won' else ''
            report_list = [self.current_round, player.valuation[-1], player_bid, str(round_record['bid_winner_proposed']), str(round_record["bid_winner_payment"]), result, player.utility[-1]]
            report_prompts = get_prompt(report_file, report_list)
            report_prompts = [
                {"role": f"{'assistant' if i == 1 else 'user'}", "content": msg}
                for i, msg in enumerate(report_prompts)
            ]
            player.prompt = player.prompt + report_prompts
        return

    def plot_v_b(self, players_list):
        os.makedirs("figures", exist_ok=True)
        os.makedirs(f'figures/{self.name_exp}_{self.mode}_{self.version}', exist_ok=True)
        player_color =  ['#e6194B', '#42d4f4', '#ffe119', '#3cb44b', '#f032e6', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3', '#000075', '#a9a9a9', '#000000']
        markers = ['o', 's', 'p', 'h', 'd', 'o', 's', 'p', 'h', 'd']
        round_numbers = [str(i+1) for i in range(self.round_id)]
        for index, player in enumerate(players_list):
            valuations = np.array(player.valuation)
            bids = np.array(player.records)
            differences = valuations - bids
            plt.plot(round_numbers, differences, label=player.id, color=player_color[index], marker='x')
            
            # for i, diff in enumerate(differences):
            #     plt.annotate(player.id, (round_numbers[i], diff), textcoords="offset points", xytext=(0,10), ha='center')

        plt.axhline(0, color='grey', linewidth=0.5, linestyle='--')

        plt.title('Valuation - Bid')
        plt.xlabel('Round')
        plt.ylabel('Difference')
        # plt.legend()
        # plt.grid(True)
        plt.savefig(f'figures/{self.name_exp}_{self.mode}_{self.version}/{self.name_exp}_v-b_plot.svg', dpi=300)
        # plt.show()

    def graphical_analysis(self, players_list):
        os.makedirs("figures", exist_ok=True)
        os.makedirs(f'figures/{self.name_exp}_{self.mode}_{self.version}', exist_ok=True)
        # plt.figure(figsize=(15, 10))  # Increase figure size 
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        player_color =  ['#e6194B', '#42d4f4', '#ffe119', '#3cb44b', '#f032e6', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3', '#000075', '#a9a9a9', '#000000']
        markers = ['o', 's', 'p', 'h', 'd', 'o', 's', 'p', 'h', 'd']
        # Choice Analysis
        
        # User Proposal Tendency
        for index, player in enumerate(players_list):
            player_records = [player.records[i] for i in range(self.round_id)]
            # player_valuation_records = [player.valuation[i] for i in range(self.round_id)]
            # player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
            plt.plot(round_numbers, player_records, marker='x', color=player_color[index], label=player.id)
                # plt.plot(round_numbers, player_valuation_records, marker='o', color=player_color[-1], label=player.id)
        plt.title(f'Bid Each Round')
        plt.xlabel('Round')
        plt.ylabel('Bid')
        # plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}_{self.mode}_{self.version}/{self.name_exp}_bid_each_round.svg', dpi=300)
        plt.clf()
        
        # Player Revenue / Utility
        for index, player in enumerate(players_list):
            player_utility = [player.utility[i] for i in range(self.round_id)]
            plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        plt.title(f'Sealed Bid Auction')
        plt.xlabel('Round')
        plt.ylabel('Utility')
        # plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}_{self.mode}_{self.version}/{self.name_exp}_utility.svg', dpi=300)
        plt.clf()
        self.plot_v_b(players_list)
    
        plt.close()
        
    def save(self, savename):
        game_info = {
            "valuation_min": self.valuation_min,
            "valuation_max": self.valuation_max,
            "interval": self.interval,
            "seed": self.seed
        }
        return super().save(savename, game_info)


    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
    

    def start(self, round):
        print(f"Round {round}: ")
        self.round_id = round
        print(self.seed)
        random.seed(self.seed)
        self.current_round = round
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        self.round_valuation = random.sample(range(self.valuation_min, self.valuation_max + self.interval, self.interval), self.player_num)
        # valuation of item should be randomized here
        responses = []

        for idx, player in enumerate(tqdm(self.players)):
            # rand_valuation = random.choice(range(self.valuation_min, self.valuation_max + self.interval, self.interval))
            # while rand_valuation in self.round_valuation:
            #     rand_valuation = random.choice(range(self.valuation_min, self.valuation_max + self.interval, self.interval))
            # self.round_valuation.append(rand_valuation)
            player.valuation.append(self.round_valuation[idx])

            cot_msg = get_cot_prompt(self.cot)
            if self.cot:
                output_format = f'{cot_msg} Please provide your thinking process and bid in the following JSON format: {{"explanation": "thinking_process", "bid": "integer_between_0_and_{player.valuation[-1]}"}}'
            else:
                output_format = f'Please provide your bid in the following JSON format: {{"bid": "integer_between_0_and_{player.valuation[-1]}"}}'
            request_list = [self.current_round, player.valuation[-1], output_format]
            request_msg = get_prompt(request_file, request_list)
            request_prompt = [{"role": "user", "content": request_msg}]
            # player.prompt = player.prompt + request_prompt
            while True:
                gpt_responses = player.request(self.round_id, player.prompt + request_prompt)
                try:
                    # Find the start of the JSON substring
                    json_start_index = gpt_responses.find('{')
                    json_end_index = gpt_responses.rfind('}')
                    # Extract the JSON substring from the original string
                    gpt_responses = gpt_responses[json_start_index:json_end_index+1]
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = int(parsered_responses["bid"])
                    player.records.append(parsered_responses)
                    responses.append(parsered_responses)
                    # player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
                    break
                except:
                    pass
        round_record = self.compute_result(responses)
        self.report_result(round_record)
        self.seed += 1
        # savefile = self.save(f'{self.name_exp}.json')
        # self.load(savefile)


    def run(self, rounds, cot=None, role=None):
        self.cot = cot
        role_msg = get_role_msg(role)
        # Update system prompt (number of round)
        round_message = f" There will be {rounds} rounds." if rounds > 1 else ""
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        description_list = [self.player_num, self.round_id+rounds, self.mode, role_msg]
        super().run(rounds, description_file, description_list)