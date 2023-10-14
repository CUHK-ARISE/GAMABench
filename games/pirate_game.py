from tqdm import tqdm
import matplotlib.pyplot as plt
from statistics import mean
from ast import literal_eval
import re
import numpy as np
from server import *

class PirateGame(GameServer):
    def __init__(self, player_num, rounds, gold, name_exp='pirate game'):
        # Call the constructor of the base class
        description_file = 'prompt_template/pirate_game_description.txt'
        description_list = [player_num, gold]
        goal = "1. You want to survive.\n2. Given survival, you want to maximize the number of gold coins you receive.\n3. You would prefer to throw another overboard, if all other results would otherwise be equal"
        super().__init__(player_num, rounds, description_file, description_list, goal)
        self.name_exp = name_exp
        self.gold = gold
        self.accepting_list = []
    # def compute_result(self, responses):

    def report_result(self, gold_distribution):
        count = 0
        report_file = 'prompt_template/pirate_game_report.txt'
        accepting_rate = self.accepted / (self.n - self.current_round + 1)
        self.accepting_list.append(accepting_rate)
        for player in self.players:
            current_player_id = int(player.id.split('_')[1])
            if current_player_id + 1 < self.current_round:
                continue
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
                with open(f"records/{player.id}.txt", 'a') as f:
                    f.write(f"{result}\n----\n")
            else:
                result = 'The ' + self.player_id_manipulation(self.current_round) + ' most senior pirate was thrown overboard from the pirate ship and died. The game continues. Your gold is ' + str(gold_distribution[count]) + '.'

            report_list = [self.accepted, self.n - self.current_round + 1, player_choice, majority, result]
            report_prompt = [{"role": "user", "content": self.get_prompt(report_file, report_list)}]
            player.prompt = player.prompt + report_prompt
            count += 1
        self.report_result_graph(gold_distribution)
        return
        
    def report_result_graph(self, gold_distribution):
        count = 0
        labels_added = set()  # To keep track of which labels have been added
        for player in self.players:
            current_player_id = int(player.id.split('_')[1])
            
            # If the player has already been thrown overboard
            if current_player_id + 1 < self.current_round:
                if 'thrown' not in labels_added:
                    plt.plot(current_player_id + 1, 0, 'x', color='grey', label='thrown')  # Plot at y=0 to indicate no gold
                    labels_added.add('thrown')
                else:
                    plt.plot(current_player_id + 1, 0, 'x', color='grey')
            
            # If the player is still in the game
            else:
                color = 'green' if player.records[-1] == 'Yes' else 'red'
                label = 'accept' if color == 'green' and 'accept' not in labels_added else 'reject' if color == 'red' and 'reject' not in labels_added else None
                print
                plt.plot(current_player_id + 1, gold_distribution[count], 'o', color=color, label=label)
                if label:
                    labels_added.add(label)
                count += 1

        plt.title(f'Pirate Game (players = {self.n})')
        plt.xlabel('Players')
        plt.ylabel('Gold Distribution')
        plt.ylim(-10 , self.gold + 10)
        plt.xlim(-1 , self.n + 1)
        plt.legend(loc='best')  # 'best' will position it where there's most space
        fig = plt.gcf()
        fig.savefig(f'{self.name_exp} Voting {self.current_round}.png', dpi=300)
        plt.show()
        plt.clf()

    def graphical_analysis(self):
        # round_numbers = [str(i) for i in range(1, self.rounds+1)]
        # mean_list = [r["mean_ratio"] for r in self.round_records]
        # winning_list = [r["winner"] for r in self.round_records]
        
        # for player in self.players:
        #     plt.plot(round_numbers, player.records, marker='x', color='b')
            
        # for index, winner in enumerate(winning_list):
        #     if index == 0:
        #         plt.plot(index, winner, marker='o', color='g', label='Winner')
        #     else:
        #         plt.plot(index, winner, marker='o', color='g')
                
        plt.plot(np.array([i + 1 for i in range(len(self.accepting_list))]), np.array(self.accepting_list), 'o', color='r')
        plt.title(f'Pirate Game (players = {self.n})')
        plt.xlabel('Senior Pirate turns')
        plt.ylabel('Accepting Rate')
        plt.ylim(0, 1)
        # plt.legend()
        fig = plt.gcf()
        fig.savefig(f'{self.name_exp}.png', dpi=300)
        plt.show()
        plt.clf()
    
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

    def start(self):
        self.next_round = True
        self.current_plan = None
        for round in range(1, self.rounds + 1):
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
                    request_file2 = 'prompt_template/pirate_game_request2.txt'
                    # request_list2 = [self.current_player, self.n, self.gold]
                    request_list2 = [current_player_id + 1, self.n, self.gold]
                    request_msg2 = self.get_prompt(request_file2, request_list2)
                    request_prompt2 = [{"role": "user", "content": request_msg2}]
                    player.prompt = player.prompt + request_prompt2
                else: 
                    request_file1 = 'prompt_template/pirate_game_request1.txt'
                    request_list1 = [self.current_player, self.current_round, self.current_plan]
                    request_msg1 = self.get_prompt(request_file1, request_list1)    
                    request_prompt1 = [{"role": "user", "content": request_msg1}]
                    player.prompt = player.prompt + request_prompt1

                while True:
                    gpt_responses = player.gpt_request(player.prompt)
                    try:
                        if self.current_round == current_player_id + 1:
                            json_str_match = re.search(r'{\s*(?:(?:"[^"]+"|\'[^\']+\')\s*:\s*\d+\s*,?\s*)+}', gpt_responses)
                            if json_str_match:
                                json_str = json_str_match.group(0)
                                # Convert the string to a dictionary
                            player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                            gpt_responses = literal_eval(json_str)
                            self.current_plan = gpt_responses
                            gold_distribution = list(gpt_responses.values())
                            player.records.append('Yes')
                            self.accepted += 1
                            responses.append('Yes')
                            break
                        else: 
                            if 'no' not in gpt_responses and 'No' not in gpt_responses and 'yes' not in gpt_responses and 'Yes' not in gpt_responses: 
                                continue
                            elif 'yes' in gpt_responses or 'Yes' in gpt_responses:
                                player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                                gpt_responses = 'Yes'
                                self.accepted += 1
                                player.records.append('Yes')
                            elif 'no' in gpt_responses or 'No' in gpt_responses:
                                player.prompt = player.prompt + [{"role": "assistant", "content": str(gpt_responses)}]
                                gpt_responses = 'No'
                                self.declined += 1
                                player.records.append('No')
                            responses.append(gpt_responses)
                            break  
                    except:
                        pass
            self.report_result(gold_distribution)
            if not self.next_round:
                self.senior_pirate_turns = self.current_round
                self.add_end_info()
                break
            if self.current_round == self.n:
                self.senior_pirate_turns = self.n
                self.next_round = False
                self.add_end_info()
                break
        self.graphical_analysis()
