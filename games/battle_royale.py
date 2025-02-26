"""
Author: Eric John LI (ejli@link.cuhk.edu.hk)
"""
import matplotlib.pyplot as plt
import json
from random import seed
import numpy as np
from server import *
import re

seed(9)

class BattleRoyale(GameServer):
    def __init__(self, player_num=10, version='v1', base_hit_rate=35, interval=5, name_exp='battle_royale', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'battle_royale', models, version)
        # save the game parameters
        self.game_name = 'Battle'
        self.base_hit_rate = base_hit_rate
        self.interval = interval
        self.name_exp = name_exp
        self.version = version
        self.player_info = []
        # initialize players
        for index, player in enumerate(self.players):
            # player object contains
            self.player_info.append([player, base_hit_rate + interval * (index)])
        
        """sort the players to make players with lower hit rate shoot first"""
        # self.player_info = sorted(self.player_info, key=lambda x: x[1])
        
        # player with lowest hit rate goes first
        self.current_player_info = self.player_info[0]
        # record the information of removed player, and how many players left 
        self.removed_player_info = []
        self.player_remaining = []
        # boolean for checking whether the game ends or not
        self.end = False



    """Return number as ordinal string"""
    def ordinal(self, num):
        num = int(num)
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            # switcher dictionary maps the numbers 1-3 to their respective ordinal suffixes
            # .get() method then applies the default 'th' to numbers outside this range
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return f"{num}{suffix}"
    
    def player_info_str_print(self):
        players_list = []
        for player, hit_rate in self.player_info:
            player_index = self.player_info.index([player, hit_rate]) + 1
            player_data = {
                f"The {self.ordinal(player_index)} player to shot": player.id,
                "hit_rate": f"{hit_rate}%"
            }
            players_list.append(player_data)

        return json.dumps(players_list, indent=0)

    def compute_result(self, responses):
        """
        action: the action that the current player takes: "shoot", or "miss"
        out: whether the player is out of this game
        player_shot_info: the info of the player shot
        shot_player: the player who got shot
        shot: whether any player is shot    
        """
        action = "shoot"
        out = False
        player_shot_info = []
        shot_player = responses[-1]
        shot = True
        if "-1" in str(shot_player) or shot_player == "null":
            shot = False
            action = "miss"
        initial_players = [[player_info[0].id, player_info[1]] for player_info in self.player_info]
        # when a player is shot
        if shot:
            # find the player that is shot
            for player, hit_rate in self.player_info:
                
                if str(shot_player) in player.id:
                    player_shot_info = [player, hit_rate]
                    shot_player = player.id
                    out = self.out()
                    if out:
                        self.player_info.remove(player_shot_info)
                        self.removed_player_info.append(player.id)
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
            "action": action,
            "out": out
        }
        self.round_records.append(record)
        return record
    
    """determine whether the shooting player successfully hit the shot player or not"""
    def out(self):
        true_or_false = np.random.choice([True, False], p=[self.current_player_info[1] / 100, 1 - self.current_player_info[1] / 100])
        # convert nump.bool_ to python boolean
        return bool(true_or_false)

    """find the next player that should be shooting"""
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
    
    """report the round result"""
    def report_result(self, round_record):
        report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
        report_file2 = f'prompt_template/{self.prompt_folder}/report2_{self.version}.txt'
        result = ""
        result2 = ""
        # handle case of "miss" (shooting no one)
        if round_record["action"] == "miss":
            result = 'intentionally missed the shot.'
            result2 = 'You intentionally missed your shot.'
        # handle the case of "shoot
        else:
            result = f'shot at player_{round_record["shot_player"]}'
            result2 = f'You shot at player_{round_record["shot_player"]}'
            # the case of hitting
            if round_record["out"]:
                result += f' and hit. player_{round_record["shot_player"]} is eliminated from the game.'
                result2 += f' and hit. player_{round_record["shot_player"]} is eliminated from the game.'
            # the case of failing
            else:
                result += " but missed."
                result2 += " but missed."
        report_list = [self.round_id, self.current_player_info[0].id, result, len(self.player_info)]
        """printing round msg for next round request"""
        for i in range(len(self.player_info)):
            if self.player_info[i][0] == self.current_player_info[0]:
                report_list2 = [self.round_id, round_record["action"], round_record["shot_player"], result2, len(self.player_info)]
                report_prompts = get_prompt(report_file2, report_list2)
                gemini_msg = []
                if self.player_info[i][0].model.startswith('gemini'):
                    for k, msg in enumerate(report_prompts):
                        if k == 0:
                            self.player_info[i][0].prompt[-1]['parts'].append(msg)
                        elif k == 1:
                            self.player_info[i][0].prompt.append({'role': 'model', 'parts': [msg]})
                        else:         
                            gemini_msg.append(msg)
                    self.player_info[i][0].prompt.append({'role': 'user', 'parts': gemini_msg})
                else:
                    report_prompts = [
                        {"role": f"{'assistant' if k == 1 else 'user'}", "content": msg}
                        for k, msg in enumerate(report_prompts)
                    ]
                    self.player_info[i][0].prompt = self.player_info[i][0].prompt + report_prompts
            # round reports for all 
            report_msg = get_prompt(report_file, report_list)
            gemini_msg = []
            if self.player_info[i][0].model.startswith('gemini'):
                if self.player_info[i][0].prompt[-1]['role'] == "model":
                    self.player_info[i][0].prompt.append({'role': 'user', 'parts': report_msg})
                else:
                    self.player_info[i][0].prompt[-1]['parts'].append(report_msg)
            else:
                report_prompts = [{"role": "user", "content": report_msg}]
                self.player_info[i][0].prompt = self.player_info[i][0].prompt + report_prompts
                
        # switch to the next player
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

    def compute_score(self):
        S = self.analyze()[1][-1]
        return S * 100
        
    def analyze(self):
        rounds = list(range(1, self.round_id))
        players_list = list(range(1, self.player_num + 1))
        graph_iter = {player_id: False for player_id in players_list}
        player_order = list(reversed([info[0].split("_")[1] for info in self.round_records[0]['initial_players']]))
        player_order = list(reversed(player_order))
        graph_iter = {player_id: graph_iter[player_id] for player_id in player_order if player_id in graph_iter}
        

        added_labels = set()
        counts = []
        temp = 0
        
        for round_num, record in enumerate(self.round_records, start=1):
            x = round_num
            y = record["player_shooting"]
            if record["action"] == "miss":
                label = 'Intentionally miss'
                if label not in added_labels:
                    added_labels.add(label)
            else:
                color = 'red' if record['out'] else 'blue'
                label = 'Shot and hit' if record['out'] else 'Shot and missed'
                if record['shot_player'] != "null":
                    player_shot = int(record['shot_player']) + 1
                    if player_shot in players_list:
                        if players_list[-1] == int(y) + 1:
                            if player_shot == players_list[-2]:
                                temp += 1
                        else:
                            if player_shot == players_list[-1]:
                                temp += 1
                    
                    if color == 'red':
                        players_list.remove(player_shot)
                    
            counts.append(temp)
        
        correct_aims = counts[-1]
        top_hit_rate = [x / y for x, y in zip(counts, rounds)]
        # print(top_hit_rate[-1] == correct_aims/ (len(top_hit_rate)))
        return 1, top_hit_rate


    """graph analysis"""
    def graphical_analysis(self, players_list):
        # Choice Analysis
        os.makedirs("figures", exist_ok=True)
        os.makedirs(f"figures/{self.name_exp}", exist_ok=True)
        # Number of players over round
        rounds = [i for i in range(1, self.round_id)]
        plt.plot(rounds, self.player_remaining, color='blue', marker='.')
        plt.title('Number of Players Over Rounds')
        plt.yticks(range(1, self.player_num + 1))
        plt.xticks([i for i in range(1, self.round_id + 1) if i % 2 == 0])
        plt.xlabel('Round')
        plt.ylabel('Number of Players Remaining')
        plt.savefig(f'figures/{self.name_exp}/players_over_rounds.svg', dpi = 300)
        # plt.show()
        plt.clf()

        # Assuming self.round_records, self.players, and other required variables are defined
        players_list = [i + 1 for i in range(self.player_num)]
        graph_iter = {player.id.split("_")[1]: False for player in self.players}
        player_order = [info[0].split("_")[1] for info in self.round_records[0]['initial_players']]
        player_order = list(reversed(player_order))
        graph_iter = {player_id: graph_iter[player_id] for player_id in player_order if player_id in graph_iter}
        rounds = range(1, len(self.round_records) + 1)
        
        plt.figure()
        # for labeling
        added_labels = set()
        counts = []
        temp = 0
        for round_num, record in enumerate(self.round_records, start=1):
            x = round_num
            y = record["player_shooting"]
            # labeling and plotting for intentional misses
            if record["action"] == "miss":
                label = 'Intentionally miss'
                # avoid redundant labels
                if label not in added_labels:
                    plt.scatter(x, player_order.index(y), marker='x', color='black', label=label)
                    added_labels.add(label)
                else:
                    plt.scatter(x, player_order.index(y), marker='x', color='black')
            else:
                # labeling for shots
                color = 'red' if record['out'] else 'blue'
                label = 'Shot and hit' if record['out'] else 'Shot and missed'
                if record['shot_player'] != "null":
                    player_shot = int(record['shot_player']) + 1
                    # count the highest hit rate player aiming shots
                    if player_shot in players_list:
                        if players_list[-1] == int(y) + 1:
                            if player_shot == players_list[-2]:
                                temp += 1
                        else:
                            if player_shot == players_list[-1]:
                                temp += 1
                    
                    if color == 'red':
                        players_list.remove(player_shot)
                        
                # plotting the shots according to label
                # avoiding redundant labeling in legend
                if label not in added_labels:
                    plt.scatter(x, player_order.index(y), marker='o', color=color, label=label)
                    added_labels.add(label)
                else:
                    plt.scatter(x, player_order.index(y), marker='o', color=color)
                plt.text(x, player_order.index(y) + 0.1, player_shot, fontsize=10, ha='center', va='bottom')
                
            counts.append(temp)

        plt.title('Player Decisions Over Rounds')
        plt.xlabel('Round')
        plt.ylabel('Player ID')
        plt.xticks([i for i in range(1, self.round_id + 1) if i % 2 == 0])
        plt.yticks(range(len(self.players)), labels=[int(player) + 1 for player in player_order])
        # Adjusting the position of the legend to the right
        # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.legend(loc='lower left') 

        plt.tight_layout()
        plt.savefig(f'figures/{self.name_exp}/player_decisions_over_rounds.svg', bbox_inches='tight', dpi=300)   
        # plt.show()
        plt.clf()
        
        self.correct_aim = counts[-1]
        top_hit_rate = [x / y for x, y in zip(counts, rounds)]
        plt.plot(rounds, top_hit_rate, marker='.', color='blue')
        plt.xticks([i for i in range(1, self.round_id + 1) if i % 2 == 0])
        plt.ylim(-0.05, 1.05)
        plt.title("Rate of Aiming Highest Hit Rate Player")
        plt.xlabel("Round")
        plt.ylabel("Hit Rate (0-1)")
        plt.savefig(f'figures/{self.name_exp}/Highest Hit Aiming Rate.svg', dpi=300)
        plt.clf()
        plt.close()
    
    def save(self, savename):
        game_info = {
            "base_hit_rate": self.base_hit_rate,
            "interval": self.interval
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
        cot_msg = get_cot_prompt(self.cot)
        if self.cot:
            output_format = f'{cot_msg} Please provide your thinking process and action in the following JSON format: {{"explanation": "thinking_process", "action": "shoot_or_miss", "target": "playerID_or_null"}}'
        else:
            output_format = f'Please provide your action in the following JSON format: {{"action": "shoot_or_miss", "target": "playerID_or_null"}}'
        
        responses = []
        request_list = [self.round_id, self.player_info_str_print(), self.current_player_info[0].id, self.current_player_info[1], int(self.player_info.index(self.current_player_info)) + 1, output_format]
        request_msg = []
        request_msg = get_prompt(request_file, request_list)
        request_prompt = [{"role": "user", "content": request_msg}]
        print(f'Player making decision: {self.current_player_info[0].id}')
        while True:
            # deal with gemini
            if self.current_player_info[0].model.startswith("gemini"):
                # print(self.current_player_info[0].prompt[-1]['parts'])
                self.current_player_info[0].prompt[-1]['parts'].append(request_msg)
                gpt_responses = self.current_player_info[0].request(self.round_id, self.current_player_info[0].prompt)
            # deal with others
            else:
                gpt_responses = self.current_player_info[0].request(self.round_id, self.current_player_info[0].prompt + request_prompt)
            try:
                parsered_responses = json.loads(gpt_responses)
                # extract action
                action = parsered_responses["action"]
                # extract target
                parsered_responses = parsered_responses["target"]
                if parsered_responses == None:
                    parsered_responses = "null"
                else:
                    # invalid response handling
                    if parsered_responses == "playerID_or_null":
                        continue
                    try:
                        # try to extract the player_id
                        parsered_responses = parsered_responses.split("_")[1]
                    except:
                        pass
                self.current_player_info[0].records.append(parsered_responses)
                responses.append(parsered_responses)
                break
            # if not in exact required json format, but with extra descriptions
            # regular expressions used to search for json
            except:
                try:
                    action = re.search(r'"action":\s*(\d+|"[^"]+"|null)', gpt_responses)
                    action = action.group(1).strip('"') if action else None
                    # if not (action == "shoot" or action == "miss"):
                    #     continue
                    match = re.search(r'"target":\s*(\d+|"[^"]+"|null)', gpt_responses)
                    # Retrieve the value if the pattern is found
                    parsered_responses = match.group(1).strip('"') if match else None
                    if parsered_responses == None or parsered_responses == "playerID_or_null":
                        continue
                    try:
                        parsered_responses = parsered_responses[1].split("_")[1]                      
                    except:
                        # specifically for gemini output
                        if parsered_responses.find('player') != -1:
                            parsered_responses = parsered_responses.split("_")[1]
                        # manipulate either 'null' or a single digit for 'player' representation
                        elif parsered_responses == 'null' or len(parsered_responses) == 1:
                            parsered_responses = parsered_responses      
                    responses.append(parsered_responses)
                    break
                except:
                    pass
                
        round_record = self.compute_result(responses)
        self.report_result(round_record)    
        self.show()
        if len(self.player_info) == 1 or self.round_id >= self.rounds + 1: 
            print(f"The winner is {self.player_info[0][0].id} with a hit rate of {self.player_info[0][1]}%!")
            print("\n====\n")
            print(f"Score: {self.correct_aim/ (self.round_id - 1) * 100:.2f}")
            self.end = True
            return

    def update_system_prompt(self, description_file, role):
        role_msg = get_role_msg(role)
        for player, hit_rate in self.player_info:
            description_list = [self.player_num, self.player_info_str_print(), player.id, hit_rate, int(player.id.split("_")[1]) + 1, role_msg]
            description_prompt = get_prompt(description_file, description_list)
            if player.model.startswith("gemini"):
                for item in player.prompt:
                    if item.get("role") == "user":
                        item["parts"] = [description_prompt]
                        break
            else:
                for item in player.prompt:
                    if item.get("role") == "system":
                        item["content"] = description_prompt
                        break
                
    def run(self, rounds, cot=None, role=None):
        self.cot = cot
        # Update system prompt (number of round)
        round_message = f"There will be {self.round_id+rounds} rounds." if rounds > 1 else ""
        self.rounds = rounds
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        self.update_system_prompt(description_file, role)
        target_list = []
        for round_count in range(self.round_id+1, self.round_id+rounds+1):
            self.start(round_count)
            self.save(self.name_exp)
            if self.end:
                for record in self.round_records:
                    target_list.append(record['shot_player'])
                return target_list
            time.sleep(1)    
        for record in self.round_records:
            target_list.append(record['shot_player'])
        return target_list