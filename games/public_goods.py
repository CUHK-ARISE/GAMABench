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
    def __init__(self, player_num, tokens, ratio=2, version='v1', name_exp='public_goods', token_initialization = "random", reset = False, round_id=0, rand_min = 11, models='gpt-3.5-turbo'):
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
            report_list = [self.round_id, self.round_records[-1]['responses'], player.records[-1], total_tokens, round(total_tokens * self.ratio/self.player_num - player.records[-1], 2), player_tokens_list[index], player_tokens_list]
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


    def graphical_analysis(self, players_list):
        # plt.figure(figsize=(30, 20)) 
        # Choice Analysis
        os.makedirs("figures", exist_ok=True)
        round_numbers = [i for i in range(1, self.round_id+1)]
        player_color = [self.cstm_color(x, 1, 10) for x in range(1,11)]

        
        os.makedirs(f"figures/{self.name_exp}_{self.version}_{self.token_initialization}_R={self.ratio}_reset={self.reset}", exist_ok=True)
        # Individual Donations and Total Donations
        total_donations_list = [r["total_tokens"] for r in self.round_records]
        max_donation = 0
        donation_list = []
        for index, player in enumerate(players_list):
            player_donations = [record for record in player.records]
            for donation in player_donations:
                if donation >= max_donation:
                    max_donation = donation
            adjusted_donations = []
            for i, donation in enumerate(player_donations):
                adjusted_donation = donation / player.tokens[i] * 100
                adjusted_donations.append(adjusted_donation)
            temp_list = []
            for j, donation in enumerate(player_donations):
                donation_in_terms_of_default = donation / player.tokens[j] * 20
                temp_list.append(donation_in_terms_of_default)
            donation_list.append(temp_list)
            plt.plot(round_numbers, adjusted_donations, marker='.', color=player_color[index], label=f'{player.id} Donations')
        self.temp_score = np.mean(np.mean(donation_list, axis=0), axis=0)
        # clear the offset for another 

        plt.title(f'Contributed Tokens Percentage')
        plt.xlabel('Round')
        plt.ylabel('Contributed Tokens (%)')
        plt.yticks(range(0, 120, 20))
        plt.ylim(-1, 101)
        plt.xticks([_ for _ in range(1, self.round_id+1) if _ % 2 == 0])
        plt.savefig(f'figures/{self.name_exp}_{self.version}_{self.token_initialization}_R={self.ratio}_reset={self.reset}/contribution_percentage.svg', dpi=300)
        plt.clf()
        
        for index, player in enumerate(players_list):
            player_donations = [record for record in player.records]
            for donation in player_donations:
                if donation >= max_donation:
                    max_donation = donation
            adjusted_donations = []
            for i, donation in enumerate(player_donations):
                adjusted_donation = donation
                adjusted_donations.append(adjusted_donation)
            plt.plot(round_numbers, adjusted_donations, marker='.', color=player_color[index], label=f'{player.id} Donations')
        # clear the offset for another 

        plt.title(f'Contributed Tokens')
        plt.xlabel('Round')
        plt.ylabel('Contributed Tokens')
        plt.xticks([_ for _ in range(1, self.round_id+1) if _ % 2 == 0])
        plt.savefig(f'figures/{self.name_exp}_{self.version}_{self.token_initialization}_R={self.ratio}_reset={self.reset}/contribution.svg', dpi=300)
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
            plt.plot(round_numbers, player_rankings, marker='.', label=f'{player_index + 1}', color=player_color[player_index])
            # for i, rank in enumerate(player_rankings):
            #     plt.annotate(str(rank), (round_numbers[i], rank), textcoords="offset points", xytext=(0,10), ha='center', color=player_color[int(player.id.split('_')[1])])

        plt.title(f'Ranking Over Time')
        plt.xlabel('Round')
        plt.ylabel('Ranking')
        
        plt.xticks([_ for _ in range(1, self.round_id+1) if _ % 2 == 0])
        plt.yticks(range(1, self.player_num + 1))

        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.tight_layout()
        # Enable the grid
        # plt.grid(True, which='both', axis='both', linestyle='-', color='k', linewidth=0.5)
        plt.gca().invert_yaxis()  # Invert the y-axis so that the top rank is at the top of the y-axis
        plt.savefig(f'figures/{self.name_exp}_{self.version}_{self.token_initialization}_R={self.ratio}_reset={self.reset}/ranking.svg', dpi=300)
        plt.clf()

        plt.close()


    def save(self, savename):
        game_info = {
            "tokens": self.tokens,
            "ratio": self.ratio,
            "token_initialization": self.token_initialization,
            "reset": self.reset,
            "rand_min": self.rand_min
        }
        return self.save2(savename, game_info)

    def save2(self, savename, game_info={}):
        save_data = {
            "meta": {
                "name_exp": self.name_exp,
                "player_num": self.player_num,
                **game_info,
                "round_id": self.round_id,
                "version": self.version,
                "model": self.models
            },
            "round_records": self.round_records,
            "player_data": [],
        }
        
        for player in self.players:
            # if player.model.startswith("gemini"):
            #     if self.round_id > 10:
            #         player.prompt[2:][0]["parts"][0] = player.prompt[0]["parts"][0]
            #         player.prompt = player.prompt[2:]
            # else:
            #     if self.round_id > 10:
            #         player.prompt = player.prompt[:1] + player.prompt[2:]
            
            if not player.model.startswith("gemini"):
                if self.round_id > 10:
                    player.prompt = player.prompt[:1] + player.prompt[2:]  
                    
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
        
        responses = []
        initial_tokens = []

        for player in tqdm(self.players):
            if self.token_initialization == "random":
                if round == 1: 
                    rand_token = randint(self.rand_min, self.tokens)
                    while(rand_token in initial_tokens):
                        rand_token = randint(self.rand_min, self.tokens + 1)
                    initial_tokens.append(rand_token) 
                    player.tokens.append(rand_token)
            elif self.token_initialization == "fixed":
                rand_token = self.tokens
                if round == 1:
                    initial_tokens.append(rand_token) 
                    player.tokens.append(rand_token)
                if self.reset:
                    player.tokens.append(rand_token)
        
            cot_msg = get_cot_prompt(self.cot)
            if self.cot:
                output_format = f'{cot_msg} Please provide your thinking process and the number of tokens in the following JSON format: {{"explanation": "thinking_process", "tokens_contributed": "integer_between_0_and_{player.tokens[-1]}"}}'
            else:
                output_format = f'Please provide the number of tokens in the following JSON format: {{"tokens_contributed": "integer_between_0_and_{player.tokens[-1]}"}}'
            request_list = [self.round_id, player.tokens[-1], output_format]
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
                    parsered_responses = int(parsered_responses["tokens_contributed"])
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
        role_msg = get_role_msg(role)
        # Update system prompt (number of round)
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        description_list = [self.player_num, self.round_id+rounds, self.ratio, role_msg]
        super().run(rounds, description_file, description_list)
        print("\n====\n")
        print(f"Score: {100 - self.temp_score * 5:.2f}")