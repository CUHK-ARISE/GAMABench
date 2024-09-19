import time
import os
import json
import copy
import matplotlib.pyplot as plt
import numpy as np

from utils import *
from global_functions import *

# Import LLM settings
from llm_settings.openai_models import *
from llm_settings.gemini_models import *
from llm_settings.deepinfra_models import *

def get_prompt(filename, inputs):
    with open(filename, 'r') as file:
        generated_prompt = file.read().split("<commentblockmarker>###</commentblockmarker>")[1].strip()
    for index, item in enumerate(inputs):
        key = f"!<INPUT {index}>!"
        generated_prompt = generated_prompt.replace(key, str(item))
    if "<part>///</part>" in generated_prompt:
        generated_prompt = [p.strip() for p in generated_prompt.split("<part>///</part>")]
    return generated_prompt


def get_rephrase_prompt(filename, inputs):
    with open(filename, 'r') as file:
        generated_prompt = file.read().split("<commentblockmarker>###</commentblockmarker>")[1].strip()
    for index, item in enumerate(inputs):
        key = f"!<REPHRASE_INPUT {index}>!"
        generated_prompt = generated_prompt.replace(key, str(item))
    return generated_prompt


def get_cot_prompt(cot):
    if cot:
        return " " + get_prompt(f"prompt_template/cot_prompts/cot{cot}.txt", [])
    else:
        return ""
    

def get_role_msg(role):
    if role:
        return " " + get_prompt(f"prompt_template/role_prompts/role{role}.txt", [])
    else:
        return ""


def select_players(player_list, attr_name, metric_list):
    if metric_list == 'ALL':
        return player_list
    else:
        return [player for player in player_list if getattr(player, attr_name, None) in metric_list]


class Player:
    def __init__(self, model, id, prompt, records=None, utility=None, tokens=None, valuation=None):
        self.model = model
        self.id = id
        self.prompt = prompt
        self.records = records if records else []
        self.utility = utility if utility else []
        self.tokens = tokens if tokens else []
        self.valuation = valuation if valuation else []
        
    def request(self, round_id, inputs, request_key="option"):
        if self.model == "user":
            return self.user_request(inputs, request_key)
        
        elif self.model.startswith("specified"):
            return self.specified_request(round_id, request_key)
        
        else:
            return self.gpt_request(inputs)
        
    def user_request(self, outputs, request_key):
        output_str = '\n'.join([prompt["content"] for prompt in outputs])
        response = input(f"{output_str}\nPlease input the answer for {request_key}:")
        response = f'{{"{request_key}": "{response}"}}'
        return response
    
    def specified_request(self, round_id, request_key):
        options = self.model.split("=")[1].split('/')
        option_num = len(options)
        response = options[(round_id - 1) % option_num]
        response = f'{{"{request_key}": "{response}"}}'
        return response


    def gpt_request(self, inputs):
        start_time = time.time()
        while time.time() - start_time < 10:
            
            # OpenAI models
            if self.model.startswith(('gpt-3.5-turbo', 'gpt-4')):
                response = chat(self.model, inputs).strip()
                self.print_prompt(self.id, inputs, response)
                return response
            
            # Gemini models
            elif self.model.startswith('gemini'):
                response = gemini_chat(self.model, inputs).strip()
                self.print_prompt(self.id, inputs, response)
                return response
            
            # Open source models from Deep Infra
            elif self.model.startswith(('meta-llama', 'mistralai', 'Qwen')):
                response = deepinfra_chat(self.model, inputs).strip()
                self.print_prompt(self.id, inputs, response)
                return response
            
            else:
                raise ValueError("The model is not supported or does not exist.")
    
    
    def print_prompt(self, id, inputs, response):
        os.makedirs("records", exist_ok=True)
        with open(f"records/{id}.txt", 'a') as f:
            f.write(f"{inputs}\n----\n")
            f.write(f"{response}\n====\n")
        return


class GameServer:
    def __init__(self, player_num, round_id, prompt_folder, models, version):
        if models.startswith("gemini"):
            default_prompt = [
                {"role": "user", "parts": None}
            ]
        else:
            default_prompt = [
                {"role": "system", "content": ""}
            ]
        self.models = models
        self.round_id = round_id
        self.player_num = player_num
        self.round_records = []
        self.prompt_folder = prompt_folder
        self.version = version
        
        if isinstance(models, str):
            self.players = [Player(models, f"player_{i}", copy.deepcopy(default_prompt)) for i in range(player_num)]
        elif isinstance(models, list):
            self.players = [Player(models[i], f"player_{i}", copy.deepcopy(default_prompt)) for i in range(player_num)]

    def cstm_color(self, x, min_x, max_x):
        # https://matplotlib.org/stable/gallery/color/colormap_reference.html
        # autumn(_r), viridis(_r), plasma, RdBu_r, Paired, coolwarm
        return plt.cm.plasma_r((np.clip(x,min_x,max_x)-min_x)/(max_x - min_x))

    def update_system_prompt(self, description_file, description_list):
        for player in self.players:
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
    
    def save(self, savename, game_info={}):
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
            # Set the records limitation (prevent tokens from exceeding)
            # if player.model.startswith("gemini"):
            #     if self.round_id > 20:
            #         player.prompt[2:][0]["parts"][0] = player.prompt[0]["parts"][0]
            #         player.prompt = player.prompt[2:]
            # else:
            #     if self.round_id > 20:
            #         player.prompt = player.prompt[:1] + player.prompt[2:]
            
            if not player.model.startswith("gemini"):
                if self.round_id > 20:
                    player.prompt = player.prompt[:1] + player.prompt[2:]
            
            player_info = {
                "model": player.model,
                "id": player.id,
                "prompt": player.prompt,
                "records": player.records,
                "utility": player.utility
            }
            save_data["player_data"].append(player_info)
        
        os.makedirs("save", exist_ok=True)
        savepath = f'save/{savename}.json'
        with open(savepath, 'w') as json_file:
            json.dump(save_data, json_file, indent=2)
        return savepath
    
    
    def load(self, round_records, players):
        self.round_records = round_records
        for index, loaded_player in enumerate(players):
            self.players[index] = Player(**loaded_player)            
        return
    
    def run(self, rounds, description_file, description_list):
        self.update_system_prompt(description_file, description_list)

        for round_count in range(self.round_id+1, self.round_id+rounds+1):
            self.start(round_count)
            self.save(self.name_exp)
            self.show()
            time.sleep(1)
