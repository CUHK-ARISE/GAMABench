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
    def __init__(self, player_num=10, valuation_min=0, valuation_max=200, interval=10, version="v1", mode='highest bid', name_exp='sealed_bid_auction', seed=42, round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'sealed_bid_auction', models, version)
        self.game_name = 'Auction'
        self.version = version
        self.mode = mode
        self.name_exp = name_exp
        self.valuation_min = valuation_min
        self.valuation_max = valuation_max
        self.interval = interval
        self.round_valuation = []
        self.seed = seed
    
    def compute_score(self):
        MAX_V = self.valuation_max
        S = np.mean(self.analyze()[1])
        # if self.mode.find('second') != -1:
        #     return 100 - S / MAX_V * 100
        # else:
        return S * 100
        
    def analyze(self):
        # extract all valuations and responses at once
        valuations = np.array([r['valuations'] for r in self.round_records])
        responses = np.array([r['responses'] for r in self.round_records])
        # use adjusted valuations only for the calculation (because only 1 zero would exist)
        differences = valuations - responses
        adjusted_valuations = np.where(valuations == 0, 1, valuations)
        adjusted_differences = differences / adjusted_valuations
        adjusted_differences = np.where(adjusted_differences < 0 , 0, adjusted_differences)
        # assign a score of 0 where the response (bid) is greater than the valuation
        # calculate and return the mean of these scores
        differences_each_round = [np.mean(curr_round_diff) for curr_round_diff in differences]
        adjusted_differences_each_round = [np.mean(curr_round_diff) for curr_round_diff in adjusted_differences]
        return 1, adjusted_differences_each_round
        # return np.mean([(np.array(valuations[i]) - np.array(responses[i])) / np.array(valuations[i]) for i in range(20)])
    
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
        if len(winning_player) > 1:
            winning_player = winning_player[randint(0, len(winning_player) - 1)].id
        else:
            winning_player = winning_player[0].id
        # print(f"bid_winner: {winning_player}, bid_winner_pay: {bid_winner_pay}, responses: {responses}")
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

    def plot_val_bid_diff(self):
        plt.rc('font', size=12)          # controls default text sizes
        plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
        plt.rc('legend', fontsize=8)     # legend fontsize
        plt.rc('figure', titlesize=12)   # fontsize of the figure title
        # make figure directories
        os.makedirs("figures", exist_ok=True)
        os.makedirs(f'figures/sealed_bid_auction', exist_ok=True)
        round_numbers = [i for i in range(1, self.round_id+1)]
        player_color = [self.cstm_color(x, 1, self.player_num) for x in range(1,self.player_num+1)]
        valuations = np.array([r['valuations'] for r in self.round_records])
        responses = np.array([r['responses'] for r in self.round_records])
        # use adjusted valuations only for the calculation (because only 1 zero would exist)
        differences = valuations - responses
        adjusted_valuations = np.where(valuations == 0, 1, valuations)
        adjusted_differences = differences / adjusted_valuations
        adjusted_differences = np.where(adjusted_differences < 0 , 0, adjusted_differences)
        # assign a score of 0 where the response (bid) is greater than the valuation
        # calculate and return the mean of these scores
        differences_each_round = [np.mean(curr_round_diff) for curr_round_diff in differences]
        adjusted_differences_each_round = [np.mean(curr_round_diff) for curr_round_diff in adjusted_differences]        
        plt.plot(round_numbers, adjusted_differences_each_round, color='blue', marker='.')
        plt.xticks([_ for _ in range(1, self.round_id+1) if _ % 2 == 0])

        plt.fill_between(
            round_numbers,
            [y - s for y, s in zip(adjusted_differences_each_round, np.std(np.transpose(adjusted_differences), axis=0))],
            [y + s for y, s in zip(adjusted_differences_each_round, np.std(np.transpose(adjusted_differences), axis=0))],
            alpha=0.2, color='blue'
        )
        plt.savefig(f'figures/sealed_bid_auction/mean_std.svg', dpi=300)
        plt.clf()
        plt.close()
        
        for idx, diff in enumerate(np.transpose(adjusted_differences)):
            plt.plot(round_numbers, diff, color=player_color[idx], marker='.')
            
        # plt.title('Valuation - Bid / ')
        # plt.xlabel('Round')
        # plt.ylabel('Difference')
        # plt.legend()
        plt.savefig(f'figures/sealed_bid_auction/val_bid_diff.svg', dpi=300)
        plt.clf()
        plt.close()
        # # define player colors
        # differences = []
        # # add a line for comparing to Nash Equilibrium    
        # plt.axhline(0, color='black', linestyle='--')
        # plt.xticks([_ for _ in range(1, self.round_id+1) if _ % 2 == 0])
        

        


    def graphical_analysis(self, players_list):
        os.makedirs("figures", exist_ok=True)
        os.makedirs(f'figures/sealed_bid_auction', exist_ok=True)
        # plt.figure(figsize=(15, 10))  # Increase figure size 
        player_color = [self.cstm_color(x, 1, self.player_num) for x in range(1,self.player_num+1)]
        round_numbers = [i for i in range(1, self.round_id+1)]
        
        # User Proposal Tendency
        for index, player in enumerate(players_list):
            player_records = [player.records[i] for i in range(self.round_id)]
            plt.plot(round_numbers, player_records, marker='.', color=player_color[index], label=player.id)
                # plt.plot(round_numbers, player_valuation_records, marker='o', color=player_color[-1], label=player.id)
        plt.title(f'Bid Each Round')
        plt.xlabel('Round')
        plt.ylabel('Bid')
        plt.xticks([_ for _ in range(1, self.round_id+1) if _ % 2 == 0])
        # plt.legend()
        plt.savefig(f'figures/sealed_bid_auction/bid_each_round.svg', dpi=300)
        plt.clf()
        plt.close()
        self.plot_val_bid_diff()
        
    def save(self, savename):
        game_info = {
            "valuation_min": self.valuation_min,
            "valuation_max": self.valuation_max,
            "interval": self.interval,
            "seed": self.seed,
            "mode": self.mode,
        }
        return super().save(savename, game_info)


    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
    

    def start(self, round):
        print(f"Round {round}: ")
        self.round_id = round
        # Fix seed for fair comparison
        random.seed(self.seed)
        self.current_round = round
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        # randomize valuations to players
        self.round_valuation = random.sample(range(self.valuation_min, self.valuation_max + self.interval, self.interval), self.player_num)
        # valuation of item should be randomized here
        responses = []

        for idx, player in enumerate(tqdm(self.players)):
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
                if player.model.startswith("gemini"):
                    player.prompt[-1]['parts'].append(request_msg)
                    gpt_responses = player.request(self.round_id, player.prompt)
                else:
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
