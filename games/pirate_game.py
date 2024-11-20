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
    def __init__(self, player_num=10, gold=100, version="v1", name_exp='pirate_game', round_id=0, models='gpt-3.5-turbo'):
        super().__init__(player_num, round_id, 'pirate_game', models, version)
        self.game_name = 'Pirate'
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

    def compute_score(self):        
        # in analyze, S_P is already calculated in terms of gold = 100 base
        S_P, S_V = self.analyze()
        return (2 * 100 - S_P) / (2 * 100) * 50 + S_V * 50

    def analyze(self):
        L1_distances = []
        correct_actions = 0
        total_actions = 0
        accuracy = []
        for index1, round_record in enumerate(self.round_records):
            current_gold_distribution = round_record["gold_distribution"]
            NE_gold_distribution = self.return_NE_plan(self.player_num - index1, 100)
            L1_distances.append(self.L1_dist(current_gold_distribution, NE_gold_distribution))
            is_proposer = True
            relatively_odd = False
            # print(f"gold distribution: {current_gold_distribution}, len: {len(current_gold_distribution)}")
            for index2 in range(len(current_gold_distribution)):
                if is_proposer:
                    is_proposer = False
                    continue
                
                player_gold = current_gold_distribution[index2]
                # print(player_gold)
                player_records = round_record['responses']
                if player_gold >= 2:
                    if player_records[index2] == 'accept':
                        correct_actions += 1
                elif player_gold == 1 and relatively_odd:
                    if player_records[index2] == 'accept':
                        correct_actions += 1
                elif player_gold == 0:
                    if player_records[index2] == 'reject':
                        correct_actions += 1
                relatively_odd = not relatively_odd
            total_actions += len(current_gold_distribution) - 1
            accuracy.append(correct_actions / total_actions)
            # print(self.models)
            # print(accuracy)
        return np.mean(L1_distances, axis=0), accuracy[-1]

    def report_result(self, gold_distribution):
        count = 0
        report_file = f'prompt_template/{self.prompt_folder}/report_{self.version}.txt'
        accepting_rate = self.accepted / (self.player_num - self.current_round + 1)
        self.accepting_list.append(accepting_rate)
        print(f'accepting list: {self.accepting_list}')
        for player in self.players:
            # for assistant format reply
            result2 = player.records[-1]
            current_player_id = int(player.id.split('_')[1])
            if current_player_id + 1 < self.current_round:
                continue
            player_choice = 'accept' if player.records[-1] == 'accept' else 'reject'
            if accepting_rate >= 0.5:
                majority = 'Equal to or greater'
                self.next_round = False
            else:
                majority = "Less"
                self.next_round = True

            if current_player_id + 1 == self.current_round and not self.next_round:
                result = f'Your plan was accepted. The game ends. You receive {gold_distribution[count]} golds.'
            elif current_player_id + 1 != self.current_round and not self.next_round:
                result = f'The {self.player_id_manipulation(self.current_round)}-th most senior pirate\'s plan was accepted. The game ends. You receive {gold_distribution[count]} golds.'
            elif current_player_id + 1 == self.current_round and self.next_round:
                result = f'Your plan was rejected. You are eliminated from the game and receive nothing.'
                with open(f"records/player_{current_player_id}.txt", 'a') as f:
                    f.write(f"{result}\n====\n")
            else:
                result = f'The {self.player_id_manipulation(self.current_round)}-th most senior pirate was thrown overboard and eliminated from the game. The game continues.'

            report_list = [self.player_id_manipulation(self.current_round), self.current_plan, self.accepted, self.player_num - self.current_round + 1, result2, majority, result]
            # assistant reply format report
            # report_list = [self.player_id_manipulation(self.current_round), self.current_plan, self.accepted, self.player_num - self.current_round + 1, result2, majority, result]
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
        self.plot_proposal()
        return
        
    def plot_proposal(self):
        os.makedirs(f'figures/{self.name_exp}', exist_ok=True)
        player_golds_each_round = defaultdict(list)
        player_golds_each_round_list = defaultdict(list)
        player_color = [self.cstm_color(x, 1, self.player_num) for x in range(1,self.player_num+1)]
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

        plt.title(f'Pirate Game (players = {self.player_num})')
        plt.xlabel('Players')
        plt.ylabel('Gold Distribution')
        plt.xlim(0, self.current_round + 2)
        plt.ylim(0, self.gold + self.gold * 0.01)
        plt.xticks(range(1, self.current_round + 1))
        plt.legend(handles=legend_patches, loc='best')  # 'best' will position it where there's most space
        fig = plt.gcf()
        fig.savefig(f'figures/{self.name_exp}/proposal.svg', dpi=300)
        plt.clf()
        plt.close()

    def L1_dist(self, gold_dis, NE_gold_dis):
        dist = 0
        for i in range(len(gold_dis)):
            dist += abs(gold_dis[i] / self.gold * 100 - NE_gold_dis[i]) 
        return dist
    
    def save(self, savename):
        game_info = {
            "gold": self.gold 
        }
        return super().save(savename, game_info)
    
    def graphical_analysis(self, player_list):
        if self.next_round == False and self.end == True :
            return
        if self.next_round == False:
            self.end = True
        # Data points
        os.makedirs("figures", exist_ok=True)
        os.makedirs(f'figures/{self.name_exp}', exist_ok=True)
        # x_values = np.array([i + 1 for i in range(len(self.accepting_list))])
        # y_values = np.array(self.accepting_list)
        # # Plotting each point
        # plt.plot(x_values, y_values, 'o', color='black')
        # # Adding annotations for each point
        # for x, y in zip(x_values, y_values):
        #     plt.annotate(f'({x:.0f}, {self.round_to_3_sig_fig(y)})',  # Text to display
        #                 (x, y),                  # Position to start the text
        #                 textcoords="offset points",  # Offset (in points)
        #                 xytext=(0,10),            # Distance from text to points (x,y)
        #                 ha='center')              # Horizontal alignment can be left, right or center
        # # Rest of your plot settings
        # plt.title(f'Pirate Game (players = {self.player_num})')
        # plt.xlabel('Senior Pirate turns')
        # plt.ylabel('Accepting Rate')
        # yrange = range(0, 12, 2)
        # yrange = [i / 10 for i in yrange]
        # plt.yticks(yrange)
        # plt.xticks(range(1, len(x_values) + 1))
        # fig = plt.gcf()
        # fig.savefig(f'figures/{self.name_exp}_{self.version}/accepting_rate.svg', dpi=300)
        # plt.clf()
        # plt.close()
        L1_distances = []
        correct_actions = 0
        total_actions = 0
        accuracy = []
        for index1, round_record in enumerate(self.round_records):
            current_gold_distribution = round_record["gold_distribution"]
            NE_gold_distribution = self.return_NE_plan(self.player_num - index1, 100)
            L1_distances.append(self.L1_dist(current_gold_distribution, NE_gold_distribution))
            is_proposer = True
            relatively_odd = False
            round_responses = round_record['responses']
            # print(f"gold distribution: {current_gold_distribution}, len: {len(current_gold_distribution)}")
            for index2, _ in enumerate(round_responses):
                # skip the proposer
                if is_proposer:
                    is_proposer = False
                    continue
                
                player_gold = current_gold_distribution[index2]
                if player_gold >= 2:
                    if round_responses[index2] == 'accept':
                        correct_actions += 1
                elif player_gold == 1 and relatively_odd:
                    if round_responses[index2] == 'accept':
                        correct_actions += 1
                elif player_gold == 0:
                    if round_responses[index2] == 'reject':
                        correct_actions += 1
                relatively_odd = not relatively_odd
                
            total_actions += len(current_gold_distribution) - 1
            accuracy.append(correct_actions / total_actions)
                
        # Create the first plot
        
        fig, ax1 = plt.subplots()
        rounds = [i + 1 for i in range(len(accuracy))]
        rounds2 = [i + 1 + 1 + len(rounds) for i in range(len(accuracy))]
        ax1.plot(rounds, L1_distances, marker='x', color='red', label='L1 distance')
        ax1.tick_params(axis='y')
        plt.axvline(x=len(accuracy) + 1, color='black', linestyle='--')

        # Create a second y-axis for the second dataset
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

 
        ax2.plot(rounds2, accuracy, marker='.',color='blue', label='Accuracy')
        ax2.tick_params(axis='y')
        # Handle legends
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        plt.legend(lines + lines2, labels + labels2, loc='best')

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.xticks([i + 1 for i in range(2 * len(rounds) + 1)], rounds + [''] + rounds)
        plt.title("Accuracy and L1 distance")
        ax1.set_xlabel('rounds')
        ax1.set_ylabel('L1 distance')
        ax2.set_ylabel('Accuracy')  # we already handled the x-label with ax1
        plt.legend()
        plt.savefig(f'figures/{self.name_exp}/AccuracyAndL1.svg', dpi=300)
        plt.clf()
        
        player_color = [self.cstm_color(x, 1, 10) for x in range(1,11)]
        
        fig, ax1 = plt.subplots()
        ax1.set_ylim(bottom=-100, top=200)

        ax2 = ax1.twinx()
        ax2.set_ylim(bottom=-100, top=200)   
        count = 0
        x = np.arange(self.round_id) + 1
        width = 0.15
        # for l1, acc in zip(L1_distances_list, accuracy_list):
        ax1.bar(x, L1_distances, width, color=player_color[count])
        ax2.bar(x, [(-100) * j for j in accuracy], width, color=player_color[count])
        count += 1
        
        ax1.set_xticks(x)
        ax1.set_xticklabels(x)

        ax1.set_yticks([0, 50, 100, 150, 200])

        ax2.set_yticks([0, -50, -100])
        ax2.set_yticklabels(['0.0', '0.5', '1.0'])

        ax1.axhline(y=0, color='black', linestyle='-')
        ax2.axhline(y=0, color='black', linestyle='-')
        # plt.legend()
        plt.savefig(f'figures/{self.name_exp}/L1_acc.svg', dpi=300)
    
        plt.close()
        self.L1 = np.mean(L1_distances,axis=0)
        self.accuracy = accuracy[-1]

    def round_to_3_sig_fig(self, num):
        
        round_to_n = lambda x, n: x if x == 0 else round(x, -int(floor(log10(abs(x)))) + (n - 1))
        
        # Round the number to 3 significant figure
        return round_to_n(num, 3)
    
    def return_NE_plan(self, players, gold):
        num_of_ones = []
        for i in range(players):
            if i % 2 == 0 and i != 0:
                num_of_ones.append(i)
        
        proposal = [0] * players
        for index in num_of_ones:
            proposal[index] = 1
        proposal[0] = gold - len(num_of_ones)
        return proposal
    
    def return_random_proposal(self, players, gold):
        dis = []
        for i in range(players):
            gold_i = random.randint(0, gold)
            dis.append(gold_i)
            gold -= gold_i
        return dis
    
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
        self.round_id = round
        responses = []
        gold_distribution = []
        cot_msg = None
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
                    cot_msg = get_cot_prompt(self.cot)
                    output_format = '{{"explanation": "thinking_process", "proposal": {{"{g_input_0}-th": "g_{g_input_0}", ..., "{g_input_2}-th": "g_{g_input_2}"}}}}'.format(g_input_0=g_input_0, g_input_2=g_input_2, cot_msg=cot_msg)
                else:
                    output_format = f'Please provide your proposal of the golds distributed to each pirate from the you to the {g_input_2}-th most senior in the following JSON format only: {{"proposal": {{"{g_input_0}-th": "g_{g_input_0}", ..., "{g_input_2}-th": "g_{g_input_2}"}}}}'
                request_list2 = [current_player_id + 1, self.gold, output_format]
                request_msg2 = get_prompt(request_file2, request_list2)
                request_prompt2 = [{"role": "user", "content": request_msg2}]
                request_msg = request_msg2
                # player.prompt = player.prompt + request_prompt2
                request_prompt = request_prompt2
            else: 
                request_file1 = f'prompt_template/{self.prompt_folder}/request1_{self.version}.txt'
                
                cot_msg = get_cot_prompt(self.cot)
                if self.cot:
                    output_format = f'{cot_msg} Please provide your thinking process and decision on the current proposal in the following JSON format: {{"explanation": "thinking_process", "decision": "accept_or_reject"}}'
                else:
                    output_format = f'Please only provide your decision on the current proposal in the following JSON format: {{"decision": "accept_or_reject"}}'
                
                request_list1 = [self.current_round, self.current_plan, gold_distribution[current_player_id - self.current_round + 1], output_format]
                request_msg1 = get_prompt(request_file1, request_list1)    
                request_prompt1 = [{"role": "user", "content": request_msg1}]
                request_msg = request_msg1
                request_prompt = request_prompt1
                # player.prompt = player.prompt + request_prompt1
            while True:
                if player.model.startswith("gemini"):
                    player.prompt[-1]['parts'].append(request_msg)
                    gpt_responses = player.request(self.round_id, player.prompt)
                else:
                    gpt_responses = player.request(self.round_id, player.prompt + request_prompt)
                print(f'proposing pirate: {self.current_round}, voting pirate:{current_player_id + 1}')
                print(f'current plan: {self.current_plan}')
                try:
                    gpt_responses = gpt_responses.replace('\\', '')
                except:
                    pass
                # if json format is given as responses as desired
                try:
                    if self.current_round == current_player_id + 1:
                        # Convert to JSON format
                        try:
                            if cot_msg:
                                traget_str = '"explanation"'
                            else: 
                                traget_str = '"proposal"'
                            targetIndex = gpt_responses.rfind(traget_str)
                            json_start_index = gpt_responses.rfind("{", 0, targetIndex)
                            json_end_index = json_start_index + gpt_responses[json_start_index:].rfind('}')
                            gpt_responses = gpt_responses[json_start_index:json_end_index+1]
                        except:
                            pass
                        # print(f'gpt response: {gpt_responses}')
                        parsered_responses = json.loads(gpt_responses)
                        parsered_responses = dict((parsered_responses["proposal"]))
                        # player.records.append(parsered_responses)
                        self.current_plan = parsered_responses
                        # responses.append(parsered_responses)
                        # player.prompt = player.prompt + [{"role": "assistant", "content": gpt_responses}]
                        print(f'current_plan updated: {self.current_plan}')
                        gold_distribution = [int(gold) for gold in list(self.current_plan.values())]
                        if sum(gold_distribution) != self.gold or len(gold_distribution) != self.player_num - self.current_round + 1:
                            continue
                        # player.records.append(gold_distribution)
                        player.records.append('accept')
                        self.accepted += 1
                        responses.append('accept')
                        break
                    else: 
                        try:
                            if cot_msg:
                                traget_str = '"explanation"'
                            else: 
                                traget_str = '"decision"'
                            targetIndex = gpt_responses.rfind(traget_str)
                            json_start_index = gpt_responses.rfind("{", 0, targetIndex)
                            json_end_index = json_start_index + gpt_responses[json_start_index:].rfind('}')
                            gpt_responses= gpt_responses[json_start_index:json_end_index+1]
                        except:
                            pass
                        # print(f'gpt response: {gpt_responses}')
                        parsered_responses = json.loads(gpt_responses)
                        gpt_responses = parsered_responses["decision"]
                        if 'accept' not in gpt_responses and 'Accept' not in gpt_responses and 'reject' not in gpt_responses and 'Reject' not in gpt_responses: 
                            continue
                        elif 'accept' in gpt_responses or 'Accept' in gpt_responses:
                            # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                            gpt_responses = 'accept'
                            self.accepted += 1
                            responses.append('accept')
                            player.records.append('accept')
                        elif 'reject' in gpt_responses or 'Reject' in gpt_responses:
                            # player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                            gpt_responses = 'reject'
                            self.declined += 1
                            responses.append('reject')
                            player.records.append('reject')
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

    def update_system_prompt(self, description_file, role):
        role_msg = get_role_msg(role)
        for player in self.players:
            description_list = [self.player_num, self.gold, int(player.id.split('_')[1]) + 1, role_msg]
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
        # Call the constructor of the base class
        description_file = f'prompt_template/{self.prompt_folder}/description_{self.version}.txt'
        self.update_system_prompt(description_file, role)
        for round_count in range(self.round_id+1, self.round_id+rounds+1):
            self.start(round_count)
            self.save(self.name_exp)
            self.show()
            time.sleep(1)
