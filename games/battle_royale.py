"""
Author: Eric John LI (ejli@link.cuhk.edu.hk)
"""
from tqdm import tqdm
import matplotlib.pyplot as plt
import json
from random import seed
from math import log10
import numpy as np
from server import *

seed(9)
class BattleRoyale(GameServer):
    def __init__(self, player_num, version, name_exp='battle_royale', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'battle_royale', models, version)
        self.name_exp = name_exp
        self.player_info = []
        print("Initializing players:")
        self.version = version
        for player in tqdm(self.players):
            self.player_info.append([player, self.round_to_1_sig_fig(random.uniform(0, 100))])
        self.player_info = sorted(self.player_info, key=lambda x: x[1])
        self.current_player_info = self.player_info[0]
        self.removed_player_info = []
        self.player_remaining = []
        self.player_colors = {f'{player.id}':plt.cm.viridis(int(player.id.split('_')[1]) / player_num) for player in self.players}
        self.player_removed_info = {}

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
        shot_player = str(responses[-1])
        initial_players= [player_info[0].id for player_info in self.player_info]
        shot = True if responses[-1] !='None' else False
        if shot:
            for player, hit_rate in self.player_info:
                if str(responses[-1]) in player.id:
                    player_shot_info = [player, hit_rate]
                    shot_player = player.id
                    out = self.out()
                    if out:
                        self.player_info.remove(player_shot_info)
                        self.removed_player_info.append(player.id)
                        self.player_removed_info[player.id] = self.round_id
        self.player_remaining.append(len(self.player_info))
        print(f'round_id: {self.round_id}, players left:{len(self.player_info)}')
        print(f'player shot: {shot_player}, out:{out}')
        record = {
            "responses": responses,
            "initial_players": initial_players,
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
        report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
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

        self.current_player_info[0].prompt = self.current_player_info[0].prompt + report_prompt
        # switch to the next player
        # try:
        if self.player_info.index(self.current_player_info) + 1 == self.player_num:
            self.current_player_info = self.player_info[0]
        else:
            self.current_player_info = self.player_info[self.player_info.index(self.current_player_info) + 1]
        # except:
        #     self.current_player_info = self.player_info[0]
        self.current_player_info[0].prompt  = self.current_player_info[0].prompt + report_prompt
        self.round_id += 1

        return


    def graphical_analysis(self, players_list):
        # Choice Analysis
        os.makedirs("figures", exist_ok=True)
        # Number of players over round
        rounds = [i for i in range(1, self.round_id)]
        plt.plot(rounds, self.player_remaining, marker='o')
        plt.title('Number of Players Over Rounds')
        plt.xlabel('Round')
        plt.ylabel('Number of Players Remaining')
        plt.savefig(f'figures/players_over_rounds-{self.version}.png')
        # plt.show()
        plt.clf()

        # Assuming self.round_records, self.players, and other required variables are defined

        graph_iter = {player.id: False for player in self.players}
        player_order = self.round_records[0]['initial_players']
        graph_iter = {player_id: graph_iter[player_id] for player_id in player_order if player_id in graph_iter}
        count = 0
        keys = list(graph_iter.keys())
        rounds = range(1, len(self.round_records) + 1)
        fig, ax = plt.subplots(figsize=(10,6))

        added_labels = set()

        for round_num, record in enumerate(self.round_records, start=1):
            player_id = keys[count]
            count += 1
            if count >= len(keys):
                count = 0
            if round_num > self.player_removed_info.get(player_id, 99999) + 1:
                player_id = keys[count]
                count += 1
            if count >= len(keys):
                count = 0
            x = round_num
            y = int(player_id.split('_')[1])
            
            if not record['shot']:
                label = 'Shot no one'
                if label not in added_labels:
                    ax.scatter(x, y, marker='x', color='black', label=label)
                    added_labels.add(label)
                else:
                    ax.scatter(x, y, marker='x', color='black')
            else:
                color = 'red' if record['out'] else 'green'
                label = 'Shot and hit' if record['out'] else 'Shot and missed'
                if label not in added_labels:
                    ax.scatter(x, y, marker='o', color=color, label=label)
                    added_labels.add(label)
                else:
                    ax.scatter(x, y, marker='o', color=color)
                if record['shot']:
                    player_shot = record['shot_player']
                    ax.text(x, y, f'{player_shot}', fontsize=8, ha='right', va='bottom')


        ax.set_title('Player Decisions Over Rounds')
        ax.set_xlabel('Round')
        ax.set_ylabel('Player ID')
        ax.set_xticks(rounds)
        ax.set_yticks(range(len(self.players)), labels=[player.id for player in self.players])

        # Adjusting the position of the legend to the right
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.tight_layout()
        plt.savefig(f'figures/player_decisions_over_rounds-{self.version}.png', bbox_inches='tight')  # Save the figure with the legend
        # plt.show()
        plt.clf()

    
    def save(self, savename):
        game_info = {
            # "player_info": self.player_info
        }
        return super().save(savename, game_info)

    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        if len(self.player_info) == 1:
            return
        else:
            self.graphical_analysis(eligible_players)

    def start(self, round):
        if len(self.player_info) == 1:
            print(f"The winner is {self.player_info[0][0].id} with a hit rate of {self.player_info[0][1]}%!")
            return
        print(f"Round {round}: ")
        self.round_id = round
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        responses = []
        request_list = [self.current_player_info[0].id ,self.round_id, self.current_player_info[1]]
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
        self.rounds = rounds
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        player_info_str = self.player_info_str_print()
        # description_list = [self.player_num, player_info_str, self.ordinal(self.player_info.index([self.current_player_info[0], self.current_player_info[1]]) + 1)]
        description_list = [self.player_num, player_info_str]
        super().run(rounds, description_file, description_list)