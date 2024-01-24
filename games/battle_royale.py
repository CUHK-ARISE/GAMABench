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
import re

seed(9)
class BattleRoyale(GameServer):
    def __init__(self, player_num, version, name_exp='battle_royale', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'battle_royale', models, version)
        self.name_exp = name_exp
        self.player_info = []
        print("Initializing players:")
        self.version = version
        hit_rate = 10
        for index, player in enumerate(self.players):
            self.player_info.append([player, hit_rate * (index + 1)])
        self.player_info = sorted(self.player_info, key=lambda x: x[1])
        self.current_player_info = self.player_info[0]
        self.removed_player_info = []
        self.player_remaining = []
        self.player_colors = {f'{player.id}':plt.cm.viridis(int(player.id.split('_')[1]) / player_num) for player in self.players}
        self.player_removed_info = {}
        self.end = False

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
        # for player, hit_rate in tqdm(self.player_info):
        #     player_info_str += 'The {} player to shoot: {}, hit rate: {}%.\n'.format(self.ordinal(self.player_info.index([player, hit_rate]) + 1), player.id, hit_rate) + "\n"
        # return player_info_str
        players_list = []
        for player, hit_rate in tqdm(self.player_info):
            player_index = self.player_info.index([player, hit_rate]) + 1
            player_data = {
                f"The {self.ordinal(player_index)} player to shot": player.id,
                "hit_rate": f"{hit_rate}%"
            }
            players_list.append(player_data)

        return json.dumps(players_list, indent=0)

    def compute_result(self, responses):
        # self.remove = False
        # self.start_again = False
        out = False
        player_shot_info = []
        shot_player = responses[-1]
        shot = True
        initial_players = [[player_info[0].id, player_info[1]] for player_info in self.player_info]
        if "-1" in str(shot_player):
            shot = False
        if shot:
            for player, hit_rate in self.player_info:
                if shot_player in player.id:
                    player_shot_info = [player, hit_rate]
                    shot_player = player.id
                    out = self.out()
                    if out:
                        self.player_info.remove(player_shot_info)
                        self.removed_player_info.append(player.id)
                        self.player_removed_info[player.id] = self.round_id
                    break
        self.player_remaining.append(len(self.player_info))
        print(f'round_id: {self.round_id}, players left:{len(self.player_info)}')
        print(f'player shot: {shot_player}, out: {out}')
        try:
            shot_player = shot_player.split('_')[1]
        except:
            pass
        record = {
            "responses": responses,
            "player_shooting": self.current_player_info[0].id.split('_')[1],
            "initial_players": initial_players,
            "shot_player": shot_player,
            "removed_player_info": self.removed_player_info,
            "shot": shot,
            "out": out
        }
        self.round_records.append(record)
        return record
        
    def out(self):
        true_or_false = np.random.choice([True, False], p=[self.current_player_info[1] / 100, 1 - self.current_player_info[1] / 100])
        return bool(true_or_false)

    def find_next_in_current_order(self, player_order, current_player_order, current_player_id):
        # Find the index of the current player in player_order
        current_index = player_order.index(current_player_id)
        
        # Loop through player_order starting from the element after current_player_id
        # Use modulo to cycle through the list
        n = len(player_order)
        for i in range(1, n):
            next_index = (current_index + i) % n
            next_player_id = player_order[next_index]
            
            # Check if the next player is in current_player_order
            if next_player_id in current_player_order and "player_" + str(next_player_id) not in self.removed_player_info and next_player_id != self.current_player_info[0]:
                return next_player_id

        # Return None if no suitable player is found
        return None
    
    def report_result(self, round_record):
        report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
        result = ""
        if not round_record["shot"]:
            result = 'intentionally missed his/her shot.'
        else:
            print(f'shot:{round_record["shot"]}, {round_record["shot_player"]}')
            result = 'shot ' + str(round_record["shot_player"])
            if round_record["out"]:
                result += " and hit. " + str(round_record['shot_player']) + " was out."
            else:
                result += "but missed."
        report_list = [self.round_id, self.ordinal(int(self.current_player_info[0].id.split('_')[1]) + 1), result, len(self.player_info)]
        report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]
        for i in range(len(self.player_info)):
            self.player_info[i][0].prompt = self.player_info[i][0].prompt + report_prompt
        # self.current_player_info[0].prompt = self.current_player_info[0].prompt + report_prompt
        # # switch to the next player
        current_player_id = self.current_player_info[0].id
        player_order = [int(player[0].split('_')[1]) for player in self.round_records[0]['initial_players']]
        current_player_order = [int(player[0].id.split('_')[1]) for player in self.player_info]
        current_player_id = int(current_player_id.split('_')[1])
        next_player = self.find_next_in_current_order(player_order, current_player_order, current_player_id)
        for player_info in self.player_info:
            if int(player_info[0].id.split("_")[1]) == next_player:
                self.current_player_info = player_info
                break
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
        plt.savefig(f'figures/players_over_rounds_{self.version}.png', dpi = 300)
        # plt.show()
        plt.clf()

        # Assuming self.round_records, self.players, and other required variables are defined

        graph_iter = {player.id.split("_")[1]: False for player in self.players}
        player_order = [info[0].split("_")[1] for info in self.round_records[0]['initial_players']]
        player_order = list(reversed(player_order))
        # player_order = [player_info[0].id.split('_')[1] for player_info in self.player_info]
        # print(player_order)
        graph_iter = {player_id: graph_iter[player_id] for player_id in player_order if player_id in graph_iter}
        # print(graph_iter)
        rounds = range(1, len(self.round_records) + 1)
        fig, ax = plt.subplots(figsize=(10,6))

        added_labels = set()

        for round_num, record in enumerate(self.round_records, start=1):
            x = round_num
            y = record["player_shooting"]
            if not record['shot']:
                label = 'Intentionally miss'
                if label not in added_labels:
                    ax.scatter(x, player_order.index(y), marker='x', color='black', label=label)
                    added_labels.add(label)
                else:
                    ax.scatter(x, player_order.index(y), marker='x', color='black')
            else:
                color = 'red' if record['out'] else 'green'
                label = 'Shot and hit' if record['out'] else 'Shot and missed'
                if label not in added_labels:
                    ax.scatter(x, player_order.index(y), marker='o', color=color, label=label)
                    added_labels.add(label)
                else:
                    ax.scatter(x, player_order.index(y), marker='o', color=color)
                if record['shot']:
                    if record['shot_player'] == "-1":
                        player_shot = -1
                    else:
                        player_shot = int(record['shot_player']) + 1
                    ax.text(x, player_order.index(y) + 0.1, player_shot, fontsize=10,ha='center', va='bottom')


        ax.set_title('Player Decisions Over Rounds')
        ax.set_xlabel('Round')
        ax.set_ylabel('Player ID')
        ax.set_xticks(rounds)
        ax.set_yticks(range(len(self.players)), labels=[int(player) + 1 for player in player_order])

        # Adjusting the position of the legend to the right
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.tight_layout()
        plt.savefig(f'figures/player_decisions_over_rounds_{self.version}.png', bbox_inches='tight', dpi=300)  # Save the figure with the legend
        # plt.show()
        plt.clf()

    
    def save(self, savename):
        game_info = {
            # "player_info": self.player_info
        }
        return super().save(savename, game_info)

    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)

    def start(self, round):
        if self.end:
            return
        print(f"Round {round}: ")
        self.round_id = round
        request_file = f'prompt_template/{self.prompt_folder}/request_{self.version}.txt'
        
        if self.cot:
            output_format = '{"explanation": "<description of your thinking process>", "option": "<playerid>"}' 
        else:
            output_format = '{"option": "<playerid>"}'
        cot_msg = get_cot_prompt(self.cot)
        
        responses = []
        request_list = [self.round_id, self.player_info_str_print(), self.current_player_info[1], output_format, cot_msg]
        request_msg = []
        request_msg = get_prompt(request_file, request_list)
        request_prompt = [{"role": "user", "content": request_msg}]
        # self.current_player_info[0].prompt = self.current_player_info[0].prompt + request_prompt
        print(f'Player making decision: {self.current_player_info[0].id}')
        while True:
            gpt_responses = self.current_player_info[0].gpt_request(self.current_player_info[0].prompt + request_prompt)
            try:
                parsered_responses = json.loads(gpt_responses)
                try:
                    parsered_responses = parsered_responses["option"].split("_")[1]
                except:
                    parsered_responses = parsered_responses["option"]
                self.current_player_info[0].records.append(parsered_responses)
                responses.append(parsered_responses)
                # self.current_player_info[0].prompt = self.current_player_info[0].prompt + [{"role": "assistant", "content": gpt_responses}]
                break
            except:
                try:
                    match = re.search(r'"option":\s*(\d+|"[^"]+")', gpt_responses)
                    # Retrieve the value if the pattern is found
                    parsered_responses = match.group(1).strip('"') if match else None
                    if parsered_responses is None:
                        continue
                    if parsered_responses == None:
                        continue
                    try:
                        parsered_responses = parsered_responses[1].split("_")[1]
                    except:
                        parsered_responses = parsered_responses[1]
                    self.current_player_info[0].records.append(parsered_responses)
                    responses.append(parsered_responses)
                    break
                except:
                    pass
        print(f'responses:{responses}')
        round_record = self.compute_result(responses)
        self.report_result(round_record)     
        if len(self.player_info) == 1:
            print(f"The winner is {self.player_info[0][0].id} with a hit rate of {self.player_info[0][1]}%!")
            self.end = True
            return
        
    def update_system_prompt(self, description_file):
        for player in self.player_info:
            description_list = [self.player_num, self.player_info_str_print(), self.player_info.index(player) + 1]
            description_prompt = get_prompt(description_file, description_list)
            for item in player[0].prompt:
                if item.get("role") == "system":
                    item["content"] = description_prompt
                    break
                
    def run(self, rounds, cot=None):
        self.cot = cot
        # Update system prompt (number of round)
        round_message = f"There will be {self.round_id+rounds} rounds." if rounds > 1 else ""
        self.rounds = rounds
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        self.update_system_prompt(description_file)
        for round_count in range(self.round_id+1, self.round_id+rounds+1):
            self.start(round_count)
            self.save(self.name_exp)
            self.show()
            time.sleep(1)    