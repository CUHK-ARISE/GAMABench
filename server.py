from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import openai
import time
import os
import json
import random
from utils import *
openai.api_key = openai_api_key

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


def get_prompt(filename, inputs):
    with open(filename, 'r') as file:
        generated_prompt = file.read().split("<commentblockmarker>###</commentblockmarker>")[1].strip()
    for index, item in enumerate(inputs):
        key = f"!<INPUT {index}>!"
        generated_prompt = generated_prompt.replace(key, str(item))
    return generated_prompt


def select_players(player_list, attr_name, metric_list):
    if metric_list == 'ALL':
        return player_list
    else:
        return [player for player in player_list if getattr(player, attr_name, None) in metric_list]


class Player:
    def __init__(self, model, id, prompt, records=None, utility=None):
        self.model = model
        self.id = id
        self.prompt = prompt
        self.records = records if records else []
        self.utility = utility if utility else []
    

    def gpt_request(self, inputs):
        start_time = time.time()
        while time.time() - start_time < 10:
            if self.model == 'text-davinci-003':
                response = completion(self.model, inputs).strip()
                self.print_prompt(inputs, response)
                return response
            elif self.model in ['gpt-3.5-turbo', 'gpt-4']:
                response = chat(self.model, inputs).strip()
                # Debug use
                # response = f'''{{"option": "{random.randint(0,100)}"}}'''
                # response = '{"option": "yes"}' if random.randint(0,2) < 1 else '{"option": "no"}'
                # response = '{"option": "expensive"}' if random.randint(0,2) < 1 else '{"option": "cheap"}'
                # response = f'''{{"propose": "{random.randint(0,100)}"}}'''
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
    def __init__(self, player_num, round_id, models='gpt-3.5-turbo'):
        default_prompt = [
            {"role": "system", "content": ""}
        ]
        self.round_id = round_id
        self.player_num = player_num
        self.round_records = []
        
        if isinstance(models, str):
            self.players = [Player('gpt-3.5-turbo', f"player_{i}", default_prompt) for i in range(player_num)]
        elif isinstance(models, list):
            self.players = [Player(models[i], f"player_{i}", default_prompt) for i in range(player_num)]


    def update_system_prompt(self, description_file, description_list):
        for player in self.players:
            description_prompt = get_prompt(description_file, description_list)
            for item in player.prompt:
                if item.get("role") == "system":
                    item["content"] = description_prompt
                    break
    
    
    def save(self, savename, game_info={}):
        save_data = {
            "meta": {
                "player_num": self.player_num,
                **game_info,
                "round_id": self.round_id,
            },
            "name_exp": self.name_exp,
            "round_records": self.round_records,
            "player_data": [],
        }
        
        for player in self.players:
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
    

    
    