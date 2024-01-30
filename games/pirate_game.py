from tqdm import tqdm
import matplotlib.pyplot as plt
from statistics import mean
from ast import literal_eval
import re
import numpy as np
from server import *
from math import log10, floor
from collections import defaultdict 
import matplotlib.patches as mpatches
class PirateGame(GameServer):
    def __init__(self, player_num, gold, version, name_exp='pirate_game', round_id=0, models='gpt-3.5'):
        super().__init__(player_num, round_id, 'pirate_game', models, version)
        self.version = version
        self.name_exp = name_exp
        self.gold = gold
        self.accepting_list = []
        self.next_round = True
        self.end = False
        self.current_plan = None

    def compute_result(self, responses, gold_distribution):
        record = {
            "gold_distribution": gold_distribution,
            "responses": responses,
        }
        self.round_records.append(record)
        return record

    def report_result(self, gold_distribution):
        count = 0
        report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
        accepting_rate = self.accepted / (self.player_num - self.current_round + 1)
        print(f'accepting rate: {accepting_rate}')
        self.accepting_list.append(accepting_rate)
        print(f'accepting list: {self.accepting_list}')
        for player in self.players:
            # for assistant format reply
            # result2 = player.records[-1]
            current_player_id = int(player.id.split('_')[1])
            if current_player_id + 1 < self.current_round:
                continue
            print(f'player_records: {player.records}')
            player_choice = 'to accept' if player.records[-1] == 'Yes' else 'not to accept'
            if accepting_rate >= 0.5:
                majority = 'Greater or equal to half of the'
                self.next_round = False
            else:
                majority = "Less than half"
                self.next_round = True

            if current_player_id + 1 == self.current_round and not self.next_round:
                result = 'The ' + self.player_id_manipulation(self.current_round) + ' most senior pirate\'s plan was accepted. The game ends. Your gold is ' + str(gold_distribution[count]) + '. ' + 'Congradulations! You won.'
            elif current_player_id + 1 != self.current_round and not self.next_round:
                result = 'The ' + self.player_id_manipulation(self.current_round) + ' most senior pirate\'s plan was accepted. The game ends. Your gold is ' + str(gold_distribution[count]) +  '.'
            elif current_player_id + 1 == self.current_round and self.next_round:
                result = 'The ' + self.player_id_manipulation(self.current_round) + ' most senior pirate\'s plan was rejected. The game ends. Your gold is ' + str(gold_distribution[count]) +  '. ' + 'You died.'
                with open(f"records/player_{current_player_id}.txt", 'a') as f:
                    f.write(f"{result}\n====\n")
            else:
                result = 'The ' + self.player_id_manipulation(self.current_round) + ' most senior pirate was thrown overboard from the pirate ship and died. The game continues. Your gold is ' + str(gold_distribution[count]) + '.'

            report_list = [self.player_id_manipulation(self.current_round), self.current_plan, self.accepted, self.player_num - self.current_round + 1, player_choice, majority, result]
            # assistant reply format report
            # report_list = [self.player_id_manipulation(self.current_round), self.current_plan, self.accepted, self.player_num - self.current_round + 1, result2, majority, result]
            report_prompt = [{"role": "user", "content": get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
            count += 1
        self.report_result_graph()
        return
        
    def report_result_graph(self):
        os.makedirs(f'figures/{self.name_exp}_{self.version}', exist_ok=True)
        player_golds_each_round = defaultdict(list)
        player_golds_each_round_list = defaultdict(list)
        player_color =  ['#e6194B', '#42d4f4', '#ffe119', '#3cb44b', '#f032e6', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3', '#000075', '#a9a9a9', '#000000'] 
        rounds = [i + 1 for i in range(self.current_round)]
        for index1, round_record in enumerate(self.round_records):
            for index2, player in enumerate(self.players):
                current_round_gold_distribution = [0] * index1 + round_record["gold_distribution"]
                player_golds_each_round[index2].append(current_round_gold_distribution[index2])
                player_golds_each_round_list[index1].append(current_round_gold_distribution[index2])

        for index2, player in enumerate(self.players):
            bottom_start = np.sum([player_golds_each_round[i] for i in range(index2 + 1, len(player_golds_each_round))], axis=0)
            plt.bar(rounds, player_golds_each_round[index2], color=player_color[index2], edgecolor='black', bottom=bottom_start)
        # Add labels here, outside the inner loop
        legend_patches = [mpatches.Patch(color=player_color[index], label=f"Rank {index + 1}") for index, player in enumerate(self.players)]

        # count = 0
        # labels_added = set()  # To keep track of which labels have been added
        # for player in self.players:
        #     current_player_id = int(player.id.split('_')[1])
            
        #     # If the player has already been thrown overboard
        #     if current_player_id + 1 < self.current_round:
        #         if 'thrown' not in labels_added:
        #             plt.plot(current_player_id + 1, 0, 'x', color='grey', label='thrown')  # Plot at y=0 to indicate no gold
        #             labels_added.add('thrown')
        #             # plt.annotate(str(gold_distribution[count]), (current_player_id + 1, gold_distribution[count]),textcoords="offset points",  xytext=(0, 5), ha='center') 
        #         else:
        #             plt.plot(current_player_id + 1, 0, 'x', color='grey')
        #             # plt.annotate(str(gold_distribution[count]), (current_player_id + 1, gold_distribution[count]),textcoords="offset points",  xytext=(0, 5), ha='center') 
        #     # If the player is still in the game
        #     else:
        #         color = 'green' if player.records[-1] == 'Yes' else 'red'
        #         label = 'accept' if color == 'green' and 'accept' not in labels_added else 'reject' if color == 'red' and 'reject' not in labels_added else None
        #         plt.plot(current_player_id + 1, gold_distribution[count], 'o', color=color, label=label)
        #         plt.annotate(str(gold_distribution[count]), (current_player_id + 1, gold_distribution[count]),textcoords="offset points",  xytext=(0, 5), ha='center') 
        #         if current_player_id + 1 == self.current_round and not self.next_round:
        #             plt.plot(current_player_id + 1, gold_distribution[count], 'o', color='orange', label='winner')

        #         if label:
        #             labels_added.add(label)
        #         count += 1

        plt.title(f'Pirate Game (players = {self.player_num})')
        plt.xlabel('Players')
        plt.ylabel('Gold Distribution')
        plt.ylim(-10 , self.gold + 10)
        plt.xlim(0 , self.current_round + 4) 
        plt.legend(handles=legend_patches, loc='best')  # 'best' will position it where there's most space
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}_{self.version}/proposal.svg', dpi=300)
        plt.clf()

    def graphical_analysis(self, player_list):
        if self.next_round == False and self.end == True :
            return
        if self.next_round == False:
            self.end = True
        # Data points
        os.makedirs("figures", exist_ok=True)
        os.makedirs(f'figures/{self.name_exp}_{self.version}', exist_ok=True)
        x_values = np.array([i + 1 for i in range(len(self.accepting_list))])
        y_values = np.array(self.accepting_list)
        # Plotting each point
        plt.plot(x_values, y_values, 'o', color='black')
        # Adding annotations for each point
        for x, y in zip(x_values, y_values):
            plt.annotate(f'({x:.0f}, {self.round_to_3_sig_fig(y)})',  # Text to display
                        (x, y),                  # Position to start the text
                        textcoords="offset points",  # Offset (in points)
                        xytext=(0,10),            # Distance from text to points (x,y)
                        ha='center')              # Horizontal alignment can be left, right or center
        # Rest of your plot settings
        plt.title(f'Pirate Game (players = {self.player_num})')
        plt.xlabel('Senior Pirate turns')
        plt.ylabel('Accepting Rate')
        plt.ylim(-.1, 1.1)
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}_{self.version}/accepting_rate.svg', dpi=300)
        plt.clf()

    def round_to_3_sig_fig(self, num):
        
        round_to_n = lambda x, n: x if x == 0 else round(x, -int(floor(log10(abs(x)))) + (n - 1))
        
        # Round the number to 3 significant figure
        return round_to_n(num, 3)
    
    def player_id_manipulation(self, player_id):
        player_id = int(player_id)
        if player_id == 1:
            return str(player_id) + '-st'
        elif player_id == 2:
            return str(player_id) + '-nd'      
        elif player_id == 3:
            return str(player_id) + '-rd' 
        else:
            return str(player_id) + '-th'

    def add_end_info(self):
        # os.makedirs("records", exist_ok=True)
        for player in tqdm(self.players):
            current_player_id = int(player.id.split('_')[1])
            if current_player_id + 1 < self.current_round:
                    continue
            with open(f"records/{player.id}.txt", 'a') as f:
                f.write(f"{player.prompt}\n----\n")
        return

    def show(self, attr_name=None, metric_list='ALL'):
        eligible_players = select_players(self.players, attr_name, metric_list)
        self.graphical_analysis(eligible_players)
        return

    def start(self, round):
        if self.next_round == False:
            return
        # for round in range(1, self.rounds + 1):
        self.accepted = 0
        self.declined = 0
        print(f"Round {round}: ")
        self.current_round = round
        responses = []
        gold_distribution = []
        for player in tqdm(self.players):
            current_player_id = int(player.id.split('_')[1])
            if current_player_id + 1 < self.current_round:
                continue
            self.current_player = self.player_id_manipulation(current_player_id + 1)
            if self.current_round == current_player_id + 1:
                request_file2 = f'prompt_template/{self.prompt_folder}/request2_{self.version}.txt'
                
                g_input_0 = current_player_id + 1
                g_input_2 = self.player_num

                if self.cot:
                    output_format = f'{{"explanation": "<description of your thinking process>", "option": {{"{g_input_0}-th": g_{g_input_0}, ..., "{g_input_2}-th": g_{g_input_2}}}}}'
                else:
                    output_format = f'{{"option": {{"{g_input_0}-th": g_{g_input_0}, ..., "{g_input_2}-th": g_{g_input_2}}}}}'
                    cot_msg = get_cot_prompt(self.cot)
                
                request_list2 = [current_player_id + 1, self.gold, self.player_num, output_format, cot_msg]
                request_msg2 = get_prompt(request_file2, request_list2)
                request_prompt2 = [{"role": "user", "content": request_msg2}]
                # player.prompt = player.prompt + request_prompt2
                request_prompt = request_prompt2
            else: 
                request_file1 = f'prompt_template/{self.prompt_folder}/request1_{self.version}.txt'
                
                if self.cot:
                    output_format = '{"explanation": "<description of your thinking process>", "option": "<answer>"}' 
                else:
                    output_format = '{"option": "<answer>"}'
                cot_msg = get_cot_prompt(self.cot)
                
                request_list1 = [self.current_round, self.current_plan, gold_distribution[current_player_id - self.current_round + 1], output_format, cot_msg]
                request_msg1 = get_prompt(request_file1, request_list1)    
                request_prompt1 = [{"role": "user", "content": request_msg1}]
                request_prompt = request_prompt1
                # player.prompt = player.prompt + request_prompt1
            while True:
                gpt_responses = player.request(self.round_id, player.prompt + request_prompt)
                print(f'proposing pirate: {self.current_round}, voting pirate:{current_player_id + 1}')
                print(f'current plan: {self.current_plan}')
                print(f'gpt response before manipulating: {gpt_responses}')
                # if json format is given as responses as desired
                try:
                    if self.current_round == current_player_id + 1:
                        parsered_responses = json.loads(gpt_responses)
                        parsered_responses = dict((parsered_responses["option"]))
                        # player.records.append(parsered_responses)
                        self.current_plan = parsered_responses
                        # responses.append(parsered_responses)
                        # player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
                        print(f'current_plan updated: {self.current_plan}')
                        gold_distribution = list(self.current_plan.values())
                        if sum(gold_distribution) != 100 or len(gold_distribution) != self.player_num - self.current_round + 1:
                            continue
                        # player.records.append(gold_distribution)
                        print(gold_distribution)
                        player.records.append('Yes')
                        self.accepted += 1
                        responses.append('Yes')
                        break
                    else: 
                        if 'no' not in gpt_responses and 'No' not in gpt_responses and 'yes' not in gpt_responses and 'Yes' not in gpt_responses: 
                            continue
                        elif 'yes' in gpt_responses or 'Yes' in gpt_responses:
                            # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                            gpt_responses = 'Yes'
                            self.accepted += 1
                            responses.append('Yes')
                            player.records.append('Yes')
                        elif 'no' in gpt_responses or 'No' in gpt_responses:
                            # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                            gpt_responses = 'No'
                            self.declined += 1
                            responses.append('No')
                            player.records.append('No')
                        break  
                except:
                    # more detailed explanation is given before json format, use regular expression to extract
                    try:
                        if self.current_round == current_player_id + 1:
                            json_str_match = re.search(r'{\s*(?:(?:"[^"]+"|\'[^\']+\')\s*:\s*\d+\s*,?\s*)+}', gpt_responses)
                            if json_str_match:
                                json_str = json_str_match.group(0)
                            parsered_responses = json.loads(json_str)
                            # player.records.append(parsered_responses)
                            self.current_plan = parsered_responses
                            # responses.append(parsered_responses)
                            # player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
                            print(f'current_plan updated: {self.current_plan}')
                            gold_distribution = list(self.current_plan.values())
                            gold_distribution = list(self.current_plan.values())
                            if sum(gold_distribution) != 100 or len(gold_distribution) != self.player_num - self.current_round + 1:
                                continue
                            print(gold_distribution)
                            player.records.append('Yes')
                            self.accepted += 1
                            responses.append('Yes')
                            break
                        else:
                            if 'no' not in gpt_responses and 'No' not in gpt_responses and 'yes' not in gpt_responses and 'Yes' not in gpt_responses: 
                                continue
                            elif 'yes' in gpt_responses or 'Yes' in gpt_responses:
                                # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                                gpt_responses = 'Yes'
                                self.accepted += 1
                                responses.append('Yes')
                                player.records.append('Yes')
                            elif 'no' in gpt_responses or 'No' in gpt_responses:
                                # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                                gpt_responses = 'No'
                                self.declined += 1
                                responses.append('No')
                                player.records.append('No')
                            break
                    except:
                        pass
                    
            if not self.next_round:
                self.senior_pirate_turns = self.current_round
                self.add_end_info()
                break
            
            if self.current_round == self.player_num:
                self.senior_pirate_turns = self.player_num
                self.next_round = False
                self.add_end_info()
                break
            
        self.compute_result(responses, gold_distribution)
        self.report_result(gold_distribution)
        # self.graphical_analysis()

    def update_system_prompt(self, description_file):
        for player in self.players:
            description_list = [int(player.id.split('_')[1]) + 1, self.player_num, self.gold]
            description_prompt = get_prompt(description_file, description_list)
            for item in player.prompt:
                if item.get("role") == "system":
                    item["content"] = description_prompt
                    break
    
    def run(self, rounds, cot=None):
        self.cot = cot
        # Update system prompt (number of round)
        round_message = f" There will be {self.round_id+rounds} rounds." if rounds > 1 else ""
        # Call the constructor of the base class
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        self.update_system_prompt(description_file)
        for round_count in range(self.round_id+1, self.round_id+rounds+1):
            self.start(round_count)
            self.save(self.name_exp)
            self.show()
            time.sleep(1)