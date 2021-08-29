import numpy as np
import time
import random
import backtrader as bt
import symdata as sd
import multiprocessing
import concurrent.futures
from RS_RSI_Pairs_FIX20 import RS_RSI_Pairs_FIX20


class RS_RSI_Pairs_FIX20_opt(RS_RSI_Pairs_FIX20):
    optimize = True


class ga:
    balance = 1000000  # in Tomans
    input_list = '../../Lists/input_data/pairs.txt'
    data_path = '../../Data/'
    start = '2010-01-01'
    end = '2020-01-01'

    def __init__(self , strategy):
        self.datas = sd.load_cerebro_data(input_list=self.input_list , data_path=self.data_path ,
                                          start=self.start , end=self.end ,
                                          add_fixincome=strategy.add_fixincome)

    def fitness(self , population: list):
        fitness_scores = list()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = executor.map(self.run_strategy , population)
        for result in results:
            fitness_scores.append(result)
        return fitness_scores

    def run_strategy(self , input_settings: list):
        cerebro = bt.Cerebro(cheat_on_open=True , stdstats=True)
        cerebro.addstrategy(strategy=RS_RSI_Pairs_FIX20_opt , **input_settings)

        # load data:
        time1 = time.time()
        for i , d in enumerate(self.datas):
            cerebro.adddata(d[0] , name=d[1])
        time2 = time.time()
        # print('load data time:' , time2 - time1 , 'seconds')

        cerebro.broker.setcash(self.balance * 10)
        cerebro.broker.set_checksubmit(checksubmit=False)
        cerebro.broker.set_coc(coc=True)

        # Add the new commissions scheme
        cerebro.broker.setcommission(0.01)
        cerebro.broker.setcommission(0.0001 , name='FIX_20%')
        time1 = time.time()
        cerebro.run()
        time2 = time.time()
        # print('cerebro.run() time:' , time2 - time1 , 'seconds')
        return int(cerebro.broker.getvalue() / 10)

    @staticmethod
    def mating_highest_probability(population: list , fitness_scores: list):
        fitness_scores_powered = list()
        for i , d in enumerate(fitness_scores):
            fitness_scores_powered.append(d ** 4)
        fitness_sum = sum(fitness_scores_powered)
        fitness_weights = list()
        for i , d in enumerate(fitness_scores_powered):
            fitness_weights.append(d / fitness_sum)

        couples = len(population) // 2
        dna_split_point = len(population[0]) // 2
        new_population = list()
        for i in range(couples):
            parents = np.random.choice(population , 2 , p=fitness_weights)
            # each couple will have 2 children:
            # first child:
            dna1 = dict(list(parents[0].items())[:dna_split_point])
            dna2 = dict(list(parents[1].items())[dna_split_point:])
            new_population.append({**dna1 , **dna2})
            # second child:
            dna3 = dict(list(parents[1].items())[:dna_split_point])
            dna4 = dict(list(parents[0].items())[dna_split_point:])
            new_population.append({**dna3 , **dna4})

        return new_population

    @staticmethod
    def mating_highest_score(population: list , fitness_scores: list):
        highest_score = list(zip(population , fitness_scores))
        highest_score.sort(key=lambda x: x[1] , reverse=True)

        dna_split_point = len(population[0]) // 2
        new_population = list()
        for i in range(0 , len(population) , 2):
            # each couple will have 2 children:
            # first child:
            dna1 = dict(list(population[i].items())[:dna_split_point])
            dna2 = dict(list(population[i + 1].items())[dna_split_point:])
            new_population.append({**dna1 , **dna2})
            # second child:
            dna3 = dict(list(population[i + 1].items())[:dna_split_point])
            dna4 = dict(list(population[i].items())[dna_split_point:])
            new_population.append({**dna3 , **dna4})

        return new_population
