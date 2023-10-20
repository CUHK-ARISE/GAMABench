"""
Author: Eric John LI (ejli@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json
from random import seed
from math import log10

from server import *

seed(9)
class BattleRoyale(GameServer):
    def __init__(self, player_num, name_exp='battle_royale', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, models)
        self.name_exp = name_exp
        self.player_info = []
        for player in tqdm(self.players):
            self.player_info.append([player, self.round_to_1_sig_fig(random.uniform(0, 100))])
        self.player_info = sorted(self.player_info, key=lambda x: x[1])
        self.current_player_info = self.player_info[0]
        self.removed_player_info = []

    def round_to_1_sig_fig(self, num):
        if num == 0:
            return 0

        # Determine the scale factor
        scale = 10 ** -int(log10(abs(num)))
        
        # Round the number to 1 significant figure
        return round(num * scale) / scale

    def ordinal(self, num):
        """Return number as ordinal string."""
        num = int(num)
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            # switcher dictionary maps the numbers 1-3 to their respective ordinal suffixes
            # .get() method then applies the default 'th' to numbers outside this range
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return f"{num}{suffix}"


    def player_info_str_print(self):
        player_info_str = ""
        for player, hit_rate in tqdm(self.player_info):
            player_info_str += 'The {} player to shoot: {}, hit rate: {}%.\n'.format(self.ordinal(self.player_info.index([player, hit_rate]) + 1), player.id, hit_rate) + "\n"
        return player_info_str

    def compute_result(self, responses):
        out = False
        player_shot_info = []
        shot = True if responses[-1] !='None' else False
        if shot:
            for player, hit_rate in self.player_info:
                if str(responses[-1]) in player.id:
                    player_shot_info = [player, hit_rate]
                    out = self.out()
                    if out:
                        self.player_info.remove(player_shot_info)
                        self.removed_player_info.append(player.id)
        print(f'test: {player_shot_info}, out:{out}')
        shot_player = player_shot_info[0].id if len(player_shot_info) > 0 else []
        record = {
            "responses": responses,
            "shot_player": shot_player,
            "removed_player_info": self.removed_player_info,
            "shot": shot,
            "out": out
        }
        self.round_records.append(record)
        return record
        
    def out(self):
        return True if random.uniform(0, 100) < self.current_player_info[1] else False

    def report_result(self, round_record):
        report_file = 'prompt_template/battle_royale_report.txt'
        result = ""
        if not round_record["shot"]:
            result = 'did not shoot anyone.'
        else:
            print(f'shot:{round_record["shot"]}, {round_record["shot_player"]}')
            result = 'shot' + str(round_record["shot_player"])
            if round_record["out"]:
                result += "and hit. " + str(round_record['shot_player']) + " was out."
            else:
                result += "but missed."

        report_list = [self.round_id, self.ordinal(self.current_player_info[0].id.split('_')[1]), result, len(self.player_info), self.player_info_str_print()]
        report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]

        self.current_player_info[0].prompt  = self.current_player_info[0].prompt + report_prompt
        # switch to the next player
        try:
            self.current_player_info = self.player_info[self.player_info.index(self.current_player_info) + 1]
        except:
            self.current_player_info = self.player_info[0]
        self.round_id += 1
        return


    def graphical_analysis(self, players_list):
        # Choice Analysis
        # os.makedirs("figures", exist_ok=True)
        # round_numbers = [str(i) for i in range(1, self.round_id+1)]
        # proposed_list = [r["total_tokens"] for r in self.round_records]
        # plt.plot(round_numbers, proposed_list, marker='x', color='b')
        # plt.axhline(y=self.tokens, color='r', linestyle='--', label='tokens')
        # plt.title(f'Public Goods Game (tokens = {self.tokens})')
        # plt.xlabel('Round')
        # plt.ylabel('Total Proposed Amount')
        # # plt.legend()
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}-proposed.png', dpi=300)
        # plt.clf()
        
        # # User tokens Tendency
        # player_color = []
        # for player in players_list:
        #     player_records = [player.records[i] for i in range(len(round_numbers))]
        #     player_color.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))
        #     plt.plot(round_numbers, player_records, marker='x', color=player_color[-1], label=player.id)
        # plt.title(f'Public Goods Game (tokens = {self.tokens})')
        # plt.xlabel('Round')
        # plt.ylabel('Proposed Amount')
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}-individual-proposed.png', dpi=300)
        # plt.clf()
        
        # # Player Revenue / Utility
        # for index, player in enumerate(players_list):
        #     player_utility = [sum(player.utility[:i+1]) for i in range(len(round_numbers))]
        #     plt.plot(round_numbers, player_utility, marker='x', color=player_color[index], label=player.id)
        # plt.title(f'Public Goods Game (tokens = {self.tokens})')
        # plt.xlabel('Round')
        # plt.ylabel('Revenue')
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}-revenue.png', dpi=300)
        # plt.clf()
        return
    
    def save(self, savename):
        game_info = {
            # "player_info": self.player_info
        }
        return super().save(savename, game_info)

    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)

    def start(self, round):
        if len(self.player_info) == 1:
            print(f"The winner is {self.player_info[0][0].id} with a hit rate of {self.player_info[0][1]}%!")
            return
        print(f"Round {round}: ")
        self.round_id = round
        request_file = 'prompt_template/battle_royale_request.txt'
        responses = []
        request_list = [self.round_id, self.current_player_info[1]]
        request_msg = []
        request_msg = get_prompt(request_file, request_list)
        request_prompt = [{"role": "user", "content": request_msg}]
        self.current_player_info[0].prompt = self.current_player_info[0].prompt + request_prompt
        print(f'Player making decision: {self.current_player_info[0].id}')
        while True:
            gpt_responses = self.current_player_info[0].gpt_request(self.current_player_info[0].prompt)
            try:
                parsered_responses = json.loads(gpt_responses)
                parsered_responses = parsered_responses["player to shoot"]
                print(parsered_responses)
                # parsered_responses = 'null' if parsered_responses == 'None' else int(parsered_responses["player to shoot"].split('_')[1]) 
                self.current_player_info[0].records.append(parsered_responses)
                responses.append(parsered_responses)
                self.current_player_info[0].prompt = self.current_player_info[0].prompt + [{"role": "assistant", "content": gpt_responses}]
                break
            except:
                pass
        print(f'responses:{responses}')
        round_record = self.compute_result(responses)
        self.report_result(round_record)     

    def run(self, rounds):
        # Update system prompt (number of round)
        round_message = f"There will be {self.round_id+rounds} rounds." if rounds > 1 else ""
        description_file = 'prompt_template/battle_royale_description.txt'
        player_info_str = self.player_info_str_print()
        print(player_info_str)
        description_list = [self.player_num, player_info_str, self.ordinal(self.player_info.index([self.current_player_info[0], self.current_player_info[1]]) + 1)]
        super().run(rounds, description_file, description_list)