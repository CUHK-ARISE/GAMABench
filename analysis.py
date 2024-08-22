import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statistics import mean, stdev
from games import *
from global_functions import *

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
            
        analyzed_games = np.mean(analyzed_games, axis=0)
        self.labels.append(label)
        self.data.append(game)
        self.analyzed.append(list(analyzed_games))
        
        if len(self.data) == 1: self.get_planes(n)
    
    
    def plot(self, index=0, title="", xlabel="Round", ylabel="", ylim=None, loc="upper right", format="svg", savename='merge', hline=None):
        colors = get_colors(len(self.analyzed))
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
    
    