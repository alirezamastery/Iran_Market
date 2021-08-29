import os
import sys  # To find out the script name (in argv[0])

os.chdir(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.abspath('../../Modules'))

import random
import geneticalgo
from RS_RSI_Pairs_FIX20 import RS_RSI_Pairs_FIX20


class RS_RSI_Pairs_FIX20_opt(RS_RSI_Pairs_FIX20):
    optimize = True


inputs = {
    'portfo':           (10 ,) ,
    'ma_period':        range(30 , 300) ,
    'signal_threshold': range(0 , 10) ,
    'fix_ma_period':    range(1 , 300) ,
    'rsi_period':       range(5 , 55) ,
    'rsi_buy_level':    range(60 , 80) ,
    'rsi_sell_level':   range(60 , 80) ,
    'rsi_above_days':   range(0 , 5)
}

population_size = 10

if __name__ == '__main__':
    settings_pool = list()
    for key , value in inputs.items():
        settings_pool.append([x for x in value])

    # create genes of the population:
    population = list()
    for i in range(population_size):
        setting = dict()
        for pair , choice_list in zip(inputs.items() , settings_pool):
            setting[pair[0]] = random.choice(choice_list)
        population.append(setting)

    print('initial population:')
    for i in population:
        print(i)
    num_generations = 10
    ga = geneticalgo.ga(strategy=RS_RSI_Pairs_FIX20_opt)

    # run over generations:
    for generation in range(num_generations):
        print('\nGeneration: ' , generation)
        # Measuring the fitness of each chromosome in the population.
        fitness = ga.fitness(population=population)

        # Selecting the best parents and creating new population from them:
        population = ga.mating_highest_probability(population=population , fitness_scores=fitness)

        print(f'best result for this generation: {max(fitness):,}'.replace(',' , '/'))
        # print('settings for best result:' , population[fitness.index(max(fitness))])
