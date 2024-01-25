"""
Author: Eric John LI (ejli@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json
from random import randint
import matplotlib as mpl
from server import *
from math import log, ceil

class PublicGoods(GameServer):
    def __init__(self, player_num, tokens, ratio, version, name_exp='public_goods', token_initialization = "random", reset = False, round_id=0, rand_min = 11, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'public_goods', models, version)
        self.version = version
        self.name_exp = name_exp
        self.tokens = tokens
        self.ratio = ratio
        self.token_initialization = token_initialization
        self.reset = reset
        self.rand_min = rand_min
    
    def compute_result(self, responses):
        total_tokens = sum(responses)
        record = {
            "responses": responses,
            "total_tokens": total_tokens,
        }
        self.round_records.append(record)
        return record
        

    def report_result(self, round_record):
        total_tokens = round_record["total_tokens"]
        player_tokens_list = []
        for player in self.players:
            player_contributed_tokens = player.records[-1]
            player_total_tokens = round(player.tokens[-1] - player_contributed_tokens + total_tokens * self.ratio/self.player_num, 2)
            player_tokens_list.append(player_total_tokens)
            # print(f"Reset?{self.reset}\nplayer_total_tokens{player_total_tokens}\nplayer tokens{player.tokens[-1]}")
            player_util = player.tokens[-1] - player_contributed_tokens 
            if self.reset:
                player.tokens.append(self.tokens)
            else: 
                player.tokens.append(player_total_tokens)
            player.utility.append(player_util)
            
        for index, player in enumerate(self.players):
            report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
            report_list = [self.round_id, player.records[-1], self.round_records[-1]['responses'], player_tokens_list,total_tokens, round(total_tokens * self.ratio/self.player_num, 2), player_tokens_list[index]]
            report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
        return


    def graphical_analysis(self, players_list):
        # plt.figure(figsize=(30, 20)) 
        # Choice Analysis
        os.makedirs("figures", exist_ok=True)
        round_numbers = [str(i) for i in range(1, self.round_id+1)]
        player_color =  ['#e6194B', '#42d4f4', '#ffe119', '#3cb44b', '#f032e6', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3', '#000075', '#a9a9a9', '#000000']
        markers = ['o', 's', 'p', 'h', 'd', 'o', 's', 'p', 'h', 'd']
        # for player in players_list:
        #     player_records = [player.records[i] for i in range(len(round_numbers))]
        #     player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
        # User tokens Tendency
        
        # for index, player in enumerate(players_list):
        #     player_utility = [sum(player.utility[:i+1]) for i in range(len(round_numbers))]
        #     plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        #     for i, utility in enumerate(player_utility):
        #         plt.annotate(str(utility), (round_numbers[i], utility), textcoords="offset points", xytext=(0,10), ha='center', color=player_color[index])
        # plt.title(f'Public Goods Game (tokens = {self.tokens})')
        # plt.xlabel('Round')
        # plt.ylabel('Revenue')
        # plt.legend()
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}-revenue-{self.version}.png', dpi=300)
        # plt.clf()

        # Player Current Tokens
        # for index, player in enumerate(players_list):
        #     player_tokens = player.tokens[1:]  # Skip the initial tokens
        #     plt.plot(round_numbers, player_tokens, marker='x', color=player_color[index], label=f'{player.id}')
        #     for i, tokens in enumerate(player_tokens):
        #         plt.annotate(str(tokens), (round_numbers[i], tokens), textcoords="offset points", xytext=(0,10), ha='center', color=player_color[index])
        # plt.axhline(y=self.tokens, color='r', linestyle='--', label='Initial Tokens')
        # plt.title(f'Public Goods Game (tokens = {self.tokens})')
        # plt.xlabel('Round')
        # plt.ylabel('Current Tokens')
        # plt.legend()
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}-current-tokens-{self.version}.png', dpi=300)
        # plt.clf()
        
        os.makedirs(f"figures/{self.name_exp}_{self.version}_{self.token_initialization}_R={self.ratio}_reset={self.reset}", exist_ok=True)
        # Individual Donations and Total Donations
        total_donations_list = [r["total_tokens"] for r in self.round_records]
        # for index, player in enumerate(players_list):
        #     player_donations = [record for record in player.records]
        #     plt.plot(round_numbers, player_donations, marker='x', color=player_color[index], label=f'{player.id} Donations')
        #     for i, donation in enumerate(player_donations):
        #         plt.annotate(str(donation), (round_numbers[i], donation), textcoords="offset points", xytext=(0,10), ha='center', color=player_color[index])
        # plt.plot(round_numbers, total_donations_list, marker='o', color='k', linestyle='--', label='Total Donations')
        # for i, total_donation in enumerate(total_donations_list):
        #     plt.annotate(str(total_donation), (round_numbers[i], total_donation), textcoords="offset points", xytext=(0,10), ha='center', color='k')
        # plt.title(f'Public Goods Game (tokens = {self.tokens})')
        # plt.xlabel('Round')
        # plt.ylabel('Contributed Tokens')
        # plt.legend()
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}_{self.version}/{self.name_exp}_contribution.png', dpi=300)
        # plt.clf()


        # # Set the default font size
        # mpl.rcParams['font.size'] = 40  # You can adjust this value as needed    
        # # Initialize a dictionary to keep track of the vertical offsets for each point
        # max_donation = 0
        # if self.reset:
        #     offset = 0.5
        # else:
        #     offset = 0.05
        # for index, player in enumerate(players_list):
        #     player_donations = [record for record in player.records]
        #     for donation in player_donations:
        #         if donation >= max_donation:
        #             max_donation = donation
        #     adjusted_donations = []
        #     player_id = int(player.id.split("_")[1])
        #     for i, donation in enumerate(player_donations):
        #         # Count the occurrences of each point and adjust the offset
        #         # if point not in point_offsets:
        #         point_offsets = player_id
        #         # Calculate the adjusted y-coordinate for both the point and its annotation
        #         if not self.reset:
        #             adjusted_donation = log(donation + 1, 10) + point_offsets / self.player_num * offset
        #         else:
        #             adjusted_donation = donation + point_offsets * offset  # Adjust by 0.1 or any small value
        #         adjusted_donations.append(adjusted_donation)
        #         # Annotate at the adjusted point
        #         plt.annotate(str(donation), (round_numbers[i], adjusted_donation), 
        #                     textcoords="offset points", xytext=(-40, -15), 
        #                     ha='center', color=player_color[index], fontsize=35)
        #     # Plot the adjusted point
        #     plt.plot(round_numbers, adjusted_donations, marker=markers[index], color=player_color[index], label=f'{player.id} Donations', markeredgewidth=5, linewidth=5, markerfacecolor='none', markersize=20)
        # # clear the offset for another 

        # # Plot and annotate total donations similarly
        # # plt.plot(round_numbers, total_donations_list, marker='o', color='k', linestyle='--', label='Total Donations')
        # # for i, total_donation in enumerate(total_donations_list):
        # #     plt.annotate(str(total_donation), (round_numbers[i], total_donation), 
        # #                 textcoords="offset points", xytext=(0, -10), 
        # #                 ha='center', color='k')

        # plt.title(f'Public Goods Game (tokens = {self.tokens})')
        # plt.xlabel('Round')
        # plt.ylabel('Contributed Tokens')
        # if not self.reset:
        #     if max_donation == 0:
        #         max_donation = 10
        #     y_ticks = [i for i in range(1, ceil(log(max_donation, 10)) + 1)]
        #     y_tick_labels = [10 ** i for i in range(1, ceil(log(max_donation, 10)) + 1)]
        #     y_ticks = [0] + y_ticks
        #     y_tick_labels = [0] + y_tick_labels
        #     # for y_tick in y_ticks:
        #     #     plt.axhline(y=y_tick, color='lightgray', linestyle='-', linewidth=3)
        #     plt.yticks(y_ticks)
        #     plt.gca().set_yticklabels(y_tick_labels)
        # # plt.legend()
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}_{self.version}/{self.name_exp}_contribution.png', dpi=300)
        # plt.clf()

        # Set the default font size
        # mpl.rcParams['font.size'] = 40  # You can adjust this value as needed    
        # Initialize a dictionary to keep track of the vertical offsets for each point
        max_donation = 0
        for index, player in enumerate(players_list):
            player_donations = [record for record in player.records]
            for donation in player_donations:
                if donation >= max_donation:
                    max_donation = donation
            adjusted_donations = []
            for i, donation in enumerate(player_donations):
                # Count the occurrences of each point and adjust the offset
                # if point not in point_offsets:
                # Calculate the adjusted y-coordinate for both the point and its annotation
                adjusted_donation = donation / player.tokens[i] * 100
                adjusted_donations.append(adjusted_donation)
                # Annotate at the adjusted point
                # plt.annotate(str(donation), (round_numbers[i], adjusted_donation), 
                #             textcoords="offset points", xytext=(-40, -15), 
                #             ha='center', color=player_color[index], fontsize=35)
            # Plot the adjusted point
            # plt.plot(round_numbers, adjusted_donations, marker=markers[index], color=player_color[index], label=f'{player.id} Donations', markeredgewidth=5, linewidth=5, markerfacecolor='none', markersize=20)
            plt.plot(round_numbers, adjusted_donations, marker='x', color=player_color[index], label=f'{player.id} Donations')
        # clear the offset for another 

        # Plot and annotate total donations similarly
        # plt.plot(round_numbers, total_donations_list, marker='o', color='k', linestyle='--', label='Total Donations')
        # for i, total_donation in enumerate(total_donations_list):
        #     plt.annotate(str(total_donation), (round_numbers[i], total_donation), 
        #                 textcoords="offset points", xytext=(0, -10), 
        #                 ha='center', color='k')

        plt.title(f'Contributed Tokens Percentage')
        plt.xlabel('Round')
        plt.ylabel('Contributed Tokens (%)')
        # if not self.reset:
        #     if max_donation == 0:
        #         max_donation = 10
        #     y_ticks = [i for i in range(1, ceil(log(max_donation, 10)) + 1)]
        #     y_tick_labels = [10 ** i for i in range(1, ceil(log(max_donation, 10)) + 1)]
        #     y_ticks = [0] + y_ticks
        #     y_tick_labels = [0] + y_tick_labels
        #     # for y_tick in y_ticks:
        #     #     plt.axhline(y=y_tick, color='lightgray', linestyle='-', linewidth=3)
        #     plt.yticks(y_ticks)
        #     plt.gca().set_yticklabels(y_tick_labels)
        # plt.legend()
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}_{self.version}_{self.token_initialization}_R={self.ratio}_reset={self.reset}/{self.name_exp}_contribution_percentage.png', dpi=300)
        plt.clf()
    
        rankings_over_time = []

        # Calculate rankings for each round
        for i in range(self.round_id):
            if self.reset:
                round_tokens = [player.tokens[i] - player.records[i] + self.round_records[i]['total_tokens'] * self.ratio/self.player_num for player in self.players]  # i+1 to skip the initial tokens
            else:
                round_tokens = [player.tokens[i+1] for player in self.players]
            sorted_indices = [idx for idx, token in sorted(enumerate(round_tokens), key=lambda x: x[1], reverse=True)]
            rankings = [0] * self.player_num
            for rank, idx in enumerate(sorted_indices):
                rankings[idx] = rank + 1
            rankings_over_time.append(rankings)

        # Plot rankings over time
        for player_index, player in enumerate(self.players):
            player_rankings = [round_rankings[player_index] for round_rankings in rankings_over_time]
            plt.plot(round_numbers, player_rankings, marker='x', label=f'{player_index + 1}', color=player_color[player_index])
            # for i, rank in enumerate(player_rankings):
            #     plt.annotate(str(rank), (round_numbers[i], rank), textcoords="offset points", xytext=(0,10), ha='center', color=player_color[int(player.id.split('_')[1])])

        plt.title(f'Ranking Over Time')
        plt.xlabel('Round')
        plt.ylabel('Ranking')
        
        plt.xticks(round_numbers)
        plt.yticks(range(1, self.player_num + 1))

        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.tight_layout()
        # Enable the grid
        # plt.grid(True, which='both', axis='both', linestyle='-', color='k', linewidth=0.5)
        plt.gca().invert_yaxis()  # Invert the y-axis so that the top rank is at the top of the y-axis
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}_{self.version}_{self.token_initialization}_R={self.ratio}_reset={self.reset}/{self.name_exp}_rankings.png', dpi=300)
        plt.clf()

        plt.close()


    def save(self, savename):
        game_info = {
            "tokens": self.tokens,
        }
        return super().save(savename, game_info)

    def save(self, savename, game_info={}):
        save_data = {
            "meta": {
                "name_exp": self.name_exp,
                "player_num": self.player_num,
                **game_info,
                "round_id": self.round_id,
            },
            "round_records": self.round_records,
            "player_data": [],
        }
        
        for player in self.players:
            player_info = {
                "model": player.model,
                "id": player.id,
                "prompt": player.prompt,
                "records": player.records,
                "tokens": player.tokens,
                "utility": player.utility
            }
            save_data["player_data"].append(player_info)
        
        os.makedirs("save", exist_ok=True)
        savepath = f'save/{savename}.json'
        with open(savepath, 'w') as json_file:
            json.dump(save_data, json_file, indent=2)
        return savepath

    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
    

    def start(self, round):
        print(f"Round {round}: ")
        self.round_id = round
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        
        if self.cot:
            output_format = '{"explanation": "<description of your thinking process>", "option": "<tokens>"}' 
        else:
            output_format = '{"option": "<tokens>"}'
        cot_msg = get_cot_prompt(self.cot)
        
        responses = []
        initial_tokens = []

        for player in tqdm(self.players):
            if self.token_initialization == "random":
                if round == 1: 
                    rand_token = randint(self.rand_min, self.tokens)
                    while(rand_token in initial_tokens):
                        rand_token = randint(1, self.tokens + 1)
                    initial_tokens.append(rand_token) 
                    player.tokens.append(rand_token)
            elif self.token_initialization == "fixed":
                rand_token = self.tokens
                if round == 1:
                    initial_tokens.append(rand_token) 
                    player.tokens.append(rand_token)
                if self.reset:
                    player.tokens.append(rand_token)
            request_list = [self.round_id, player.tokens[-1], output_format, cot_msg]
            request_msg = get_prompt(request_file, request_list)
            request_prompt = [{"role": "user", "content": request_msg}]
            # player.prompt = player.prompt + request_prompt
            while True:
                gpt_responses = player.gpt_request(player.prompt + request_prompt)
                try:
                    parsered_responses = json.loads(gpt_responses)
                    parsered_responses = int(parsered_responses["option"])
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
        round_message = f"There will be {self.round_id+rounds} rounds." if rounds > 1 else ""
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        description_list = [self.player_num, self.ratio, round_message]
        super().run(rounds, description_file, description_list)
