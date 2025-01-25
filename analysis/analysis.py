import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statistics import mean, stdev
from games import *
from global_functions import *
from games.battle_royale import *
from games.sealed_bid_auction import *
from games.pirate_game import *

plt.rc('font', size=12)          # controls default text sizes
plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
plt.rc('legend', fontsize=8)     # legend fontsize
plt.rc('figure', titlesize=12)   # fontsize of the figure title

def cstm_color(x, min_x, max_x):
    # https://matplotlib.org/stable/gallery/color/colormap_reference.html
    # autumn(_r), viridis(_r), plasma, RdBu_r, Paired, coolwarm
    return plt.cm.plasma_r((np.clip(x,min_x,max_x)-min_x)/(max_x - min_x))

def get_colors(n):
    colors = [cstm_color(x, 1, n) for x in range(1,n+1)]
    return colors


def map_to_range(lst, x, y):
    scale_factor = 100 / (y - x)
    mapped_values = [(value - x) * scale_factor for value in lst]
    return mapped_values

def battle_royale_padding(analyzed_games):
    longest_sublist = max(analyzed_games, key=len)
    max_len = len(longest_sublist)
    analyzed_games = [sublist + [np.nan] * (max_len - len(sublist)) for sublist in analyzed_games]
    return analyzed_games

class Analysis:
    def __init__(self, game):
        self.game = game
        self.data = []
        self.files = []
        self.labels = []
        self.analyzed = []
        self.figs = []
        self.axs = []
    
    
    def get_planes(self, n):
        self.figs, self.axs = zip(*[plt.subplots() for _ in range(n)])
        self.round_num = self.data[0].round_id

    
    def add(self, file, label):
        game = load(file, self.game)
        self.data.append(game)
        self.labels.append(label)
        n, analyzed_game = game.analyze()
        self.analyzed.append(analyzed_game)
        if len(self.data) == 1: self.get_planes(n)
            
    
    def add_avg(self, files, label):
        analyzed_games = []
        for file in files:
            game = load(file, self.game)
            n, result = game.analyze()
            analyzed_games.append(result)
        if self.game == BattleRoyale:
            analyzed_games = battle_royale_padding(analyzed_games)
            analyzed_games = np.nanmean(analyzed_games, axis=0)
        elif self.game == SealedBidAuction:
            analyzed_games = [result[0] for result in analyzed_games]
            analyzed_games = np.mean(analyzed_games, axis=0)
        elif self.game == PirateGame:
            pass   
        else:
            analyzed_games = np.mean(analyzed_games, axis=0)
        self.labels.append(label)
        self.data.append(game)
        self.analyzed.append(list(analyzed_games))
        
        if len(self.data) == 1: self.get_planes(n)
    
    
    def plot(self, index=0, title="", xlabel="Round", ylabel="", ylim=None, loc="upper right", format="svg", savename='merge', hline=None):
        colors = get_colors(len(self.analyzed))
        if self.game == PirateGame:
            max_len = max([max([len(t[0]) for t in analyzed]) for analyzed in self.analyzed])

            self.analyzed = [
                [
                    (
                        L1_list + [np.nan] * (max_len - len(L1_list)),
                        accuracy_list + [np.nan] * (max_len - len(accuracy_list))
                    )
                    for L1_list, accuracy_list in analyzed
                ]
                for analyzed in self.analyzed
            ]

            x = np.arange(max_len) + 1
            fig, ax1 = plt.subplots()
            ax1.set_ylim(bottom=-100, top=200)
            
            ax2 = ax1.twinx()
            ax2.set_ylim(bottom=-100, top=200)   
            
            width = 1 / (len(self.analyzed) + 1)
            analyzed = self.analyzed
            
            for i, analysis in enumerate(analyzed):
                L1_list = np.nanmean([t[0] for t in analysis], axis=0)  # Extract L1_list from tuples
                accuracy_list = [t[1] for t in analysis]  # Extract accuracy_list from tuples
                accuracy_list = np.nanmean(accuracy_list, axis=0)
                ax1.bar(
                    x - width / 2 * (5 - 2 * i), 
                    L1_list, 
                    width, 
                    label='L1 Norm', 
                    color=colors[i]
                )
                ax2.bar(
                    x - width / 2 * (5 - 2 * i), 
                    [-100 * j for j in accuracy_list], 
                    width, 
                    label=self.labels[i], 
                    color=colors[i]
                )
            
            ax1.set_xticks(x)
            ax1.set_xticklabels(x)

            ax1.set_yticks([0, 50, 100, 150, 200])

            ax2.set_yticks([0, -50, -100])
            ax2.set_yticklabels(['0.0', '0.5', '1.0'])

            ax1.axhline(y=0, color='black', linestyle='-')
            ax2.axhline(y=0, color='black', linestyle='-')
            plt.legend()
            
        else:
            if self.game == BattleRoyale:
                self.analyzed = battle_royale_padding(self.analyzed)
                self.rounds = [str(i+1) for i in range(len(self.analyzed[0]))]
                self.round_num = len(self.analyzed[0])
            else:
                self.rounds = [str(i+1) for i in range(self.round_num)]
            analyzed = self.analyzed if len(self.axs) == 1 else [r[index] for r in self.analyzed]
            ax, fig = self.axs[index], self.figs[index]
                        
            for j, record in enumerate(analyzed):
                ax.plot(self.rounds, record, marker='.', color=colors[j], label=self.labels[j], zorder=100)
            
            ax.legend(loc=loc).set_zorder(1000)
            ax.set_xticks(ticks=range(1,self.round_num+1,2))
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            
            if hline is not None:
                ax.axhline(y=hline, color='black', linestyle='--', zorder=100)

            if ylim is not None:
                ax.set_ylim(*ylim)
            
            os.makedirs("analyzed", exist_ok=True)
            fig.savefig(f'analyzed/{savename}.{format}', format=format, dpi=300)
    
    