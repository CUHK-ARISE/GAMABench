from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import openai
import time
import os
import json
import copy
import random
from utils import *
import google.generativeai as genai
import matplotlib.pyplot as plt
import numpy as np
openai.api_key = openai_api_key
genai.configure(api_key=google_api_key)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def chat(
    model,                      # gpt-4, gpt-4-0314, gpt-4-32k, gpt-4-32k-0314, gpt-3.5-turbo, gpt-3.5-turbo-0301
    messages,                   # [{"role": "system"/"user"/"assistant", "content": "Hello!", "name": "example"}]
    temperature=temperature,    # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
    n=1,                        # Chat completion choices to generate for each input message.
    max_tokens=1024,            # The maximum number of tokens to generate in the chat completion.
    delay=delay_time            # Seconds to sleep after each request.
):
    time.sleep(delay)
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
    )
    
    if n == 1:
        return response['choices'][0]['message']['content']
    else:
        return [i['message']['content'] for i in response['choices']]


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion(
    model,                      # text-davinci-003, text-davinci-002, text-curie-001, text-babbage-001, text-ada-001
    prompt,                     # The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.
    temperature=temperature,    # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
    n=1,                        # Completions to generate for each prompt.
    max_tokens=1024,            # The maximum number of tokens to generate in the chat completion.
    delay=delay_time            # Seconds to sleep after each request.
):
    time.sleep(delay)
    
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
    )
    
    if n == 1:
        return response['choices'][0]['text']
    else:
        response = response['choices']
        response.sort(key=lambda x: x['index'])
        return [i['text'] for i in response['choices']]

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def gemini_chat(
    model,                      # gemini-1.0-pro, gemini-1.0-pro-001, gemini-1.0-pro-latest, gemini-1.0-pro-vision-latest, gemini-pro, gemini-pro-vision
    messages,                   # [{'role': 'user', 'parts': "In one sentence, explain how a computer works to a young child."}, {'role': "model', 'parts': "A computer is like a very smart machine that can understand and follow our instructions, help us with our work, and even play games with us!"}
    temperature=temperature,    # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
    n=1,                        # Chat response choices to generate for each input message.
    max_tokens=1024,            # The maximum number of tokens to generate in the chat completion.
    delay=delay_time            # Seconds to sleep after each request.
):
    time.sleep(delay)
    model = genai.GenerativeModel(model)
    response = model.generate_content(
        messages,
        generation_config=genai.types.GenerationConfig(
            # Only one candidate for now.
            candidate_count=n,
            # stop_sequences=['x'],
            max_output_tokens=max_tokens,
            temperature=temperature)
    )   
    
    if n == 1:
        return response.text

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
            if self.model == 'text-davinci-003':
                response = completion(self.model, inputs).strip()
                self.print_prompt(inputs, response)
                return response
            elif self.model.startswith(('gpt-3.5-turbo', 'gpt-4')):
                response = chat(self.model, inputs).strip()
                # Debug use
                # response = f'''{{"option": "{random.randint(0,100)}"}}'''
                # response = '{"option": "yes"}' if random.randint(0,2) < 1 else '{"option": "no"}'
                # response = '{"option": "expensive"}' if random.randint(0,2) < 1 else '{"option": "cheap"}'
                # response = f'''{{"propose": "{random.randint(0,100)}"}}'''
                self.print_prompt(self.id, inputs, response)
                return response
            elif self.model.startswith('gemini'):
                response = gemini_chat(self.model, inputs).strip()
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
